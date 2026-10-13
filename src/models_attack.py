"""Stage 3 attack. Header xG (goal) and on target models.

Only information known at the moment of the header goes in. Where the shot ended
up (end_location) is left out on purpose, since it is part of the outcome.
StatsBomb's own xG is scored on the same rows as a benchmark and never used as an
input."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import (PROC, RES, attach_physical, boosting_importance, calibration_table,  # noqa: E402
                      logistic_effects, physical_columns, run)

NUM = ["dist", "angle", "dlv_length", "dlv_pace", "dlv_flight_time", "turn_angle",
       "dlv_start_x", "dlv_wide", "n_def_in_cone", "n_att_in_cone", "nearest_opp_dist",
       "n_opp_within_2m", "n_opp_in_box", "gk_dist_goal", "gk_dist_shooter", "score_diff"]
# StatsBomb's under_pressure flag is left out. It mostly duplicates nearest_opp_dist
# (pressured headers have a defender 0.9 yards away on average vs 2.1 yards), and with both in
# the model the flag picks up a misleading positive sign even though pressured headers
# score about half as often at every distance.
BOOL = ["in_six", "aerial_won", "gk_in_cone", "diving"]
CAT = ["dlv_type", "dlv_height", "dlv_technique"]


def prepare():
    s = pd.read_csv(PROC / "headed_shots.csv.gz", low_memory=False)
    s = s[s["shot_type"] != "Penalty"].reset_index(drop=True)
    s["dlv_wide"] = (s["dlv_start_y"] - 40).abs()  # how wide the delivery started
    s["diving"] = (s["technique"] == "Diving Header")
    for c in BOOL:
        s[c] = s[c].fillna(False).astype(int)
    for c in CAT:
        s[c] = s[c].fillna("none").astype(str)
    return attach_physical(s, "player_id", "")


def main():
    s = prepare()
    phys = physical_columns(s)
    num = NUM + BOOL + phys
    print(f"{len(s)} headed shots, physical inputs used {phys or 'none yet'}")

    all_metrics, preds = [], []
    for target, name in (("goal", "xg"), ("on_target", "xot")):
        bench = "sb_xg" if target == "goal" else None
        m, oof, full = run(s, num, CAT, target, name, benchmark=bench)
        all_metrics.append(m)
        preds.append(oof)
        print(m.round(4).to_string(index=False))
        logistic_effects(full["logistic"], num, CAT).to_csv(RES / f"{name}_logistic_effects.csv", index=False)
        boosting_importance(s, num, CAT, target).to_csv(RES / f"{name}_gbm_importance.csv", index=False)
        best = oof[f"{name}_gbm"] if m.set_index("model").loc["boosting", "log_loss"] <= \
            m.set_index("model").loc["logistic", "log_loss"] else oof[f"{name}_lr"]
        calibration_table(s[target].values, best.values).to_csv(RES / f"{name}_calibration.csv", index=False)

    out = pd.concat([s[["event_id", "match_id", "comp_season", "player_id", "player", "team",
                        "goal", "on_target", "sb_xg", "x", "y", "dlv_type"]]] + preds, axis=1)
    out.to_csv(PROC / "attack_predictions.csv.gz", index=False)
    pd.concat(all_metrics).to_csv(RES / "attack_metrics.csv", index=False)


if __name__ == "__main__":
    main()
