# Stage 4 header quality rankings

Data is every men's match in StatsBomb open data. Most of the volume comes from the four full 2015/16 seasons (Premier League, La Liga, Serie A, Ligue 1), so these are mostly 2015/16 rankings. Players are compared with the Stage 3 models' out of fold predictions, so a player is never judged by a model that saw his own headers.

Above-expected numbers are shrunk toward zero with empirical Bayes. A player with few headers is pulled close to average, one with hundreds keeps most of his number. The 80% range shows how sure we are.

## Which metrics measure a real skill

Each player's matches are split randomly into two halves and his above-expected rate in one half is correlated with the other, across all qualified players. A reliability near 0 means the metric is mostly luck at these sample sizes, and values above about 0.5 mean it is repeatable.

| Metric | Minimum sample | Players | Reliability |
|---|---|---|---|
| Headed goals minus xG | 25 | 47 | 0.02 |
| Headers on target vs expected | 25 | 47 | 0.24 |
| Aerial duels won vs expected | 100 | 512 | 0.67 |
| Opponent shots prevented after clearances | 75 | 224 | 0.17 |
| Next ball won after defensive headers vs expected | 75 | 192 | 0.05 |

Aerial duel ability is clearly a skill, even after the model accounts for both players' heights, positions, the delivery and the location. Heading accuracy is weakly repeatable. Headed finishing (goals minus xG) cannot be told apart from luck in this data, so that table below is descriptive only.

## Attack

### What makes a header a goal

| Rank | Factor | Share of importance |
|---|---|---|
| 1 | Angle to goal | 41% |
| 2 | Distance to goal | 21% |
| 3 | Space to nearest defender | 7% |
| 4 | Keeper distance from header | 7% |
| 5 | Defenders in the shooting lane | 5% |
| 6 | Header won a contested duel | 5% |

### What makes a header land on target

| Rank | Factor | Share of importance |
|---|---|---|
| 1 | Angle to goal | 24% |
| 2 | Speed of the delivery | 21% |
| 3 | Header won a contested duel | 18% |
| 4 | Defenders in the shooting lane | 13% |
| 5 | How wide the delivery started | 7% |
| 6 | Space to nearest defender | 6% |

### Headers on target above expected (forwards, 25+ headed shots)

| # | Player | Pos | Main club | Height | Headed shots | Actual | Expected | Above expected per 100 (shrunk) | 80% range |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Andy Carroll | ST | West Ham United | 193 | 26 | 14 | 7.9 | +2.0 | -1.3 to +5.2 |
| 2 | Olivier Giroud | ST | Arsenal | 192 | 57 | 24 | 17.2 | +2.0 | -1.1 to +5.1 |
| 3 | Raúl García | AM | Athletic Club | ? | 26 | 12 | 6.5 | +1.9 | -1.3 to +5.1 |
| 4 | Karim Benzema | ST | Real Madrid | 185 | 30 | 16 | 9.9 | +1.8 | -1.4 to +5.1 |
| 5 | Luis Suárez | ST | Barcelona | 182 | 47 | 24 | 18.2 | +1.6 | -1.6 to +4.7 |
| 6 | Gareth Bale | W | Real Madrid | 186 | 28 | 13 | 8.6 | +1.4 | -1.8 to +4.6 |
| 7 | Romelu Lukaku | ST | Everton | 190 | 30 | 15 | 10.7 | +1.2 | -2.0 to +4.5 |
| 8 | Fernando Llorente | ST | Sevilla | 195 | 28 | 13 | 9.6 | +1.0 | -2.2 to +4.3 |
| 9 | Alexis Sánchez | W | Barcelona | 169 | 44 | 19 | 15.5 | +1.0 | -2.2 to +4.2 |
| 10 | Aritz Aduriz | ST | Athletic Club | 181 | 42 | 17 | 14.4 | +0.8 | -2.4 to +3.9 |

### Headed goals minus xG (25+ headed shots, descriptive only, reliability 0.02)

| # | Player | Pos | Main club | Headed shots | Goals | xG | Goals minus xG |
|---|---|---|---|---|---|---|---|
| 1 | Gareth Bale | W | Real Madrid | 28 | 10 | 4.0 | +6.0 |
| 2 | Sergio Ramos | CB | Real Madrid | 41 | 8 | 3.8 | +4.2 |
| 3 | Luis Suárez | ST | Barcelona | 47 | 11 | 7.3 | +3.7 |
| 4 | Raúl García | AM | Athletic Club | 26 | 5 | 2.0 | +3.0 |
| 5 | Andy Carroll | ST | West Ham United | 26 | 5 | 2.2 | +2.8 |
| 6 | Olivier Giroud | ST | Arsenal | 57 | 9 | 6.2 | +2.8 |
| 7 | Graziano Pellè | ST | Southampton | 30 | 5 | 3.0 | +2.0 |
| 8 | Karim Benzema | ST | Real Madrid | 30 | 7 | 5.0 | +2.0 |
| 9 | Scott Dann | CB | Crystal Palace | 25 | 3 | 1.1 | +1.9 |
| 10 | Seydou Kéita | CM | Barcelona | 34 | 5 | 3.1 | +1.9 |

### Strongest forwards in the air (aerial duels won vs expected, 100+ duels)

| # | Player | Pos | Main club | Height | Duels | Actual | Expected | Above expected per 100 (shrunk) | 80% range |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Aritz Aduriz | ST | Athletic Club | 181 | 423 | 239 | 151.3 | +18.2 | +15.4 to +20.9 |
| 2 | Souleymane Camara | ST | Montpellier | 174 | 144 | 70 | 42.3 | +14.0 | +10.0 to +18.0 |
| 3 | Álvaro Negredo | ST | Valencia | 186 | 221 | 127 | 89.6 | +13.2 | +9.6 to +16.8 |
| 4 | Deyverson | ST | Levante UD | 187 | 333 | 197 | 149.8 | +11.9 | +8.8 to +15.0 |
| 5 | Guido Carrillo | ST | AS Monaco | 187 | 231 | 132 | 99.1 | +11.2 | +7.6 to +14.8 |
| 6 | Troy Deeney | ST | Watford | 184 | 599 | 299 | 225.6 | +11.1 | +8.8 to +13.5 |
| 7 | Sloan Privat | ST | Guingamp | 186 | 202 | 111 | 82.4 | +10.8 | +7.0 to +14.6 |
| 8 | Riccardo Meggiorini | ST | Chievo | 182 | 171 | 84 | 59.3 | +10.7 | +6.8 to +14.6 |
| 9 | Shane Long | ST | Southampton | 180 | 260 | 119 | 85.1 | +10.7 | +7.4 to +14.0 |
| 10 | Cameron Jerome | ST | Norwich City | 185 | 211 | 111 | 82.1 | +10.6 | +6.9 to +14.3 |

## Defense

### What decides an aerial duel

| Rank | Factor | Share of importance |
|---|---|---|
| 1 | Distance from own goal line | 20% |
| 2 | Where the delivery started (length) | 19% |
| 3 | Height difference | 17% |
| 4 | Phase of play | 12% |
| 5 | Defender's position | 11% |
| 6 | Delivery type | 6% |

### What makes the opponent shoot within 10 seconds of a defensive header

| Rank | Factor | Share of importance |
|---|---|---|
| 1 | Distance from own goal | 74% |
| 2 | Under pressure | 10% |
| 3 | How wide the header was | 5% |
| 4 | Distance from own goal line | 4% |
| 5 | Phase of play | 3% |
| 6 | Length of the delivery | 2% |

### Best defenders in the air (aerial duels won vs expected, 100+ duels)

| # | Player | Pos | Main club | Height | Duels | Actual | Expected | Above expected per 100 (shrunk) | 80% range |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Konstantinos Manolas | CB | AS Roma | 185 | 197 | 160 | 128.5 | +12.3 | +8.6 to +16.0 |
| 2 | Federico Peluso | FB | Sassuolo | 188 | 134 | 104 | 80.7 | +11.8 | +7.5 to +16.2 |
| 3 | Micah Richards | CB | Aston Villa | 180 | 112 | 81 | 63.8 | +9.9 | +5.2 to +14.5 |
| 4 | Dejan Lovren | CB | Liverpool | 188 | 213 | 169 | 142.9 | +9.7 | +6.2 to +13.3 |
| 5 | Faouzi Ghoulam | FB | Napoli | 184 | 121 | 89 | 71.4 | +9.5 | +5.0 to +14.1 |
| 6 | Bacary Sagna | FB | Manchester City | 176 | 159 | 100 | 78.7 | +9.5 | +5.4 to +13.7 |
| 7 | Thiago Silva | CB | Paris Saint-Germain | 181 | 148 | 109 | 90.2 | +9.0 | +4.8 to +13.2 |
| 8 | Lucas Digne | FB | AS Roma | 178 | 207 | 138 | 114.2 | +8.8 | +5.0 to +12.6 |
| 9 | Šime Vrsaljko | FB | Sassuolo | 181 | 150 | 103 | 84.3 | +8.8 | +4.5 to +13.0 |
| 10 | Adama Soumaoro | CB | Lille | 187 | 136 | 106 | 91.0 | +7.8 | +3.6 to +12.0 |

### Weakest defenders in the air

| # | Player | Pos | Main club | Height | Duels | Actual | Expected | Above expected per 100 (shrunk) | 80% range |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Daley Blind | CB | Manchester United | 180 | 138 | 53 | 81.8 | -14.4 | -18.7 to -10.1 |
| 2 | Jorge Meré | CB | Sporting Gijón | 182 | 107 | 55 | 69.5 | -8.8 | -13.4 to -4.2 |
| 3 | Kévin Théophile-Catherine | FB | Saint-Étienne | 183 | 118 | 56 | 71.4 | -8.6 | -13.1 to -4.0 |
| 4 | Elseid Hysaj | FB | Napoli | 182 | 104 | 44 | 56.5 | -7.5 | -12.2 to -2.7 |
| 5 | Diego Llorente | CB | Rayo Vallecano | 186 | 204 | 112 | 131.5 | -7.4 | -11.1 to -3.7 |

### Clearances that stop the opponent shooting (75+ defensive headers, weak signal, reliability 0.17)

| # | Player | Pos | Main club | Height | Def. headers | Actual | Expected | Above expected per 100 (shrunk) | 80% range |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Sol Campbell | CB | Arsenal | ? | 230 | 220 | 210.8 | +0.9 | -0.2 to +2.0 |
| 2 | Sébastien Bassong | CB | Norwich City | 187 | 153 | 149 | 142.0 | +0.8 | -0.3 to +1.9 |
| 3 | Wes Morgan | CB | Leicester City | 185 | 180 | 171 | 164.5 | +0.6 | -0.5 to +1.8 |
| 4 | Eliaquim Mangala | CB | Manchester City | 187 | 79 | 78 | 72.7 | +0.6 | -0.5 to +1.8 |
| 5 | Issiaga Sylla | FB | Gazélec Ajaccio | 180 | 79 | 78 | 73.7 | +0.6 | -0.6 to +1.7 |
| 6 | Micah Richards | CB | Aston Villa | 180 | 97 | 94 | 88.5 | +0.6 | -0.6 to +1.7 |
| 7 | Víctor Ruíz | CB | Villarreal | 184 | 142 | 135 | 129.3 | +0.6 | -0.6 to +1.7 |
| 8 | Iván Ramis | CB | Eibar | 189 | 93 | 90 | 84.6 | +0.6 | -0.6 to +1.7 |
| 9 | Kyle Walker | FB | Tottenham Hotspur | 183 | 93 | 91 | 86.9 | +0.6 | -0.6 to +1.7 |
| 10 | David Lombán | CB | Granada | 185 | 79 | 77 | 71.5 | +0.6 | -0.6 to +1.7 |

## Caveats

- Heights come from Transfermarkt and are missing for about 10% of headers. Duel rankings only include players with a known height.
- Free data has no measure of strength, jumping or speed. Whatever those add shows up inside a player's above-expected number, which is the point of the ranking but means we cannot say which physical trait drives it.
- Club seasons outside 2015/16 cover only one team (mostly Barcelona), so those players and their opponents are over represented.
- Expected values come from models with modest accuracy for duels (AUC 0.67), so some of what looks like skill could be context the model misses, such as a team's set piece routines.
- Team effects look small. Across 496 players with 100+ duels, a player's above-expected duel rate barely tracks his teammates' rate (correlation 0.10), and the spread between teams is about a third of the spread between players.