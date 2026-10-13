# Do strength, jumping and speed explain header skill?

EA FC ratings (FIFA 15 to 22) are used as rough proxies for physical traits. They are judgments by EA's scouts, not physical tests, and they are kept out of the main models. Matching uses name, nationality, birth year and club, and a match is dropped when EA's height is more than 5 cm from Transfermarkt's. EA ratings were found for 4,941 players, covering 88% of headed shots and 79% of duels (both players).

## 1. Do EA ratings make the models more accurate?

| Model | Target | Inputs | Log loss | AUC |
|---|---|---|---|---|
| logistic | Aerial duel won | height only | 0.6396 | 0.657 |
| boosting | Aerial duel won | height only | 0.6342 | 0.667 |
| logistic | Aerial duel won | height + EA ratings | 0.6353 | 0.666 |
| boosting | Aerial duel won | height + EA ratings | 0.6304 | 0.675 |
| logistic | Header is a goal | height only | 0.2993 | 0.743 |
| boosting | Header is a goal | height only | 0.2998 | 0.741 |
| logistic | Header is a goal | height + EA ratings | 0.2996 | 0.743 |
| boosting | Header is a goal | height + EA ratings | 0.2997 | 0.740 |
| logistic | Header on target | height only | 0.5980 | 0.628 |
| boosting | Header on target | height only | 0.6004 | 0.621 |
| logistic | Header on target | height + EA ratings | 0.5982 | 0.628 |
| boosting | Header on target | height + EA ratings | 0.6006 | 0.620 |

## 2. Do the players who beat expectations have better EA physical ratings?

Players with 100+ aerial duels and an EA match (483 players). Their duels-above-expected number comes from a model that knows both players' heights but no EA ratings. Spearman correlation between that number and each EA rating.

| EA rating | Correlation | p value | Players |
|---|---|---|---|
| Jumping | +0.28 | 0.000 | 483 |
| Heading accuracy | +0.18 | 0.000 | 483 |
| Strength | +0.12 | 0.008 | 483 |
| Weight | +0.06 | 0.164 | 483 |
| Sprint speed | +0.03 | 0.553 | 483 |

All five together (weighted regression, standardised ratings, 483 players) explain 12% of the spread in duels above expected. Change in duels won above expected per 100 for one standard deviation of each rating, holding the others fixed.

| EA rating | Per 1 SD |
|---|---|
| Jumping | +1.2 |
| Weight | +0.6 |
| Heading accuracy | +0.5 |
| Sprint speed | +0.4 |
| Strength | +0.1 |

## The top five players in the air, with their EA ratings

| Player | Pos | Above expected per 100 | Jumping | Strength | Heading |
|---|---|---|---|---|---|
| Aritz Aduriz | ST | +18.2 | 96 | 82 | 95 |
| Clément Chantôme | DM | +14.2 | 72 | 73 | 73 |
| Souleymane Camara | ST | +14.0 | 68 | 66 | 70 |
| Álvaro Negredo | ST | +13.2 | 76 | 90 | 84 |
| Konstantinos Manolas | CB | +12.3 | 86 | 82 | 80 |

## Caveat

EA's heading accuracy rating is partly set by watching how players do in the air, so its link with duels above expected is partly circular. Jumping and strength are less directly tied to aerial results, but they are still opinions, not measurements.

EA FC ratings come from the Kaggle dataset by Stefano Leone (scraped from sofifa.com) and are not republished here.