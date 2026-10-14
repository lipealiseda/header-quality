"""How much each input matters to the aerial duel model, measured carefully.

Method: permutation importance. Fit the model on training matches, then on the held
out matches shuffle one input (or a group of inputs) at random and measure how much
worse the predictions get, as the increase in log loss. Shuffling breaks the link
between that input and the outcome while keeping everything else the same, so the
damage done is what the model was getting from that input.

Two versions are reported.
  Single inputs, as in the original claim ("height difference is the third biggest
  driver"), from modeling.boosting_importance (one fold, five shuffles).
  Grouped inputs over all five match grouped folds and three shuffles each. Related
  inputs are shuffled together (for example both heights and their difference),
  because shuffling one of several overlapping inputs understates the group, since
  the model can still lean on the others.
A drop column check (refit without any height input) is also shown, from the
comparison run in models_defense.py with HQ_NO_PHYSICAL=1.

Outputs
    results/duel_importance_grouped.csv, results/duel_importance.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import RES, boosting  # noqa: E402
from models_defense import DLV_CAT, prepare_duels  # noqa: E402

RNG = np.random.default_rng(5)
NUM = ["x", "wide", "in_own_box", "dlv_length", "dlv_pace", "dlv_start_x", "f360_opp_within_3m",
       "def_height_cm", "att_height_cm", "height_diff"]
CAT = DLV_CAT + ["play_pattern", "def_pos", "att_pos"]
GROUPS = {
    "Where the duel happens (distance from goal line, width, inside the box)": ["x", "wide", "in_own_box"],
    "Where the delivery started": ["dlv_start_x"],
    "Height (both players and the difference)": ["def_height_cm", "att_height_cm", "height_diff"],
    "Phase of play (goal kick, corner, open play and so on)": ["play_pattern"],
    "Positions of the two players": ["def_pos", "att_pos"],
    "Type and flight of the delivery (type, height, length, speed)": ["dlv_type", "dlv_height", "dlv_length", "dlv_pace"],
    "Crowding around the duel (360 data)": ["f360_opp_within_3m"],
}


def main(repeats=3):
    d = prepare_duels()
    X, y, g = d[NUM + CAT], d["def_won"].astype(int).values, d["match_id"].values
    rows = []
    for fold, (tr, te) in enumerate(GroupKFold(5).split(X, y, g)):
        m = boosting(NUM, CAT).fit(X.iloc[tr], y[tr])
        Xte = X.iloc[te].reset_index(drop=True)
        base = log_loss(y[te], m.predict_proba(Xte)[:, 1])
        for name, cols in GROUPS.items():
            for r in range(repeats):
                Xp = Xte.copy()
                perm = RNG.permutation(len(Xp))
                Xp[cols] = Xte[cols].iloc[perm].values  # same shuffle for the whole group
                rows.append({"fold": fold, "repeat": r, "group": name,
                             "increase": log_loss(y[te], m.predict_proba(Xp)[:, 1]) - base})
        print("fold", fold, "done", flush=True)
    t = pd.DataFrame(rows)
    t["share"] = t["increase"] / t.groupby(["fold", "repeat"])["increase"].transform(lambda s: s.clip(lower=0).sum())
    t["rank"] = t.groupby(["fold", "repeat"])["increase"].rank(ascending=False)
    summ = (t.groupby("group").agg(increase=("increase", "mean"), increase_sd=("increase", "std"),
                                  share=("share", "mean"), share_min=("share", "min"), share_max=("share", "max"),
                                  rank_mean=("rank", "mean"), rank_min=("rank", "min"), rank_max=("rank", "max"))
            .sort_values("increase", ascending=False).reset_index())
    summ.to_csv(RES / "duel_importance_grouped.csv", index=False)

    single = pd.read_csv(RES / "duel_gbm_importance.csv")
    single["share"] = single["importance"].clip(lower=0) / single["importance"].clip(lower=0).sum()
    single["rank"] = np.arange(1, len(single) + 1)
    m_full = pd.read_csv(RES / "defense_metrics.csv")
    m_noh = pd.read_csv(RES / "defense_metrics_noheight.csv")
    f = lambda df: df[(df.target == "duel") & (df.model == "boosting")].iloc[0]  # noqa: E731
    full, noh = f(m_full), f(m_noh)

    L = ["# What drives the aerial duel model", "",
         "Permutation importance: shuffle an input on held out matches and measure how much the log loss gets worse. "
         "Bigger damage means the model relied on that input more.", "",
         "## Single inputs (the method behind the original claim)", "",
         "Gradient boosting, one held out fold of matches, each input shuffled five times.", "",
         "| Rank | Input | Share |", "|---|---|---|"]
    for r in single.head(8).itertuples():
        L.append(f"| {r.rank} | {r.feature} | {r.share:.0%} |")
    L += ["", "Height difference ranks third on its own. But the model also sees both raw heights, which carry "
          "overlapping information, so shuffling one height input at a time understates what height as a whole "
          "is worth.", "",
          "## Grouped inputs over all five folds", "",
          "Related inputs are shuffled together. Each of the 5 folds is shuffled 3 times, giving 15 measurements "
          "per group. The range shows the lowest and highest share and rank across those 15.", "",
          "| Rank | Group of inputs | Share (range) | Rank range | Log loss increase |", "|---|---|---|---|---|"]
    for i, r in enumerate(summ.itertuples()):
        L.append(f"| {i + 1} | {r.group} | {r.share:.0%} ({r.share_min:.0%} to {r.share_max:.0%}) | "
                 f"{int(r.rank_min)} to {int(r.rank_max)} | {r.increase:.4f} |")
    L += ["", "## Drop column check", "",
          f"Refitting the duel model with every height input removed lowers AUC from {full.auc:.3f} to {noh.auc:.3f} "
          f"and raises log loss from {full.log_loss:.4f} to {noh.log_loss:.4f}. This measures what height adds that "
          "no other input can stand in for."]
    (RES / "duel_importance.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
