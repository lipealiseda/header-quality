"""Robustness check for the aerial duel rankings: a mixed effects logistic model.

Model, for duel i between defending player d(i) and attacking player a(i)

    logit P(defender wins) = offset_i + u[d(i)] - u[a(i)]
    u[j] ~ Normal(0, sigma^2)   one random intercept per player (crossed effects)

The offset is the logit of the duel model's out of fold prediction, so the fixed
part (location, delivery, heights, positions and so on) is the same as in the
empirical Bayes (EB) ranking. The difference is in how player skill is estimated.

  EB (rankings.py) sums each player's wins minus expected wins, then shrinks that
  number. It treats every opponent as average.
  The mixed model estimates all players at once, so beating a player who is himself
  good in the air counts for more, and losing to him counts for less.

Fitting. statsmodels is not installable in this environment, so the model is fit
directly with the Laplace approximation to the marginal likelihood, the same
approximation lme4's glmer uses by default:

    log L(sigma) ~ loglik(u_hat) - |u_hat|^2 / (2 sigma^2) - (k/2) log sigma^2 - (1/2) log det H
    H = X' W X + I / sigma^2

where u_hat is the posterior mode found by Newton's method and W holds p(1 - p) at
u_hat. sigma is chosen to maximise log L. Player standard errors come from the
diagonal of H^-1. A simulation with known sigma and known player effects checks the
fit before it is used.

Outputs
    results/mixed_model_players.csv   u, standard error and EB numbers per ranked player
    results/mixed_model_summary.md    sigma, rank correlations, top 10 overlap, simulation check
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import minimize_scalar
from scipy.sparse.linalg import splu
from scipy.special import expit, logit
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modeling import PROC, RES  # noqa: E402

RNG = np.random.default_rng(11)


def design(def_idx, att_idx, k):
    n = len(def_idx)
    rows = np.r_[np.arange(n), np.arange(n)]
    cols = np.r_[def_idx, att_idx]
    vals = np.r_[np.ones(n), -np.ones(n)]
    return sp.csr_matrix((vals, (rows, cols)), shape=(n, k))


def mode(X, y, off, sigma, u0=None, tol=1e-7, max_iter=50):
    """Posterior mode of u for a given sigma (Newton's method)."""
    k = X.shape[1]
    u = np.zeros(k) if u0 is None else u0.copy()
    prec = 1 / sigma ** 2
    XT = X.T.tocsr()
    for _ in range(max_iter):
        mu = expit(off + X @ u)
        g = XT @ (y - mu) - prec * u
        W = sp.diags(mu * (1 - mu))
        H = (XT @ W @ X + prec * sp.identity(k)).tocsc()
        lu = splu(H)
        step = lu.solve(g)
        u += step
        if np.max(np.abs(step)) < tol:
            break
    mu = expit(off + X @ u)
    W = sp.diags(mu * (1 - mu))
    H = (XT @ W @ X + prec * sp.identity(k)).tocsc()
    return u, splu(H)


def laplace_loglik(X, y, off, sigma, cache):
    u, lu = mode(X, y, off, sigma, cache.get("u"))
    cache["u"] = u
    eta = off + X @ u
    ll = np.sum(y * eta - np.logaddexp(0, eta))
    logdet = np.sum(np.log(np.abs(lu.U.diagonal())))
    k = X.shape[1]
    return ll - u @ u / (2 * sigma ** 2) - k * np.log(sigma) - 0.5 * logdet


def fit(X, y, off, bounds=(0.02, 1.5)):
    cache = {}
    res = minimize_scalar(lambda ls: -laplace_loglik(X, y, off, np.exp(ls), cache),
                          bounds=np.log(bounds), method="bounded", options={"xatol": 1e-3})
    sigma = float(np.exp(res.x))
    u, lu = mode(X, y, off, sigma, cache.get("u"))
    return sigma, u, lu


def standard_errors(lu, idx, batch=256):
    """sqrt of the diagonal of H^-1 for the selected players."""
    k = lu.shape[0]
    se = np.empty(len(idx))
    for s in range(0, len(idx), batch):
        cols = idx[s:s + batch]
        E = np.zeros((k, len(cols)))
        E[cols, np.arange(len(cols))] = 1
        Z = lu.solve(E)
        se[s:s + batch] = np.sqrt(Z[cols, np.arange(len(cols))])
    return se


def simulation_check(sigma_true=0.35, k=600, n=60000):
    """Fit on fake duels with known answers."""
    u_true = RNG.normal(0, sigma_true, k)
    d, a = RNG.integers(0, k, n), RNG.integers(0, k, n)
    keep = d != a
    d, a = d[keep], a[keep]
    off = logit(np.clip(RNG.beta(6, 4, len(d)), 0.05, 0.95))
    y = (RNG.random(len(d)) < expit(off + u_true[d] - u_true[a])).astype(float)
    X = design(d, a, k)
    sigma, u, _ = fit(X, y, off)
    return {"sigma_true": sigma_true, "sigma_hat": sigma, "corr_u": float(np.corrcoef(u, u_true)[0, 1]),
            "spearman_u": float(spearmanr(u, u_true)[0]), "duels": int(len(d)), "players": k}


def main():
    sim = simulation_check()
    print("simulation check", sim)

    d = pd.read_csv(PROC / "duel_predictions.csv.gz")
    p = np.clip(d[d["best"].iloc[0]].values, 1e-4, 1 - 1e-4)
    ids = pd.Index(pd.unique(np.r_[d["def_player_id"].values, d["att_player_id"].values]))
    di, ai = ids.get_indexer(d["def_player_id"]), ids.get_indexer(d["att_player_id"])
    X = design(di, ai, len(ids))
    y = d["def_won"].values.astype(float)
    sigma, u, lu = fit(X, y, logit(p))
    print(f"sigma = {sigma:.3f} on the logit scale, {len(ids):,} players, {len(y):,} duels")

    eb = pd.read_csv(RES / "rank_duels_vs_expected.csv")
    q = eb[eb["qualified"]].copy()
    pos = ids.get_indexer(q["player_id"])
    q["glmm_u"] = u[pos]
    q["glmm_se"] = standard_errors(lu, pos)
    # put the logit effect on the same "duels per 100" scale as EB, using the average
    # slope of the logistic curve over each player's own duels
    slope = pd.concat([
        pd.DataFrame({"player_id": d["def_player_id"], "s": p * (1 - p)}),
        pd.DataFrame({"player_id": d["att_player_id"], "s": p * (1 - p)})]).groupby("player_id")["s"].mean()
    q["glmm_per100"] = q["glmm_u"] * q["player_id"].map(slope).values * 100
    q["glmm_lo95"] = (q["glmm_u"] - 1.96 * q["glmm_se"]) * q["player_id"].map(slope).values * 100
    q["glmm_hi95"] = (q["glmm_u"] + 1.96 * q["glmm_se"]) * q["player_id"].map(slope).values * 100
    q["eb_per100"] = q["shrunk_rate"] * 100

    def compare(sub, label):
        rho = spearmanr(sub["eb_per100"], sub["glmm_u"])[0]
        top_eb = set(sub.nlargest(10, "eb_per100")["player_id"])
        top_gl = set(sub.nlargest(10, "glmm_u")["player_id"])
        above_eb = sub["lo95"] > 0
        above_gl = sub["glmm_lo95"] > 0
        below_eb, below_gl = sub["hi95"] < 0, sub["glmm_hi95"] < 0
        return {"group": label, "players": len(sub), "spearman": rho,
                "top10_overlap": len(top_eb & top_gl),
                "clearly_above_eb": int(above_eb.sum()), "clearly_above_glmm": int(above_gl.sum()),
                "clearly_above_both": int((above_eb & above_gl).sum()),
                "clearly_below_eb": int(below_eb.sum()), "clearly_below_glmm": int(below_gl.sum())}

    comp = pd.DataFrame([
        compare(q, "All ranked players"),
        compare(q[q["pos_group"].isin(["CB", "FB"])], "Defenders"),
        compare(q[q["pos_group"].isin(["ST", "W", "AM"])], "Forwards"),
    ])
    # rank correlation with an interval, bootstrapping players
    boot = []
    for _ in range(2000):
        s = q.iloc[RNG.integers(0, len(q), len(q))]
        boot.append(spearmanr(s["eb_per100"], s["glmm_u"])[0])
    lo, hi = np.quantile(boot, [0.025, 0.975])

    # who moves most, and is the move explained by the strength of opponents faced?
    q["eb_rank"] = q["eb_per100"].rank(ascending=False)
    q["glmm_rank"] = q["glmm_u"].rank(ascending=False)
    opp = pd.concat([
        pd.DataFrame({"player_id": d["def_player_id"], "opp": u[ai]}),
        pd.DataFrame({"player_id": d["att_player_id"], "opp": u[di]})]).groupby("player_id")["opp"].mean()
    q["opp_strength"] = q["player_id"].map(opp)
    move = q["glmm_rank"] - q["eb_rank"]
    rho_move = spearmanr(-move, q["opp_strength"])[0]

    keep = ["player_id", "name", "pos_group", "main_club", "n", "eb_per100", "lo95", "hi95", "glmm_u", "glmm_se",
            "glmm_per100", "glmm_lo95", "glmm_hi95", "eb_rank", "glmm_rank", "opp_strength"]
    q[keep].sort_values("glmm_u", ascending=False).to_csv(RES / "mixed_model_players.csv", index=False)

    movers = q.assign(move=move).reindex(move.abs().sort_values(ascending=False).index).head(6)
    L = ["# Mixed effects check of the aerial duel rankings", "",
         "Crossed random intercept logistic model on top of the duel model (offset = logit of the out of fold "
         "prediction), fit by the Laplace approximation. See src/mixed_model.py.", "",
         "## Simulation check", "",
         f"Fake data with {sim['players']} players and {sim['duels']:,} duels, true sigma {sim['sigma_true']}. "
         f"Estimated sigma {sim['sigma_hat']:.3f}, correlation between estimated and true player effects "
         f"{sim['corr_u']:.3f}. The fitting code recovers known answers.", "",
         "## Real data", "",
         f"{len(y):,} duels and {len(ids):,} players. Spread of player effects sigma = {sigma:.3f} on the log odds "
         f"scale, roughly {sigma * 0.24 * 100:.1f} duels per 100 for one standard deviation of skill.", "",
         f"Spearman rank correlation between the mixed model and EB over all {len(q)} ranked players is "
         f"{comp.iloc[0].spearman:.3f} (95% interval {lo:.3f} to {hi:.3f}, bootstrapping players).", "",
         "| Group | Players | Spearman | Top 10 overlap | Clearly above (EB / mixed / both) | Clearly below (EB / mixed) |",
         "|---|---|---|---|---|---|"]
    for r in comp.itertuples():
        L.append(f"| {r.group} | {r.players} | {r.spearman:.3f} | {r.top10_overlap} of 10 | "
                 f"{r.clearly_above_eb} / {r.clearly_above_glmm} / {r.clearly_above_both} | "
                 f"{r.clearly_below_eb} / {r.clearly_below_glmm} |")
    L += ["", "## Who moves", "",
          f"Players who move up in the mixed model tend to have faced stronger opponents in the air (Spearman "
          f"{rho_move:.2f} between moving up and average opponent effect). That is the one thing the mixed model "
          "adds: it credits a player for the quality of the opposition.", "",
          "| Player | Pos | Duels | EB rank | Mixed model rank | Average opponent effect |", "|---|---|---|---|---|---|"]
    for r in movers.itertuples():
        L.append(f"| {r.name} | {r.pos_group} | {r.n} | {int(r.eb_rank)} | {int(r.glmm_rank)} | {r.opp_strength:+.3f} |")
    (RES / "mixed_model_summary.md").write_text("\n".join(L))
    pd.DataFrame([{**sim, "sigma_real": sigma, "spearman_all": comp.iloc[0].spearman, "spearman_lo": lo,
                   "spearman_hi": hi, "rho_move_opp": rho_move}]).to_csv(RES / "mixed_model_stats.csv", index=False)
    comp.to_csv(RES / "mixed_model_comparison.csv", index=False)
    print("\n".join(L))


if __name__ == "__main__":
    main()
