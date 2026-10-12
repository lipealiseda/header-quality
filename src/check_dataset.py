"""Stage 2 checks. Prints row counts, label rates and missing values so problems
show up before any modelling. Writes data/processed/dataset_report.md."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"


def main():
    s = pd.read_csv(PROC / "headed_shots.csv.gz", low_memory=False)
    d = pd.read_csv(PROC / "aerial_duels.csv.gz", low_memory=False)
    f = pd.read_csv(PROC / "defensive_headers.csv.gz", low_memory=False)
    pm = pd.read_csv(PROC / "player_matches.csv.gz")
    lines = ["# Dataset report", ""]

    def add(txt=""):
        lines.append(txt)
        print(txt)

    add(f"Matches {pm['match_id'].nunique():,}, players {pm['player_id'].nunique():,}")
    add(f"Headed shots {len(s):,}, goals {s['goal'].sum():,} ({s['goal'].mean():.1%}), "
        f"on target {s['on_target'].sum():,} ({s['on_target'].mean():.1%})")
    add(f"StatsBomb xG sum {s['sb_xg'].sum():.1f} vs goals {s['goal'].sum()} (should be close)")
    add(f"Headed shots with freeze frame {s['has_ff'].mean():.1%}, with 360 {s['f360_available'].mean():.1%}")
    add(f"Aerial duels {len(d):,}, delivering team known {d['def_team_id'].notna().mean():.1%}, "
        f"with 360 {d['f360_available'].mean():.1%}")
    add(f"Defensive headers {len(f):,} ({(f['action'] == 'Clearance').sum():,} clearances), "
        f"aerial won {f['aerial_won'].mean():.1%}")
    add(f"  next ball kept by defending team {f['next_team_won'].mean():.1%} "
        f"(unknown {f['next_team_won'].isna().mean():.1%})")
    add(f"  opponent shot within 10s {f['opp_shot_10s'].mean():.1%}, "
        f"opponent goal within 10s {f['opp_goal_10s'].mean():.2%}")
    add()
    add("## Headed shots by competition")
    t = (s.groupby("comp_season").agg(shots=("goal", "size"), goals=("goal", "sum"),
                                      xg=("sb_xg", "sum")).sort_values("shots", ascending=False))
    add(t.round(1).to_string())
    add()
    add("## Delivery type of headed shots")
    add(s.groupby("dlv_type").agg(n=("goal", "size"), goal_rate=("goal", "mean"),
                                  on_target=("on_target", "mean")).round(3).to_string())
    add()
    add("## Missing values in key shot features")
    keys = ["dist", "angle", "turn_angle", "dlv_pace", "n_def_in_cone", "gk_dist_goal",
            "nearest_opp_dist", "f360_nearest_opp"]
    add(s[keys].isna().mean().round(3).to_string())
    (PROC / "dataset_report.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
