# Stage 3 model results

Match grouped 5 fold cross validation on all men's StatsBomb open data matches. Lower log loss and Brier are better, higher AUC is better. Skill is the share of log loss removed compared with always predicting the base rate.

| Target | Rows | Model | Log loss | Brier | AUC | Skill |
|---|---|---|---|---|---|---|
| Header xG (goal) | 10,327 | logistic | 0.2992 | 0.0856 | 0.743 | 11.8% |
| Header xG (goal) | 10,327 | boosting | 0.3000 | 0.0858 | 0.739 | 11.6% |
| Header xG (goal) | 10,327 | sb_xg | 0.2975 | 0.0850 | 0.749 | 12.3% |
| Header on target | 10,327 | logistic | 0.5982 | 0.2045 | 0.627 | 3.6% |
| Header on target | 10,327 | boosting | 0.5999 | 0.2056 | 0.622 | 3.3% |
| Aerial duel won (defending side) | 93,684 | logistic | 0.6517 | 0.2300 | 0.630 | 3.9% |
| Aerial duel won (defending side) | 93,684 | boosting | 0.6456 | 0.2271 | 0.643 | 4.8% |
| Opponent shot within 10s | 75,968 | logistic | 0.2594 | 0.0730 | 0.737 | 10.3% |
| Opponent shot within 10s | 75,968 | boosting | 0.2585 | 0.0729 | 0.739 | 10.6% |
| Defending team keeps next ball | 68,844 | logistic | 0.6249 | 0.2180 | 0.683 | 9.3% |
| Defending team keeps next ball | 68,844 | boosting | 0.6123 | 0.2134 | 0.694 | 11.1% |

Physical inputs (height, weight, EA ratings) are not in these runs yet. The scripts pick them up automatically once data/processed/player_physical.csv.gz exists.

The Pass or Clearance labels on defensive headers are left out of the clearance models because StatsBomb tends to log a header as a pass when it reaches a teammate, which leaks the outcome.