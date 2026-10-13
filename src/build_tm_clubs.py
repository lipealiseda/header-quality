"""Optional helper for match_players.py. Builds a table of every club each
Transfermarkt player has appeared for, which separates players who share a name
(two Konstantinos Manolas, several Marquinhos).

Needs appearances.csv and clubs.csv from the same Kaggle dataset
(davidcariboo/player-scores) saved in data/external/.

Output
    data/external/transfermarkt_player_clubs.csv
"""
from pathlib import Path

import pandas as pd

EXT = Path(__file__).resolve().parents[1] / "data" / "external"


def main():
    a = pd.read_csv(EXT / "appearances.csv", usecols=["player_id", "player_club_id"]).drop_duplicates()
    c = pd.read_csv(EXT / "clubs.csv", usecols=["club_id", "name"])
    pc = a.merge(c, left_on="player_club_id", right_on="club_id")
    out = (pc.groupby("player_id")["name"].apply(lambda s: "|".join(sorted(set(s))))
           .reset_index().rename(columns={"name": "clubs"}))
    out.to_csv(EXT / "transfermarkt_player_clubs.csv", index=False)
    print(len(out), "players with club history")


if __name__ == "__main__":
    main()
