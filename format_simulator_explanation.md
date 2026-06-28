# Current and New Format Simulator Explanation

This document explains the World Cup format simulators in this project.

## File Overview

The core materials in this repository consist of four files:

```text
current_format_simulator.py: simulator for the 12 groups of four teams format, with group top two plus best third-placed teams
new_format_simulator.py: simulator for the 16 groups of 3 teams, 2-point bridge format
新老赛制模拟程序说明.md: Chinese documentation
format_simulator_explanation.md: English documentation
```

---

## Purpose

The purpose of this project is not to predict the actual result of a specific World Cup. Instead, it compares how two tournament structures distribute qualification and advancement probabilities under the same simplified probability model.

The main comparison is between:

- the current 12-group format with best third-placed teams;
- a proposed 16-group bridge format with no best third-placed teams.

---

## Quick Start

Run the 12-group format simulation:

```bash
python3 current_format_simulator.py 10000 -w 8 --seed 2026
```

Run the bridge-format simulation:

```bash
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

Parameter meanings:

```text
10000: simulate 10000 World Cups
-w 8: use 8 worker threads
--seed 2026: fix the random seed for reproducible results
```

---

This document covers two independent simulators:

```text
current_format_simulator.py: 12 groups of four teams, with group top two plus best third-placed teams
new_format_simulator.py: 16 groups of 3 teams, using the three-team 2-point bridge format
```

The two programs use the same core probability model, the same team ratings, the same command-line interface, and the same output fields. The intended differences are limited to the tournament structures: group size, qualification rules, bridge matches, third-placed team handling, and the round-of-32 bracket.

---

## 1. Core Simulation Concepts

### 1. Monte Carlo Simulation

The programs use Monte Carlo simulation.

The basic idea is:

```text
Randomly simulate a complete World Cup many times;
record how far each team goes in each simulation;
estimate qualification and advancement probabilities from the resulting frequencies.
```

For example, after 10000 simulations, if a team qualifies from the group stage 7200 times, its qualification rate is:

```text
7200 / 10000 = 72.0%
```

The programs do not attempt to predict the single true result of any real match. Instead, they use repeated random trials to observe the long-run probability distribution created by each tournament structure.

---

### 2. Team Strength: Elo-like Rating

Each team has a `rating`, which can be interpreted as an approximate Elo-like strength value.

A higher rating means a stronger team. The team ratings in the programs are roughly in the range:

```text
1200 - 2200
```

This rating is not an official ranking and is not a precise prediction model. It is an input parameter used to distinguish team strength in the simulation.

---

### 3. Elo Win Probability

Knockout matches, penalty shootouts, and other winner-takes-all situations use ratings to calculate a two-outcome win probability.

The formula is:

```text
P(A beats B) = 1 / (1 + 10 ^ ((rating_B - rating_A) / K))
```

In the programs:

```text
K = 800
```

Meaning:

```text
When two teams have similar ratings, the win probability is close to 50%-50%;
when the rating gap is larger, the stronger team has a higher win probability;
but the weaker team still retains upset probability.
```

---

### 4. Match-Level Form Variation

Knockout matches and penalty shootouts are not calculated from fixed ratings alone.

The programs add match-level random form variation to each team:

```text
match_rating = rating + random form
```

The random form follows a normal distribution:

```text
mean = 0
standard deviation = 120
```

This means:

```text
stronger teams usually remain stronger;
but a single match still includes form, performance, and randomness.
```

---

### 5. Group-Stage Scores: Poisson Model

The group stage needs concrete scores because ranking depends on:

```text
points
goal difference
goals scored
head-to-head results
```

Therefore, group-stage matches are not drawn directly as win/draw/loss outcomes. Scores are generated first.

The programs use a Poisson distribution to generate goals.

The basic process is:

```text
first calculate each team's expected goals from the rating gap;
then randomly generate actual goals from those expected goals;
finally obtain a 90-minute scoreline.
```

Expected goals are calculated as:

```text
A_expected_goals = base + (rating_A - rating_B) / rating_scale
B_expected_goals = base - (rating_A - rating_B) / rating_scale
```

In the programs:

```text
base = 1.25
rating_scale = 800
min_goals = 0.20
```

Meaning:

```text
when two teams are close, both expected goals are about 1.25;
the stronger team has higher expected goals, and the weaker team has lower expected goals;
min_goals prevents the weaker team's expected goals from being pushed down to an unrealistic 0.
```

---

### 6. Penalty Shootout Handling

Penalty shootout goals do not count as goals scored and do not affect goal difference.

In the bridge format, if a cross-group bridge match is tied after 90 minutes:

```text
the 90-minute scoreline remains a draw;
that scoreline counts toward goals scored and goal difference;
then the Elo win model is used to simulate the penalty shootout winner;
the penalty winner receives the 2 bridge-match points.
```

For example:

```text
A 1-1 B
A wins on penalties
```

The points and records are counted as:

```text
A: goals for +1, goals against +1, goal difference 0, bridge-match win, 2 points
B: goals for +1, goals against +1, goal difference 0, bridge-match loss, 0 points
```

The penalty shootout does not change the score to 2-1 and does not add goal difference for the winner.

---

### 7. Random Seed

Both simulators support the `--seed` parameter.

The random seed allows the same command to reproduce the same simulation results:

```bash
python3 current_format_simulator.py 10000 -w 8 --seed 2026
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

In parallel simulation, the program derives a separate random seed for each task chunk from the base seed. If the following parameters are the same:

```text
number of simulations
number of worker threads
seed
```

then the output is reproducible.

---

## 2. 12-Group Format Simulator

The 12-group format simulator is:

```text
current_format_simulator.py
```

It simulates a 48-team format with 12 groups, four teams per group, group top two plus best third-placed teams qualifying.

---

### 1. Program Goal

`current_format_simulator.py` does one thing:

```text
repeatedly simulate a complete World Cup under the 12-group format and output each team's stage probabilities.
```

Command-line usage:

```bash
python3 current_format_simulator.py <number_of_simulations> -w <workers> --seed <random_seed>
```

Example:

```bash
python3 current_format_simulator.py 10000 -w 8 --seed 2026
```

The `--seed` parameter is optional. If omitted, each run uses fresh random results.

---

### 2. Complete Flow of One Simulation

Each simulation represents one complete World Cup.

The flow is:

```text
1. Randomly draw the 48 teams into A1 through L4;
2. play the group stage with 12 four-team groups;
3. each group of four teams plays a single round robin;
4. the top two teams in each group qualify directly;
5. the 12 third-placed teams are compared across groups, and the best 8 qualify;
6. the third-placed assignment table determines the round-of-32 matchups;
7. the fixed round-of-32 bracket and knockout stage are played;
8. each team's final stage is recorded;
9. repeat many times and output probabilities.
```

---

### 3. Random Draw

The program performs a new random draw in every simulation.

The 48 teams are shuffled and assigned in order to:

```text
A1, A2, A3, A4,
B1, B2, B3, B4,
...
L1, L2, L3, L4
```

This means the simulation results include:

```text
team strength effect
draw randomness effect
format structure effect
```

The program does not use the fixed group draw of any specific tournament edition.

---

### 4. Group Structure

The 12-group format has 12 four-team groups:

```text
A, B, C, D, E, F, G, H, I, J, K, L
```

Each group has four teams.

Using `Group X` as an example:

```text
Group X: X1, X2, X3, X4
```

The group stage is a single round robin:

```text
X1-X2
X1-X3
X1-X4
X2-X3
X2-X4
X3-X4
```

Therefore, each group has 6 matches, and each team plays 3 group-stage matches.

---

### 5. Points Rule

Group-stage matches use standard football points:

```text
win: 3 points
draw: 1 point
loss: 0 points
```

All group-stage scores are generated by the Poisson model.

---

### 6. Group Ranking Rules

The program ranks teams in the following order:

```text
1. total points
2. total goal difference
3. total goals scored
4. head-to-head points
5. head-to-head goal difference
6. head-to-head goals scored
7. rating
8. random fallback value
```

Items 4 through 6 are used only when items 1 through 3 still cannot separate the tied teams.

The program does not have fair-play points data, so it uses:

```text
rating
random fallback value
```

as the final tie-breaking fallback.

---

### 7. Qualification Rules

After each four-team group is ranked:

```text
group winner qualifies
group runner-up qualifies
group third-placed team enters cross-group comparison
group fourth-place team is eliminated
```

The 12 third-placed teams are then compared in the following order:

```text
1. total points
2. total goal difference
3. total goals scored
4. wins
5. rating
6. random fallback value
```

The highest-ranked 8 third-placed teams qualify.

Therefore:

```text
12 groups x 2 teams = 24 teams
8 best third-placed teams = 8 teams
32 teams qualify in total
```

---

### 8. Round-of-32 Bracket

The round of 32 uses a fixed bracket.

Eight group winners face a best third-placed team. Which third-placed group each one faces depends on which 8 third-placed teams qualified.

The program handles this rule with a third-placed assignment table:

```text
first identify the set of qualified third-placed groups;
then use the table to determine which third-placed group faces A1, B1, D1, E1, G1, I1, K1, and L1.
```

The fixed base round-of-32 bracket is:

```text
A2-B2
E1-third place
F1-C2
C1-F2
I1-third place
E2-I2
A1-third place
L1-third place
D1-third place
G1-third place
K2-L2
H1-J2
B1-third place
J1-H2
K1-third place
D2-G2
```

The program uses internal match numbers:

```text
73, 74, ..., 88
```

Later knockout rounds use:

```text
W73, W74, ...
```

to refer to the winner of the corresponding match.

These numbers are internal program references and do not represent official match numbers.

---

### 9. Knockout Simulation

The knockout stage starts from the round of 32 and is single elimination.

Every knockout match must produce a winner.

The program uses the Elo win model with match-level form variation:

```text
match_rating = rating + random form
```

It then calculates both teams' win probabilities and randomly produces a winner.

This treats:

```text
90 minutes
extra time
penalties
```

as one combined "who advances" outcome.

---

### 10. Output

The program outputs each team's stage probabilities across all simulations:

```text
Qualified
Round of 16
Quarterfinal
Semifinal
Final
Champion
```

Example columns:

```text
Team    Qualified    Round of 16    Quarterfinal    Semifinal    Final    Champion
```

Meaning:

```text
Qualified = entered the round of 32
Round of 16 = won the round-of-32 match
Quarterfinal = won the round-of-16 match
Semifinal = won the quarterfinal
Final = won the semifinal
Champion = won the final
```

---

### 11. Program Scope

This program is suitable for answering:

```text
Given team strengths, random draws, and the 12-group format structure,
how do long-run advancement probabilities roughly distribute across teams?
```

This program should not be interpreted as:

```text
a precise prediction of the real World Cup;
a precise score prediction for any single match;
an official assessment of team strength.
```

Its main purpose is:

```text
to provide structural and probabilistic simulation reference for the 12-group format.
```

---

## 3. Bridge-Format Simulator

The bridge-format simulator is:

```text
new_format_simulator.py
```

It simulates the 48-team World Cup under the three-team 2-point bridge format.

---

### 1. Program Goal

`new_format_simulator.py` does one thing:

```text
repeatedly simulate a complete World Cup under the bridge format and output each team's stage probabilities.
```

Command-line usage:

```bash
python3 new_format_simulator.py <number_of_simulations> -w <workers> --seed <random_seed>
```

Example:

```bash
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

The `--seed` parameter is optional. If omitted, each run uses fresh random results.

---

### 2. Complete Flow of One Simulation

Each simulation represents one complete World Cup.

The flow is:

```text
1. Randomly draw the 48 teams into A1 through P3;
2. play the group stage with 16 three-team groups;
3. each pair of adjacent groups forms a six-team bridge unit;
4. each team plays 2 intra-group matches and 1 cross-group bridge match;
5. the top two teams in each group qualify for the round of 32;
6. the fixed round-of-32 bracket and knockout stage are played;
7. each team's final stage is recorded;
8. repeat many times and output probabilities.
```

---

### 3. Random Draw

The program performs a new random draw in every simulation.

The 48 teams are shuffled and assigned in order to:

```text
A1, A2, A3,
B1, B2, B3,
...
P1, P2, P3
```

This means the simulation results include:

```text
team strength effect
draw randomness effect
schedule structure effect
```

---

### 4. Group and Bridge Structure

The bridge format has 16 three-team groups:

```text
A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P
```

Adjacent groups are paired into six-team bridge units:

```text
AB, CD, EF, GH, IJ, KL, MN, OP
```

Every bridge unit uses the same schedule template.

Using `Group X + Group Y` as an example:

```text
Group X: X1, X2, X3
Group Y: Y1, Y2, Y3
```

The schedule is:

```text
Round 1: X1-X2, X3-Y1, Y2-Y3
Round 2: X1-X3, X2-Y2, Y1-Y3
Round 3: X2-X3, X1-Y3, Y1-Y2
```

Where:

```text
intra-group matches: X1-X2, X1-X3, X2-X3, Y1-Y2, Y1-Y3, Y2-Y3
cross-group bridge matches: X3-Y1, X2-Y2, X1-Y3
```

---

### 5. Points Rule

Intra-group matches use standard football points:

```text
win: 3 points
draw: 1 point
loss: 0 points
```

Cross-group bridge matches use the bridge-format points rule:

```text
win: 2 points
loss: 0 points
draw: none
```

If a bridge match is tied after 90 minutes, a penalty shootout is simulated to determine the winner.

Note:

```text
penalties only decide who receives the 2 points;
penalties do not count as goals scored;
penalties do not affect goal difference.
```

---

### 6. Group Ranking Rules

The program ranks teams in the following order:

```text
1. total points
2. total goal difference
3. total goals scored
4. head-to-head points
5. head-to-head goal difference
6. head-to-head goals scored
7. rating
8. random fallback value
```

Items 4 through 6 are used only when items 1 through 3 still cannot separate the tied teams.

The program does not have fair-play points data, so it uses:

```text
rating
random fallback value
```

as the final tie-breaking fallback.

---

### 7. Qualification Rules

After each three-team group is ranked:

```text
group winner qualifies
group runner-up qualifies
group third-placed team is eliminated
```

Therefore:

```text
16 groups x 2 teams = 32 teams
```

There are no best third-placed teams.

---

### 8. Round-of-32 Bracket

The round of 32 uses a fixed bracket.

Left half:

```text
A1-P2
C1-N2
B1-O2
D1-M2
E1-L2
G1-J2
F1-K2
H1-I2
```

Right half:

```text
I1-H2
K1-F2
J1-G2
L1-E2
M1-D2
O1-B2
N1-C2
P1-A2
```

The program uses internal match numbers:

```text
73, 74, ..., 88
```

Later knockout rounds use:

```text
W73, W74, ...
```

to refer to the winner of the corresponding match.

These numbers are internal program references and do not represent official match numbers.

---

### 9. Knockout Simulation

The knockout stage starts from the round of 32 and is single elimination.

Every knockout match must produce a winner.

The program uses the Elo win model with match-level form variation:

```text
match_rating = rating + random form
```

It then calculates both teams' win probabilities and randomly produces a winner.

This treats:

```text
90 minutes
extra time
penalties
```

as one combined "who advances" outcome.

---

### 10. Output

The program outputs each team's stage probabilities across all simulations:

```text
Qualified
Round of 16
Quarterfinal
Semifinal
Final
Champion
```

Example columns:

```text
Team    Qualified    Round of 16    Quarterfinal    Semifinal    Final    Champion
```

Meaning:

```text
Qualified = group top two, entered the round of 32
Round of 16 = won the round-of-32 match
Quarterfinal = won the round-of-16 match
Semifinal = won the quarterfinal
Final = won the semifinal
Champion = won the final
```

---

### 11. Program Scope

This program is suitable for answering:

```text
Given team strengths, random draws, and this format structure,
how do long-run advancement probabilities roughly distribute across teams?
```

This program should not be interpreted as:

```text
a precise prediction of the real World Cup;
a precise score prediction for any single match;
an official assessment of team strength.
```

Its main purpose is:

```text
to provide structural and probabilistic simulation reference for the bridge format.
```
