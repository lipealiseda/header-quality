"""Download StatsBomb open data (events, lineups, 360 frames) for the matches we use.

The StatsBomb user agreement does not allow redistributing the raw data, so this
repo never commits it. Run this script to fetch it locally into data/raw/.

It uses a git sparse checkout, which is much faster than fetching thousands of
JSON files one at a time and works anywhere git can reach GitHub.

Usage
    python src/download_statsbomb.py            # men's competitions (default)
    python src/download_statsbomb.py --all      # men's and women's
"""
import argparse
import json
import subprocess
from pathlib import Path

BATCH = 150
REPO_URL = "https://github.com/hudl/open-data.git"
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "open-data"


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True)


def main(include_women: bool):
    if not DEST.exists():
        DEST.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO_URL, str(DEST))
    git("sparse-checkout", "set", "--no-cone", "/data/competitions.json", "/data/matches/", cwd=DEST)

    comps = json.loads((DEST / "data" / "competitions.json").read_text())
    paths = []
    for c in comps:
        if c["competition_gender"] != "male" and not include_women:
            continue
        mfile = DEST / "data" / "matches" / str(c["competition_id"]) / f"{c['season_id']}.json"
        for m in json.loads(mfile.read_text()):
            mid = m["match_id"]
            paths += [f"/data/events/{mid}.json", f"/data/lineups/{mid}.json"]
            if c.get("match_available_360"):
                paths.append(f"/data/three-sixty/{mid}.json")

    # skip files we already have, then fetch the rest in small batches so one huge
    # request never stalls and a rerun picks up where it stopped
    todo = [p for p in paths if not (DEST / p.lstrip("/")).exists()]
    print(f"{len(paths)} files wanted, {len(todo)} still to fetch")
    for k in range(0, len(todo), BATCH):
        chunk = todo[k:k + BATCH]
        subprocess.run(["git", "sparse-checkout", "add", "--stdin"],
                       cwd=DEST, input="\n".join(chunk), text=True, check=True)
        print(f"  {min(k + BATCH, len(todo))}/{len(todo)}", flush=True)
    print("Done. Data is in", DEST)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include women's competitions")
    main(ap.parse_args().all)
