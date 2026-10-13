"""Stage 4. Header quality rankings.

For every player and metric we compare what happened with what the Stage 3 model
expected (out of fold predictions, so a player is never judged by a model that saw
his own headers). Raw "above expected" numbers are noisy for small samples, so each
one is shrunk toward zero with empirical Bayes

    shrunk = raw_rate * tau2 / (tau2 + sigma2 / n)

where raw_rate is (actual minus expected) per event, sigma2 is the average event
level noise p(1 - p) for that player, n is his number of events and tau2 is how
much true skill varies between players, estimated from the data. A player with few
headers is pulled almost all the way to zero, one with hundreds keeps most of his
number.

We also report split half reliability. Each player's events are split randomly in
two and the above-expected rates of the halves are correlated across players. Near
zero means the metric is mostly luck, higher means it captures a repeatable skill.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES, SEED  # noqa: E402

RNG = np.random.default_rng(SEED)
DEFENDERS = {"CB", "FB"}


def best_col(metrics_file, target, prefix):
    m = pd.read_csv(RES / metrics_file)
    m = m[(m["target"] == target) & m["model"].isin(["logistic", "boosting"])].set_index("model")
    return f"{prefix}_gbm" if m.loc["boosting", "log_loss"] <= m.loc["logistic", "log_loss"] else f"{prefix}_lr"


def tau2_estimate(g, min_n=30):
    """Method of moments. Variance of players' raw rates minus the part explained
    by sampling noise. Only players with a decent sample are used."""
    g = g[g["n"] >= min_n]
    if len(g) < 20:
        return 0.0
    w = g["n"] / g["n"].sum()
    mean = np.sum(w * g["raw_rate"])
    total = np.sum(w * (g["raw_rate"] - mean) ** 2)
    noise = np.sum(w * g["sigma2"] / g["n"])
    return max(total - noise, 1e-8)


def player_table(ev, actual, expected, min_n):
    """ev has one row per event with player_id, actual (0/1) and expected (prob)."""
    ev = ev.assign(resid=ev[actual] - ev[expected], var=ev[expected] * (1 - ev[expected]))
    g = ev.groupby("player_id").agg(n=("resid", "size"), actual=(actual, "sum"), expected=(expected, "sum"),
                                    resid=("resid", "sum"), sigma2=("var", "mean")).reset_index()
    g["raw_rate"] = g["resid"] / g["n"]
    tau2 = tau2_estimate(g)
    g["weight"] = tau2 / (tau2 + g["sigma2"] / g["n"])
    g["shrunk_rate"] = g["raw_rate"] * g["weight"]
    # a rough 80% interval for the shrunk rate (posterior sd under a normal model)
    post_sd = np.sqrt(1 / (1 / tau2 + g["n"] / g["sigma2"])) if tau2 > 0 else 0
    g["lo80"], g["hi80"] = g["shrunk_rate"] - 1.28 * post_sd, g["shrunk_rate"] + 1.28 * post_sd
    g["qualified"] = g["n"] >= min_n
    return g, tau2


def split_half(ev, actual, expected, min_n, reps=50):
    """Average correlation between the two random halves, Spearman Brown corrected
    to full sample length."""
    ev = ev[["player_id", "match_id", actual, expected]].copy()
    ev["resid"] = ev[actual] - ev[expected]
    keep = ev.groupby("player_id")["resid"].transform("size") >= min_n
    ev = ev[keep]
    matches = ev["match_id"].unique()
    rs = []
    for _ in range(reps):
        # halves are split by match, so one match never feeds both halves
        side = pd.Series(RNG.integers(0, 2, len(matches)), index=matches)
        half = ev["match_id"].map(side).values
        t = ev.assign(h=half).groupby(["player_id", "h"])["resid"].mean().unstack()
        t = t.dropna()
        if len(t) > 10:
            rs.append(t[0].corr(t[1]))
    r = float(np.mean(rs)) if rs else np.nan
    return {"players": int(ev["player_id"].nunique()), "split_half_r": r,
            "full_length_reliability": 2 * r / (1 + r) if r == r and r > -1 else np.nan}


def player_info():
    pl = pd.read_csv(PROC / "players.csv.gz")
    pl["name"] = pl["player_nickname"].fillna(pl["player_name"])
    pm = pd.read_csv(PROC / "player_matches.csv.gz")
    from models_defense import POS_GROUP
    pm["pos_group"] = pm["main_position"].map(POS_GROUP).fillna("other")
    pos = pm.groupby("player_id").apply(lambda s: s.groupby("pos_group")["minutes"].sum().idxmax(),
                                        include_groups=False).rename("pos_group")
    team = pm[~pm["competition"].isin(["FIFA World Cup", "UEFA Euro", "Copa America",
                                       "African Cup of Nations"])]
    team = team.groupby("player_id")["team"].agg(lambda s: s.value_counts().index[0]).rename("main_club")
    seasons = pm.groupby("player_id")["comp_season"].agg(lambda s: ", ".join(sorted(set(s))[:3]) +
                                                         (" ..." if s.nunique() > 3 else "")).rename("seasons")
    mins = pm.groupby("player_id")["minutes"].sum().rename("minutes")
    ph = pd.read_csv(PROC / "player_physical.csv.gz")[["player_id", "height_cm"]]
    return (pl[["player_id", "name", "country"]].merge(pos, on="player_id", how="left")
            .merge(team, on="player_id", how="left").merge(seasons, on="player_id", how="left")
            .merge(mins, on="player_id", how="left").merge(ph, on="player_id", how="left"))


def main():
    info = player_info()
    reliability, tables = [], {}

    # ------------------------------------------------------------------ attack
    a = pd.read_csv(PROC / "attack_predictions.csv.gz")
    xg_col = best_col("attack_metrics.csv", "xg", "xg")
    xot_col = best_col("attack_metrics.csv", "xot", "xot")
    for actual, expected, key, min_n in (("goal", xg_col, "goals_vs_xg", 25),
                                         ("on_target", xot_col, "on_target_vs_expected", 25)):
        g, tau2 = player_table(a, actual, expected, min_n)
        tables[key] = g
        reliability.append({"metric": key, "min_events": min_n, "tau2": tau2, **split_half(a, actual, expected, min_n)})

    # ------------------------------------------------------------------ aerial duels
    d = pd.read_csv(PROC / "duel_predictions.csv.gz")
    dcol = d["best"].iloc[0]
    # every duel counts for both players, from each one's point of view
    both = pd.concat([
        pd.DataFrame({"player_id": d["def_player_id"], "match_id": d["match_id"], "won": d["def_won"],
                      "p": d[dcol], "role": "defending"}),
        pd.DataFrame({"player_id": d["att_player_id"], "match_id": d["match_id"], "won": 1 - d["def_won"],
                      "p": 1 - d[dcol], "role": "attacking"}),
    ], ignore_index=True)
    # the duel model uses both players' heights, so a player with no height on file
    # would get his height counted as skill. Only players with a known height are ranked.
    known = set(pd.read_csv(PROC / "player_physical.csv.gz").dropna(subset=["height_cm"])["player_id"])
    both = both[both["player_id"].isin(known)]
    g, tau2 = player_table(both, "won", "p", 100)
    tables["duels_vs_expected"] = g
    reliability.append({"metric": "duels_vs_expected", "min_events": 100, "tau2": tau2,
                        **split_half(both, "won", "p", 100)})

    # ------------------------------------------------------------------ clearances
    c = pd.read_csv(PROC / "clearance_predictions.csv.gz")
    s10 = best_col("defense_metrics.csv", "shot10", "shot10")
    kp = best_col("defense_metrics.csv", "keep", "keep")
    # flip so that positive always means good for the defender
    c["no_shot"] = 1 - c["opp_shot_10s"]
    c["p_no_shot"] = 1 - c[s10]
    g, tau2 = player_table(c, "no_shot", "p_no_shot", 75)
    tables["shots_prevented"] = g
    reliability.append({"metric": "shots_prevented", "min_events": 75, "tau2": tau2,
                        **split_half(c, "no_shot", "p_no_shot", 75)})
    ck = c[c["next_team_won"].notna()].copy()
    g, tau2 = player_table(ck, "next_team_won", kp, 75)
    tables["next_ball_vs_expected"] = g
    reliability.append({"metric": "next_ball_vs_expected", "min_events": 75, "tau2": tau2,
                        **split_half(ck, "next_team_won", kp, 75)})

    rel = pd.DataFrame(reliability)
    rel.to_csv(RES / "metric_reliability.csv", index=False)
    print(rel.round(3).to_string(index=False))

    for key, g in tables.items():
        out = info.merge(g, on="player_id").sort_values("shrunk_rate", ascending=False)
        out.to_csv(RES / f"rank_{key}.csv", index=False)
    return tables, info


if __name__ == "__main__":
    main()
