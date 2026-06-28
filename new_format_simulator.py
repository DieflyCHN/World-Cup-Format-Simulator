"""
Monte Carlo simulator for the 48-team "three-team, 2-point bridge" format.

The script has three user-facing inputs: number of simulations, number of worker
threads, and an optional random seed. Each simulation performs:
random draw -> bridge group stage -> fixed 32-team bracket -> aggregate odds.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import math
import os
import random

# Elo logistic scale used for winner-takes-all matches.
KNOCKOUT_K = 800

# Per-match form noise. It prevents knockout/penalty outcomes from being purely
# deterministic by rating while keeping stronger teams favored.
KNOCKOUT_FORM_SIGMA = 120

GROUP_WIN_POINTS = 3
GROUP_DRAW_POINTS = 1
BRIDGE_WIN_POINTS = 2


@dataclass(frozen=True)
class Team:
    code: str
    name: str
    rating: int


# Accumulated counts across many simulations. Each worker/batch should build
# its own TeamStats table and merge it later to avoid shared writes.
@dataclass
class TeamStats:
    qualified: int = 0
    round_of_16: int = 0
    quarterfinal: int = 0
    semifinal: int = 0
    final: int = 0
    champion: int = 0


# A single full tournament simulation returns only stage membership, not the
# big aggregate counters. This keeps one simulation independent and parallel-safe.
@dataclass(frozen=True)
class SimulationResult:
    qualified: list[str]
    round_of_16: list[str]
    quarterfinal: list[str]
    semifinal: list[str]
    final: list[str]
    champion: str


# Knockout stages are separated from the full result so the group stage and
# knockout stage can evolve independently.
@dataclass(frozen=True)
class KnockoutResult:
    round_of_16: list[str]
    quarterfinal: list[str]
    semifinal: list[str]
    final: list[str]
    champion: str


@dataclass(frozen=True)
class GroupStageResult:
    qualified: list[str]
    qualifiers_by_slot: dict[str, str]


# Per-team group table row. It stores the fields needed for a realistic first
# ranking pass: points, goal difference, goals for, then fallback tie breakers.
@dataclass
class GroupStanding:
    code: str
    points: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    tie_breaker: float = 0.0

    @property
    def goal_diff(self):
        return self.goals_for - self.goals_against


# New format: 16 three-team groups, paired into eight six-team bridge units.
# Concrete teams are randomly drawn into A1..P3 before each simulation.
GROUP_NAMES = tuple("ABCDEFGHIJKLMNOP")
GROUP_PAIRS = tuple(zip(GROUP_NAMES[::2], GROUP_NAMES[1::2]))
GROUP_SIZE = 3

# Round-of-32 bracket supplied by the format design. Match numbers are local IDs:
# later knockout rounds refer to these winners as W73, W74, etc.
ROUND_OF_32_MATCHES = (
    (73, "A1", "P2"),
    (74, "C1", "N2"),
    (75, "B1", "O2"),
    (76, "D1", "M2"),
    (77, "E1", "L2"),
    (78, "G1", "J2"),
    (79, "F1", "K2"),
    (80, "H1", "I2"),
    (81, "I1", "H2"),
    (82, "K1", "F2"),
    (83, "J1", "G2"),
    (84, "L1", "E2"),
    (85, "M1", "D2"),
    (86, "O1", "B2"),
    (87, "N1", "C2"),
    (88, "P1", "A2"),
)

# Fixed knockout tree after the round of 32. "W89" means the winner of match 89.
KNOCKOUT_MATCHES = (
    (89, "W74", "W77"),
    (90, "W73", "W75"),
    (91, "W76", "W78"),
    (92, "W79", "W80"),
    (93, "W83", "W84"),
    (94, "W81", "W82"),
    (95, "W86", "W88"),
    (96, "W85", "W87"),
    (97, "W89", "W90"),
    (98, "W93", "W94"),
    (99, "W91", "W92"),
    (100, "W95", "W96"),
    (101, "W97", "W98"),
    (102, "W99", "W100"),
    (104, "W101", "W102"),
)

# Initial ratings are approximate Elo-like strengths on a 1200-2200-ish scale.
# They are deliberately easy to tune without touching simulation logic.
teams = {
    "ARG": Team("ARG", "Argentina", 2114),
    "AUS": Team("AUS", "Australia", 1777),
    "AUT": Team("AUT", "Austria", 1830),
    "BEL": Team("BEL", "Belgium", 1893),
    "BIH": Team("BIH", "Bosnia and Herzegovina", 1595),
    "BRA": Team("BRA", "Brazil", 1991),
    "CAN": Team("CAN", "Canada", 1788),
    "CHE": Team("CHE", "Switzerland", 1891),
    "CIV": Team("CIV", "Cote d'Ivoire", 1695),
    "COD": Team("COD", "DR Congo", 1652),
    "COL": Team("COL", "Colombia", 1982),
    "CPV": Team("CPV", "Cape Verde", 1578),
    "CUW": Team("CUW", "Curacao", 1434),
    "CZE": Team("CZE", "Czechia", 1740),
    "DEU": Team("DEU", "Germany", 1932),
    "DZA": Team("DZA", "Algeria", 1760),
    "ECU": Team("ECU", "Ecuador", 1938),
    "EGY": Team("EGY", "Egypt", 1696),
    "ENG": Team("ENG", "England", 2021),
    "ESP": Team("ESP", "Spain", 2157),
    "FRA": Team("FRA", "France", 2063),
    "GHA": Team("GHA", "Ghana", 1510),
    "HRV": Team("HRV", "Croatia", 1911),
    "HTI": Team("HTI", "Haiti", 1548),
    "IRN": Team("IRN", "Iran", 1772),
    "IRQ": Team("IRQ", "Iraq", 1618),
    "JOR": Team("JOR", "Jordan", 1680),
    "JPN": Team("JPN", "Japan", 1906),
    "KOR": Team("KOR", "Korea Republic", 1758),
    "MAR": Team("MAR", "Morocco", 1827),
    "MEX": Team("MEX", "Mexico", 1875),
    "NLD": Team("NLD", "Netherlands", 1948),
    "NOR": Team("NOR", "Norway", 1914),
    "NZL": Team("NZL", "New Zealand", 1562),
    "PAN": Team("PAN", "Panama", 1730),
    "PRT": Team("PRT", "Portugal", 1986),
    "PRY": Team("PRY", "Paraguay", 1833),
    "QAT": Team("QAT", "Qatar", 1421),
    "SAU": Team("SAU", "Saudi Arabia", 1569),
    "SCO": Team("SCO", "Scotland", 1782),
    "SEN": Team("SEN", "Senegal", 1867),
    "SWE": Team("SWE", "Sweden", 1712),
    "TUN": Team("TUN", "Tunisia", 1628),
    "TUR": Team("TUR", "Turkey", 1910),
    "URY": Team("URY", "Uruguay", 1892),
    "USA": Team("USA", "United States", 1726),
    "UZB": Team("UZB", "Uzbekistan", 1714),
    "ZAF": Team("ZAF", "South Africa", 1518),
}


def create_rng(seed=None):
    return random.Random(seed)


def get_rng(rng):
    return rng if rng is not None else random


# Two-result win probability. This is mainly for knockout matches, where extra
# time and penalties are treated as part of the same winner-takes-all outcome.
def win_prob_from_ratings(ra, rb, k=KNOCKOUT_K):
    return 1 / (1 + 10 ** ((rb - ra) / k))


def match_rating(code, rng=None, form_sigma=KNOCKOUT_FORM_SIGMA):
    rng = get_rng(rng)
    return teams[code].rating + rng.gauss(0, form_sigma)


def knockout_win_prob(a, b, rng=None, form_sigma=KNOCKOUT_FORM_SIGMA):
    ra = match_rating(a, rng, form_sigma)
    rb = match_rating(b, rng, form_sigma)
    return win_prob_from_ratings(ra, rb)


# Small standard-library Poisson sampler for goals. It avoids adding numpy while
# keeping score generation close to a common football modeling approach.
def poisson(lam, rng=None):
    rng = get_rng(rng)
    threshold = math.exp(-lam)
    product = 1.0
    goals = 0

    while product > threshold:
        goals += 1
        product *= rng.random()

    return goals - 1


# Convert rating difference into expected goals. `base` controls average scoring,
# `rating_scale` controls how strongly rating gaps affect the scoreline, and
# `min_goals` prevents huge mismatches from making the weaker side impossible.
def expected_goals(a, b, base=1.25, rating_scale=800, min_goals=0.20):
    diff = teams[a].rating - teams[b].rating
    a_expected = base + diff / rating_scale
    b_expected = base - diff / rating_scale
    return max(min_goals, a_expected), max(min_goals, b_expected)


def play_group_score(a, b, rng=None):
    a_expected, b_expected = expected_goals(a, b)
    return poisson(a_expected, rng), poisson(b_expected, rng)


# Knockout and penalty outcomes are modeled as one winner-takes-all event.
def play_knockout_match(a, b, rng=None):
    rng = get_rng(rng)
    if rng.random() < knockout_win_prob(a, b, rng):
        return a
    return b


# The random tie breaker is intentionally created per simulated group table. It
# is only reached after football ranking fields and rating cannot separate teams.
def create_group_table(group_codes, rng=None):
    rng = get_rng(rng)
    return {
        code: GroupStanding(code=code, tie_breaker=rng.random())
        for code in group_codes
    }


# Update points and score columns from a concrete scoreline.
def record_group_match(table, a, b, goals_a, goals_b):
    table[a].goals_for += goals_a
    table[a].goals_against += goals_b
    table[b].goals_for += goals_b
    table[b].goals_against += goals_a

    if goals_a == goals_b:
        table[a].points += GROUP_DRAW_POINTS
        table[b].points += GROUP_DRAW_POINTS
        table[a].draws += 1
        table[b].draws += 1
        return

    winner = a if goals_a > goals_b else b
    loser = b if winner == a else a
    table[winner].points += GROUP_WIN_POINTS
    table[winner].wins += 1
    table[loser].losses += 1


def record_bridge_match(table, a, b, goals_a, goals_b, winner):
    table[a].goals_for += goals_a
    table[a].goals_against += goals_b
    table[b].goals_for += goals_b
    table[b].goals_against += goals_a

    if winner not in (a, b):
        raise ValueError(f"bridge winner must be one of the teams: {winner}")

    loser = b if winner == a else a
    table[winner].points += BRIDGE_WIN_POINTS
    table[winner].wins += 1
    table[loser].losses += 1


def play_bridge_score(a, b, rng=None):
    # A drawn 90-minute bridge match keeps its drawn scoreline for goals and
    # goal difference; a simulated penalty winner receives the 2 bridge points.
    goals_a, goals_b = play_group_score(a, b, rng)
    if goals_a > goals_b:
        return goals_a, goals_b, a
    if goals_b > goals_a:
        return goals_a, goals_b, b
    return goals_a, goals_b, play_knockout_match(a, b, rng)


def head_to_head_key(standing, tied_codes, match_results):
    code = standing.code
    tied_codes = set(tied_codes)
    points = 0
    goals_for = 0
    goals_against = 0

    for a, b, goals_a, goals_b in match_results:
        if a not in tied_codes or b not in tied_codes:
            continue
        if code == a:
            goals_for += goals_a
            goals_against += goals_b
            if goals_a > goals_b:
                points += 3
            elif goals_a == goals_b:
                points += 1
        elif code == b:
            goals_for += goals_b
            goals_against += goals_a
            if goals_b > goals_a:
                points += 3
            elif goals_a == goals_b:
                points += 1

    return points, goals_for - goals_against, goals_for


def rank_three_team_group(table, match_results):
    standings = sorted(
        table.values(),
        key=lambda standing: (
            standing.points,
            standing.goal_diff,
            standing.goals_for,
        ),
        reverse=True,
    )
    ranked = []
    index = 0

    while index < len(standings):
        base_key = (
            standings[index].points,
            standings[index].goal_diff,
            standings[index].goals_for,
        )
        tied = []
        while index < len(standings):
            candidate_key = (
                standings[index].points,
                standings[index].goal_diff,
                standings[index].goals_for,
            )
            if candidate_key != base_key:
                break
            tied.append(standings[index])
            index += 1

        if len(tied) == 1:
            ranked.extend(tied)
            continue

        tied_codes = [standing.code for standing in tied]
        ranked.extend(sorted(
            tied,
            key=lambda standing: (
                *head_to_head_key(standing, tied_codes, match_results),
                teams[standing.code].rating,
                standing.tie_breaker,
            ),
            reverse=True,
        ))

    return ranked


def draw_groups(rng=None):
    rng = get_rng(rng)
    codes = list(teams)
    rng.shuffle(codes)
    return {
        group_name: codes[index * GROUP_SIZE:(index + 1) * GROUP_SIZE]
        for index, group_name in enumerate(GROUP_NAMES)
    }


def simulate_bridge_unit(x_group, y_group, drawn_groups, rng=None):
    x1, x2, x3 = drawn_groups[x_group]
    y1, y2, y3 = drawn_groups[y_group]
    table = create_group_table([x1, x2, x3, y1, y2, y3], rng)

    # Template from the format proposal:
    # R1: X1-X2, X3-Y1, Y2-Y3
    # R2: X1-X3, X2-Y2, Y1-Y3
    # R3: X2-X3, X1-Y3, Y1-Y2
    group_matches = (
        (x1, x2),
        (y2, y3),
        (x1, x3),
        (y1, y3),
        (x2, x3),
        (y1, y2),
    )
    bridge_matches = (
        (x3, y1),
        (x2, y2),
        (x1, y3),
    )
    match_results = {
        x_group: [],
        y_group: [],
    }

    for a, b in group_matches:
        goals_a, goals_b = play_group_score(a, b, rng)
        record_group_match(table, a, b, goals_a, goals_b)
        if a in drawn_groups[x_group] and b in drawn_groups[x_group]:
            match_results[x_group].append((a, b, goals_a, goals_b))
        elif a in drawn_groups[y_group] and b in drawn_groups[y_group]:
            match_results[y_group].append((a, b, goals_a, goals_b))

    for a, b in bridge_matches:
        goals_a, goals_b, winner = play_bridge_score(a, b, rng)
        record_bridge_match(table, a, b, goals_a, goals_b, winner)

    return {
        x_group: rank_three_team_group({
            code: table[code]
            for code in drawn_groups[x_group]
        }, match_results[x_group]),
        y_group: rank_three_team_group({
            code: table[code]
            for code in drawn_groups[y_group]
        }, match_results[y_group]),
    }


def simulate_group_stage_tables(rng=None):
    drawn_groups = draw_groups(rng)
    group_tables = {}

    for x_group, y_group in GROUP_PAIRS:
        group_tables.update(simulate_bridge_unit(x_group, y_group, drawn_groups, rng))

    return group_tables


def resolve_knockout_slot(slot, group_stage_result):
    if slot not in group_stage_result.qualifiers_by_slot:
        raise ValueError(f"unknown knockout slot: {slot}")

    return group_stage_result.qualifiers_by_slot[slot]


def resolve_knockout_ref(ref, group_stage_result, winners):
    if ref.startswith("W"):
        match_no = int(ref[1:])
        return winners[match_no]

    return resolve_knockout_slot(ref, group_stage_result)


def play_knockout_fixture(match_no, left, right, winners, rng=None):
    winner = play_knockout_match(left, right, rng)
    winners[match_no] = winner
    return winner


def create_stats():
    return {code: TeamStats() for code in teams}


def record_simulation(stats, result):
    for code in result.qualified:
        stats[code].qualified += 1
    for code in result.round_of_16:
        stats[code].round_of_16 += 1
    for code in result.quarterfinal:
        stats[code].quarterfinal += 1
    for code in result.semifinal:
        stats[code].semifinal += 1
    for code in result.final:
        stats[code].final += 1
    stats[result.champion].champion += 1


def make_simulation_result(group_stage_result, knockout_result):
    return SimulationResult(
        qualified=group_stage_result.qualified,
        round_of_16=knockout_result.round_of_16,
        quarterfinal=knockout_result.quarterfinal,
        semifinal=knockout_result.semifinal,
        final=knockout_result.final,
        champion=knockout_result.champion,
    )


# Workers return batch-local stats; the main thread merges them without shared
# mutable writes during simulation.
def merge_stats(total, partial):
    if set(total) != set(partial):
        raise ValueError("stats tables must contain the same teams")

    for code in total:
        total[code].qualified += partial[code].qualified
        total[code].round_of_16 += partial[code].round_of_16
        total[code].quarterfinal += partial[code].quarterfinal
        total[code].semifinal += partial[code].semifinal
        total[code].final += partial[code].final
        total[code].champion += partial[code].champion


# Runs a self-contained batch and returns only local aggregate counts.
def simulate_batch(n, seed=None):
    stats = create_stats()
    rng = create_rng(seed)

    for _ in range(n):
        result = simulate_once(rng=rng)
        record_simulation(stats, result)

    return stats


def chunk_simulations(n, workers):
    if n < 1:
        raise ValueError("simulation count must be positive")


    # More chunks than workers gives the executor enough work to balance, while
    # keeping each returned partial stats table reasonably large.
    chunk_count = min(n, max(1, workers * 20))
    base = n // chunk_count
    extra = n % chunk_count
    return [
        base + (1 if index < extra else 0)
        for index in range(chunk_count)
    ]


def make_chunk_seeds(seed, chunk_count):
    if seed is None:
        return [None] * chunk_count

    rng = create_rng(seed)
    return [
        rng.randrange(0, 2 ** 63)
        for _ in range(chunk_count)
    ]


def simulate_parallel(n, workers=None, seed=None):
    workers = workers or os.cpu_count() or 1
    workers = max(1, workers)
    chunks = chunk_simulations(n, workers)
    chunk_seeds = make_chunk_seeds(seed, len(chunks))
    stats = create_stats()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(simulate_batch, chunk, chunk_seed): chunk
            for chunk, chunk_seed in zip(chunks, chunk_seeds)
        }

        for future in as_completed(futures):
            partial_stats = future.result()
            merge_stats(stats, partial_stats)

    return stats


def format_stat(count, simulations):
    percentage = count / simulations * 100 if simulations else 0
    return f"{percentage:5.1f}%"


def print_stats(stats, simulations):
    rows = sorted(
        stats.items(),
        key=lambda item: (
            item[1].champion,
            item[1].final,
            item[1].semifinal,
            item[1].quarterfinal,
            item[1].round_of_16,
            item[1].qualified,
        ),
        reverse=True,
    )

    print("\t".join([
        "Team",
        "Qualified",
        "Round of 16",
        "Quarterfinal",
        "Semifinal",
        "Final",
        "Champion",
    ]))
    for code, team_stats in rows:
        print(
            "\t".join([
                f"{teams[code].name}({code})",
                format_stat(team_stats.qualified, simulations),
                format_stat(team_stats.round_of_16, simulations),
                format_stat(team_stats.quarterfinal, simulations),
                format_stat(team_stats.semifinal, simulations),
                format_stat(team_stats.final, simulations),
                format_stat(team_stats.champion, simulations),
            ])
        )


# One complete tournament simulation. It should keep all tournament state local
# and return a SimulationResult for the aggregate layer to record.
def simulate_once(rng=None):
    rng = rng if rng is not None else create_rng()
    group_stage_result = group_stage_sim(rng)
    knockout_result = knockout_stage_sim(group_stage_result, rng)
    return make_simulation_result(group_stage_result, knockout_result)


def group_stage_sim(rng=None):
    group_tables = simulate_group_stage_tables(rng)
    qualified = []
    qualifiers_by_slot = {}

    for group_name in GROUP_NAMES:
        table = group_tables[group_name]
        qualifiers_by_slot[f"{group_name}1"] = table[0].code
        qualifiers_by_slot[f"{group_name}2"] = table[1].code
        qualified.extend(standing.code for standing in table[:2])

    return GroupStageResult(
        qualified=qualified,
        qualifiers_by_slot=qualifiers_by_slot,
    )


def knockout_stage_sim(group_stage_result, rng=None):
    winners = {}

    for match_no, left_slot, right_slot in ROUND_OF_32_MATCHES:
        left = resolve_knockout_slot(left_slot, group_stage_result)
        right = resolve_knockout_slot(right_slot, group_stage_result)
        play_knockout_fixture(match_no, left, right, winners, rng)

    round_of_16 = [winners[match_no] for match_no in range(73, 89)]

    for match_no, left_ref, right_ref in KNOCKOUT_MATCHES:
        left = resolve_knockout_ref(left_ref, group_stage_result, winners)
        right = resolve_knockout_ref(right_ref, group_stage_result, winners)
        play_knockout_fixture(match_no, left, right, winners, rng)

    quarterfinal = [winners[match_no] for match_no in range(89, 97)]
    semifinal = [winners[match_no] for match_no in range(97, 101)]
    final = [winners[101], winners[102]]

    return KnockoutResult(
        round_of_16=round_of_16,
        quarterfinal=quarterfinal,
        semifinal=semifinal,
        final=final,
        champion=winners[104],
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simulate the bridge-format 2026 World Cup and print team odds."
    )
    parser.add_argument(
        "simulations",
        type=int,
        help="number of tournament simulations to run",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="number of CPU worker threads to use",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="base random seed for reproducible runs",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.simulations < 1:
        raise SystemExit("simulations must be positive")
    if args.workers < 1:
        raise SystemExit("workers must be positive")

    stats = simulate_parallel(args.simulations, workers=args.workers, seed=args.seed)
    print_stats(stats, args.simulations)


if __name__ == "__main__":
    main()
