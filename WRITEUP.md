# Who wins in the air, and does it last?

*Filipe Aliseda, University of Florida. Data from StatsBomb open data (2,651 men's matches) and Transfermarkt heights.*

## The short version

Winning aerial duels is a real, repeatable skill, and the free data can measure it. Headed finishing shows no sign of skill, but free data has too few headers per player to rule it out either. Clubs looking for aerial strength should scout duel win rate against expectation, and should not trust headed goals above xG in either direction.

## Five findings

**1. Height matters more than almost anything for winning the header.** When the defender is 10 cm or more shorter than the attacker he wins about 4 in 10 aerial duels. When he is 10 cm or more taller he wins about 3 in 4. Within 2 cm of the same height the defending side still wins 59%, so defending a cross starts with an edge. Height is the most important input in the duel model. Shuffling both heights and their difference on unseen matches costs 30% of the model's accuracy (range 26% to 35% over 15 repeats), more than where the duel happens (17%) or where the ball came from (16%).

**2. Height does nothing once the header is won.** Taller players do not score more headed goals than their xG says, and adding height to the header xG model left its accuracy unchanged. Height wins you the ball. Where you are and how much space you have decides whether it goes in. Angle and distance to goal explain about 60% of what the xG model knows.

**3. Corners and long balls make the worst headed chances.** About 8% of headers from corners are scored, against 12% from open play crosses and 21% from flick ons. Corner headers face 8.6 defenders in the box on average (5.9 for other deliveries), and 63% are under pressure.

**4. Where you clear it matters far more than who clears it.** A defensive header made inside your own box is followed by an opponent shot within 10 seconds 14% of the time, compared with under 3% outside it. Individual clearance quality barely repeats from one set of matches to the next (reliability 0.16, 95% interval below 0 to 0.38).

**5. Some defenders win far more than their size predicts.** After accounting for both players' heights and positions, the delivery and the location, Konstantinos Manolas (Roma, 185 cm) won about 12 more duels per 100 than expected (95% range +7 to +18), with Dejan Lovren and Thiago Silva also in the top 10. The top of the list cannot be ordered precisely, though. Manolas's 95% rank range is 1st to 32nd, and only 18 of 228 defenders are clearly above average. Daley Blind (Man United, 180 cm) won 14 fewer per 100 and ranks 218th to 228th, clearly the weakest. Among forwards, Aritz Aduriz stands out at +18 per 100 over 423 duels, with a rank range of 1st to 4th. Players EA FC rates as strong jumpers tend to beat their height more (correlation 0.28, 95% interval 0.19 to 0.36), but all of EA's physical ratings together explain only 12% of who beats expectations (6% to 19%), so most of it is something the ratings miss.

## How sure are we

Each metric was tested by splitting the matches into two random halves, checking whether a player's number in one half predicts the other, and correcting to the full sample. This was repeated for 200 random splits, with players also resampled to get a 95% interval.

| Metric | Reliability (0 = luck, 1 = skill) | 95% interval |
|---|---|---|
| Aerial duels won vs expected | 0.67 | 0.59 to 0.74 |
| Headers on target vs expected | 0.21 | below 0 to 0.60 |
| Opponent shots prevented after clearing | 0.16 | below 0 to 0.38 |
| Next ball won after clearing | 0.03 | below 0 to 0.34 |
| Headed goals minus xG | about 0 | below 0 to 0.53 |

Only duel ability clears the bar, and its whole interval does. The wide intervals for finishing and accuracy come from having only 47 players with 25 or more headed shots. It also looks individual, since a player's above-expected rate barely tracks his teammates' (correlation 0.10).

## Method in brief

Headed shots, aerial duels and defensive headers were pulled from StatsBomb events, with shot freeze frames for keeper and defender positions. Heights were matched from Transfermarkt by name, nationality, birth year and club history (90% coverage). Each outcome was modelled with logistic regression and gradient boosting, validated by grouping matches so no match appears in both training and testing. The header xG model reaches AUC 0.743 (95% interval 0.728 to 0.758 from resampling matches). On the same shots it cannot be told apart from StatsBomb's own xG (difference -0.006, interval -0.014 to +0.003), and it is better calibrated, predicting 0.106 goals per header against a real 0.107. Player numbers are shrunk toward average with empirical Bayes, and every player gets a posterior range and a rank range. A mixed effects model that also adjusts for opponents ranks players almost identically (rank correlation 0.988), and dropping the seasons that follow one team, mostly Barcelona (18% of duels), leaves the duel reliability at 0.67.

## Limits

Most data comes from the 2015/16 Premier League, La Liga, Serie A and Ligue 1, so the rankings describe that season more than today. Free data has no measure of strength, jumping or speed beyond EA video game ratings, which are opinions, so a player's above-expected number bundles all of them together. A side test on two games of Metrica tracking data found no sign that speed or run up picks the duel winner. With 38 duels it could only reliably detect a large effect (the winner ahead in 73% or more of duels), so a modest one cannot be ruled out. Only 47 players have 25 or more headed shots, which is why finishing can be neither confirmed nor ruled out as a skill. The duel model is useful but modest (AUC 0.67), so some context it misses, like a team's set piece routines, could still be hiding inside player numbers.
