# Mixed effects check of the aerial duel rankings

Crossed random intercept logistic model on top of the duel model (offset = logit of the out of fold prediction), fit by the Laplace approximation. See src/mixed_model.py.

## Simulation check

Fake data with 600 players and 59,878 duels, true sigma 0.35. Estimated sigma 0.331, correlation between estimated and true player effects 0.917. The fitting code recovers known answers.

## Real data

93,684 duels and 5,978 players. Spread of player effects sigma = 0.304 on the log odds scale, roughly 7.3 duels per 100 for one standard deviation of skill.

Spearman rank correlation between the mixed model and EB over all 512 ranked players is 0.988 (95% interval 0.985 to 0.990, bootstrapping players).

| Group | Players | Spearman | Top 10 overlap | Clearly above (EB / mixed / both) | Clearly below (EB / mixed) |
|---|---|---|---|---|---|
| All ranked players | 512 | 0.988 | 8 of 10 | 64 / 91 / 64 | 32 / 26 |
| Defenders | 228 | 0.976 | 9 of 10 | 18 / 33 / 18 | 8 / 4 |
| Forwards | 178 | 0.993 | 10 of 10 | 30 / 35 / 30 | 17 / 16 |

## Who moves

Players who move up in the mixed model tend to have faced stronger opponents in the air (Spearman 0.86 between moving up and average opponent effect). That is the one thing the mixed model adds: it credits a player for the quality of the opposition.

| Player | Pos | Duels | EB rank | Mixed model rank | Average opponent effect |
|---|---|---|---|---|---|
| Angelo Ogbonna | CB | 122 | 262 | 158 | +0.197 |
| Chris Smalling | CB | 277 | 259 | 166 | +0.136 |
| Ryan Bennett | CB | 120 | 307 | 227 | +0.197 |
| Federico Fernández | CB | 190 | 401 | 328 | +0.155 |
| Joleon Lescott | CB | 163 | 182 | 118 | +0.133 |
| Gareth McAuley | CB | 200 | 355 | 292 | +0.148 |