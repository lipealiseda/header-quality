"""How much does height add to the duel model? A paired comparison.

The duel model is fit twice with the same grouped folds, once with both players'
heights and the height difference, once without. Both sets of out of fold
predictions are scored on the same match bootstrap resamples (1,000 draws of
whole matches), so the interval is for the gain itself rather than for either
model on its own. DeLong's test is added as a second check; it assumes duels are
independent, so the match bootstrap is the main result.

Output (results/)
    duel_height_gain.csv   AUC, log loss skill and Brier with and without height,
                           the difference and its 95% interval
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES, run  # noqa: E402
from models_defense import DUEL_CAT, DUEL_NUM, prepare_duels  # noqa: E402
from uncertainty import B, boot_weights, delong, metrics  # noqa: E402


def main():
    d = prepare_duels()
    # refit without any physical inputs, same folds as the main model
    _, oof, _ = run(d, list(DUEL_NUM), list(DUEL_CAT), "def_won", "duel")
    no_h = pd.DataFrame({"event_id": d["event_id"].values, "p_noheight": oof["duel_gbm"].values})
    main_pred = pd.read_csv(PROC / "duel_predictions.csv.gz", usecols=["event_id", "match_id", "def_won", "duel_gbm"])
    m = main_pred.merge(no_h, on="event_id", how="inner", validate="one_to_one")
    assert len(m) == len(main_pred), "rows do not line up with the main duel predictions"
    y, mid = m["def_won"].astype(int).values, m["match_id"].values
    p_h, p_0 = m["duel_gbm"].values, m["p_noheight"].values

    point_h, point_0 = metrics(y, p_h), metrics(y, p_0)
    keys = ("auc", "skill", "brier")
    diffs = {k: [] for k in keys}
    for w in boot_weights(mid):
        a, b = metrics(y, p_h, w), metrics(y, p_0, w)
        for k in keys:
            diffs[k].append(a[k] - b[k])
    rows = []
    for k in keys:
        s = np.array(diffs[k])
        p_two = 2 * min((s <= 0).mean(), (s >= 0).mean())
        rows.append({"metric": k, "with_height": point_h[k], "without_height": point_0[k],
                     "difference": point_h[k] - point_0[k], "lo": np.quantile(s, 0.025),
                     "hi": np.quantile(s, 0.975), "p": max(p_two, 1 / B), "method": "paired match bootstrap"})
    dl = delong(y, p_h, p_0)
    rows.append({"metric": "auc", "with_height": dl["auc_1"], "without_height": dl["auc_2"],
                 "difference": dl["diff"], "lo": dl["lo"], "hi": dl["hi"], "p": dl["p"], "method": "DeLong"})
    out = pd.DataFrame(rows)
    out.to_csv(RES / "duel_height_gain.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
