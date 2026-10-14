"""Run every stage of the project in order.

    python run_all.py                    # everything, including the 30 minute download
    python run_all.py --skip-download    # raw data already in data/raw/
    python run_all.py --from models      # start at a stage (see STAGES below)
    python run_all.py --only charts site # run just these stages
    python run_all.py --list             # show the stages

Optional inputs are used when present and skipped with a note when not
    data/external/transfermarkt_players.csv            heights (needed from the match stage on)
    data/external/appearances.csv, clubs.csv           better name matching
    data/external/ea/players_15.csv ... players_22.csv  EA FC side test
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXT = ROOT / "data" / "external"
PY = sys.executable


def step(script, env=None):
    return {"script": script, "env": env or {}}


STAGES = [
    ("download", "Download StatsBomb open data (Stage 1)", [step("download_statsbomb.py")]),
    ("dataset", "Build the header tables and check them (Stage 2)",
     [step("build_dataset.py"), step("check_dataset.py")]),
    ("match", "Join Transfermarkt heights and EA ratings to players",
     [step("build_tm_clubs.py"), step("match_players.py")]),
    ("models", "Fit and validate all models, with and without height (Stage 3)",
     [step("models_attack.py"), step("models_defense.py"),
      step("models_attack.py", {"HQ_NO_PHYSICAL": "1"}), step("models_defense.py", {"HQ_NO_PHYSICAL": "1"})]),
    ("uncertainty", "Match bootstrap, calibration, xG vs StatsBomb, importance, height gain, Stage 3 report",
     [step("uncertainty.py"), step("importance.py"), step("height_gain.py"),
      step("stage3_report.py")]),
    ("rankings", "Player rankings, reliability, mixed model check, data sanity (Stage 4)",
     [step("rankings.py"), step("stage4_report.py"), step("mixed_model.py"), step("sanity.py")]),
    ("ea", "EA FC ratings side test", [step("ea_ratings.py")]),
    ("tracking", "Speed before aerial duels from Metrica tracking data (Stage 5)", [step("stage5_tracking.py")]),
    ("charts", "Charts (Stage 6) and the home page headline numbers", [step("charts.py"), step("headline_numbers.py")]),
    ("site", "Website in docs/", [step("build_site.py")]),
]


def skip_reason(name, script):
    if script == "build_tm_clubs.py" and not (EXT / "appearances.csv").exists():
        return "appearances.csv and clubs.csv not in data/external, name matching runs without club history"
    if name == "ea" and not list((EXT / "ea").glob("players_*.csv")):
        return "no EA files in data/external/ea"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--from", dest="start", choices=[s[0] for s in STAGES])
    ap.add_argument("--only", nargs="+", choices=[s[0] for s in STAGES])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for name, desc, _ in STAGES:
            print(f"{name:12s} {desc}")
        return
    names = [s[0] for s in STAGES]
    todo = names[names.index(a.start):] if a.start else names
    if a.only:
        todo = [n for n in names if n in a.only]
    if a.skip_download and "download" in todo:
        todo.remove("download")
    if any(n in todo for n in ("match", "models")) and not (EXT / "transfermarkt_players.csv").exists():
        sys.exit("Missing data/external/transfermarkt_players.csv. Download players.csv from "
                 "https://www.kaggle.com/datasets/davidcariboo/player-scores and save it there.")
    t_all = time.time()
    for name, desc, steps in STAGES:
        if name not in todo:
            continue
        print(f"\n=== {name}: {desc}", flush=True)
        for s in steps:
            why = skip_reason(name, s["script"])
            if why:
                print(f"  skip {s['script']}: {why}")
                continue
            tag = " ".join(f"{k}={v}" for k, v in s["env"].items())
            print(f"  run  {tag + ' ' if tag else ''}{s['script']}", flush=True)
            t0 = time.time()
            r = subprocess.run([PY, str(ROOT / "src" / s["script"])], env={**os.environ, **s["env"]}, cwd=ROOT)
            if r.returncode != 0:
                sys.exit(f"Stopped: {s['script']} failed with exit code {r.returncode}")
            print(f"       done in {time.time() - t0:.0f} s")
    print(f"\nAll requested stages finished in {(time.time() - t_all) / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
