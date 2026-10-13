"""Stage 5 stretch goal. Does speed and run up before an aerial duel matter?

Free event data has no speed, so this uses Metrica Sports' two anonymised sample
games, which have every player's position 25 times a second, synced to events.
Players have no names or heights here, so this is a small test of whether movement
before the jump carries signal, not something that can feed the main rankings.

For every aerial duel where both the winner and the loser are logged (a won
challenge and an opposing lost challenge within 10 frames), each player gets
    speed_at_jump    average speed over the last 0.2 s before contact (m/s)
    peak_speed_1s    top speed in the last 1 s
    run_up_1s        distance covered in the last 1 s (m)
    toward_ball      speed component toward the contact point over the last 0.5 s
    accel_1s         change in speed over the last 1 s
and we test whether the winner tends to be the one moving more.

Metrica asks that public use of the sample data acknowledges the source.
"""
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from scipy.stats import binomtest, wilcoxon
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneOut

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "metrica"
RES = ROOT / "results"
FPS, PITCH_X, PITCH_Y = 25, 105.0, 68.0
RNG = np.random.default_rng(7)


def download():
    if (RAW / "data" / "Sample_Game_2").exists():
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                    "https://github.com/metrica-sports/sample-data.git", str(RAW)], check=True)
    subprocess.run(["git", "sparse-checkout", "set", "/data/Sample_Game_1/", "/data/Sample_Game_2/"],
                   cwd=RAW, check=True)


def load_tracking(game, team):
    f = RAW / "data" / f"Sample_Game_{game}" / f"Sample_Game_{game}_RawTrackingData_{team}_Team.csv"
    head = pd.read_csv(f, skiprows=2, nrows=0).columns.tolist()
    cols = []
    for i, c in enumerate(head):
        if c.startswith("Player") or c == "Ball":
            cols += [f"{c}_x", f"{c}_y"]
        elif not c.startswith("Unnamed"):
            cols.append(c)
    df = pd.read_csv(f, skiprows=3, header=None, names=cols).set_index("Frame")
    for c in df.columns:
        if c.endswith("_x"):
            df[c] *= PITCH_X
        elif c.endswith("_y"):
            df[c] *= PITCH_Y
    return df


def velocities(df):
    """Smoothed velocity per player. Savitzky Golay over 0.28 s, then speeds above
    12 m/s (tracking glitches) are dropped."""
    out = {}
    for c in [c[:-2] for c in df.columns if c.endswith("_x") and c.startswith("Player")]:
        x, y = df[f"{c}_x"].values, df[f"{c}_y"].values
        ok = ~np.isnan(x)
        vx, vy = np.full(len(x), np.nan), np.full(len(x), np.nan)
        if ok.sum() > 20:
            # fill short gaps then smooth
            xs = pd.Series(x).interpolate(limit=10).values
            ys = pd.Series(y).interpolate(limit=10).values
            good = ~np.isnan(xs)
            vx[good] = savgol_filter(xs[good], 7, 2, deriv=1) * FPS
            vy[good] = savgol_filter(ys[good], 7, 2, deriv=1) * FPS
        sp = np.hypot(vx, vy)
        bad = sp > 12
        vx[bad], vy[bad], sp[bad] = np.nan, np.nan, np.nan
        out[c] = pd.DataFrame({"x": x, "y": y, "vx": vx, "vy": vy, "speed": sp}, index=df.index)
    return out


def features(track, frame, contact):
    """Movement of one player in the second before the duel."""
    t = track.loc[frame - FPS:frame]
    if len(t) < FPS * 0.8 or t["speed"].isna().mean() > 0.3:
        return None
    last5 = t.iloc[-5:]
    last12 = t.iloc[-12:]
    to_ball = contact - t[["x", "y"]].values[-12:]
    norm = np.linalg.norm(to_ball, axis=1)
    norm[norm < 0.5] = np.nan
    if np.isnan(norm).all():
        return None
    toward = np.nanmean((last12["vx"].values * to_ball[:, 0] + last12["vy"].values * to_ball[:, 1]) / norm)
    step = np.hypot(np.diff(t["x"].values), np.diff(t["y"].values))
    return {
        "speed_at_jump": last5["speed"].mean(),
        "peak_speed_1s": t["speed"].max(),
        "run_up_1s": np.nansum(step),
        "toward_ball": toward,
        "accel_1s": t["speed"].iloc[-3:].mean() - t["speed"].iloc[:3].mean(),
    }


def duels(game):
    ev = pd.read_csv(RAW / "data" / f"Sample_Game_{game}" / f"Sample_Game_{game}_RawEventsData.csv")
    ch = ev[(ev["Type"] == "CHALLENGE") & ev["Subtype"].isin(["AERIAL-WON", "AERIAL-LOST"])].copy()
    won, lost = ch[ch["Subtype"] == "AERIAL-WON"], ch[ch["Subtype"] == "AERIAL-LOST"]
    used, pairs = set(), []
    for _, w in won.iterrows():
        cand = lost[(lost["Team"] != w["Team"]) & ((lost["Start Frame"] - w["Start Frame"]).abs() <= 10)
                    & ~lost.index.isin(used)]
        if len(cand):
            l = cand.iloc[(cand["Start Frame"] - w["Start Frame"]).abs().argmin()]
            used.add(l.name)
            pairs.append((w, l))
    return pairs


def main():
    download()
    rows = []
    for game in (1, 2):
        tracks = {}
        for team in ("Home", "Away"):
            raw = load_tracking(game, team)
            tracks.update(velocities(raw))
            if team == "Home":
                ball = raw[["Ball_x", "Ball_y"]]
        for w, l in duels(game):
            frame = int(min(w["Start Frame"], l["Start Frame"]))
            # the contact point is the tracked ball at the moment of the duel. The event's
            # own location is logged at the winner's position, which would leak the result.
            b = ball.loc[frame - 2:frame + 2].mean().values
            if np.isnan(b).any():
                continue
            contact = b
            fw = features(tracks[w["From"]], frame, contact) if w["From"] in tracks else None
            fl = features(tracks[l["From"]], frame, contact) if l["From"] in tracks else None
            if fw and fl:
                rows.append({"game": game, "frame": frame, **{f"win_{k}": v for k, v in fw.items()},
                             **{f"lose_{k}": v for k, v in fl.items()}})
    d = pd.DataFrame(rows)
    feats = ["speed_at_jump", "peak_speed_1s", "run_up_1s", "toward_ball", "accel_1s"]
    print(f"{len(d)} aerial duels with both players tracked")

    lines = ["# Stage 5. Speed and run up before aerial duels (tracking data)", "",
             f"Metrica Sports sample games 1 and 2 (anonymised, 25 frames per second). {len(d)} aerial duels "
             "where both the winner and the loser are logged and tracked for the full second before contact.", "",
             "| Feature | Winner (median) | Loser (median) | Winner higher in | Paired test p |",
             "|---|---|---|---|---|"]
    units = {"speed_at_jump": "m/s", "peak_speed_1s": "m/s", "run_up_1s": "m", "toward_ball": "m/s", "accel_1s": "m/s"}
    names = {"speed_at_jump": "Speed at the jump (last 0.2 s)", "peak_speed_1s": "Peak speed in last 1 s",
             "run_up_1s": "Distance covered in last 1 s", "toward_ball": "Speed toward the contact point (last 0.5 s)",
             "accel_1s": "Change in speed over last 1 s"}
    for f in feats:
        diff = (d[f"win_{f}"] - d[f"lose_{f}"]).dropna()
        p = wilcoxon(diff).pvalue
        share = (diff > 0).mean()
        lines.append(f"| {names[f]} | {d[f'win_{f}'].median():.2f} {units[f]} | {d[f'lose_{f}'].median():.2f} {units[f]} | "
                     f"{share:.0%} of duels | {p:.2f} |")

    # can movement pick the winner? each duel is shown in a random orientation
    X = np.vstack([(d[f"win_{f}"] - d[f"lose_{f}"]).fillna(0).values for f in feats]).T
    flip = RNG.integers(0, 2, len(d)) * 2 - 1
    X, y = X * flip[:, None], (flip > 0).astype(int)
    pred = np.zeros(len(y))
    for tr, te in LeaveOneOut().split(X):
        m = LogisticRegression(C=0.5, max_iter=1000).fit(X[tr], y[tr])
        pred[te] = m.predict_proba(X[te])[:, 1]
    auc = roc_auc_score(y, pred)
    boot = []
    for _ in range(2000):
        i = RNG.integers(0, len(y), len(y))
        if len(set(y[i])) == 2:
            boot.append(roc_auc_score(y[i], pred[i]))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    correct = int(((pred > 0.5) == y).sum())
    bt = binomtest(correct, len(y), 0.5)
    lines += ["", f"A logistic regression on the five winner minus loser differences, tested leave one out, "
              f"picks the winner with AUC {auc:.2f} (95% bootstrap range {lo:.2f} to {hi:.2f}). It is right in "
              f"{correct} of {len(y)} duels (binomial p = {bt.pvalue:.2f} against a coin flip).", ""]
    verdict = ("Movement before the jump shows a signal worth chasing with more data."
               if lo > 0.5 else
               "With this few duels the test cannot show that speed or run up decides aerial duels. "
               "The range is wide enough that a real but modest effect is still possible.")
    lines += [verdict, "",
              "A leak caught along the way. The first version measured movement toward the event's own location. "
              "Metrica logs that at the winner's position, so the winner was by definition moving toward it, and "
              "the model scored an AUC of 0.90. Measuring toward the tracked ball instead dropped it to the value "
              "above. Any tracking feature built on an event location needs this check.", "",
              "Why it is only a stretch result. Two games, anonymous players with no heights, so speed cannot be "
              "compared with height or put into the main duel model. Tracking with names (for example SkillCorner "
              "broadcast data for leagues that also have StatsBomb events) would let speed enter the model directly.",
              "", "Data from Metrica Sports sample data (github.com/metrica-sports/sample-data)."]
    (RES / "stage5_tracking.md").write_text("\n".join(lines))
    d.to_csv(RES / "stage5_duel_movement.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
