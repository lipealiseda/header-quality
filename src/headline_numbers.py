"""The headline numbers on the website's home page.

How big a part of the game headers are, counted over every men's match in the
StatsBomb open data: the share of non penalty goals scored with the head, and the
share of headed goals that came from a corner or a free kick.

Output (results/)
    headline_numbers.csv   one row per number, with the counts behind it
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dataset import RAW  # noqa: E402
from modeling import PROC, RES  # noqa: E402


def main():
    comps = json.loads((RAW / "competitions.json").read_text())
    goals = head = 0
    for c in comps:
        if c["competition_gender"] != "male":
            continue
        f = RAW / "matches" / str(c["competition_id"]) / f"{c['season_id']}.json"
        if not f.exists():
            continue
        for m in json.loads(f.read_text()):
            ev = RAW / "events" / f"{m['match_id']}.json"
            if not ev.exists():
                continue
            for e in json.loads(ev.read_text()):
                if e["type"]["name"] != "Shot":
                    continue
                s = e["shot"]
                if s["outcome"]["name"] == "Goal" and s["type"]["name"] != "Penalty":
                    goals += 1
                    head += s["body_part"]["name"] == "Head"
    h = pd.read_csv(PROC / "headed_shots.csv.gz", low_memory=False)
    g = h[(h["goal"] == 1) & (h["shot_type"] != "Penalty")]
    sp = int(g["dlv_type"].isin(["corner", "free_kick"]).sum())
    out = pd.DataFrame([
        {"number": "headed share of non penalty goals", "count": head, "of": goals, "share": head / goals},
        {"number": "headed goals from a corner or free kick", "count": sp, "of": len(g), "share": sp / len(g)},
    ])
    out.to_csv(RES / "headline_numbers.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
