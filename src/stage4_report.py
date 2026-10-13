"""Write results/stage4_rankings.md from the ranking tables and model drivers."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import RES  # noqa: E402

NICE = {
    "dist": "Distance to goal", "angle": "Angle to goal", "gk_dist_shooter": "Keeper distance from header",
    "gk_dist_goal": "Keeper distance off his line", "gk_in_cone": "Keeper in the shooting lane",
    "nearest_opp_dist": "Space to nearest defender", "n_def_in_cone": "Defenders in the shooting lane",
    "n_att_in_cone": "Teammates in the shooting lane", "n_opp_within_2m": "Defenders within 2 yards",
    "n_opp_in_box": "Defenders in the box", "aerial_won": "Header won a contested duel",
    "dlv_pace": "Speed of the delivery", "dlv_length": "Length of the delivery",
    "dlv_flight_time": "Delivery flight time", "dlv_technique": "Inswinger, outswinger or straight",
    "dlv_type": "Delivery type", "dlv_height": "Delivery height", "dlv_start_x": "Where the delivery started (length)",
    "dlv_wide": "How wide the delivery started", "turn_angle": "How much the header redirects the ball",
    "diving": "Diving header", "in_six": "Inside the six yard box", "score_diff": "Score difference",
    "height_cm": "Player height", "def_height_cm": "Defender height", "att_height_cm": "Attacker height",
    "height_diff": "Height difference", "x": "Distance from own goal line", "wide": "How wide the header was",
    "in_own_box": "Inside own box", "def_pos": "Defender's position", "att_pos": "Attacker's position",
    "play_pattern": "Phase of play", "f360_opp_within_3m": "Opponents within 3 yards (360 data)",
    "dist_own_goal": "Distance from own goal", "under_pressure": "Under pressure",
    "pos_group": "Player's position", "f360_opp_within_10m": "Opponents within 10 yards (360 data)",
    "f360_nearest_opp": "Nearest opponent (360 data)",
}


def drivers(name, k=6):
    t = pd.read_csv(RES / f"{name}_gbm_importance.csv").head(k)
    total = pd.read_csv(RES / f"{name}_gbm_importance.csv")["importance"].clip(lower=0).sum()
    rows = [f"| {i + 1} | {NICE.get(r.feature, r.feature)} | {r.importance / total:.0%} |"
            for i, r in enumerate(t.itertuples())]
    return ["| Rank | Factor | Share of importance |", "|---|---|---|"] + rows


def fmt_rank(df, k, label, scale=100, extra_filter=None, ascending=False):
    d = df[df["qualified"]]
    if extra_filter is not None:
        d = d[extra_filter(d)]
    d = d.sort_values("shrunk_rate", ascending=ascending).head(k)
    lines = [f"| # | Player | Pos | Main club | Height | {label} | Actual | Expected | Above expected per 100 (shrunk) | 80% range |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(d.itertuples()):
        h = f"{r.height_cm:.0f}" if r.height_cm == r.height_cm else "?"
        lines.append(f"| {i + 1} | {r.name} | {r.pos_group} | {r.main_club} | {h} | {r.n} | {r.actual:.0f} | "
                     f"{r.expected:.1f} | {r.shrunk_rate * scale:+.1f} | {r.lo80 * scale:+.1f} to {r.hi80 * scale:+.1f} |")
    return lines


def main():
    rel = pd.read_csv(RES / "metric_reliability.csv").set_index("metric")
    duels = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    xot = pd.read_csv(RES / "rank_on_target_vs_expected.csv")
    gxg = pd.read_csv(RES / "rank_goals_vs_xg.csv")
    sp = pd.read_csv(RES / "rank_shots_prevented.csv")
    defenders = lambda d: d["pos_group"].isin(["CB", "FB"])  # noqa: E731
    forwards = lambda d: d["pos_group"].isin(["ST", "W", "AM"])  # noqa: E731

    L = ["# Stage 4 header quality rankings", "",
         "Data is every men's match in StatsBomb open data. Most of the volume comes from the four full 2015/16 "
         "seasons (Premier League, La Liga, Serie A, Ligue 1), so these are mostly 2015/16 rankings. Players are "
         "compared with the Stage 3 models' out of fold predictions, so a player is never judged by a model that "
         "saw his own headers.", "",
         "Above-expected numbers are shrunk toward zero with empirical Bayes. A player with few headers is pulled "
         "close to average, one with hundreds keeps most of his number. The 80% range shows how sure we are.", "",
         "## Which metrics measure a real skill", "",
         "Each player's matches are split randomly into two halves and his above-expected rate in one half is "
         "correlated with the other, across all qualified players. A reliability near 0 means the metric is mostly "
         "luck at these sample sizes, and values above about 0.5 mean it is repeatable.", "",
         "| Metric | Minimum sample | Players | Reliability |", "|---|---|---|---|"]
    names = {"goals_vs_xg": "Headed goals minus xG", "on_target_vs_expected": "Headers on target vs expected",
             "duels_vs_expected": "Aerial duels won vs expected", "shots_prevented": "Opponent shots prevented after clearances",
             "next_ball_vs_expected": "Next ball won after defensive headers vs expected"}
    for m, r in rel.iterrows():
        L.append(f"| {names[m]} | {r.min_events:.0f} | {r.players:.0f} | {r.full_length_reliability:.2f} |")
    L += ["", "Aerial duel ability is clearly a skill, even after the model accounts for both players' heights, "
          "positions, the delivery and the location. Heading accuracy is weakly repeatable. Headed finishing "
          "(goals minus xG) cannot be told apart from luck in this data, so that table below is descriptive only.", ""]

    L += ["## Attack", "", "### What makes a header a goal", ""] + drivers("xg") + [
        "", "### What makes a header land on target", ""] + drivers("xot") + [
        "", "### Headers on target above expected (forwards, 25+ headed shots)", ""]
    L += fmt_rank(xot, 10, "Headed shots", extra_filter=forwards)
    L += ["", "### Headed goals minus xG (25+ headed shots, descriptive only, reliability "
          f"{rel.loc['goals_vs_xg', 'full_length_reliability']:.2f})", "",
          "| # | Player | Pos | Main club | Headed shots | Goals | xG | Goals minus xG |", "|---|---|---|---|---|---|---|---|"]
    g = gxg[gxg["qualified"]].assign(gmx=lambda d: d["actual"] - d["expected"]).sort_values("gmx", ascending=False)
    for i, r in enumerate(g.head(10).itertuples()):
        L.append(f"| {i + 1} | {r.name} | {r.pos_group} | {r.main_club} | {r.n} | {r.actual:.0f} | {r.expected:.1f} | {r.gmx:+.1f} |")
    L += ["", "### Strongest forwards in the air (aerial duels won vs expected, 100+ duels)", ""]
    L += fmt_rank(duels, 10, "Duels", extra_filter=forwards)

    L += ["", "## Defense", "", "### What decides an aerial duel", ""] + drivers("duel") + [
        "", "### What makes the opponent shoot within 10 seconds of a defensive header", ""] + drivers("shot10") + [
        "", "### Best defenders in the air (aerial duels won vs expected, 100+ duels)", ""]
    L += fmt_rank(duels, 10, "Duels", extra_filter=defenders)
    L += ["", "### Weakest defenders in the air", ""]
    L += fmt_rank(duels, 5, "Duels", extra_filter=defenders, ascending=True)
    L += ["", "### Clearances that stop the opponent shooting (75+ defensive headers, weak signal, reliability "
          f"{rel.loc['shots_prevented', 'full_length_reliability']:.2f})", ""]
    L += fmt_rank(sp, 10, "Def. headers", extra_filter=defenders)
    L += ["", "## Caveats", "",
          "- Heights come from Transfermarkt and are missing for about 10% of headers. Duel rankings only include players with a known height.",
          "- Free data has no measure of strength, jumping or speed. Whatever those add shows up inside a player's above-expected number, which is the point of the ranking but means we cannot say which physical trait drives it.",
          "- Club seasons outside 2015/16 cover only one team (mostly Barcelona), so those players and their opponents are over represented.",
          "- Expected values come from models with modest accuracy for duels (AUC 0.67), so some of what looks like skill could be context the model misses, such as a team's set piece routines.",
          "- Team effects look small. Across 496 players with 100+ duels, a player's above-expected duel rate barely tracks his teammates' rate (correlation 0.10), and the spread between teams is about a third of the spread between players."]
    (RES / "stage4_rankings.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
