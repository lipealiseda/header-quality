# Who wins in the air, and does it last?

*Filipe Aliseda, University of Florida. Data from StatsBomb open data (2,651 men's matches) and Transfermarkt heights.*

## The short version

Winning aerial duels is a real, repeatable skill, and the free data can measure it. Scoring with your head is not something the free data can separate from luck. Clubs looking for aerial strength should scout duel win rate against expectation and treat headed goals above xG as noise.

## Five findings

**1. Height matters more than almost anything for winning the header.** When the defender is 10 cm or more shorter than the attacker he wins about 4 in 10 aerial duels. When he is 10 cm or more taller he wins about 3 in 4. At equal height the defending side still wins 58%, so defending a cross starts with an edge. Height difference is the third most important input in the duel model, behind where the duel happens and where the ball came from.

**2. Height does nothing once the header is won.** Taller players do not score more headed goals than their xG says, and adding height to the header xG model left its accuracy unchanged. Height wins you the ball. Where you are and how much space you have decides whether it goes in. Angle and distance to goal explain about 60% of what the xG model knows.

**3. Corners and long balls make the worst headed chances.** About 8% of headers from corners are scored, against 12% from open play crosses and 21% from flick ons. Corner headers face 8.6 defenders in the box on average (5.9 for other deliveries), and 63% are under pressure.

**4. Where you clear it matters far more than who clears it.** A defensive header made inside your own box is followed by an opponent shot within 10 seconds 14% of the time, compared with under 3% outside it. Individual clearance quality barely repeats from one set of matches to the next (reliability 0.17).

**5. Some defenders win far more than their size predicts.** After accounting for both players' heights and positions, the delivery and the location, Konstantinos Manolas (Roma, 185 cm) won about 12 more duels per 100 than expected, with Dejan Lovren and Thiago Silva also in the top 10. Daley Blind (Man United, 180 cm) won 14 fewer per 100, the weakest of 228 qualified defenders. Among forwards, Aritz Aduriz stands out at +18 per 100 over 423 duels. Players EA FC rates as strong jumpers tend to beat their height more (correlation 0.28), but all of EA's physical ratings together explain only 12% of who beats expectations, so most of it is something the ratings miss.

## How sure are we

Each metric was tested by splitting every player's matches into two random halves and checking whether one half predicts the other.

| Metric | Reliability (0 = luck, 1 = skill) |
|---|---|
| Aerial duels won vs expected | 0.67 |
| Headers on target vs expected | 0.24 |
| Opponent shots prevented after clearing | 0.17 |
| Next ball won after clearing | 0.05 |
| Headed goals minus xG | 0.02 |

Only duel ability clears the bar. It also looks individual, since a player's above-expected rate barely tracks his teammates' (correlation 0.10).

## Method in brief

Headed shots, aerial duels and defensive headers were pulled from StatsBomb events, with shot freeze frames for keeper and defender positions. Heights were matched from Transfermarkt by name, nationality, birth year and club history (90% coverage). Each outcome was modelled with logistic regression and gradient boosting, validated by grouping matches so no match appears in both training and testing. The header xG model reaches AUC 0.74, close to StatsBomb's own xG on the same shots (0.75). Player numbers are shrunk toward average with empirical Bayes so small samples cannot top a list.

## Limits

Most data comes from the 2015/16 Premier League, La Liga, Serie A and Ligue 1, so the rankings describe that season more than today. Free data has no measure of strength, jumping or speed beyond EA video game ratings, which are opinions, so a player's above-expected number bundles all of them together. A side test on two games of Metrica tracking data found no sign that speed or run up picks the duel winner, but 38 duels is far too few to rule it out. Only 47 players have 25 or more headed shots, which is the main reason finishing cannot be judged. The duel model is useful but modest (AUC 0.67), so some context it misses, like a team's set piece routines, could still be hiding inside player numbers.
