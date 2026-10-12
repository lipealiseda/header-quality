"""Join physical data to StatsBomb players by name, nationality and club.

StatsBomb gives full legal names ("José Diogo Dalot Teixeira"), a nickname
("Diogo Dalot") and a country, but no date of birth, so matching is fuzzy. A match
is accepted only when the best candidate scores high and clearly beats the runner
up. Everything else is left missing and written to unmatched_players.csv so you can
check it by hand. A wrong height is worse than a missing one.

Inputs (any that exist are used)
    data/external/transfermarkt_players.csv   (CC0, Kaggle davidcariboo/player-scores)
    data/external/wikidata_players.csv        (CC0, from fetch_physical.py)
    data/external/ea/players_XX.csv           (optional EA FC ratings, XX = 15..24)

Output
    data/processed/player_physical.csv.gz
"""
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
PROC = ROOT / "data" / "processed"

ACCEPT, MARGIN = 0.88, 0.06


def norm(s):
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z ]", " ", s.lower())
    return " ".join(s.split())


def name_sim(a, b):
    """1.0 when every token of the shorter name appears in the longer one
    ("diogo dalot" vs "jose diogo dalot teixeira"), otherwise a string ratio."""
    if not a or not b:
        return 0.0
    ta, tb = a.split(), b.split()
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(short) >= 2 and all(t in long_ for t in short):
        return 1.0
    if len(short) == 1 and short[0] in long_ and len(long_) == 1:
        return 1.0
    return SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()


class Source:
    """A table of candidate players with a token index for fast lookup."""

    def __init__(self, df, name_cols, country_col, club_col=None):
        self.df = df.reset_index(drop=True)
        self.names = [[norm(n) for c in name_cols for n in str(r[c]).split("|") if norm(n)]
                      for _, r in self.df.iterrows()]
        self.country = [norm(c) for c in self.df[country_col].fillna("")] if country_col else None
        self.club = [norm(c) for c in self.df[club_col].fillna("")] if club_col else None
        self.index = defaultdict(set)
        for i, ns in enumerate(self.names):
            for n in ns:
                for tok in n.split():
                    if len(tok) >= 3:
                        self.index[tok].add(i)

    def best(self, sb_names, country, clubs):
        cands = set()
        for n in sb_names:
            for tok in n.split():
                cands |= self.index.get(tok, set())
        scored = []
        for i in cands:
            s = max(name_sim(a, b) for a in sb_names for b in self.names[i])
            if self.country is not None and country and self.country[i]:
                s += 0.05 if self.country[i] in country or country in self.country[i] else -0.15
            if self.club is not None and clubs and self.club[i]:
                if any(name_sim(self.club[i], c) > 0.8 for c in clubs):
                    s += 0.05
            scored.append((s, i))
        if not scored:
            return None, 0.0
        scored.sort(reverse=True)
        top, second = scored[0][0], scored[1][0] if len(scored) > 1 else 0.0
        if top >= ACCEPT and top - second >= MARGIN:
            return scored[0][1], top
        return None, top


def load_sources():
    src = {}
    p = EXT / "transfermarkt_players.csv"
    if p.exists():
        tm = pd.read_csv(p)
        tm = tm[tm["height_in_cm"].notna()]
        src["transfermarkt"] = (Source(tm, ["name"], "country_of_citizenship"), tm, "height_in_cm", None)
    p = EXT / "wikidata_players.csv"
    if p.exists():
        wd = pd.read_csv(p)
        wd = (wd.groupby("p").agg(name=("name", "first"), aliases=("aliases", "first"),
                                  height=("height", "median"), mass=("mass", "median"),
                                  country=("country", lambda s: " ".join(sorted(set(s.dropna())))))
              .reset_index())
        wd["height_cm"] = wd["height"] * 100
        wd = wd[(wd["height_cm"] > 150) & (wd["height_cm"] < 215)]
        src["wikidata"] = (Source(wd, ["name", "aliases"], "country"), wd, "height_cm", "mass")
    ea = {}
    for f in sorted((EXT / "ea").glob("players_*.csv")):
        v = int(re.findall(r"\d+", f.stem)[0])
        df = pd.read_csv(f, low_memory=False)
        ea[v] = (Source(df, ["long_name", "short_name"], "nationality_name", "club_name"), df)
    return src, ea


def ea_version_for(season):
    """FIFA 16 ratings describe the 2015/16 season, and so on."""
    m = re.match(r"(\d{4})", str(season))
    if not m:
        return None
    y = int(m.group(1))
    return (y + 1) % 100 if "/" in str(season) else y % 100


def main():
    players = pd.read_csv(PROC / "players.csv.gz")
    pm = pd.read_csv(PROC / "player_matches.csv.gz")
    clubs = pm.groupby("player_id")["team"].apply(lambda s: [norm(t) for t in set(s)]).to_dict()
    seasons = pm.groupby("player_id")["season"].agg(lambda s: s.mode().iat[0]).to_dict()
    src, ea = load_sources()
    if not src and not ea:
        print("No physical data found in data/external. See fetch_physical.py.")
        return

    out, unmatched = [], []
    for _, r in players.iterrows():
        pid = r["player_id"]
        names = [n for n in {norm(r["player_name"]), norm(r.get("player_nickname"))} if n]
        country = norm(r.get("country"))
        row = {"player_id": pid, "height_cm": np.nan, "weight_kg": np.nan,
               "height_source": None, "match_score": np.nan}
        for key in ("transfermarkt", "wikidata"):
            if key not in src or not np.isnan(row["height_cm"]):
                continue
            s, df, hcol, mcol = src[key]
            i, score = s.best(names, country, None)
            if i is not None:
                row.update(height_cm=float(df.at[i, hcol]), height_source=key, match_score=score)
                if mcol and pd.notna(df.at[i, mcol]):
                    row["weight_kg"] = float(df.at[i, mcol])
        # EA ratings from the matching game year, else the nearest one we have
        v = ea_version_for(seasons.get(pid))
        if ea and v is not None:
            vv = min(ea, key=lambda k: abs(k - v))
            s, df = ea[vv]
            i, score = s.best(names, country, clubs.get(pid))
            if i is not None:
                rec = df.loc[i]
                row.update({
                    "ea_version": vv,
                    "ea_height_cm": rec.get("height_cm"), "ea_weight_kg": rec.get("weight_kg"),
                    "ea_strength": rec.get("power_strength"), "ea_jumping": rec.get("power_jumping"),
                    "ea_heading": rec.get("attacking_heading_accuracy"),
                    "ea_sprint": rec.get("movement_sprint_speed"),
                    "ea_accel": rec.get("movement_acceleration"),
                })
                if np.isnan(row["height_cm"]) and pd.notna(rec.get("height_cm")):
                    row.update(height_cm=float(rec["height_cm"]), height_source="ea", match_score=score)
                if np.isnan(row["weight_kg"]) and pd.notna(rec.get("weight_kg")):
                    row["weight_kg"] = float(rec["weight_kg"])
        out.append(row)
        if np.isnan(row["height_cm"]):
            unmatched.append({"player_id": pid, "player_name": r["player_name"],
                              "nickname": r.get("player_nickname"), "country": r.get("country")})

    res = pd.DataFrame(out)
    res.to_csv(PROC / "player_physical.csv.gz", index=False)
    pd.DataFrame(unmatched).to_csv(PROC / "unmatched_players.csv", index=False)
    print(f"height found for {res['height_cm'].notna().mean():.1%} of {len(res)} players")
    print(res["height_source"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
