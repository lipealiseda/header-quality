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

ACCEPT, MARGIN = 0.95, 0.06


def norm(s):
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z ]", " ", s.lower())
    return " ".join(s.split())


def name_sim(a, b):
    """1.1 for an exact name match, 1.0 when every token of the shorter name appears
    in the longer one ("diogo dalot" vs "jose diogo dalot teixeira"), otherwise a
    string ratio. The exact bonus stops a partial name like "sergio garcia" from
    tying with "sergio ramos" for "Sergio Ramos Garcia"."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.1
    ta, tb = a.split(), b.split()
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if len(short) >= 2 and all(t in long_ for t in short):
        return 1.0
    return SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()


# the same country spelled differently across sources
COUNTRY_ALIAS = {
    "bosnia herzegovina": "bosnia and herzegovina", "dr congo": "congo kinshasa",
    "congo dr": "congo kinshasa", "korea south": "south korea", "korea republic": "south korea",
    "cote d ivoire": "ivory coast", "usa": "united states", "united states of america": "united states",
    "turkiye": "turkey", "czechia": "czech republic", "ireland": "republic of ireland",
    "cape verde islands": "cape verde", "curacao": "curacao", "north macedonia": "macedonia",
    "russian federation": "russia", "iran islamic republic of": "iran",
}
GENERIC = {"club", "football", "futbol", "sporting", "sportiva", "associazione", "calcio",
           "deportivo", "sociedad", "spa", "sad", "the", "and", "del", "les", "fc", "cf", "ac",
           "sc", "afc", "olympique", "athletic", "atletico", "de", "real", "s", "p", "a"}


def canon_country(c):
    c = norm(c)
    return COUNTRY_ALIAS.get(c, c)


def country_match(a, b):
    """Same country after aliasing, or sharing a distinctive word (bosnia, congo)."""
    a, b = canon_country(a), canon_country(b)
    if not a or not b:
        return None
    if a == b or a in b or b in a:
        return True
    return bool({t for t in a.split() if len(t) >= 5} & {t for t in b.split() if len(t) >= 5})


def club_match(sb_club, tm_club):
    """Every distinctive word of the StatsBomb club appears in the Transfermarkt name
    ("roma" in "associazione sportiva roma")."""
    toks = [t for t in sb_club.split() if t not in GENERIC and len(t) >= 3]
    tm = set(tm_club.split())
    return bool(toks) and all(t in tm for t in toks)


class Source:
    """A table of candidate players with a token index for fast lookup. Optional
    birth year and club lists are used to separate players who share a name."""

    def __init__(self, df, name_cols, country_col, club_col=None, dob_col=None):
        self.df = df.reset_index(drop=True)
        self.names = [[norm(n) for c in name_cols for n in str(r[c]).split("|") if norm(n)]
                      for _, r in self.df.iterrows()]
        self.country = list(self.df[country_col].fillna("")) if country_col else None
        self.club = ([[norm(x) for x in str(c).split("|") if norm(x)] for c in self.df[club_col].fillna("")]
                     if club_col else None)
        self.byear = (pd.to_datetime(self.df[dob_col], errors="coerce").dt.year.tolist()
                      if dob_col else None)
        self.index = defaultdict(set)
        for i, ns in enumerate(self.names):
            for n in ns:
                for tok in n.split():
                    if len(tok) >= 3:
                        self.index[tok].add(i)

    def best(self, sb_names, country, clubs, years=None, nickname=None):
        cands = set()
        for n in sb_names:
            for tok in n.split():
                cands |= self.index.get(tok, set())
        scored = []
        for i in cands:
            # a player must be 16 to 41 in the seasons he appears in StatsBomb
            if years and self.byear is not None and not np.isnan(self.byear[i]):
                if years[0] - self.byear[i] > 41 or years[1] - self.byear[i] < 16:
                    continue
            s = max(name_sim(a, b) for a in sb_names for b in self.names[i])
            # a player known by a nickname ("Maniche") that does not match should not
            # be matched on part of his legal name ("Ricardo Ribeiro")
            if nickname and s < 1.1 and max(name_sim(nickname, b) for b in self.names[i]) < 1.0:
                s = min(s, 0.85)
            if self.country is not None and country:
                cm = country_match(country, self.country[i])
                if cm is not None:
                    s += 0.05 if cm else -0.15
            if self.club is not None and clubs and self.club[i]:
                if any(club_match(c, t) for c in clubs for t in self.club[i]):
                    s += 0.10  # shared club history is strong evidence
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
        tm = tm[tm["height_in_cm"].between(150, 215)].reset_index(drop=True)  # drops typos like 17 cm
        clubs_file = EXT / "transfermarkt_player_clubs.csv"  # optional, built from appearances.csv
        if clubs_file.exists():
            tm = tm.merge(pd.read_csv(clubs_file), on="player_id", how="left")
        else:
            tm["clubs"] = tm["current_club_name"]
        src["transfermarkt"] = (Source(tm, ["name"], "country_of_citizenship", "clubs", "date_of_birth"),
                                tm, "height_in_cm", None)
    p = EXT / "wikidata_players.csv"
    if p.exists():
        wd = pd.read_csv(p)
        wd = (wd.groupby("p").agg(name=("name", "first"), aliases=("aliases", "first"),
                                  height=("height", "median"), mass=("mass", "median"),
                                  country=("country", lambda s: " ".join(sorted(set(s.dropna())))),
                                  dob=("dob", "first"))
              .reset_index())
        wd["height_cm"] = wd["height"] * 100
        wd = wd[(wd["height_cm"] > 150) & (wd["height_cm"] < 215)].reset_index(drop=True)
        src["wikidata"] = (Source(wd, ["name", "aliases"], "country", None, "dob"), wd, "height_cm", "mass")
    ea = {}
    for f in sorted((EXT / "ea").glob("players_*.csv")):
        v = int(re.findall(r"\d+", f.stem)[0])
        df = pd.read_csv(f, low_memory=False)
        ea[v] = (Source(df, ["long_name", "short_name"], "nationality_name", "club_name", "dob"), df)
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
    pm["year"] = pm["season"].astype(str).str[:4].astype(int)
    years = pm.groupby("player_id")["year"].agg(["min", "max"]).apply(tuple, axis=1).to_dict()
    src, ea = load_sources()
    if not src and not ea:
        print("No physical data found in data/external. See fetch_physical.py.")
        return

    out, unmatched = [], []
    for _, r in players.iterrows():
        pid = r["player_id"]
        names = [n for n in {norm(r["player_name"]), norm(r.get("player_nickname"))} if n]
        nick = norm(r.get("player_nickname"))
        nick = nick if nick and nick != norm(r["player_name"]) else None
        country = norm(r.get("country"))
        row = {"player_id": pid, "height_cm": np.nan, "weight_kg": np.nan,
               "height_source": None, "match_score": np.nan}
        for key in ("transfermarkt", "wikidata"):
            if key not in src or not np.isnan(row["height_cm"]):
                continue
            s, df, hcol, mcol = src[key]
            i, score = s.best(names, country, clubs.get(pid), years.get(pid), nick)
            if i is not None:
                row.update(height_cm=float(df.at[i, hcol]), height_source=key, match_score=score,
                           matched_name=df.at[i, "name"])  # kept so matches can be audited by hand
                if mcol and pd.notna(df.at[i, mcol]):
                    row["weight_kg"] = float(df.at[i, mcol])
        # EA ratings from the matching game year, else the nearest one we have
        v = ea_version_for(seasons.get(pid))
        if ea and v is not None:
            vv = min(ea, key=lambda k: abs(k - v))
            s, df = ea[vv]
            i, score = s.best(names, country, clubs.get(pid), years.get(pid), nick)
            rec = df.loc[i] if i is not None else None
            # an EA height far from the Transfermarkt height means EA matched someone else
            if rec is not None and not np.isnan(row["height_cm"]) and pd.notna(rec.get("height_cm")) \
                    and abs(rec["height_cm"] - row["height_cm"]) > 5:
                rec = None
            if rec is not None:
                row.update({
                    "ea_version": vv,
                    "ea_height_cm": rec.get("height_cm"), "ea_weight_kg": rec.get("weight_kg"),
                    "ea_strength": rec.get("power_strength"), "ea_jumping": rec.get("power_jumping"),
                    "ea_heading": rec.get("attacking_heading_accuracy"),
                    "ea_sprint": rec.get("movement_sprint_speed"),
                    "ea_accel": rec.get("movement_acceleration"),
                })
                # EA heights are not used to fill gaps, so the main models stay on one
                # height source (Transfermarkt) and earlier results do not shift
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
