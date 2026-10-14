"""Uncertainty and calibration for every Stage 3 model.

1. Match bootstrap. Matches are resampled with replacement (rows from one match
   always travel together, since events in a match are not independent) and every
   metric is recomputed on the out of fold predictions. 95% percentile intervals
   for AUC, log loss skill and Brier score.
   Caveat. The predictions are fixed, so this captures uncertainty from which
   matches happen to be in the data, not from refitting the models.
2. Calibration. Ten equal sized bins of predicted probability, observed rate per
   bin with a match bootstrap interval, plus calibration intercept and slope
   (logistic regression of the outcome on logit(p)), calibration in the large
   (mean observed minus mean predicted) and expected calibration error.
3. Header xG against StatsBomb's xG on the same shots. Paired match bootstrap of
   the AUC, log loss and Brier differences, plus DeLong's test for two correlated
   AUCs (which assumes independent shots, so the bootstrap is the main result).

Outputs (results/)
    model_uncertainty.csv     estimate and 95% interval per target, model and metric
    calibration_bins.csv      binned reliability curves
    calibration_summary.csv   intercept, slope, CITL, ECE with intervals
    xg_vs_statsbomb.csv       paired comparison
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES  # noqa: E402

B = 1000
RNG = np.random.default_rng(2026)
EPS = 1e-6


def targets():
    a = pd.read_csv(PROC / "attack_predictions.csv.gz")
    d = pd.read_csv(PROC / "duel_predictions.csv.gz")
    c = pd.read_csv(PROC / "clearance_predictions.csv.gz")
    ck = c[c["next_team_won"].notna()]
    return {
        "xg": (a["goal"].values, a["match_id"].values,
               {"logistic": a["xg_lr"].values, "boosting": a["xg_gbm"].values, "statsbomb": a["sb_xg"].values}),
        "xot": (a["on_target"].values, a["match_id"].values,
                {"logistic": a["xot_lr"].values, "boosting": a["xot_gbm"].values}),
        "duel": (d["def_won"].values, d["match_id"].values,
                 {"logistic": d["duel_lr"].values, "boosting": d["duel_gbm"].values}),
        "shot10": (c["opp_shot_10s"].astype(int).values, c["match_id"].values,
                   {"logistic": c["shot10_lr"].values, "boosting": c["shot10_gbm"].values}),
        "keep": (ck["next_team_won"].astype(int).values, ck["match_id"].values,
                 {"logistic": ck["keep_lr"].values, "boosting": ck["keep_gbm"].values}),
    }


def metrics(y, p, w=None):
    p = np.clip(p, EPS, 1 - EPS)
    w = np.ones_like(p) if w is None else w
    sw = w.sum()
    ll = -np.sum(w * (y * np.log(p) + (1 - y) * np.log(1 - p))) / sw
    base = np.sum(w * y) / sw
    ll0 = -(base * np.log(base) + (1 - base) * np.log(1 - base))
    return {"auc": roc_auc_score(y, p, sample_weight=w), "log_loss": ll, "skill": 1 - ll / ll0,
            "brier": np.sum(w * (y - p) ** 2) / sw}


def boot_weights(match_ids):
    """Yield row weights equal to how many times each row's match was drawn."""
    codes, uniq = pd.factorize(match_ids)
    m = len(uniq)
    for _ in range(B):
        counts = np.bincount(RNG.integers(0, m, m), minlength=m)
        yield counts[codes].astype(float)


def calib_fit(y, p, w):
    """Calibration intercept and slope from a logistic fit of y on logit(p)."""
    from sklearn.linear_model import LogisticRegression
    z = np.log(np.clip(p, EPS, 1 - EPS) / (1 - np.clip(p, EPS, 1 - EPS))).reshape(-1, 1)
    lr = LogisticRegression(C=1e6, max_iter=200).fit(z, y, sample_weight=w)
    return float(lr.intercept_[0]), float(lr.coef_[0, 0])


# ----------------------------------------------------------------------------- DeLong
def _midrank(x):
    order = np.argsort(x)
    xs = x[order]
    n = len(x)
    t = np.zeros(n)
    i = 0
    while i < n:
        j = i
        while j < n and xs[j] == xs[i]:
            j += 1
        t[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    out = np.empty(n)
    out[order] = t
    return out


def delong(y, p1, p2):
    """DeLong et al. (1988) test for two correlated AUCs, fast version (Sun and Xu 2014)."""
    pos, neg = y == 1, y == 0
    m, n = pos.sum(), neg.sum()
    aucs, v01, v10 = [], [], []
    for p in (p1, p2):
        x, yv = p[pos], p[neg]
        tx, ty, tz = _midrank(x), _midrank(yv), _midrank(np.r_[x, yv])
        auc = tz[:m].sum() / m / n - (m + 1) / (2 * n)
        aucs.append(auc)
        v01.append((tz[:m] - tx) / n)
        v10.append(1 - (tz[m:] - ty) / m)
    s01, s10 = np.cov(np.vstack(v01)), np.cov(np.vstack(v10))
    s = s01 / m + s10 / n
    diff = aucs[0] - aucs[1]
    se = np.sqrt(s[0, 0] + s[1, 1] - 2 * s[0, 1])
    z = diff / se
    return {"auc_1": aucs[0], "auc_2": aucs[1], "diff": diff, "se": se,
            "lo": diff - 1.96 * se, "hi": diff + 1.96 * se, "p": 2 * norm.sf(abs(z))}


# ----------------------------------------------------------------------------- main
def main():
    rows, bins_out, cal_out = [], [], []
    paired = None
    for target, (y, mid, models) in targets().items():
        print(f"{target}: {len(y):,} rows, {len(np.unique(mid)):,} matches", flush=True)
        point = {k: metrics(y, p) for k, p in models.items()}
        # fixed bins from the full data, per model
        edges = {k: np.unique(np.quantile(p, np.linspace(0, 1, 11))) for k, p in models.items()}
        bidx = {k: np.clip(np.searchsorted(edges[k], p, side="right") - 1, 0, len(edges[k]) - 2)
                for k, p in models.items()}
        boot = {k: [] for k in models}
        bin_boot = {k: [] for k in models}
        cal_boot = {k: [] for k in models}
        diffs = []
        for b, w in enumerate(boot_weights(mid)):
            for k, p in models.items():
                boot[k].append(metrics(y, p, w))
                nb = bidx[k].max() + 1
                ws = np.bincount(bidx[k], weights=w, minlength=nb)
                bin_boot[k].append(np.bincount(bidx[k], weights=w * y, minlength=nb) / np.maximum(ws, EPS))
                if b < 200:  # calibration slope is slower, 200 draws are enough for its interval
                    cal_boot[k].append(calib_fit(y, p, w))
            if target == "xg":
                diffs.append({m: boot["logistic"][-1][m] - boot["statsbomb"][-1][m]
                              for m in ("auc", "log_loss", "brier", "skill")})
        for k in models:
            bt = pd.DataFrame(boot[k])
            for m in ("auc", "skill", "log_loss", "brier"):
                rows.append({"target": target, "model": k, "metric": m, "estimate": point[k][m],
                             "lo": bt[m].quantile(0.025), "hi": bt[m].quantile(0.975), "n": len(y)})
            # calibration curve
            bb = np.vstack(bin_boot[k])
            for i in range(bidx[k].max() + 1):
                sel = bidx[k] == i
                bins_out.append({"target": target, "model": k, "bin": i, "n": int(sel.sum()),
                                 "predicted": models[k][sel].mean(), "observed": y[sel].mean(),
                                 "lo": np.quantile(bb[:, i], 0.025), "hi": np.quantile(bb[:, i], 0.975)})
            a0, b0 = calib_fit(y, models[k], np.ones(len(y)))
            cb = np.array(cal_boot[k])
            sel_bins = pd.DataFrame([r for r in bins_out if r["target"] == target and r["model"] == k])
            ece = float(np.sum(sel_bins["n"] * (sel_bins["observed"] - sel_bins["predicted"]).abs()) / len(y))
            cal_out.append({"target": target, "model": k, "intercept": a0,
                            "intercept_lo": np.quantile(cb[:, 0], 0.025), "intercept_hi": np.quantile(cb[:, 0], 0.975),
                            "slope": b0, "slope_lo": np.quantile(cb[:, 1], 0.025), "slope_hi": np.quantile(cb[:, 1], 0.975),
                            "citl": y.mean() - models[k].mean(), "ece": ece,
                            "mean_pred": models[k].mean(), "mean_obs": y.mean()})
        if target == "xg":
            dd = pd.DataFrame(diffs)
            dl = delong(y, models["logistic"], models["statsbomb"])
            paired = []
            for m in ("auc", "log_loss", "brier", "skill"):
                est = point["logistic"][m] - point["statsbomb"][m]
                s = dd[m]
                p_two = 2 * min((s <= 0).mean(), (s >= 0).mean())
                paired.append({"metric": m, "ours": point["logistic"][m], "statsbomb": point["statsbomb"][m],
                               "difference": est, "lo": s.quantile(0.025), "hi": s.quantile(0.975),
                               "bootstrap_p": max(p_two, 1 / B), "method": "paired match bootstrap"})
            paired.append({"metric": "auc", "ours": dl["auc_1"], "statsbomb": dl["auc_2"], "difference": dl["diff"],
                           "lo": dl["lo"], "hi": dl["hi"], "bootstrap_p": dl["p"], "method": "DeLong"})
    pd.DataFrame(rows).to_csv(RES / "model_uncertainty.csv", index=False)
    pd.DataFrame(bins_out).to_csv(RES / "calibration_bins.csv", index=False)
    pd.DataFrame(cal_out).to_csv(RES / "calibration_summary.csv", index=False)
    pd.DataFrame(paired).to_csv(RES / "xg_vs_statsbomb.csv", index=False)
    print(pd.DataFrame(rows).pivot_table(index=["target", "model"], columns="metric",
                                         values=["estimate", "lo", "hi"]).round(4).to_string())
    print(pd.DataFrame(cal_out).round(3).to_string())
    print(pd.DataFrame(paired).round(4).to_string())


if __name__ == "__main__":
    main()
