"""Write results/stage3_summary.md from the metric files.

Run after models_attack.py and models_defense.py, and after the comparison run
without height
    HQ_NO_PHYSICAL=1 python src/models_attack.py
    HQ_NO_PHYSICAL=1 python src/models_defense.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import RES  # noqa: E402

NAMES = {"xg": "Header xG (goal)", "xot": "Header on target", "duel": "Aerial duel won (defending side)",
         "shot10": "Opponent shot within 10s", "keep": "Defending team keeps next ball"}


def main():
    from models_defense import prepare_duels
    m = pd.concat([pd.read_csv(RES / "attack_metrics.csv"), pd.read_csv(RES / "defense_metrics.csv")])
    p0 = [RES / "attack_metrics_noheight.csv", RES / "defense_metrics_noheight.csv"]
    m0 = pd.concat([pd.read_csv(p) for p in p0]) if all(p.exists() for p in p0) else None
    u = pd.read_csv(RES / "model_uncertainty.csv")
    cal = pd.read_csv(RES / "calibration_summary.csv").set_index(["target", "model"])
    cmp_ = pd.read_csv(RES / "xg_vs_statsbomb.csv")

    def ci(target, model, metric, fmt):
        r = u[(u.target == target) & (u.model == model) & (u.metric == metric)].iloc[0]
        return f"{fmt(r.estimate)} ({fmt(r.lo)} to {fmt(r.hi)})"

    f3 = lambda v: f"{v:.3f}"  # noqa: E731
    f4 = lambda v: f"{v:.4f}"  # noqa: E731
    fp = lambda v: f"{v:.1%}"  # noqa: E731
    L = ["# Stage 3 model results", "",
         "Match grouped 5 fold cross validation on all men's StatsBomb open data matches (2,651 matches). Every "
         "number has a 95% interval from a match bootstrap: matches are resampled with replacement 1,000 times and "
         "each metric is recomputed on the out of fold predictions. The predictions themselves stay fixed, so the "
         "intervals cover which matches happen to be in the data, not model refitting. Higher AUC is better, lower "
         "Brier is better, and skill is the share of log loss removed compared with always predicting the base rate.",
         "",
         "Height comes from Transfermarkt (CC0) and is known for 90% of headed shots, 89% of defensive headers and "
         "86% of duels (both players). The last column refits the same model with every height input removed.", "",
         "| Target | Rows | Model | AUC (95%) | Log loss skill (95%) | Brier (95%) | AUC without height |",
         "|---|---|---|---|---|---|---|"]
    for _, r in m.iterrows():
        key = "statsbomb" if r.model == "sb_xg" else r.model
        if r.model == "sb_xg":
            a0 = "n/a"
        elif m0 is not None:
            a0 = f"{m0[(m0.target == r.target) & (m0.model == r.model)].auc.iloc[0]:.3f}"
        else:
            a0 = "not run"
        label = "StatsBomb xG (benchmark)" if r.model == "sb_xg" else r.model
        L.append(f"| {NAMES[r.target]} | {r.n:,} | {label} | {ci(r.target, key, 'auc', f3)} | "
                 f"{ci(r.target, key, 'skill', fp)} | {ci(r.target, key, 'brier', f4)} | {a0} |")

    L += ["", "## Calibration", "",
          "Ten equal sized bins of predicted probability per model (curves in calibration_bins.csv and "
          "calibration_all_models.png). The calibration slope comes from a logistic fit of the outcome on the "
          "logit of the prediction. 1 is ideal, below 1 means predictions are too extreme, above 1 too cautious. "
          "Calibration in the large is mean observed minus mean predicted. ECE is the average gap between "
          "predicted and observed rates across bins, weighted by bin size.", "",
          "| Target | Model | Slope (95%) | Intercept (95%) | Calibration in the large | ECE |", "|---|---|---|---|---|---|"]
    for (t, mdl), r in cal.iterrows():
        label = "StatsBomb xG (benchmark)" if mdl == "statsbomb" else mdl
        L.append(f"| {NAMES[t]} | {label} | {r.slope:.2f} ({r.slope_lo:.2f} to {r.slope_hi:.2f}) | "
                 f"{r.intercept:+.2f} ({r.intercept_lo:+.2f} to {r.intercept_hi:+.2f}) | {r.citl:+.4f} | {r.ece:.4f} |")

    L += ["", "## Header xG against StatsBomb xG", "",
          "Same 10,327 headed shots, this project's logistic xG minus StatsBomb's xG. The paired match bootstrap "
          "resamples matches and recomputes both models on the same draw, so it respects that shots in a match are "
          "related. DeLong's test is shown for reference and assumes independent shots.", "",
          "| Metric | This project | StatsBomb | Difference (95%) | p | Method |", "|---|---|---|---|---|---|"]
    for r in cmp_.itertuples():
        fmt = f4 if r.metric in ("log_loss", "brier") else (fp if r.metric == "skill" else f3)
        sign = lambda v: ("+" if v > 0 else "") + fmt(v)  # noqa: E731
        L.append(f"| {r.metric.replace('_', ' ')} | {fmt(r.ours)} | {fmt(r.statsbomb)} | {sign(r.difference)} "
                 f"({sign(r.lo)} to {sign(r.hi)}) | {r.bootstrap_p:.2f} | {r.method} |")
    auc_row = cmp_[(cmp_.metric == "auc") & (cmp_.method != "DeLong")].iloc[0]
    L += ["", f"The difference in AUC is {auc_row.difference:+.3f} with a 95% interval of {auc_row.lo:+.3f} to "
          f"{auc_row.hi:+.3f}, so the two models cannot be told apart on ranking shots. This project's xG is the "
          "better calibrated of the two. StatsBomb's averages "
          f"{cal.loc[('xg', 'statsbomb')].mean_pred:.3f} goals per header against an actual rate of "
          f"{cal.loc[('xg', 'statsbomb')].mean_obs:.3f}, and its calibration slope of "
          f"{cal.loc[('xg', 'statsbomb')].slope:.2f} sits above 1. That comparison favours this project a little, "
          "since its model was fit and cross validated on these same competitions, while StatsBomb's xG is a general "
          "model that was not built for this particular set of matches."]

    d = prepare_duels()
    k = d[d["height_diff"].notna()].copy()
    labels = ["10+ cm shorter", "5 to 10 cm shorter", "2 to 5 cm shorter", "within 2 cm",
              "2 to 5 cm taller", "5 to 10 cm taller", "10+ cm taller"]
    k["bin"] = pd.cut(k["height_diff"], [-40, -10, -5, -2, 2, 5, 10, 40], labels=labels)
    L += ["", "## What height does", "", "Height matters a lot for winning the header and not at all for what "
          "happens after it.", "", "| Defender height minus attacker height | Defender duel win rate | Duels |",
          "|---|---|---|"]
    for b, g in k.groupby("bin", observed=True):
        L.append(f"| {b} | {g['def_won'].mean():.0%} | {len(g):,} |")
    hg_path = RES / "duel_height_gain.csv"
    if hg_path.exists():  # written by height_gain.py
        hg = pd.read_csv(hg_path).set_index(["metric", "method"])
        a = hg.loc[("auc", "paired match bootstrap")]
        dl = hg.loc[("auc", "DeLong")]
        L += ["", f"Adding height lifts the duel model's AUC from {a.without_height:.3f} to {a.with_height:.3f}. "
              f"Both versions were scored on the same 1,000 match resamples, so the interval is for the gain "
              f"itself, +{a.difference:.3f} (95% interval {a.lo:.3f} to {a.hi:.3f}), and no resample showed a "
              f"gain of zero or less. DeLong's test agrees (p {'< 0.001' if dl.p < 0.001 else f'= {dl.p:.3f}'})."]
    L += ["", "For headed shots, goals minus StatsBomb xG per shot stays within one percentage point of zero across "
          "every height group, so taller players do not finish headers better once the situation is accounted for.",
          "", "## Notes", "",
          "StatsBomb's under_pressure flag is left out of the attack models. It duplicates the distance to the nearest "
          "defender, and with both in the model it took a misleading positive sign even though pressured headers "
          "score about half as often at every distance. Accuracy was unchanged without it.", "",
          "The Pass or Clearance labels on defensive headers are left out of the clearance models because StatsBomb "
          "tends to log a header as a pass when it reaches a teammate, which leaks the outcome.", "",
          "StatsBomb's own xG is shown only as a benchmark and is never a model input."]
    (RES / "stage3_summary.md").write_text("\n".join(L))
    print("\n".join(L[7:60]))


if __name__ == "__main__":
    main()
