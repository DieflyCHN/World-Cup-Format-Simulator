# The Three-Team, 2-Point Bridge Format for a 48-Team World Cup

## 1. Format Objectives

This format is designed to address structural issues in a 48-team World Cup when reducing the field to 32 teams:

1. Avoid cross-group comparison of "best third-placed teams";
2. Avoid natural byes in three-team groups;
3. Keep three group-stage matches for every team;
4. Keep the group stage at 72 matches;
5. Keep the full tournament at 104 matches;
6. Make qualification for the round of 32 depend as much as possible on direct competition, rather than goal difference, goals scored, or schedule timing across unrelated third-placed teams.

---

## 2. Basic Structure

Total number of teams: 48.

The teams are divided into 16 groups, with 3 teams in each group:

```text
Group A, Group B, Group C, Group D, Group E, Group F, Group G, Group H,
Group I, Group J, Group K, Group L, Group M, Group N, Group O, Group P
```

The three teams in each group are assigned positions:

```text
Team 1, Team 2, Team 3
```

For example:

```text
Group A: A1, A2, A3
Group B: B1, B2, B3
```

---

## 3. Adjacent Group Binding Rule

The 16 groups are paired into 8 six-team schedule units:

```text
AB, CD, EF, GH, IJ, KL, MN, OP
```

Each six-team unit consists of two three-team groups.

For example:

```text
AB unit = Group A + Group B
CD unit = Group C + Group D
```

Every six-team unit uses the same schedule template.

---

## 4. Number of Matches per Team

Each team plays 3 group-stage matches:

```text
2 intra-group matches + 1 cross-group bridge match
```

Intra-group matches: against the other two teams in the same group.

Cross-group bridge match: against one team from the paired adjacent group.

---

## 5. Standard AB Unit Schedule Template

Using Groups A and B as an example:

```text
Group A: A1, A2, A3
Group B: B1, B2, B3
```

The three-round schedule is:

| Round | Match 1  | Match 2  | Match 3  |
| --- | -------- | -------- | -------- |
| Round 1 | A1 vs A2 | A3 vs B1 | B2 vs B3 |
| Round 2 | A1 vs A3 | A2 vs B2 | B1 vs B3 |
| Round 3 | A2 vs A3 | A1 vs B3 | B1 vs B2 |

Under this template, each team's opponents are:

```text
A1: A2, A3, B3
A2: A1, A3, B2
A3: A1, A2, B1

B1: B2, B3, A3
B2: B1, B3, A2
B3: B1, B2, A1
```

Therefore, every team plays:

```text
2 intra-group matches + 1 cross-group bridge match
```

No team has a bye.

---

## 6. Full Group-Stage Scheduling Rule

All adjacent group pairs use the same template.

For example, the CD unit:

```text
Group C: C1, C2, C3
Group D: D1, D2, D3
```

The schedule is:

| Round | Match 1  | Match 2  | Match 3  |
| --- | -------- | -------- | -------- |
| Round 1 | C1 vs C2 | C3 vs D1 | D2 vs D3 |
| Round 2 | C1 vs C3 | C2 vs D2 | D1 vs D3 |
| Round 3 | C2 vs C3 | C1 vs D3 | D1 vs D2 |

The EF, GH, IJ, KL, MN, and OP units follow the same rule.

---

## 7. Group Table Calculation

Each team's three matches all count toward its own group table.

For example, Group A ranking counts:

```text
the three matches played by A1, A2, and A3
```

including:

```text
2 Group A intra-group matches
1 cross-group match against a Group B team
```

Group B is treated in the same way.

The result of a cross-group match counts in both teams' respective group tables.

---

## 8. Points Rules

Intra-group matches use standard football points:

```text
Win: 3 points
Draw: 1 point
Loss: 0 points
```

Each group is ranked in the following order:

1. Points;
2. Goal difference;
3. Total goals scored;
4. Head-to-head points;
5. Head-to-head goal difference;
6. Head-to-head goals scored;
7. Fair-play points;
8. Drawing of lots or pre-tournament ranking rule.

Items 4 through 6 apply only when the tied teams have direct head-to-head matches.

In the accompanying simulator, fair-play points are not available. Therefore, the final fallback rules in the simulation are:

```text
7. rating;
8. random fallback value.
```

This is only a simulation fallback for unresolved ties. It does not change the principle that an official competition can use fair-play points or drawing of lots.

Cross-group bridge matches use an original points rule:

```text
Win: 2 points
Loss: 0 points
Draw: none
```

A cross-group bridge match is first played as a standard 90-minute match. If the 90-minute score is tied, a penalty shootout directly decides the bridge-match winner.

The penalty shootout only decides who receives the 2 points. Penalty goals do not count as goals scored and do not affect goal difference.

For example:

```text
A 1-1 B
A wins on penalties
```

This is recorded as:

```text
A: goals for 1, goals against 1, goal difference 0, bridge-match win, 2 points
B: goals for 1, goals against 1, goal difference 0, bridge-match loss, 0 points
```

This removes the incentive for both teams in a cross-group match to settle for a draw and take 1 point each. It also limits the impact of unequal cross-group opponent strength.

At the same time, a cross-group win is worth 2 points, so it does not override intra-group results:

```text
cross-group win < intra-group win
cross-group win = two intra-group draws
cross-group win > one intra-group draw
```

Looking only at the three intra-group matches in a three-team group, possible point patterns include:

```text
6-3-0, 6-1-1, 4-4-0, 4-3-1, 4-2-1, 3-3-3, 2-2-2
```

When a team wins both intra-group matches or loses both intra-group matches, the cross-group match has limited practical effect. The cross-group match matters most when the intra-group matches contain draws and the group itself does not fully separate the teams.

If all three intra-group matches are draws, the cross-group winner receives an additional 2 points. If teams remain tied, goal difference, total goals scored, and head-to-head rules continue to apply.

---

## 9. Qualification Rules

The top two teams in each of the 16 groups qualify for the round of 32:

```text
16 groups x 2 teams = 32 teams
```

Every group third-placed team is eliminated directly.

There are no "best third-placed teams".

There is no cross-group comparison among third-placed teams.

---

## 10. Match Count

### 1. Each Six-Team Unit

Each adjacent-group unit has 6 teams.

There are 3 matches per round and 3 rounds:

```text
3 rounds x 3 matches = 9 matches
```

### 2. Group Stage Total

There are 8 six-team units:

```text
8 x 9 = 72 matches
```

### 3. Knockout Stage

A 32-team single-elimination stage:

```text
Round of 32: 16 matches
Round of 16: 8 matches
Quarterfinals: 4 matches
Semifinals: 2 matches
Final: 1 match
Third-placed match: 1 match
```

Knockout total:

```text
16 + 8 + 4 + 2 + 1 + 1 = 32 matches
```

### 4. Full Tournament Total

```text
Group stage 72 matches + knockout stage 32 matches = 104 matches
```

This is the same total as the 48-team, 12 groups of 4 teams format with group top two plus best third-placed teams.

---

## 11. Comparison with the 48-Team 12-Group Format

| Item | 12 groups of 4 teams | Adjacent three-team bridge format |
| --- | ---: | ---: |
| Total teams | 48 | 48 |
| Number of groups | 12 | 16 |
| Teams per group | 4 | 3 |
| Group-stage matches per team | 3 | 3 |
| Group-stage total matches | 72 | 72 |
| Knockout matches | 32 | 32 |
| Total matches | 104 | 104 |
| Qualification method | Group top two + 8 best third-placed teams | Group top two |
| Best third-placed teams | Yes | No |
| Third-placed cross-group comparison | Required | Not required |
| Group-stage byes | No | No |
| Cross-group influence | Exists through third-place comparison | Exists through fixed bridge matches |

---

## 12. Advantages

### 1. Eliminating the Best Third-Placed Problem

In the 12-group format, the 12 third-placed teams must be compared across groups. This can create:

```text
cross-group scoring comparison
information asymmetry
late-round strategic draws
advantage for groups playing later
teams in early groups forced to wait
```

In this format, each group has a fixed top-two qualification rule. All third-placed teams are eliminated, so third-placed cross-group comparison does not exist.

---

### 2. Eliminating Byes in Three-Team Groups

A normal three-team group schedule is:

```text
A vs B
A vs C
B vs C
```

One team must be idle in each round, which creates information asymmetry in the final round.

This format fills the bye with a cross-group bridge match, so every team plays in all three rounds.

---

### 3. No Increase in Match Count

The group stage remains 72 matches, and the tournament remains 104 matches.

The format does not solve the problem by adding matches. It reorganizes the existing 72 group-stage matches.

---

### 4. Front-Loading Uncertainty

Traditional draws already contain uncertainty, including strong groups and weak groups.

This format moves most uncertainty to the draw and to fixed cross-group bridge matches, rather than leaving it to late-stage third-placed cross-group comparison.

In short:

```text
draw luck is acceptable;
late schedule information asymmetry and cross-group scoring comparison should be reduced.
```

---

## 13. Main Risks

### 1. Unequal Cross-Group Opponent Strength

Because each team plays one cross-group bridge match, different teams may face cross-group opponents of different strength. This is the format's main source of unfairness.

However, this is similar to traditional "group of death" draw variance. It is part of the draw structure rather than late-stage dynamic information asymmetry.

The 2-point bridge rule also limits the practical impact of this external factor on the group table.

---

### 2. Incentive Structure of Cross-Group Matches

Cross-group bridge matches affect two group tables at once, so they must not be designed in a way that allows both teams to benefit from a draw.

This format uses:

```text
cross-group winner receives 2 points;
loser receives 0 points;
90-minute draw goes directly to penalties;
penalties do not count as goals scored or goal difference.
```

This removes the "one point each for a draw" incentive. Even if the 90-minute match is tied, one team must receive the 2 points through penalties.

It must still be acknowledged that no group-stage format can completely eliminate strategic incentives in the final round. This format addresses the issue through:

```text
1. all three third-round matches in the same six-team unit kicking off simultaneously;
2. no draw points in cross-group bridge matches;
3. group top two qualification only, with no third-placed teams waiting on other groups.
```

Therefore, the remaining risk is concentrated within the same six-team unit rather than spreading into global cross-group third-placed calculations.

---

### 3. Final Round Still Requires Simultaneous Kickoff

To reduce information asymmetry, all third-round matches in the same six-team unit must kick off at the same time.

That is:

```text
AB unit third-round matches kick off simultaneously;
CD unit third-round matches kick off simultaneously;
...
OP unit third-round matches kick off simultaneously.
```

---

## 14. Implementation Rules

### 1. Draw Procedure

In this format, A1, A2, A3, ..., P1, P2, P3 are pre-defined positions before the draw. They are not numbers assigned by organizers after the group draw.

Before the draw, every position already determines:

1. Group;
2. Three group-stage opponents;
3. Cross-group bridge opponent;
4. Group-stage round order;
5. Potential knockout path.

During the draw, teams draw specific positions such as A3, B1, or P2, rather than first drawing a group and then being assigned a number within that group.

Except for pre-announced pot rules, confederation restrictions, or fixed host positions, no team may be renumbered, moved, or re-bridged after the draw.

All bridge relationships, schedule templates, and knockout bracket positions are fixed before the draw. They must not be adjusted based on team strength, commercial value, broadcast demand, or draw outcome.

---

### 2. Adjacent Group Binding Cannot Be Adjusted

The binding relationships are fixed before the tournament:

```text
AB, CD, EF, GH, IJ, KL, MN, OP
```

They must not be changed based on draw strength.

---

### 3. Schedule Template Cannot Be Adjusted

Every adjacent-group unit must use the same template.

Using an XY unit as the general form:

```text
Group X: X1, X2, X3
Group Y: Y1, Y2, Y3
```

The schedule is:

| Round | Match 1  | Match 2  | Match 3  |
| --- | -------- | -------- | -------- |
| Round 1 | X1 vs X2 | X3 vs Y1 | Y2 vs Y3 |
| Round 2 | X1 vs X3 | X2 vs Y2 | Y1 vs Y3 |
| Round 3 | X2 vs X3 | X1 vs Y3 | Y1 vs Y2 |

---

## 15. Core Conclusion

This format can be summarized as:

```text
48 teams divided into 16 groups of 3;
adjacent groups paired into six-team units;
each team plays two intra-group matches and one cross-group bridge match;
top two in each group qualify for the round of 32;
group stage has 72 matches;
knockout stage has 32 matches;
104 matches in total.
```

The core value of the format is:

```text
replace best third-placed cross-group comparison with one pre-defined cross-group bridge match.
```

It cannot completely eliminate draw luck or all strategic-match incentives.

But it can significantly reduce the most serious issues in the 48-team, 12-group format:

```text
third-placed cross-group scoring comparison
schedule timing information asymmetry
late groups having a global view
early groups being unable to respond
```

Therefore, under the constraints of no increase in total matches and no increase in each team's group-stage matches, this format is a more structured, more explainable, and less patched 48-team World Cup format than the "12 groups of 4 teams + best third-placed teams" format.

---

## 16. Maximum-Separation Knockout Bracket

The group-stage bridge relationships are fixed as:

```text
AB, CD, EF, GH, IJ, KL, MN, OP
```

The knockout bracket uses a maximum-separation principle, aiming to:

```text
1. place each group winner and runner-up in different halves;
2. increase the bracket distance between teams from adjacent bridge units;
3. reduce early rematches between teams already connected through group-stage bridge relationships.
```

The round-of-32 bracket is:

```text
Left half:
A1-P2
C1-N2
B1-O2
D1-M2
E1-L2
G1-J2
F1-K2
H1-I2

Right half:
I1-H2
K1-F2
J1-G2
L1-E2
M1-D2
O1-B2
N1-C2
P1-A2
```

Where:

```text
X1 = Group X winner
X2 = Group X runner-up
```

This bracket does not change the basic structure:

```text
each team plays 3 group-stage matches;
each team plays 2 intra-group matches and 1 cross-group bridge match;
top two in each group qualify;
group stage has 72 matches;
knockout stage has 32 matches;
104 matches in total.
```

The accompanying simulator `new_format_simulator.py` uses this exact round-of-32 bracket.

---

## 17. Quantitative Simulation Scope

This format is simulated with `new_format_simulator.py` using Monte Carlo simulation.

The purpose of the simulator is not to predict the exact result of a real World Cup. It compares the long-run probability distribution created by the format under many random draws and random match outcomes.

### 1. Random Draw

Before each simulation, the 48 teams are randomly shuffled and assigned to:

```text
A1, A2, A3,
B1, B2, B3,
...
P1, P2, P3
```

Therefore, the simulation results include:

```text
team strength effect;
draw randomness effect;
format structure effect.
```

### 2. Match Model

Group-stage matches use a Poisson model to generate 90-minute scores.

Knockout matches, penalty shootouts, and other winner-takes-all situations use a rating-based two-outcome win model with match-level form variation.

If a cross-group bridge match is tied after 90 minutes:

```text
the 90-minute score counts toward goals scored and goal difference;
the penalty winner receives the 2 bridge-match points;
penalties do not count as goals scored or goal difference.
```

### 3. Ranking and Output

The simulator outputs each team's probability for the following stages:

```text
Qualified
Round of 16
Quarterfinal
Semifinal
Final
Champion
```

Where:

```text
Qualified = group top two, entered the round of 32;
Round of 16 = won the round-of-32 match;
Quarterfinal = won the round-of-16 match;
Semifinal = won the quarterfinal;
Final = won the semifinal;
Champion = won the final.
```

### 4. Reproducibility

The simulator supports a random seed:

```bash
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

With the same number of simulations, worker count, and seed, the output is reproducible.

### 5. Comparison Method

To compare this format with the 12-group format, run both simulators with the same team ratings, number of simulations, worker count, and seed:

```bash
python3 current_format_simulator.py 10000 -w 8 --seed 2026
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

The two simulators use the same output fields, so stage probabilities can be compared directly across formats.

---

## 18. Statistical Results

This section presents simulation statistics based on a fixed random seed.

Both formats were tested with:

```bash
--seed 2026
```

The purpose of this comparison is to observe probability stability across tournament stages, especially whether the group qualification stage is less affected by draw structure.

### 1. K6 Residual Definition

This section introduces the `K6 residual` as a display metric.

For a given team and a given stage probability, the K6 residual compares that team's probability with the average probability of the six teams closest to it in strength ranking:

```text
K6 residual = average stage probability of nearby 6 teams - this team's stage probability
```

The metric is used to observe:

```text
whether a team's simulated probability deviates noticeably from the average of nearby-strength teams.
```

For the highest-ranked and lowest-ranked three teams, a complete set of three stronger and three weaker neighboring teams does not exist. The display tables therefore use the nearest six teams as a reference for those boundary teams. However, those boundary teams are not included in the final mean and variance calculations for K6 residuals.

### 2. Statistical Scope

K6 residuals are calculated for the following stage probabilities:

```text
Qualified
Round of 16
Quarterfinal
Semifinal
Final
Champion
```

For each stage, the following statistics are calculated:

```text
mean K6 residual
variance of K6 residual
```

The mean shows the overall direction of deviation, while the variance shows how concentrated or dispersed the deviations are across teams.

### 3. 12-Group Format Statistics

The following figure shows the simulation statistics for the 12-group format with `--seed 2026`:

![12-group format statistics](current_format_simulation_statistic_2026.png)

### 4. Bridge Format Statistics

The following figure shows the simulation statistics for the bridge format with `--seed 2026`:

![Bridge format statistics](bridge_format_simulation_statistic_2026.png)

### 5. Summary Comparison Table

The following figure summarizes the mean and variance of K6 residuals across stages for both formats:

![Summary comparison table](summary_comparison_table.png)

### 6. Statistical Conclusion

In this simulation, the main advantage of the bridge format appears at the round-of-32 qualification stage.

At the `Qualified` stage:

```text
the mean K6 residual decreases by about 56%;
the variance of K6 residuals decreases by about 24%.
```

This indicates that, at the level of how group qualification is produced, the bridge format reduces the disturbance caused by local draw structure compared with the 12-group format.

However, after the tournament enters the knockout stage, this advantage is not stable. In some knockout stages, the bridge format has slightly higher K6 residual variance than the 12-group format.

Therefore, this simulation more strongly supports the following conclusion:

```text
The bridge format improves the group qualification structure.
```

It should not be expanded into the broader claim that:

```text
The bridge format improves outcomes across all tournament stages.
```
