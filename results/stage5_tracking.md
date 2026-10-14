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

## What could 38 duels have detected?

A result that does not reach significance only means something if the test had a fair chance of finding an effect. With 38 duels, at the usual 5% significance level and 80% power, the smallest effects this test could reliably detect are

- the winner having the edge in at least 73% of duels (exact sign test),
- a standardised paired difference of 0.47, which is the winner ahead in about 68% of duels if differences are roughly normal (paired t test),
- a true AUC of about 0.76 for telling winner from loser (Mann Whitney test, simulation).

So a large effect, say the winner moving faster in three of every four duels, would probably have shown up. A modest effect, like the winner being quicker in 60% of duels, could easily be missed.

The observed shares, with 95% Wilson intervals, show which effects the data argues against.

| Feature | Winner higher in | 95% interval |
|---|---|---|
| Speed at the jump (last 0.2 s) | 14 of 38 (37%) | 23% to 53% |
| Peak speed in last 1 s | 13 of 38 (34%) | 21% to 50% |
| Distance covered in last 1 s | 15 of 38 (39%) | 26% to 55% |
| Speed toward the contact point (last 0.5 s) | 20 of 38 (53%) | 37% to 68% |
| Change in speed over last 1 s | 18 of 38 (47%) | 32% to 63% |

For speed at the jump, peak speed and run up distance, the whole interval sits at or below 55%, so in these two games the data argues against the faster player winning even 60% of duels. If anything the loser was moving faster more often, which could also be chance. For movement toward the ball and change in speed the intervals reach 63% to 68%, so a modest advantage there cannot be ruled out. Two anonymous games are also not a sample of the leagues in the main study, so none of this carries over to them directly.