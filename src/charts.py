"""Stage 6. The eight charts for the README and write up, four on attack and four on
defense. Every chart carries the StatsBomb logo, as their open data licence asks.

Colours follow one small palette (blue for the main series, orange for the second
or for "below expected", grays for everything else) checked for colour blind
separation."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Arc, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES, ROOT  # noqa: E402
from stage4_report import NICE  # noqa: E402

FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
LOGO = plt.imread(ROOT / "assets" / "statsbomb_logo.png")

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#b9b8b2"
BLUES = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
ORANGES = LinearSegmentedColormap.from_list("oranges", ["#fde3d6", "#f6a37f", "#eb6834", "#b8461b", "#6e2508"])

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
    "xtick.major.size": 0, "ytick.major.size": 0, "axes.spines.top": False, "axes.spines.right": False,
})


# ----------------------------------------------------------------------------- frame
def frame(title, subtitle, source, size=(9, 6)):
    fig = plt.figure(figsize=size, dpi=150)
    fig.text(0.04, 0.955, title, fontsize=15, fontweight="bold", ha="left", va="top")
    fig.text(0.04, 0.905, subtitle, fontsize=10.5, color=INK2, ha="left", va="top", wrap=True)
    fig.text(0.04, 0.025, source, fontsize=8, color=MUTED, ha="left", va="bottom")
    lw = 0.15
    ax_logo = fig.add_axes([0.96 - lw, 0.012, lw, lw * LOGO.shape[0] / LOGO.shape[1] * size[0] / size[1]])
    ax_logo.imshow(LOGO)
    ax_logo.axis("off")
    return fig


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=150)
    plt.close(fig)
    print("saved", name)


def grid_y(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def grid_x(ax):
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / d
    return c - h, c + h


def box_pitch(ax, x0=84):
    """Attacking end of a StatsBomb pitch, drawn vertically (goal at the top)."""
    lc, lw = "#c9c8c2", 1.0
    ax.plot([0, 80], [120, 120], color=lc, lw=lw)
    ax.add_patch(Rectangle((18, 102), 44, 18, fill=False, ec=lc, lw=lw))
    ax.add_patch(Rectangle((30, 114), 20, 6, fill=False, ec=lc, lw=lw))
    ax.add_patch(Rectangle((36, 120), 8, 1.2, fill=False, ec=INK2, lw=1.4))
    ax.add_patch(Arc((40, 108), 20, 20, theta1=217, theta2=323, color=lc, lw=lw))
    ax.scatter([40], [108], s=4, color=lc)
    ax.set_xlim(0, 80)
    ax.set_ylim(x0, 122)
    ax.set_aspect("equal")
    ax.axis("off")


def own_half(ax):
    """Defending half, own goal at the bottom."""
    lc, lw = "#c9c8c2", 1.0
    ax.add_patch(Rectangle((0, 0), 80, 60, fill=False, ec=lc, lw=lw))
    ax.add_patch(Rectangle((18, 0), 44, 18, fill=False, ec=lc, lw=lw))
    ax.add_patch(Rectangle((30, 0), 20, 6, fill=False, ec=lc, lw=lw))
    ax.add_patch(Rectangle((36, -1.2), 8, 1.2, fill=False, ec=INK2, lw=1.4))
    ax.add_patch(Arc((40, 12), 20, 20, theta1=37, theta2=143, color=lc, lw=lw))
    ax.add_patch(Arc((40, 60), 20, 20, theta1=180, theta2=360, color=lc, lw=lw))
    ax.set_xlim(-1, 81)
    ax.set_ylim(-2, 61)
    ax.set_aspect("equal")
    ax.axis("off")


SRC = "Data StatsBomb open data, 2,651 men's matches (mostly the 2015/16 top 4 leagues). Heights from Transfermarkt."


# ----------------------------------------------------------------------------- attack
def a1_xg_map():
    s = pd.read_csv(PROC / "headed_shots.csv.gz", low_memory=False)
    s = s[s["shot_type"] != "Penalty"]
    fig = frame("Where headers become goals",
                "Share of headed shots that are scored, by location. Inside the six yard box about 1 in 5 go in,\n"
                "around the penalty spot about 1 in 16, from the edge of the box about 1 in 25.", SRC, size=(9, 5.4))
    ax = fig.add_axes([0.03, 0.10, 0.76, 0.70])
    box_pitch(ax, x0=96)
    # vertical pitch: horizontal axis is StatsBomb y, vertical is StatsBomb x
    hb = ax.hexbin(s["y"], s["x"], C=s["goal"], reduce_C_function=np.mean, gridsize=(26, 9),
                   extent=(0, 80, 84, 120), mincnt=12, cmap=BLUES, vmin=0, vmax=0.4,
                   linewidths=0.6, edgecolors=SURFACE)
    box_pitch(ax, x0=96)
    ax.set_xlim(12, 68)
    cax = fig.add_axes([0.83, 0.34, 0.022, 0.42])
    cb = fig.colorbar(hb, cax=cax)
    cb.outline.set_visible(False)
    cb.set_ticks([0, 0.1, 0.2, 0.3, 0.4])
    cb.set_ticklabels(["0%", "10%", "20%", "30%", "40%+"])
    cax.set_title("Goal rate", fontsize=9, color=INK2, loc="left", pad=8)
    fig.text(0.83, 0.13, f"{len(s):,} headed shots.\nCells with fewer than\n12 shots are hidden.", fontsize=8, color=MUTED)
    save(fig, "a1_header_goal_map")


def a2_delivery():
    s = pd.read_csv(PROC / "headed_shots.csv.gz", low_memory=False)
    s = s[s["shot_type"] != "Penalty"]
    names = {"headed_flick": "Flick on from a teammate", "short_pass": "Short pass", "cross_open_play": "Cross in open play",
             "free_kick": "Free kick", "corner": "Corner", "long_ball": "Long ball"}
    g = s[s["dlv_type"].isin(names)].groupby("dlv_type").agg(n=("goal", "size"), goals=("goal", "sum"),
                                                              ot=("on_target", "sum"))
    g["gr"], g["otr"] = g["goals"] / g["n"], g["ot"] / g["n"]
    g = g.sort_values("gr")
    fig = frame("Corners and long balls make the worst headed chances",
                "Goal rate and on target rate of headed shots by how the ball arrived. Lines are 95% intervals.\n"
                "Corner headers face 8.6 defenders in the box on average (5.9 otherwise) and 63% are under pressure.", SRC)
    ax = fig.add_axes([0.30, 0.13, 0.64, 0.68])
    y = np.arange(len(g))
    for col, k, color, label, off in (("gr", "goals", BLUE, "Scored", 0.14), ("otr", "ot", ORANGE, "On target", -0.14)):
        lo, hi = wilson(g[k].values, g["n"].values)
        ax.hlines(y + off, lo, hi, color=color, lw=2, alpha=0.45)
        ax.scatter(g[col], y + off, s=55, color=color, zorder=3, label=label, edgecolors=SURFACE, linewidths=1.5)
    lo_g, hi_g = wilson(g["goals"].values, g["n"].values)
    lo_o, hi_o = wilson(g["ot"].values, g["n"].values)
    for i, (idx, r) in enumerate(g.iterrows()):
        ax.text(hi_o[i] + 0.01, i - 0.14, f"{r['otr']:.0%}", va="center", fontsize=8.5, color=INK2)
        ax.text(hi_g[i] + 0.01, i + 0.14, f"{r['gr']:.0%}", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{names[i]}  ({n:,})" for i, n in zip(g.index, g["n"])], fontsize=9.5, color=INK)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlim(0, 0.72)
    ax.spines["left"].set_visible(False)
    grid_x(ax)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.text(0.30, 0.815, "Delivery type  (headed shots)", fontsize=8.5, color=MUTED, ha="right")
    save(fig, "a2_delivery_type")


def drivers_panel(ax, name, title, color, title_x):
    t = pd.read_csv(RES / f"{name}_gbm_importance.csv")
    t["share"] = t["importance"].clip(lower=0) / t["importance"].clip(lower=0).sum()
    t = t.head(6).iloc[::-1]
    y = np.arange(len(t))
    ax.barh(y, t["share"], color=color, height=0.62)
    for i, v in enumerate(t["share"]):
        ax.text(v + 0.008, i, f"{v:.0%}", va="center", fontsize=8.5, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([NICE.get(f, f) for f in t["feature"]], fontsize=9, color=INK)
    ax.set_xlim(0, t["share"].max() * 1.25)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.figure.text(title_x, 0.80, title, fontsize=10.5, color=INK, fontweight="bold", ha="left")


def a3_drivers():
    fig = frame("Location decides goals, the delivery shapes accuracy",
                "Share of each model's accuracy lost when one factor is scrambled (permutation importance,\n"
                "gradient boosting, tested on held out matches). Height did not make either list.", SRC)
    drivers_panel(fig.add_axes([0.31, 0.14, 0.16, 0.62]), "xg", "What makes a header a goal", BLUE, 0.06)
    drivers_panel(fig.add_axes([0.79, 0.14, 0.16, 0.62]), "xot", "What puts it on target", BLUE, 0.55)
    save(fig, "a3_attack_drivers")


def a4_finishing():
    g = pd.read_csv(RES / "rank_goals_vs_xg.csv")
    rel = pd.read_csv(RES / "metric_reliability.csv").set_index("metric")
    q = g[g["qualified"]].copy()
    q["gmx"] = q["actual"] - q["expected"]
    rg = rel.loc["goals_vs_xg"]
    fig = frame("Headed finishing shows no clear skill signal",
                f"Goals vs expected goals on headers for the {len(q)} players with 25+ headed shots. Reliability is about\n"
                f"zero (95% interval below 0 to {rg['rel_ci_hi']:.2f}), so with this few players moderate skill cannot be ruled out.",
                SRC)
    ax = fig.add_axes([0.09, 0.13, 0.62, 0.70])
    m = max(q["expected"].max(), q["actual"].max()) + 1
    xs = np.linspace(0, m, 50)
    # band uses the average event variance p(1 - p) across headed shots, about 0.88 of xG
    vr = (q["sigma2"] * q["n"]).sum() / q["expected"].sum()
    ax.fill_between(xs, xs - 1.645 * np.sqrt(vr * xs), xs + 1.645 * np.sqrt(vr * xs), color="#efeeea", lw=0)
    outside = int((np.abs(q["gmx"]) > 1.645 * np.sqrt(q["sigma2"] * q["n"])).sum())
    ax.plot([0, m], [0, m], color=MUTED, lw=1)
    col = np.where(q["gmx"] >= 0, BLUE, ORANGE)
    ax.scatter(q["expected"], q["actual"], s=36 + q["n"] * 0.6, color=col, alpha=0.85, edgecolors=SURFACE, linewidths=1.2, zorder=3)
    lab = pd.concat([q.nlargest(4, "gmx"), q.nsmallest(2, "gmx"), q.nlargest(2, "expected")]).drop_duplicates("player_id")
    for r in lab.itertuples():
        ax.annotate(r.name, (r.expected, r.actual), xytext=(6, 4), textcoords="offset points", fontsize=8.5, color=INK)
    ax.set_xlabel("Expected headed goals (model)")
    ax.set_ylabel("Actual headed goals")
    ax.set_xlim(0, m)
    ax.set_ylim(0, m)
    grid_y(ax)
    fig.text(0.74, 0.62, "Gray band", fontsize=9, fontweight="bold", color=INK)
    fig.text(0.74, 0.40, "Where 90% of players\nwould land if every\nheader were a coin flip\nat its xG.\n\n"
             f"{outside} of {len(q)} players fall\noutside it. Luck alone\nwould put about {0.1 * len(q):.0f} there.",
             fontsize=9, color=INK2)
    fig.text(0.74, 0.30, "Dot size = headed shots", fontsize=8.5, color=MUTED)
    save(fig, "a4_finishing_is_luck")


# ----------------------------------------------------------------------------- defense
def d1_height():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from models_defense import prepare_duels
    d = prepare_duels()
    k = d[d["height_diff"].notna()].copy()
    k["b"] = k["height_diff"].clip(-20, 20).round().astype(int)
    k["b"] = (k["b"] // 2) * 2
    t = k.groupby("b")["def_won"].agg(["sum", "size"]).reset_index()
    t["rate"] = t["sum"] / t["size"]
    lo, hi = wilson(t["sum"].values, t["size"].values)
    fig = frame("Every few centimetres changes the aerial duel",
                "Share of aerial duels won by the defending player, by how much taller he is than the attacker.\n"
                "Band is the 95% interval. Ends are capped at 20 cm.", SRC)
    ax = fig.add_axes([0.10, 0.14, 0.84, 0.68])
    ax.fill_between(t["b"], lo, hi, color=BLUE, alpha=0.15, lw=0)
    ax.plot(t["b"], t["rate"], color=BLUE, lw=2)
    ax.scatter(t["b"], t["rate"], s=22, color=BLUE, zorder=3, edgecolors=SURFACE, linewidths=1)
    ax.axvline(0, color=GRID, lw=1)
    ax.axhline(0.5, color=GRID, lw=1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlabel("Defender height minus attacker height (cm)")
    ax.set_ylabel("Defender wins the duel")
    for b, txt, dy in ((-10, None, 0), (10, None, 0)):
        r = t[t["b"] == b].iloc[0]
        ax.annotate(f"{r['rate']:.0%}", (b, r["rate"]), xytext=(0, 12 if b > 0 else -18), textcoords="offset points",
                    ha="center", fontsize=10, fontweight="bold", color=INK)
    ax.text(-19.5, 0.505, "coin flip", fontsize=8.5, color=MUTED, va="bottom")
    grid_y(ax)
    r0 = t[t["b"] == 0].iloc[0]
    ax.annotate(f"Same height: defender still wins {r0['rate']:.0%}", (0, r0["rate"]), xytext=(10, -26),
                textcoords="offset points", fontsize=9, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.text(-20.5, 0.83, f"{len(k):,} duels with both heights known", fontsize=8.5, color=MUTED)
    save(fig, "d1_height_and_duels")


def d2_danger_map():
    f = pd.read_csv(PROC / "defensive_headers.csv.gz", low_memory=False)
    f = f[f["x"] <= 60]
    fig = frame("Clear it far from your own goal",
                "Chance the opponent gets a shot within 10 seconds of a defensive header, by where the header\n"
                "was made. Own goal at the bottom.", SRC, size=(9, 7))
    ax = fig.add_axes([0.06, 0.09, 0.72, 0.76])
    own_half(ax)
    # draw own goal at the bottom: vertical axis is StatsBomb x, horizontal is y
    hb = ax.hexbin(f["y"], f["x"], C=f["opp_shot_10s"].astype(float), reduce_C_function=np.mean,
                   gridsize=(18, 8), extent=(0, 80, 0, 60), mincnt=40, cmap=ORANGES, vmin=0, vmax=0.25,
                   linewidths=0.6, edgecolors=SURFACE)
    own_half(ax)
    cax = fig.add_axes([0.82, 0.30, 0.022, 0.40])
    cb = fig.colorbar(hb, cax=cax)
    cb.outline.set_visible(False)
    cb.set_ticks([0, 0.05, 0.10, 0.15, 0.20, 0.25])
    cb.set_ticklabels(["0%", "5%", "10%", "15%", "20%", "25%+"])
    cax.set_title("Opponent shot\nwithin 10 s", fontsize=9, color=INK2, loc="left", pad=8)
    fig.text(0.82, 0.22, f"{len(f):,} defensive headers\nCells with fewer than\n40 headers are hidden", fontsize=8, color=MUTED)
    save(fig, "d2_clearance_danger_map")


def d3_defenders():
    r = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    q = r[r["qualified"] & r["pos_group"].isin(["CB", "FB"])]
    top, bot = q.nlargest(10, "shrunk_rate"), q.nsmallest(5, "shrunk_rate").iloc[::-1]
    t = pd.concat([bot, top.iloc[::-1]])
    fig = frame("Defenders who win more headers than their height says",
                f"Aerial duels won above or below expected per 100, for {len(q)} defenders with 100+ duels. Lines are\n"
                f"95% ranges. The rank range shows where each could really sit among all {len(q)}.",
                SRC, size=(9, 7))
    ax = fig.add_axes([0.42, 0.13, 0.46, 0.68])
    y = np.r_[np.arange(5), np.arange(10) + 6]
    for yi, row in zip(y, t.itertuples()):
        c = BLUE if row.shrunk_rate > 0 else ORANGE
        ax.hlines(yi, row.lo95 * 100, row.hi95 * 100, color=c, lw=2.2, alpha=0.4)
        ax.scatter(row.shrunk_rate * 100, yi, s=55, color=c, zorder=3, edgecolors=SURFACE, linewidths=1.5)
        ax.text(1.03, yi, f"{int(row.rank_def_lo)} to {int(row.rank_def_hi)}", va="center", ha="left",
                fontsize=8.5, color=INK2, transform=ax.get_yaxis_transform())
        ax.text(row.hi95 * 100 + 0.6, yi, f"{row.shrunk_rate * 100:+.1f}", va="center", ha="left",
                fontsize=8.5, color=INK2, bbox=dict(fc=SURFACE, ec="none", pad=0.6), zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{row.name}  ({row.main_club}, {row.height_cm:.0f} cm)" for row in t.itertuples()],
                       fontsize=8.8, color=INK)
    ax.axvline(0, color=MUTED, lw=1)
    ax.axhline(5, color=GRID, lw=1)
    ax.set_xlabel("Duels won above expected per 100 (shrunk, line = 95% range)")
    ax.text(1.03, 16.3, "95% rank\nrange", ha="left", va="center", fontsize=8.5, color=INK2, fontweight="bold",
            transform=ax.get_yaxis_transform())
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-24, 24)
    grid_x(ax)
    ax.text(23.5, 15.4, "Top 10", ha="right", fontsize=9, fontweight="bold", color=BLUE)
    ax.text(23.5, 4.4, "Bottom 5", ha="right", fontsize=9, fontweight="bold", color=ORANGE)
    save(fig, "d3_best_defenders_in_the_air")


def d4_reliability():
    rel = pd.read_csv(RES / "metric_reliability.csv")
    names = {"duels_vs_expected": "Aerial duels won vs expected", "on_target_vs_expected": "Headers on target vs expected",
             "shots_prevented": "Opponent shots prevented after clearing", "next_ball_vs_expected": "Next ball won after clearing",
             "goals_vs_xg": "Headed goals minus xG"}
    side = {"duels_vs_expected": "Attack and defense", "on_target_vs_expected": "Attack", "shots_prevented": "Defense",
            "next_ball_vs_expected": "Defense", "goals_vs_xg": "Attack"}
    rel = rel.sort_values("full_length_reliability")
    fig = frame("Only one header skill clearly repeats",
                "Reliability of each metric, the average over 200 random match splits, corrected to the full sample.\n"
                "Lines are 95% intervals. 0 means pure luck, 1 means pure skill.", SRC, size=(9, 5.4))
    ax = fig.add_axes([0.40, 0.17, 0.54, 0.6])
    y = np.arange(len(rel))
    for i, r in enumerate(rel.itertuples()):
        c = BLUE if r.metric == "duels_vs_expected" else MUTED
        lo, hi, est = max(r.rel_ci_lo, 0), max(r.rel_ci_hi, 0), max(r.full_length_reliability, 0)
        ax.hlines(i, lo, hi, color=c, lw=3, alpha=0.45 if c == BLUE else 0.35)
        ax.scatter(est, i, s=70, color=c, zorder=3, edgecolors=SURFACE, linewidths=1.5)
        lo_txt = "below 0" if r.rel_ci_lo < 0 else f"{r.rel_ci_lo:.2f}"
        ax.text(hi + 0.02, i, f"{r.full_length_reliability:.2f}  ({lo_txt} to {r.rel_ci_hi:.2f})", va="center",
                fontsize=8.8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{names[m]}\n{side[m]}, {int(p)} players" for m, p in zip(rel["metric"], rel["players"])],
                       fontsize=9, color=INK, linespacing=1.3)
    ax.set_xlim(-0.04, 1.08)
    ax.set_ylim(-0.6, len(rel) - 0.4)
    ax.axvline(0.5, color=GRID, lw=1.2)
    ax.text(0.51, len(rel) - 0.55, "repeatable", fontsize=8.5, color=MUTED)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.spines["left"].set_visible(False)
    grid_x(ax)
    save(fig, "d4_which_metrics_are_skill")


def m1_xg_calibration():
    b = pd.read_csv(RES / "calibration_bins.csv")
    cs = pd.read_csv(RES / "calibration_summary.csv").set_index(["target", "model"])
    fig = frame("Header xG predictions match reality",
                "Headed shots grouped into ten equal bins by predicted chance of a goal. Each dot compares the average\n"
                "prediction with the share that went in. Lines are 95% intervals from resampling matches.", SRC)
    ax = fig.add_axes([0.09, 0.13, 0.60, 0.70])
    ax.plot([0, 0.45], [0, 0.45], color=MUTED, lw=1)
    for model, c, label, off in (("logistic", BLUE, "This project's xG", -0.002), ("statsbomb", ORANGE, "StatsBomb xG", 0.002)):
        t = b[(b.target == "xg") & (b.model == model)]
        ax.vlines(t["predicted"] + off, t["lo"], t["hi"], color=c, lw=2, alpha=0.4)
        ax.scatter(t["predicted"] + off, t["observed"], s=46, color=c, zorder=3, edgecolors=SURFACE, linewidths=1.3,
                   label=label)
    ax.set_xlim(0, 0.42)
    ax.set_ylim(0, 0.42)
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.set_xlabel("Predicted chance of a goal (bin average)")
    ax.set_ylabel("Share of headers scored")
    ax.text(0.33, 0.36, "perfect calibration", rotation=45, fontsize=8.5, color=MUTED, ha="center", va="bottom",
            rotation_mode="anchor")
    grid_y(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ours, sb = cs.loc[("xg", "logistic")], cs.loc[("xg", "statsbomb")]
    fig.text(0.72, 0.78, "Calibration slope", fontsize=9.5, fontweight="bold", color=INK, va="top")
    fig.text(0.72, 0.73, f"This project  {ours.slope:.2f}\n   95%  {ours.slope_lo:.2f} to {ours.slope_hi:.2f}\n"
             f"StatsBomb  {sb.slope:.2f}\n   95%  {sb.slope_lo:.2f} to {sb.slope_hi:.2f}", fontsize=9, color=INK2,
             va="top", linespacing=1.5)
    fig.text(0.72, 0.53, "1 is ideal. Below 1 means\npredictions are a bit too\nextreme, above 1 a bit too\ncautious.",
             fontsize=8.5, color=MUTED, va="top", linespacing=1.35)
    fig.text(0.72, 0.36, "Average prediction", fontsize=9.5, fontweight="bold", color=INK, va="top")
    fig.text(0.72, 0.31, f"This project  {ours.mean_pred:.3f}\nStatsBomb  {sb.mean_pred:.3f}\n"
             f"Actual goal rate  {ours.mean_obs:.3f}", fontsize=9, color=INK2, va="top", linespacing=1.5)
    save(fig, "m1_xg_calibration")


def calibration_grid():
    """All five models on one sheet, saved in results/ for the repository."""
    b = pd.read_csv(RES / "calibration_bins.csv")
    names = {"xg": "Header is a goal", "xot": "Header on target", "duel": "Defender wins the duel",
             "shot10": "Opponent shot within 10 s", "keep": "Defending team keeps the ball"}
    fig = frame("Calibration of every model", "Predicted against observed rate in ten equal bins, with 95% match "
                "bootstrap intervals. Blue is logistic regression, orange is gradient boosting.", SRC, size=(12, 7.6))
    for i, (t, label) in enumerate(names.items()):
        ax = fig.add_axes([0.06 + (i % 3) * 0.32, 0.50 - (i // 3) * 0.39, 0.25, 0.30])
        sub = b[b.target == t]
        top = max(sub["hi"].max(), sub["predicted"].max()) * 1.05
        lo_lim = 0 if top < 0.6 else min(sub["lo"].min(), sub["predicted"].min()) * 0.95
        ax.plot([lo_lim, top], [lo_lim, top], color=MUTED, lw=1)
        for model, c in (("logistic", BLUE), ("boosting", ORANGE)):
            m = sub[sub.model == model]
            ax.vlines(m["predicted"], m["lo"], m["hi"], color=c, lw=1.6, alpha=0.4)
            ax.scatter(m["predicted"], m["observed"], s=18, color=c, zorder=3)
        ax.set_xlim(lo_lim, top)
        ax.set_ylim(lo_lim, top)
        ax.set_title(label, fontsize=10, loc="left", color=INK)
        ax.tick_params(labelsize=8)
        grid_y(ax)
    fig.savefig(RES / "calibration_all_models.png", dpi=120)
    plt.close(fig)
    print("saved calibration_all_models")


def main():
    a1_xg_map()
    a2_delivery()
    a3_drivers()
    a4_finishing()
    d1_height()
    d2_danger_map()
    d3_defenders()
    d4_reliability()
    m1_xg_calibration()
    calibration_grid()


if __name__ == "__main__":
    main()
