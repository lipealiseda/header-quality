# Stage 3 model results

Match grouped 5 fold cross validation on all men's StatsBomb open data matches (2,651 matches). Every number has a 95% interval from a match bootstrap: matches are resampled with replacement 1,000 times and each metric is recomputed on the out of fold predictions. The predictions themselves stay fixed, so the intervals cover which matches happen to be in the data, not model refitting. Higher AUC is better, lower Brier is better, and skill is the share of log loss removed compared with always predicting the base rate.

Height comes from Transfermarkt (CC0) and is known for 90% of headed shots, 89% of defensive headers and 86% of duels (both players). The last column refits the same model with every height input removed.

| Target | Rows | Model | AUC (95%) | Log loss skill (95%) | Brier (95%) | AUC without height |
|---|---|---|---|---|---|---|
| Header xG (goal) | 10,327 | logistic | 0.743 (0.728 to 0.758) | 11.8% (10.1% to 13.3%) | 0.0856 (0.0818 to 0.0898) | 0.743 |
| Header xG (goal) | 10,327 | boosting | 0.741 (0.726 to 0.755) | 11.7% (10.1% to 13.2%) | 0.0858 (0.0820 to 0.0901) | 0.740 |
| Header xG (goal) | 10,327 | StatsBomb xG (benchmark) | 0.749 (0.733 to 0.764) | 12.3% (10.8% to 13.8%) | 0.0850 (0.0812 to 0.0891) | n/a |
| Header on target | 10,327 | logistic | 0.628 (0.617 to 0.640) | 3.6% (2.9% to 4.3%) | 0.2045 (0.2009 to 0.2080) | 0.628 |
| Header on target | 10,327 | boosting | 0.621 (0.610 to 0.633) | 3.2% (2.6% to 3.9%) | 0.2058 (0.2023 to 0.2092) | 0.622 |
| Aerial duel won (defending side) | 93,684 | logistic | 0.657 (0.653 to 0.661) | 5.7% (5.4% to 5.9%) | 0.2245 (0.2235 to 0.2255) | 0.630 |
| Aerial duel won (defending side) | 93,684 | boosting | 0.667 (0.663 to 0.670) | 6.5% (6.2% to 6.7%) | 0.2220 (0.2209 to 0.2229) | 0.643 |
| Opponent shot within 10s | 75,968 | logistic | 0.737 (0.731 to 0.743) | 10.3% (9.7% to 10.8%) | 0.0730 (0.0713 to 0.0747) | 0.737 |
| Opponent shot within 10s | 75,968 | boosting | 0.739 (0.733 to 0.745) | 10.6% (10.1% to 11.1%) | 0.0729 (0.0712 to 0.0745) | 0.739 |
| Defending team keeps next ball | 68,844 | logistic | 0.683 (0.679 to 0.687) | 9.3% (8.9% to 9.7%) | 0.2180 (0.2167 to 0.2192) | 0.683 |
| Defending team keeps next ball | 68,844 | boosting | 0.694 (0.689 to 0.698) | 11.1% (10.7% to 11.5%) | 0.2134 (0.2122 to 0.2146) | 0.694 |

## Calibration

Ten equal sized bins of predicted probability per model (curves in calibration_bins.csv and calibration_all_models.png). The calibration slope comes from a logistic fit of the outcome on the logit of the prediction. 1 is ideal, below 1 means predictions are too extreme, above 1 too cautious. Calibration in the large is mean observed minus mean predicted. ECE is the average gap between predicted and observed rates across bins, weighted by bin size.

| Target | Model | Slope (95%) | Intercept (95%) | Calibration in the large | ECE |
|---|---|---|---|---|---|
| Header xG (goal) | logistic | 0.94 (0.88 to 1.01) | -0.10 (-0.24 to +0.04) | +0.0002 | 0.0041 |
| Header xG (goal) | boosting | 1.02 (0.94 to 1.09) | +0.05 (-0.10 to +0.21) | +0.0012 | 0.0062 |
| Header xG (goal) | StatsBomb xG (benchmark) | 1.09 (1.02 to 1.17) | +0.11 (-0.04 to +0.28) | -0.0046 | 0.0086 |
| Header on target | logistic | 0.89 (0.82 to 0.97) | -0.08 (-0.16 to -0.01) | +0.0001 | 0.0133 |
| Header on target | boosting | 0.99 (0.91 to 1.09) | +0.00 (-0.09 to +0.08) | +0.0013 | 0.0161 |
| Aerial duel won (defending side) | logistic | 0.99 (0.97 to 1.01) | +0.00 (-0.01 to +0.02) | -0.0000 | 0.0078 |
| Aerial duel won (defending side) | boosting | 1.04 (1.01 to 1.06) | -0.01 (-0.03 to +0.01) | +0.0001 | 0.0072 |
| Opponent shot within 10s | logistic | 0.98 (0.95 to 1.02) | -0.03 (-0.11 to +0.05) | -0.0000 | 0.0047 |
| Opponent shot within 10s | boosting | 1.03 (1.00 to 1.07) | +0.06 (-0.01 to +0.14) | +0.0001 | 0.0022 |
| Defending team keeps next ball | logistic | 0.99 (0.97 to 1.01) | -0.00 (-0.02 to +0.01) | +0.0000 | 0.0170 |
| Defending team keeps next ball | boosting | 1.05 (1.03 to 1.08) | +0.01 (-0.00 to +0.03) | +0.0002 | 0.0040 |

## Header xG against StatsBomb xG

Same 10,327 headed shots, this project's logistic xG minus StatsBomb's xG. The paired match bootstrap resamples matches and recomputes both models on the same draw, so it respects that shots in a match are related. DeLong's test is shown for reference and assumes independent shots.

| Metric | This project | StatsBomb | Difference (95%) | p | Method |
|---|---|---|---|---|---|
| auc | 0.743 | 0.749 | -0.006 (-0.014 to +0.003) | 0.20 | paired match bootstrap |
| log loss | 0.2993 | 0.2975 | +0.0019 (-0.0008 to +0.0047) | 0.18 | paired match bootstrap |
| brier | 0.0856 | 0.0850 | +0.0006 (-0.0001 to +0.0014) | 0.12 | paired match bootstrap |
| skill | 11.8% | 12.3% | -0.6% (-1.4% to +0.2%) | 0.18 | paired match bootstrap |
| auc | 0.743 | 0.749 | -0.006 (-0.014 to +0.003) | 0.18 | DeLong |

The difference in AUC is -0.006 with a 95% interval of -0.014 to +0.003, so the two models cannot be told apart on ranking shots. This project's xG is the better calibrated of the two. StatsBomb's averages 0.111 goals per header against an actual rate of 0.107, and its calibration slope of 1.09 sits above 1. That comparison favours this project a little, since its model was fit and cross validated on these same competitions, while StatsBomb's xG is a general model that was not built for this particular set of matches.

## What height does

Height matters a lot for winning the header and not at all for what happens after it.

| Defender height minus attacker height | Defender duel win rate | Duels |
|---|---|---|
| 10+ cm shorter | 39% | 8,083 |
| 5 to 10 cm shorter | 50% | 12,514 |
| 2 to 5 cm shorter | 54% | 11,176 |
| within 2 cm | 59% | 15,860 |
| 2 to 5 cm taller | 64% | 11,117 |
| 5 to 10 cm taller | 68% | 12,696 |
| 10+ cm taller | 76% | 8,822 |

For headed shots, goals minus StatsBomb xG per shot stays within one percentage point of zero across every height group, so taller players do not finish headers better once the situation is accounted for.

## Notes

StatsBomb's under_pressure flag is left out of the attack models. It duplicates the distance to the nearest defender, and with both in the model it took a misleading positive sign even though pressured headers score about half as often at every distance. Accuracy was unchanged without it.

The Pass or Clearance labels on defensive headers are left out of the clearance models because StatsBomb tends to log a header as a pass when it reaches a teammate, which leaks the outcome.

StatsBomb's own xG is shown only as a benchmark and is never a model input.