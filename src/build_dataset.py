"""Stage 2. Build the header datasets from StatsBomb open data.

Outputs (data/processed/)
    headed_shots.csv.gz       one row per headed shot, with delivery, positioning,
                              freeze frame and 360 features plus goal / on target labels
    aerial_duels.csv.gz       one row per aerial duel pair (winner and loser known)
    defensive_headers.csv.gz  headed clearances, plus headed passes in a team's own
                              third when the ball came from the opponent, with outcomes
                              (where the ball ended, who won the next ball, opponent
                              shot and xG within 10 seconds)
    player_matches.csv.gz     minutes and position per player per match
    players.csv.gz            one row per player (name, nickname, country)

Run
    python src/download_statsbomb.py
    python src/build_dataset.py
"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometry import (angle_between, dist_to_goal, goal_angle, in_box, in_own_box,  # noqa: E402
                      in_six, point_in_triangle)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "open-data" / "data"
OUT = ROOT / "data" / "processed"

# events that mean "this team has the ball now"
BALL_EVENTS = {"Pass", "Carry", "Ball Recovery", "Clearance", "Shot", "Interception",
               "Dribble", "Miscontrol", "Goal Keeper", "Ball Receipt*", "Shield"}
ON_TARGET = {"Goal", "Saved", "Saved To Post"}
POST_L, POST_R = np.array([120.0, 36.0]), np.array([120.0, 44.0])


# ----------------------------------------------------------------------------- helpers
def tsec(e):
    h, m, s = e["timestamp"].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def flip(loc):
    return [120.0 - loc[0], 80.0 - loc[1]]


def body_part(e):
    for k in ("shot", "pass", "clearance"):
        if k in e and "body_part" in e[k]:
            return e[k]["body_part"]["name"]
    return None


def is_ball_event(e):
    t = e["type"]["name"]
    if t not in BALL_EVENTS:
        return False
    if t == "Ball Receipt*" and e.get("ball_receipt", {}).get("outcome"):
        return False  # incomplete receipt, ball never arrived
    if t == "Ball Recovery" and e.get("ball_recovery", {}).get("recovery_failure"):
        return False
    return True


def delivery_features(p, header_team, header_t, prefix="dlv_"):
    """Describe the pass that delivered the ball. Locations are put in the header
    team's attacking direction so attack and defense read the same way."""
    out = {}
    if p is None:
        out[prefix + "type"] = "none"
        return out
    pp = p["pass"]
    start = p["location"]
    end = pp.get("end_location", start)
    if p["team"]["id"] != header_team:
        start, end = flip(start), flip(end[:2])
    ptype = pp.get("type", {}).get("name", "Open Play")
    length = pp.get("length", np.nan)
    if ptype == "Corner":
        cat = "corner"
    elif ptype == "Free Kick":
        cat = "free_kick"
    elif ptype == "Throw-in":
        cat = "throw_in"
    elif ptype == "Goal Kick":
        cat = "goal_kick"
    elif pp.get("body_part", {}).get("name") == "Head":
        cat = "headed_flick"
    elif pp.get("cross"):
        cat = "cross_open_play"
    elif length >= 35:
        cat = "long_ball"
    else:
        cat = "short_pass"
    dt = header_t - tsec(p)
    out.update({
        prefix + "type": cat,
        prefix + "pass_type": ptype,
        prefix + "height": pp.get("height", {}).get("name"),
        prefix + "technique": pp.get("technique", {}).get("name"),
        prefix + "body_part": pp.get("body_part", {}).get("name"),
        prefix + "cross": bool(pp.get("cross", False)),
        prefix + "length": length,
        prefix + "start_x": start[0], prefix + "start_y": start[1],
        prefix + "end_x": end[0], prefix + "end_y": end[1],
        prefix + "flight_time": dt if dt > 0 else np.nan,
        prefix + "pace": length / dt if dt and dt > 0.2 else np.nan,
        prefix + "by_opponent": p["team"]["id"] != header_team,
    })
    return out


def last_pass_before(events, idx, max_dt=6.0):
    """Most recent pass (any team) in the few seconds before events[idx]. Events
    linked to this one (for example the winner's header in an aerial duel, which
    StatsBomb sometimes logs first) are skipped so the duel is never described
    by its own outcome."""
    e = events[idx]
    t0 = tsec(e)
    skip = set(e.get("related_events", []))
    for j in range(idx - 1, max(idx - 40, -1), -1):
        p = events[j]
        if p["period"] != e["period"] or t0 - tsec(p) > max_dt:
            break
        if p["type"]["name"] == "Pass" and p["id"] not in skip:
            return p
    return None


def look_ahead(events, idx, team_id, window=10.0):
    """What happened after a defensive header. Returns next ball owner and location
    (header team's direction), opponent shots and xG within the window."""
    e = events[idx]
    t0, per = tsec(e), e["period"]
    related = set(e.get("related_events", []))
    nxt = None
    shot, xg, goal = False, 0.0, False
    for j in range(idx + 1, min(idx + 300, len(events))):
        f = events[j]
        if f["period"] != per:
            break
        dt = tsec(f) - t0
        if dt > max(window, 15):
            break
        if nxt is None and dt <= 15 and f["id"] not in related and is_ball_event(f):
            nxt = f
        if dt <= window and f["type"]["name"] == "Shot" and f["team"]["id"] != team_id:
            shot = True
            xg += f["shot"].get("statsbomb_xg", 0.0)
            goal = goal or f["shot"]["outcome"]["name"] == "Goal"
    out = {"next_team_won": np.nan, "next_x": np.nan, "next_y": np.nan, "next_type": None,
           "opp_shot_10s": shot, "opp_xg_10s": xg, "opp_goal_10s": goal}
    if nxt is not None:
        own = nxt["team"]["id"] == team_id
        loc = nxt.get("location")
        if loc is not None:
            loc = loc if own else flip(loc)
            out["next_x"], out["next_y"] = loc[0], loc[1]
        out["next_team_won"] = float(own)
        out["next_type"] = nxt["type"]["name"]
        if nxt["type"]["name"] == "Pass":
            out["next_type"] = nxt["pass"].get("type", {}).get("name", "Pass")
    return out


def shot_freeze_features(e):
    ff = e["shot"].get("freeze_frame")
    if not ff:
        return {"has_ff": False}
    s = np.array(e["location"][:2], dtype=float)
    opp = [p for p in ff if not p["teammate"]]
    mates = [p for p in ff if p["teammate"]]
    gk = [p for p in opp if p["position"]["name"] == "Goalkeeper"]
    outf = [p for p in opp if p["position"]["name"] != "Goalkeeper"]
    d_opp = [np.hypot(*(np.array(p["location"]) - s)) for p in outf]
    out = {
        "has_ff": True,
        "n_def_in_cone": sum(point_in_triangle(np.array(p["location"]), s, POST_L, POST_R) for p in outf),
        "n_att_in_cone": sum(point_in_triangle(np.array(p["location"]), s, POST_L, POST_R) for p in mates),
        "nearest_opp_dist": min(d_opp) if d_opp else np.nan,
        "n_opp_within_2m": sum(d <= 2 for d in d_opp),
        "n_opp_within_5m": sum(d <= 5 for d in d_opp),
        "n_opp_in_box": sum(bool(in_box(*p["location"])) for p in outf),
        "n_att_in_box": sum(bool(in_box(*p["location"])) for p in mates) + int(bool(in_box(*s))),
    }
    if gk:
        g = np.array(gk[0]["location"], dtype=float)
        out.update({
            "gk_x": g[0], "gk_y": g[1],
            "gk_dist_goal": float(np.hypot(120 - g[0], 40 - g[1])),
            "gk_dist_shooter": float(np.hypot(*(g - s))),
            "gk_in_cone": point_in_triangle(g, s, POST_L, POST_R),
        })
    return out


def frame360_features(frame, prefix="f360_"):
    """Crowding around the player on the ball from a 360 frame. 360 frames carry no
    player ids, only teammate / actor / keeper flags."""
    if not frame:
        return {prefix + "available": False}
    ff = frame["freeze_frame"]
    actor = [p for p in ff if p.get("actor")]
    if not actor:
        return {prefix + "available": False}
    a = np.array(actor[0]["location"])
    opp = [np.array(p["location"]) for p in ff if not p["teammate"] and not p["keeper"]]
    mates = [np.array(p["location"]) for p in ff if p["teammate"] and not p["actor"] and not p["keeper"]]
    d_opp = [float(np.hypot(*(o - a))) for o in opp]
    d_mate = [float(np.hypot(*(m - a))) for m in mates]
    return {
        prefix + "available": True,
        prefix + "n_visible": len(ff),
        prefix + "nearest_opp": min(d_opp) if d_opp else np.nan,
        prefix + "nearest_mate": min(d_mate) if d_mate else np.nan,
        prefix + "opp_within_3m": sum(d <= 3 for d in d_opp),
        prefix + "opp_within_10m": sum(d <= 10 for d in d_opp),
        prefix + "mates_within_10m": sum(d <= 10 for d in d_mate),
        prefix + "opp_in_own_box": sum(bool(in_own_box(*o)) for o in opp),
    }


# ----------------------------------------------------------------------------- per match
def process_match(args):
    mid, meta = args
    events = json.loads((RAW / "events" / f"{mid}.json").read_text())
    lineups = json.loads((RAW / "lineups" / f"{mid}.json").read_text())
    p360 = RAW / "three-sixty" / f"{mid}.json"
    frames = {f["event_uuid"]: f for f in json.loads(p360.read_text())} if p360.exists() else {}
    by_id = {e["id"]: e for e in events}

    # running score so we know game state
    score = defaultdict(int)
    state_before = {}
    for e in events:
        state_before[e["id"]] = dict(score)
        t = e["type"]["name"]
        if t == "Shot" and e["shot"]["outcome"]["name"] == "Goal":
            score[e["team"]["id"]] += 1
        elif t == "Own Goal For":
            score[e["team"]["id"]] += 1

    def score_diff(e):
        s = state_before[e["id"]]
        own = s.get(e["team"]["id"], 0)
        return own - sum(v for k, v in s.items() if k != e["team"]["id"])

    def base(e):
        return {
            "match_id": mid, **meta,
            "event_id": e["id"], "period": e["period"], "minute": e["minute"],
            "second": e["second"], "t": tsec(e),
            "team_id": e["team"]["id"], "team": e["team"]["name"],
            "player_id": e.get("player", {}).get("id"), "player": e.get("player", {}).get("name"),
            "position": e.get("position", {}).get("name"),
            "play_pattern": e["play_pattern"]["name"],
            "under_pressure": bool(e.get("under_pressure", False)),
            "score_diff": score_diff(e),
            "x": e["location"][0], "y": e["location"][1],
        }

    shots, duels, defs = [], [], []
    for i, e in enumerate(events):
        t = e["type"]["name"]
        bp = body_part(e)

        # ---------------- headed shots
        if t == "Shot" and bp == "Head":
            s = e["shot"]
            row = base(e)
            x, y = row["x"], row["y"]
            kp = by_id.get(s.get("key_pass_id")) if s.get("key_pass_id") else None
            dlv = kp if kp is not None else last_pass_before(events, i)
            row.update({
                "outcome": s["outcome"]["name"],
                "goal": int(s["outcome"]["name"] == "Goal"),
                "on_target": int(s["outcome"]["name"] in ON_TARGET),
                "sb_xg": s.get("statsbomb_xg", np.nan),
                "shot_type": s.get("type", {}).get("name"),
                "technique": s.get("technique", {}).get("name"),
                "first_time": bool(s.get("first_time", False)),
                "aerial_won": bool(s.get("aerial_won", False)),
                "has_key_pass": kp is not None,
                "dist": float(dist_to_goal(x, y)), "angle": float(goal_angle(x, y)),
                "in_box": bool(in_box(x, y)), "in_six": bool(in_six(x, y)),
            })
            row.update(delivery_features(dlv, e["team"]["id"], tsec(e)))
            if dlv is not None and not np.isnan(row.get("dlv_start_x", np.nan)):
                inc = np.array([x - row["dlv_start_x"], y - row["dlv_start_y"]])
                row["turn_angle"] = angle_between(inc, np.array([120 - x, 40 - y]))
            row.update(shot_freeze_features(e))
            row.update(frame360_features(frames.get(e["id"])))
            shots.append(row)

        # ---------------- aerial duels (loser event links to the winner's event)
        if t == "Duel" and e["duel"]["type"]["name"] == "Aerial Lost":
            win = None
            for r in e.get("related_events", []):
                f = by_id.get(r)
                if f is None:
                    continue
                for k in ("pass", "clearance", "shot", "miscontrol"):
                    if f.get(k, {}).get("aerial_won"):
                        win = f
            if win is None:
                continue
            p = last_pass_before(events, i)
            deliver_team = p["team"]["id"] if p is not None else None
            # describe everything from the defending side when we know who delivered
            def_team = None
            if deliver_team is not None:
                def_team = e["team"]["id"] if deliver_team != e["team"]["id"] else win["team"]["id"]
            ref = e if def_team in (None, e["team"]["id"]) else win
            loc = ref["location"]
            row = {
                "match_id": mid, **meta, "event_id": e["id"], "period": e["period"],
                "minute": e["minute"], "t": tsec(e), "play_pattern": e["play_pattern"]["name"],
                "loser_id": e["player"]["id"], "loser": e["player"]["name"],
                "loser_team_id": e["team"]["id"], "loser_position": e.get("position", {}).get("name"),
                "winner_id": win["player"]["id"], "winner": win["player"]["name"],
                "winner_team_id": win["team"]["id"], "winner_position": win.get("position", {}).get("name"),
                "winner_action": win["type"]["name"],
                "def_team_id": def_team,
                "ref_team_id": ref["team"]["id"],
                "x": loc[0], "y": loc[1],  # in the reference team's attacking direction
                "loser_under_pressure": bool(e.get("under_pressure", False)),
            }
            row.update(delivery_features(p, ref["team"]["id"], tsec(e)))
            row.update(frame360_features(frames.get(e["id"])))
            duels.append(row)

        # ---------------- defensive headers
        is_def = False
        if t == "Clearance" and bp == "Head":
            is_def = True
        elif t == "Pass" and bp == "Head" and e["location"][0] < 40:
            p = last_pass_before(events, i)
            is_def = p is not None and p["team"]["id"] != e["team"]["id"]
        if is_def:
            row = base(e)
            x, y = row["x"], row["y"]
            aw = e.get("clearance", {}).get("aerial_won") or e.get("pass", {}).get("aerial_won")
            row.update({
                "action": t,
                "aerial_won": bool(aw),
                "dist_own_goal": float(np.hypot(x, 40 - y)),
                "in_own_box": bool(in_own_box(x, y)),
                "out_of_play": bool(e.get("out", False)),
            })
            if t == "Pass":
                end = e["pass"].get("end_location")
                row.update({"pass_end_x": end[0], "pass_end_y": end[1],
                            "pass_complete": int("outcome" not in e["pass"])})
            row.update(delivery_features(last_pass_before(events, i), e["team"]["id"], tsec(e)))
            row.update(look_ahead(events, i, e["team"]["id"]))
            row.update(frame360_features(frames.get(e["id"])))
            defs.append(row)

    # ---------------- minutes per player
    last_min = defaultdict(int)
    for e in events:
        last_min[e["period"]] = max(last_min[e["period"]], e["minute"])
    end_min = max(last_min.values()) + 1
    pm, players = [], []
    for team in lineups:
        for pl in team["lineup"]:
            players.append({"player_id": pl["player_id"], "player_name": pl["player_name"],
                            "player_nickname": pl.get("player_nickname"),
                            "country": (pl.get("country") or {}).get("name")})
            mins, pos_count = 0.0, defaultdict(float)
            for ps in pl.get("positions", []):
                a = _mmss(ps.get("from")) or 0.0
                b = _mmss(ps.get("to")) or float(end_min)
                mins += max(0.0, b - a)
                pos_count[ps["position"]] += max(0.0, b - a)
            if mins > 0:
                pm.append({"match_id": mid, **meta, "player_id": pl["player_id"],
                           "team": team["team_name"], "minutes": mins,
                           "main_position": max(pos_count, key=pos_count.get)})
    return shots, duels, defs, pm, players


def _mmss(s):
    if not s:
        return None
    m, sec = s.split(":")
    return int(m) + int(sec) / 60


# ----------------------------------------------------------------------------- main
def match_list():
    comps = json.loads((RAW / "competitions.json").read_text())
    jobs = []
    for c in comps:
        mfile = RAW / "matches" / str(c["competition_id"]) / f"{c['season_id']}.json"
        for m in json.loads(mfile.read_text()):
            if not (RAW / "events" / f"{m['match_id']}.json").exists():
                continue
            jobs.append((m["match_id"], {
                "competition": c["competition_name"], "season": c["season_name"],
                "gender": c["competition_gender"],
                "comp_season": f"{c['competition_name']} {c['season_name']}",
                "match_date": m["match_date"],
                "home_team": m["home_team"]["home_team_name"],
                "away_team": m["away_team"]["away_team_name"],
            }))
    return jobs


def main():
    jobs = match_list()
    print(f"{len(jobs)} matches")
    acc = [[], [], [], [], []]
    with ProcessPoolExecutor() as ex:
        for k, res in enumerate(ex.map(process_match, jobs, chunksize=8)):
            for a, r in zip(acc, res):
                a.extend(r)
            if k % 250 == 0:
                print(k, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    names = ["headed_shots", "aerial_duels", "defensive_headers", "player_matches"]
    for name, rows in zip(names, acc[:4]):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"{name}.csv.gz", index=False)
        print(name, df.shape)
    pl = pd.DataFrame(acc[4]).drop_duplicates("player_id")
    pl.to_csv(OUT / "players.csv.gz", index=False)
    print("players", pl.shape)


if __name__ == "__main__":
    main()
