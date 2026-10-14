# Data sanity checks

## Why 95,942 duels became 93,684 model rows

The duel table has 95,942 aerial duels with both players known. 2,258 of them (2.4%) had no pass in the 6 seconds before the duel, for example a loose ball or a header straight after another header. Without a delivering team there is no way to say which of the two players was defending, so those duels cannot enter the duel model, which leaves 93,684. Duel rankings then use only players with a known height.

## How much comes from Barcelona and other one team seasons

Some club seasons in StatsBomb open data follow one team in every match. There are 55 such competition seasons. Barcelona is the main one, appearing in all matches of 23 of them.

| | Matches | Aerial duels | Headed shots |
|---|---|---|---|
| Barcelona matches | 531 (20%) | 12,355 (13%) | 1,642 (16%) |
| All one team seasons | 699 (26%) | 17,562 (18%) | 2,322 (22%) |

Barcelona matches have fewer aerial duels, 23.3 per match against 39.4 in other matches, which is why their share of duels is smaller than their share of matches. A likely reason is that Barcelona kept the ball on the ground, though the data alone does not prove it.

## Do the rankings change without the one team seasons?

The duel model was refit on the other 76,537 duels with the same features and match grouped cross validation, and the rankings and reliability were rebuilt from scratch.

| | Full data | Without one team seasons |
|---|---|---|
| Duels in the model | 93,684 | 76,537 |
| Duel model AUC (boosting) | 0.667 | 0.666 |
| Ranked players (100+ duels) | 512 | 446 |
| Reliability of duels above expected | 0.67 (0.59 to 0.74) | 0.67 (0.60 to 0.75) |

For the 446 players ranked in both versions, the Spearman rank correlation is 0.987 (0.991 for defenders). 9 of the top 10 defenders are the same. 66 players drop below 100 duels without those seasons, mostly Barcelona players and their regular opponents, so they simply cannot be ranked from the remaining data.

Players who drop out include Carles Puyol, Dani Alves, Javier Mascherano, Seydou Kéita, Lionel Messi, Jordi Alba, Stefan Kießling, Ivan Rakitić.