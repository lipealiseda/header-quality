"""Do strength, jumping and speed explain header skill? A test with EA FC ratings.

Free data has no physical tests, so EA FC (FIFA 15 to 22) ratings are used as rough
proxies. They are video game ratings set by EA's scouts, partly by watching real
matches, so they are opinions about players and not measurements. They are kept
out of the main models on purpose (see modeling.physical_columns) and tested here
in two ways.

1. Model test. Refit the duel and header models with EA ratings added (strength,
   jumping, heading accuracy, sprint speed, plus weight) and compare accuracy on the
   same match grouped folds.
2. Player test. Take each player's shrunk duels-above-expected number from Stage 4
   (the model behind it knows heights but no EA ratings) and check which EA ratings
   line up with it. This asks whether the players who beat their height are the ones
   EA rates as good jumpers, strong, or good in the air.

Output
    results/ea_ratings.md
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES, run  # noqa: E402

ATTR = {"ea_jumping": "Jumping", "ea_strength": "Strength", "ea_heading": "Heading accuracy",
        "ea_sprint": "Sprint speed", "weight_kg": "Weight"}


def model_test():
    """Same rows, same folds, with and without EA ratings."""
    import models_attack
    import models_defense
    from modeling import physical_columns

    rows = []
    # duels
    d = models_defense.prepare_duels()
    base_num = ["x", "wide", "in_own_box", "dlv_length", "dlv_pace", "dlv_start_x", "f360_opp_within_3m",
                "def_height_cm", "att_height_cm", "height_diff"]
    cat = models_defense.DLV_CAT + ["play_pattern", "def_pos", "att_pos"]
    os.environ["HQ_WITH_EA"] = "1"
    ea_cols = [c for c in physical_columns(d, "def_") + physical_columns(d, "att_") if "height" not in c]
    os.environ.pop("HQ_WITH_EA")
    for label, num in (("height only", base_num), ("height + EA ratings", base_num + ea_cols)):
        m, _, _ = run(d, num, cat, "def_won", "duel")
        rows.append(m.assign(inputs=label))
    # headed shots, goal and on target
    s = models_attack.prepare()
    base = models_attack.NUM + models_attack.BOOL + ["height_cm"]
    ea_s = [c for c in ATTR if c in s.columns and s[c].notna().mean() > 0.3]
    for target, name in (("goal", "xg"), ("on_target", "xot")):
        for label, num in (("height only", base), ("height + EA ratings", base + ea_s)):
            m, _, _ = run(s, num, models_attack.CAT, target, name)
            rows.append(m.assign(inputs=label))
    out = pd.concat(rows)
    return out[out["model"].isin(["logistic", "boosting"])], ea_cols, ea_s


def _wls(q):
    X = q[list(ATTR)]
    y = q["shrunk_rate"].values * 100
    w = q["n"].values
    Z = (X - X.mean()) / X.std()
    A = np.column_stack([np.ones(len(Z)), Z.values])
    W = np.sqrt(w)[:, None]
    beta, *_ = np.linalg.lstsq(A * W, y * W[:, 0], rcond=None)
    fitted = A @ beta
    r2 = 1 - np.sum(w * (y - fitted) ** 2) / np.sum(w * (y - np.average(y, weights=w)) ** 2)
    return beta[1:], r2


def player_test(boot=2000):
    """Correlations and the joint regression, each with a 95% interval from
    resampling players with replacement."""
    rng = np.random.default_rng(3)
    r = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    ph = pd.read_csv(PROC / "player_physical.csv.gz")
    q = r[r["qualified"]].merge(ph[["player_id"] + list(ATTR)], on="player_id", how="left")
    q = q.dropna(subset=list(ATTR)).reset_index(drop=True)
    corr = []
    for a, label in ATTR.items():
        rho, p = spearmanr(q[a], q["shrunk_rate"])
        corr.append({"attribute": label, "key": a, "rho": rho, "p": p, "n": len(q)})
    corr = pd.DataFrame(corr)
    beta, r2 = _wls(q)
    bs_rho, bs_beta, bs_r2 = [], [], []
    for _ in range(boot):
        s = q.iloc[rng.integers(0, len(q), len(q))]
        bs_rho.append([spearmanr(s[a], s["shrunk_rate"])[0] for a in ATTR])
        b, rr = _wls(s)
        bs_beta.append(b)
        bs_r2.append(rr)
    bs_rho, bs_beta = np.array(bs_rho), np.array(bs_beta)
    corr["lo"], corr["hi"] = np.quantile(bs_rho, 0.025, axis=0), np.quantile(bs_rho, 0.975, axis=0)
    coefs = pd.DataFrame({"attribute": [ATTR[c] for c in ATTR], "per_sd": beta,
                          "lo": np.quantile(bs_beta, 0.025, axis=0), "hi": np.quantile(bs_beta, 0.975, axis=0)})
    r2_ci = (float(np.quantile(bs_r2, 0.025)), float(np.quantile(bs_r2, 0.975)))
    corr.to_csv(RES / "ea_correlations.csv", index=False)
    return (q, corr.sort_values("rho", ascending=False), coefs.sort_values("per_sd", ascending=False),
            r2, r2_ci, len(q))


def main():
    metrics, ea_cols, ea_s = model_test()
    q, corr, coefs, r2, r2_ci, n_reg = player_test()
    ea = pd.read_csv(PROC / "player_physical.csv.gz").set_index("player_id")["ea_jumping"]
    sh = pd.read_csv(PROC / "headed_shots.csv.gz", usecols=["player_id"])
    du = pd.read_csv(PROC / "aerial_duels.csv.gz", usecols=["winner_id", "loser_id"])
    cov_shots = sh["player_id"].map(ea).notna().mean()
    cov_duels = (du["winner_id"].map(ea).notna() & du["loser_id"].map(ea).notna()).mean()

    L = ["# Do strength, jumping and speed explain header skill?", "",
         "EA FC ratings (FIFA 15 to 22) are used as rough proxies for physical traits. They are judgments by EA's "
         "scouts, not physical tests, and they are kept out of the main models. Matching uses name, nationality, "
         "birth year and club, and a match is dropped when EA's height is more than 5 cm from Transfermarkt's. "
         f"EA ratings were found for {ph_count():,} players, covering {cov_shots:.0%} of headed shots and "
         f"{cov_duels:.0%} of duels (both players).", "",
         "## 1. Do EA ratings make the models more accurate?", "",
         "| Model | Target | Inputs | Log loss | AUC |", "|---|---|---|---|---|"]
    names = {"duel": "Aerial duel won", "xg": "Header is a goal", "xot": "Header on target"}
    for _, r in metrics.iterrows():
        L.append(f"| {r.model} | {names[r.target]} | {r.inputs} | {r.log_loss:.4f} | {r.auc:.3f} |")
    L += ["", "## 2. Do the players who beat expectations have better EA physical ratings?", "",
          f"Players with 100+ aerial duels and an EA match ({len(q)} players). Their duels-above-expected number "
          "comes from a model that knows both players' heights but no EA ratings. Spearman correlation between "
          "that number and each EA rating.", "",
          "| EA rating | Spearman correlation (95% interval) | p value | Players |", "|---|---|---|---|"]
    for _, r in corr.iterrows():
        L.append(f"| {r.attribute} | {r.rho:+.2f} ({r.lo:+.2f} to {r.hi:+.2f}) | {r.p:.3f} | {r.n} |")
    L += ["", f"All five together (weighted regression, standardised ratings, {n_reg} players) explain "
          f"{r2:.0%} of the spread in duels above expected (95% interval {r2_ci[0]:.0%} to {r2_ci[1]:.0%}). "
          "Change in duels won above expected per 100 for one standard deviation of each rating, holding the "
          "others fixed. Intervals come from resampling the players 2,000 times.", "",
          "| EA rating | Per 1 SD (95% interval) |", "|---|---|"]
    for _, r in coefs.iterrows():
        L.append(f"| {r.attribute} | {r.per_sd:+.1f} ({r.lo:+.1f} to {r.hi:+.1f}) |")
    top = q.nlargest(5, "shrunk_rate")[["name", "pos_group", "shrunk_rate", "ea_jumping", "ea_strength", "ea_heading"]]
    L += ["", "## The top five players in the air, with their EA ratings", "",
          "| Player | Pos | Above expected per 100 | Jumping | Strength | Heading |", "|---|---|---|---|---|---|"]
    for r in top.itertuples():
        L.append(f"| {r.name} | {r.pos_group} | {r.shrunk_rate * 100:+.1f} | {r.ea_jumping:.0f} | "
                 f"{r.ea_strength:.0f} | {r.ea_heading:.0f} |")
    L += ["", "## Caveat", "",
          "EA's heading accuracy rating is partly set by watching how players do in the air, so its link with duels "
          "above expected is partly circular. Jumping and strength are less directly tied to aerial results, but "
          "they are still opinions, not measurements.", "",
          "EA FC ratings come from the Kaggle dataset by Stefano Leone (scraped from sofifa.com) and are not "
          "republished here."]
    (RES / "ea_ratings.md").write_text("\n".join(L))
    print("\n".join(L))


def ph_count():
    return int(pd.read_csv(PROC / "player_physical.csv.gz")["ea_jumping"].notna().sum())


if __name__ == "__main__":
    main()
