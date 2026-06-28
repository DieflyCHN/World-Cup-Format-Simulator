# Bridge Format Design

English translation pending.

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
