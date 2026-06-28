# World Cup Format Simulator

This repository contains a small Monte Carlo simulation project for comparing two 48-team World Cup tournament formats:

1. the current 12-group format;
2. a proposed 16-group, three-team, 2-point bridge format.

The project is not intended to predict the exact result of a real World Cup. Its purpose is to compare how different tournament structures distribute qualification and advancement probabilities under the same simplified probability model.

---

## Repository Structure

### Simulators

```text
current_format_simulator.py
```

Simulator for the current 48-team format:

```text
12 groups of four teams
top two in each group qualify
8 best third-placed teams qualify
32-team knockout stage
```

```text
new_format_simulator.py
```

Simulator for the proposed bridge format:

```text
16 groups of three teams
adjacent groups form six-team bridge units
each team plays 2 intra-group matches and 1 cross-group bridge match
cross-group bridge match win = 2 points
top two in each group qualify
32-team knockout stage
```

---

### Simulator Documentation

```text
format_simulator_explanation.md
```

English explanation of the simulator model, including:

```text
Monte Carlo method
team ratings
Poisson score model
Elo-style knockout model
penalty handling
random seed usage
current format simulation
bridge format simulation
```

```text
新老赛制模拟程序说明.md
```

Chinese explanation of the same simulator model and program structure.

---

### Format Design Documents

```text
bridge_format_design_en.md
```

English design document for the proposed 16-group three-team bridge format.

This file should explain the tournament format itself, including:

```text
why the 48-team / 32-qualifier structure is mathematically difficult
why the current best-third-place system creates cross-group comparison problems
why the original 16 groups of three teams creates bye and collusion risks
how the bridge format removes the bye problem
why cross-group bridge matches use the 2-0-0 points rule
why the knockout bracket separates bridge-connected groups
```

```text
bridge_format_design_zh.md
```

Chinese design document for the proposed bridge format.

This file should contain the full Chinese version of the format proposal and its reasoning.

---

## Quick Start

Run the current 12-group format simulation:

```bash
python3 current_format_simulator.py 10000 -w 8 --seed 2026
```

Run the proposed bridge-format simulation:

```bash
python3 new_format_simulator.py 10000 -w 8 --seed 2026
```

Parameter meanings:

```text
10000: simulate 10000 World Cups
-w 8: use 8 parallel workers
--seed 2026: fix the random seed for reproducible results
```

If `--seed` is omitted, each run produces fresh random results.

---

## Output

Both simulators output each team's probability of reaching each stage:

```text
Qualified
Round of 16
Quarterfinal
Semifinal
Final
Champion
```

In this project:

```text
Qualified = reached the round of 32
Round of 16 = won the round-of-32 match
Quarterfinal = won the round-of-16 match
Semifinal = won the quarterfinal
Final = won the semifinal
Champion = won the final
```

---

## Model Scope

The simulation uses a deliberately simplified probability model.

It includes:

```text
fixed Elo-like team ratings
random group draws
Poisson-generated group-stage scores
rating-based knockout and penalty outcomes
match-level form variation
```

It does not include:

```text
real tactical matchups
injuries
suspensions
travel fatigue
confederation draw restrictions
home advantage
actual FIFA ranking procedures in full detail
fair-play points
market odds
real-time squad strength
```

Therefore, the simulator should not be read as a precise prediction model.

Its main purpose is structural comparison:

```text
Given the same simplified probability assumptions,
how do different World Cup formats affect qualification and advancement probabilities?
```

---

## Format Summary

### Current Format

```text
48 teams
12 groups of 4
3 group-stage matches per team
top 2 from each group qualify
8 best third-placed teams qualify
32-team knockout stage
```

Main structural issue:

```text
third-placed teams are compared across different groups,
which creates cross-group ranking and scheduling sensitivity.
```

---

### Proposed Bridge Format

```text
48 teams
16 groups of 3
3 group-stage matches per team
2 intra-group matches
1 cross-group bridge match
top 2 from each group qualify
32-team knockout stage
```

Bridge units:

```text
AB, CD, EF, GH, IJ, KL, MN, OP
```

Each six-team bridge unit uses this template:

```text
Round 1: X1-X2, X3-Y1, Y2-Y3
Round 2: X1-X3, X2-Y2, Y1-Y3
Round 3: X2-X3, X1-Y3, Y1-Y2
```

Intra-group matches use standard football points:

```text
win: 3
draw: 1
loss: 0
```

Cross-group bridge matches use the bridge points rule:

```text
win: 2
loss: 0
draw: none
```

If a bridge match is tied after 90 minutes, a penalty shootout decides which team receives the 2 points. Penalty goals do not count toward goals scored or goal difference.

Main structural purpose:

```text
keep the 104-match total
remove best third-placed teams
remove three-team group byes
avoid giving cross-group matches the same weight as intra-group wins
```

---

## Suggested Reading Order

For a quick overview:

```text
README.md
```

For simulator mechanics:

```text
format_simulator_explanation.md
```

For Chinese simulator documentation:

```text
新老赛制模拟程序说明.md
```

For the proposed format design:

```text
bridge_format_design_en.md
bridge_format_design_zh.md
```

For implementation details:

```text
current_format_simulator.py
new_format_simulator.py
```

---

## Disclaimer

This project is an independent format-design and simulation exercise.

It is not affiliated with FIFA, any football association, or any official tournament organizer.
