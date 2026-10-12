"""Stage 3 defense.

1. Aerial duel model. One row per duel seen from the defending side (the team that
   did not deliver the ball). Target is whether the defending player won. A player's
   expected duel wins are p when he defends and 1 minus p when he attacks.
2. Clearance quality models on defensive headers.
   a. chance the opponent shoots within 10 seconds (lower is better)
   b. chance the defending team gets the next ball (higher is better)
   Only things known before the header goes in, so where the ball landed and who
   picked it up are left out (they are the outcome).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import (PROC, RES, attach_physical, boosting_importance, calibration_table,  # noqa: E402
                      logistic_effects, physical_columns, run)

POS_GROUP = {
    "Goalkeeper": "GK",
    "Center Back": "CB", "Left Center Back": "CB", "Right Center Back": "CB",
    "Left Back": "FB", "Right Back": "FB", "Left Wing Back": "FB", "Right Wing Back": "FB",
    "Center Defensive Midfield": "DM", "Left Defensive Midfield": "DM", "Right Defensive Midfield": "DM",
    "Center Midfield": "CM", "Left Center Midfield": "CM", "Right Center Midfield": "CM",
    "Left Midfield": "WM", "Right Midfield": "WM",
    "Center Attacking Midfield": "AM", "Left Attacking Midfield": "AM", "Right Attacking Midfield": "AM",
    "Left Wing": "W", "Right Wing": "W",
    "Center Forward": "ST", "Left Center Forward": "ST", "Right Center Forward": "ST", "Secondary Striker": "ST",
}
DLV_CAT = ["dlv_type", "dlv_height"]


def pos(s):
    return s.map(POS_GROUP).fillna("other")


# ----------------------------------------------------------------------------- duels
def prepare_duels():
    d = pd.read_csv(PROC / "aerial_duels.csv.gz", low_memory=False)
    d = d[d["def_team_id"].notna()].reset_index(drop=True)
    def_is_winner = d["winner_team_id"] == d["def_team_id"]
    d["def_won"] = def_is_winner.astype(int)
    d["def_player_id"] = np.where(def_is_winner, d["winner_id"], d["loser_id"])
    d["att_player_id"] = np.where(def_is_winner, d["loser_id"], d["winner_id"])
    d["def_pos"] = pos(pd.Series(np.where(def_is_winner, d["winner_position"], d["loser_position"])))
    d["att_pos"] = pos(pd.Series(np.where(def_is_winner, d["loser_position"], d["winner_position"])))
    d["wide"] = (d["y"] - 40).abs()
    d["in_own_box"] = ((d["x"] <= 18) & (d["y"].between(18, 62))).astype(int)
    for c in DLV_CAT:
        d[c] = d[c].fillna("none").astype(str)
    d = attach_physical(d, "def_player_id", "def_")
    d = attach_physical(d, "att_player_id", "att_")
    if "def_height_cm" in d and "att_height_cm" in d:
        d["height_diff"] = d["def_height_cm"] - d["att_height_cm"]
    return d


def duel_model():
    d = prepare_duels()
    num = ["x", "wide", "in_own_box", "dlv_length", "dlv_pace", "dlv_start_x", "f360_opp_within_3m"]
    phys = physical_columns(d, "def_") + physical_columns(d, "att_") + (
        ["height_diff"] if "height_diff" in d and d["height_diff"].notna().mean() > 0.3 else [])
    num += phys
    cat = DLV_CAT + ["play_pattern", "def_pos", "att_pos"]
    print(f"{len(d)} duels, physical inputs used {phys or 'none yet'}")
    m, oof, full = run(d, num, cat, "def_won", "duel")
    print(m.round(4).to_string(index=False))
    logistic_effects(full["logistic"], num, cat).to_csv(RES / "duel_logistic_effects.csv", index=False)
    boosting_importance(d, num, cat, "def_won").to_csv(RES / "duel_gbm_importance.csv", index=False)
    best = pick(m, oof, "duel")
    calibration_table(d["def_won"].values, oof[best].values).to_csv(RES / "duel_calibration.csv", index=False)
    keep = ["event_id", "match_id", "comp_season", "def_player_id", "att_player_id", "winner",
            "loser", "def_won", "def_pos", "att_pos", "x", "y", "dlv_type"]
    pd.concat([d[keep], oof], axis=1).assign(best=best).to_csv(PROC / "duel_predictions.csv.gz", index=False)
    return m


# ----------------------------------------------------------------------------- clearances
def prepare_defs():
    f = pd.read_csv(PROC / "defensive_headers.csv.gz", low_memory=False)
    f["wide"] = (f["y"] - 40).abs()
    f["pos_group"] = pos(f["position"])
    for c in ["in_own_box", "aerial_won", "under_pressure"]:
        f[c] = f[c].fillna(False).astype(int)
    f["opp_shot_10s"] = f["opp_shot_10s"].astype(int)
    for c in DLV_CAT:
        f[c] = f[c].fillna("none").astype(str)
    return attach_physical(f, "player_id", "")


def clearance_models():
    f = prepare_defs()
    phys = physical_columns(f)
    num = ["x", "wide", "dist_own_goal", "in_own_box", "aerial_won", "under_pressure",
           "dlv_length", "dlv_pace", "dlv_start_x", "score_diff", "f360_opp_within_10m",
           "f360_nearest_opp"] + phys
    # "action" (Pass or Clearance) is left out on purpose. StatsBomb tends to log a header
    # as a pass when it reaches a teammate, so it leaks the outcome we want to predict.
    cat = DLV_CAT + ["play_pattern", "pos_group"]
    print(f"{len(f)} defensive headers, physical inputs used {phys or 'none yet'}")
    metrics, preds = [], []
    for target, name in (("opp_shot_10s", "shot10"), ("next_team_won", "keep")):
        sub = f[f[target].notna()].copy()
        sub[target] = sub[target].astype(int)
        m, oof, full = run(sub, num, cat, target, name)
        print(m.round(4).to_string(index=False))
        logistic_effects(full["logistic"], num, cat).to_csv(RES / f"{name}_logistic_effects.csv", index=False)
        boosting_importance(sub, num, cat, target).to_csv(RES / f"{name}_gbm_importance.csv", index=False)
        best = pick(m, oof, name)
        calibration_table(sub[target].values, oof[best].values).to_csv(RES / f"{name}_calibration.csv", index=False)
        metrics.append(m)
        preds.append(oof.reindex(f.index))
    keep = ["event_id", "match_id", "comp_season", "player_id", "player", "team", "pos_group", "action",
            "x", "y", "aerial_won", "opp_shot_10s", "opp_xg_10s", "next_team_won", "next_x", "next_y", "dlv_type"]
    pd.concat([f[keep]] + preds, axis=1).to_csv(PROC / "clearance_predictions.csv.gz", index=False)
    return pd.concat(metrics)


def pick(m, oof, name):
    t = m.set_index("model")["log_loss"]
    return f"{name}_gbm" if t["boosting"] <= t["logistic"] else f"{name}_lr"


def main():
    pd.concat([duel_model(), clearance_models()]).to_csv(RES / "defense_metrics.csv", index=False)


if __name__ == "__main__":
    main()
