# Stage 3 model results

Match grouped 5 fold cross validation on all men's StatsBomb open data matches (2,651 matches). Lower log loss and Brier are better, higher AUC is better. Skill is the share of log loss removed compared with always predicting the base rate.

Height comes from Transfermarkt (CC0) and is known for 90% of headed shots, 89% of defensive headers and 86% of duels (both players). Missing heights are handled by the models (median plus a missing flag for logistic regression, native handling in boosting).

| Target | Rows | Model | Log loss | Brier | AUC | Skill | AUC without height |
|---|---|---|---|---|---|---|---|
| Header xG (goal) | 10,327 | logistic | 0.2992 | 0.0856 | 0.743 | 11.8% | 0.743 |
| Header xG (goal) | 10,327 | boosting | 0.3000 | 0.0859 | 0.739 | 11.6% | 0.739 |
| Header xG (goal) | 10,327 | sb_xg | 0.2975 | 0.0850 | 0.749 | 12.3% | same |
| Header on target | 10,327 | logistic | 0.5980 | 0.2045 | 0.628 | 3.6% | 0.627 |
| Header on target | 10,327 | boosting | 0.6006 | 0.2059 | 0.620 | 3.2% | 0.622 |
| Aerial duel won (defending side) | 93,684 | logistic | 0.6396 | 0.2245 | 0.657 | 5.7% | 0.630 |
| Aerial duel won (defending side) | 93,684 | boosting | 0.6342 | 0.2220 | 0.667 | 6.5% | 0.643 |
| Opponent shot within 10s | 75,968 | logistic | 0.2594 | 0.0730 | 0.737 | 10.3% | 0.737 |
| Opponent shot within 10s | 75,968 | boosting | 0.2585 | 0.0729 | 0.739 | 10.6% | 0.739 |
| Defending team keeps next ball | 68,844 | logistic | 0.6249 | 0.2180 | 0.683 | 9.3% | 0.683 |
| Defending team keeps next ball | 68,844 | boosting | 0.6124 | 0.2134 | 0.694 | 11.1% | 0.694 |

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

For headed shots, goals minus StatsBomb xG per shot stays within one percentage point of zero across every height group, so taller players do not finish headers better once the situation is accounted for. Adding height to the header xG and clearance models leaves their scores unchanged.

## Notes

The Pass or Clearance labels on defensive headers are left out of the clearance models because StatsBomb tends to log a header as a pass when it reaches a teammate, which leaks the outcome.

StatsBomb's own xG is shown only as a benchmark and is never a model input.