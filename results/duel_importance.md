# What drives the aerial duel model

Permutation importance: shuffle an input on held out matches and measure how much the log loss gets worse. Bigger damage means the model relied on that input more.

## Single inputs (the method behind the original claim)

Gradient boosting, one held out fold of matches, each input shuffled five times.

| Rank | Input | Share |
|---|---|---|
| 1 | x | 20% |
| 2 | dlv_start_x | 19% |
| 3 | height_diff | 17% |
| 4 | play_pattern | 12% |
| 5 | def_pos | 11% |
| 6 | dlv_type | 6% |
| 7 | dlv_length | 4% |
| 8 | att_height_cm | 3% |

Height difference ranks third on its own. But the model also sees both raw heights, which carry overlapping information, so shuffling one height input at a time understates what height as a whole is worth.

## Grouped inputs over all five folds

Related inputs are shuffled together. Each of the 5 folds is shuffled 3 times, giving 15 measurements per group. The range shows the lowest and highest share and rank across those 15.

| Rank | Group of inputs | Share (range) | Rank range | Log loss increase |
|---|---|---|---|---|
| 1 | Height (both players and the difference) | 30% (26% to 35%) | 1 to 1 | 0.0306 |
| 2 | Where the duel happens (distance from goal line, width, inside the box) | 17% (14% to 19%) | 2 to 4 | 0.0168 |
| 3 | Where the delivery started | 16% (11% to 19%) | 2 to 5 | 0.0167 |
| 4 | Positions of the two players | 14% (12% to 18%) | 2 to 6 | 0.0140 |
| 5 | Type and flight of the delivery (type, height, length, speed) | 12% (10% to 15%) | 4 to 6 | 0.0126 |
| 6 | Phase of play (goal kick, corner, open play and so on) | 10% (8% to 12%) | 5 to 6 | 0.0107 |
| 7 | Crowding around the duel (360 data) | 0% (-0% to 0%) | 7 to 7 | 0.0000 |

## Drop column check

Refitting the duel model with every height input removed lowers AUC from 0.667 to 0.643 and raises log loss from 0.6342 to 0.6456. This measures what height adds that no other input can stand in for.