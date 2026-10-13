# Stage 5. Speed and run up before aerial duels (tracking data)

Metrica Sports sample games 1 and 2 (anonymised, 25 frames per second). 38 aerial duels where both the winner and the loser are logged and tracked for the full second before contact.

| Feature | Winner (median) | Loser (median) | Winner higher in | Paired test p |
|---|---|---|---|---|
| Speed at the jump (last 0.2 s) | 2.38 m/s | 2.32 m/s | 37% of duels | 0.22 |
| Peak speed in last 1 s | 3.02 m/s | 2.80 m/s | 34% of duels | 0.22 |
| Distance covered in last 1 s | 2.52 m | 2.13 m | 39% of duels | 0.37 |
| Speed toward the contact point (last 0.5 s) | 1.18 m/s | 0.99 m/s | 53% of duels | 0.73 |
| Change in speed over last 1 s | -0.19 m/s | -0.51 m/s | 47% of duels | 0.69 |

A logistic regression on the five winner minus loser differences, tested leave one out, picks the winner with AUC 0.53 (95% bootstrap range 0.34 to 0.73). It is right in 20 of 38 duels (binomial p = 0.87 against a coin flip).

With this few duels the test cannot show that speed or run up decides aerial duels. The range is wide enough that a real but modest effect is still possible.

A leak caught along the way. The first version measured movement toward the event's own location. Metrica logs that at the winner's position, so the winner was by definition moving toward it, and the model scored an AUC of 0.90. Measuring toward the tracked ball instead dropped it to the value above. Any tracking feature built on an event location needs this check.

Why it is only a stretch result. Two games, anonymous players with no heights, so speed cannot be compared with height or put into the main duel model. Tracking with names (for example SkillCorner broadcast data for leagues that also have StatsBomb events) would let speed enter the model directly.

Data from Metrica Sports sample data (github.com/metrica-sports/sample-data).