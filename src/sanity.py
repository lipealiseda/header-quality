"""Data sanity checks and a robustness test for the one team seasons.

1. Why the duel model has 93,684 rows when the duel table has 95,942.
2. How much of the data comes from Barcelona matches, and from "one team seasons":
   club competition seasons in the open data where one team appears in every match
   (Barcelona's La Liga seasons, PSG, Leverkusen, Arsenal 2003/04 and so on). Their
   opponents play that team every time, which could bias the rankings.
3. Robustness. The duel model is refit without the one team seasons (same features,
   same match grouped cross validation), the rankings and reliability are rebuilt,
   and they are compared with the full data versions.

Output
    results/data_sanity.md, results/rank_duels_no_one_team.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES, run  # noqa: E402
from models_defense import DLV_CAT, prepare_duels  # noqa: E402
import rankings  # noqa: E402

NUM = ["x", "wide", "in_own_box", "dlv_length", "dlv_pace", "dlv_start_x", "f360_opp_within_3m",
       "def_height_cm", "att_height_cm", "height_diff"]
CAT = DLV_CAT + ["play_pattern", "def_pos", "att_pos"]


def one_team_seasons(pm):
    n_matches = pm.groupby("comp_season")["match_id"].nunique()
    per = pm.drop_duplicates(["match_id", "team"]).groupby(["comp_season", "team"])["match_id"].nunique()
    per = per.reset_index().merge(n_matches.rename("n"), left_on="comp_season", right_index=True)
    dom = per[per["match_id"] == per["n"]]
    return dom


def main():
    raw = pd.read_csv(PROC / "aerial_duels.csv.gz", low_memory=False)
    pm = pd.read_csv(PROC / "player_matches.csv.gz")
    matches = pm.drop_duplicates("match_id")[["match_id", "comp_season", "home_team", "away_team"]]
    dom = one_team_seasons(pm)
    ots = set(dom["comp_season"])
    matches["one_team"] = matches["comp_season"].isin(ots)
    matches["barca"] = (matches["home_team"] == "Barcelona") | (matches["away_team"] == "Barcelona")
    raw = raw.merge(matches[["match_id", "one_team", "barca"]], on="match_id", how="left")
    shots = pd.read_csv(PROC / "headed_shots.csv.gz", usecols=["match_id"]).merge(
        matches[["match_id", "one_team", "barca"]], on="match_id")
    no_def = raw["def_team_id"].isna()
    per_match = (raw.groupby("match_id").size().rename("duels").reset_index()
                 .merge(matches, on="match_id", how="right").fillna({"duels": 0})
                 .groupby("barca")["duels"].mean())

    # ---------------- refit without one team seasons
    d = prepare_duels().merge(matches[["match_id", "one_team"]], on="match_id", how="left")
    sub = d[~d["one_team"]].reset_index(drop=True)
    m_sub, oof, _ = run(sub, NUM, CAT, "def_won", "duel")
    col = "duel_gbm" if m_sub.set_index("model").loc["boosting", "log_loss"] <= \
        m_sub.set_index("model").loc["logistic", "log_loss"] else "duel_lr"
    p = oof[col].values
    both = pd.concat([
        pd.DataFrame({"player_id": sub["def_player_id"], "match_id": sub["match_id"], "won": sub["def_won"], "p": p}),
        pd.DataFrame({"player_id": sub["att_player_id"], "match_id": sub["match_id"], "won": 1 - sub["def_won"],
                      "p": 1 - p}),
    ], ignore_index=True)
    known = set(pd.read_csv(PROC / "player_physical.csv.gz").dropna(subset=["height_cm"])["player_id"])
    both = both[both["player_id"].isin(known)]
    g, tau2 = rankings.player_table(both, "won", "p", 100)
    rel = rankings.split_half(both, "won", "p", 100)
    info = rankings.player_info()
    g = info.merge(g, on="player_id")
    g.sort_values("shrunk_rate", ascending=False).to_csv(RES / "rank_duels_no_one_team.csv", index=False)

    full = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    full_rel = pd.read_csv(RES / "metric_reliability.csv").set_index("metric").loc["duels_vs_expected"]
    fq, sq = full[full["qualified"]], g[g["qualified"]]
    both_q = fq.merge(sq[["player_id", "shrunk_rate"]], on="player_id", suffixes=("", "_sub"))
    rho = spearmanr(both_q["shrunk_rate"], both_q["shrunk_rate_sub"])[0]
    lost = fq[~fq["player_id"].isin(sq["player_id"])]
    dfq = both_q[both_q["pos_group"].isin(["CB", "FB"])]
    top_full = set(fq[fq["pos_group"].isin(["CB", "FB"])].nlargest(10, "shrunk_rate")["player_id"])
    top_sub = set(sq[sq["pos_group"].isin(["CB", "FB"])].nlargest(10, "shrunk_rate")["player_id"])
    m_full = pd.read_csv(RES / "defense_metrics.csv")
    mf = m_full[(m_full.target == "duel") & (m_full.model == "boosting")].iloc[0]
    ms = m_sub.set_index("model").loc["boosting"]
    rho_def = spearmanr(dfq["shrunk_rate"], dfq["shrunk_rate_sub"])[0]

    L = ["# Data sanity checks", "",
         "## Why 95,942 duels became 93,684 model rows", "",
         f"The duel table has {len(raw):,} aerial duels with both players known. {no_def.sum():,} of them "
         f"({no_def.mean():.1%}) had no pass in the 6 seconds before the duel, for example a loose ball or a "
         "header straight after another header. Without a delivering team there is no way to say which of the two "
         f"players was defending, so those duels cannot enter the duel model, which leaves {(~no_def).sum():,}. "
         "Duel rankings then use only players with a known height.", "",
         "## How much comes from Barcelona and other one team seasons", "",
         f"Some club seasons in StatsBomb open data follow one team in every match. There are {len(ots)} such "
         f"competition seasons. Barcelona is the main one, appearing in all matches of {int((dom['team'] == 'Barcelona').sum())} "
         "of them.", "",
         "| | Matches | Aerial duels | Headed shots |", "|---|---|---|---|",
         f"| Barcelona matches | {matches['barca'].sum():,} ({matches['barca'].mean():.0%}) | "
         f"{raw['barca'].sum():,} ({raw['barca'].mean():.0%}) | {shots['barca'].sum():,} ({shots['barca'].mean():.0%}) |",
         f"| All one team seasons | {matches['one_team'].sum():,} ({matches['one_team'].mean():.0%}) | "
         f"{raw['one_team'].sum():,} ({raw['one_team'].mean():.0%}) | {shots['one_team'].sum():,} "
         f"({shots['one_team'].mean():.0%}) |", "",
         f"Barcelona matches have fewer aerial duels, {per_match[True]:.1f} per match against {per_match[False]:.1f} "
         "in other matches, which is why their share of duels is smaller than their share of matches. A likely reason "
         "is that Barcelona kept the ball on the ground, though the data alone does not prove it.", "",
         "## Do the rankings change without the one team seasons?", "",
         f"The duel model was refit on the other {len(sub):,} duels with the same features and match grouped "
         "cross validation, and the rankings and reliability were rebuilt from scratch.", "",
         "| | Full data | Without one team seasons |", "|---|---|---|",
         f"| Duels in the model | {len(d):,} | {len(sub):,} |",
         f"| Duel model AUC (boosting) | {mf.auc:.3f} | {ms.auc:.3f} |",
         f"| Ranked players (100+ duels) | {len(fq)} | {len(sq)} |",
         f"| Reliability of duels above expected | {full_rel.full_length_reliability:.2f} "
         f"({full_rel.rel_ci_lo:.2f} to {full_rel.rel_ci_hi:.2f}) | {rel['full_length_reliability']:.2f} "
         f"({rel['rel_ci_lo']:.2f} to {rel['rel_ci_hi']:.2f}) |", "",
         f"For the {len(both_q)} players ranked in both versions, the Spearman rank correlation is {rho:.3f} "
         f"({rho_def:.3f} for defenders). {len(top_full & top_sub)} of the top 10 defenders are the same. "
         f"{len(lost)} players drop below 100 duels without those seasons, mostly Barcelona players and their "
         "regular opponents, so they simply cannot be ranked from the remaining data.", ""]
    if len(lost):
        names = ", ".join(lost.sort_values("n", ascending=False)["name"].head(8))
        L.append(f"Players who drop out include {names}.")
    (RES / "data_sanity.md").write_text("\n".join(L))
    pd.DataFrame([{"duels_all": len(raw), "no_def_team": int(no_def.sum()), "barca_match_share": matches["barca"].mean(),
                   "barca_duel_share": raw["barca"].mean(), "barca_shot_share": shots["barca"].mean(),
                   "one_team_match_share": matches["one_team"].mean(), "one_team_duel_share": raw["one_team"].mean(),
                   "one_team_shot_share": shots["one_team"].mean(), "auc_sub": ms.auc, "rel_sub": rel["full_length_reliability"],
                   "rel_sub_lo": rel["rel_ci_lo"], "rel_sub_hi": rel["rel_ci_hi"], "spearman": rho, "spearman_def": rho_def,
                   "top10_def_overlap": len(top_full & top_sub), "players_both": len(both_q), "players_lost": len(lost)}]
                 ).to_csv(RES / "data_sanity_stats.csv", index=False)
    print("\n".join(L))


if __name__ == "__main__":
    main()
