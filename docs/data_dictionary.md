# Data dictionary

All tables are built by `src/build_dataset.py` from StatsBomb open data. Coordinates
use the StatsBomb pitch (120 by 80 yards), always in the acting team's attacking
direction, so x = 120 is the goal being attacked and x = 0 is the team's own goal.

## headed_shots.csv.gz

One row per headed shot.

| Column | Meaning |
|---|---|
| goal, on_target | Labels. On target means Goal, Saved or Saved To Post |
| sb_xg | StatsBomb's own xG. Used only as a benchmark, never as a model input |
| x, y, dist, angle | Shot location, distance to goal centre, opening angle of the goal mouth in degrees |
| in_box, in_six | Inside the penalty box or six yard box |
| technique | Normal, Diving Header and so on |
| under_pressure, aerial_won, first_time | StatsBomb flags |
| score_diff, minute | Game state from the shooting team's side |
| dlv_type | How the ball arrived. corner, free_kick, throw_in, cross_open_play, long_ball, short_pass, headed_flick, goal_kick, or none (rebound or loose ball) |
| dlv_height, dlv_technique | Ground, Low or High pass. Inswinging, Outswinging or Straight |
| dlv_start_x/y, dlv_length | Where the delivery came from and how long it was |
| dlv_flight_time, dlv_pace | Seconds from the pass to the header, and length divided by that time. A rough proxy for ball speed |
| turn_angle | Angle between the ball's incoming direction and the direction to goal. Near 0 the header only has to continue the ball's path, near 180 it has to reverse it |
| n_def_in_cone, n_att_in_cone | Outfield defenders and attackers inside the triangle from the ball to both posts |
| nearest_opp_dist, n_opp_within_2m, n_opp_within_5m | Crowding around the header |
| n_opp_in_box, n_att_in_box | Bodies in the box at the moment of the header |
| gk_x, gk_y, gk_dist_goal, gk_dist_shooter, gk_in_cone | Goalkeeper position from the shot freeze frame |
| f360_* | Same kind of crowding measures from the 360 frame, when one exists |

## aerial_duels.csv.gz

One row per aerial duel. StatsBomb stores a duel as an "Aerial Lost" event for the
loser linked to the winner's pass, clearance, shot or miscontrol, so both players are
known.

| Column | Meaning |
|---|---|
| winner_id, loser_id and names, teams, positions | The two players |
| def_team_id | The team that did not deliver the ball (the defending side). Missing when no pass came in the 6 seconds before |
| x, y | Duel location in the defending team's direction (x near 0 means near their own goal) |
| winner_action | What the winner's header was logged as (Pass, Clearance, Shot, Miscontrol) |
| dlv_* | The incoming ball, as above |
| f360_* | Crowding around the losing player from the 360 frame |

## defensive_headers.csv.gz

Headed clearances anywhere, plus headed passes inside a team's own third when the
previous pass came from the opponent.

| Column | Meaning |
|---|---|
| action | Clearance or Pass |
| aerial_won | Header won a contested aerial duel |
| dist_own_goal, in_own_box | Danger of the location |
| next_team_won | 1 if the defending team had the next ball contact within 15 seconds |
| next_x, next_y, next_type | Where the next ball contact happened, in the defending team's direction. StatsBomb clearances have no end location, so this is the landing proxy |
| opp_shot_10s, opp_xg_10s, opp_goal_10s | Opponent shot, total opponent xG and goal within 10 seconds |
| dlv_* | The incoming ball, as above |

## player_matches.csv.gz and players.csv.gz

Minutes and main position per player per match from lineups, and one row per player
with full name, nickname and country.

## player_physical.csv.gz

Built by `src/match_players.py`. Height and weight from Transfermarkt (CC0) or
Wikidata (CC0), plus optional EA FC ratings (strength, jumping, heading accuracy,
sprint speed, acceleration). EA ratings are video game judgments and only a proxy.
