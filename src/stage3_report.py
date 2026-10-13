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
    L = ["# Stage 3 model results", "",
         "Match grouped 5 fold cross validation on all men's StatsBomb open data matches (2,651 matches). Lower log "
         "loss and Brier are better, higher AUC is better. Skill is the share of log loss removed compared with "
         "always predicting the base rate.", "",
         "Height comes from Transfermarkt (CC0) and is known for 90% of headed shots, 89% of defensive headers and "
         "86% of duels (both players). Missing heights are handled by the models (median plus a missing flag for "
         "logistic regression, native handling in boosting). The last column refits the same model with every "
         "height input removed.", "",
         "| Target | Rows | Model | Log loss | Brier | AUC | Skill | AUC without height |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in m.iterrows():
        if r.model == "sb_xg":
            a0 = "n/a"
        elif m0 is not None:
            a0 = f"{m0[(m0.target == r.target) & (m0.model == r.model)].auc.iloc[0]:.3f}"
        else:
            a0 = "not run"
        label = "StatsBomb xG (benchmark)" if r.model == "sb_xg" else r.model
        L.append(f"| {NAMES[r.target]} | {r.n:,} | {label} | {r.log_loss:.4f} | {r.brier:.4f} | {r.auc:.3f} | "
                 f"{r.skill_vs_base_rate:.1%} | {a0} |")

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
    print("\n".join(L[7:20]))


if __name__ == "__main__":
    main()
