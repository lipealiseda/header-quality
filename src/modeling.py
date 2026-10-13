"""Shared modelling code. Every model is fit two ways, a logistic regression that is
easy to explain and a gradient boosting model that can pick up interactions, and
both are judged on the same match grouped cross validation. Grouping by match
matters because events in one match share context (teams, weather, referee), and
letting the same match sit in train and test would flatter the scores.

Each run returns out of fold predictions, so the player rankings in Stage 4 compare
players with predictions the model made without seeing those exact events."""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RES = ROOT / "results"
RES.mkdir(exist_ok=True)
TAG = "_noheight" if os.environ.get("HQ_NO_PHYSICAL") else ""
SEED = 7


def logistic(num, cat):
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                          ("sc", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30), cat),
    ])
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=0.5, max_iter=3000))])


def boosting(num, cat):
    pre = ColumnTransformer([
        ("num", "passthrough", num),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=30, sparse_output=False), cat),
    ])
    gbm = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=400, max_leaf_nodes=15,
                                         min_samples_leaf=40, l2_regularization=1.0,
                                         early_stopping=True, validation_fraction=0.15,
                                         random_state=SEED)
    return Pipeline([("pre", pre), ("gbm", gbm)])


def scores(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    base = np.full_like(p, y.mean())
    ll, ll0 = log_loss(y, p), log_loss(y, base)
    return {"log_loss": ll, "brier": brier_score_loss(y, p), "auc": roc_auc_score(y, p),
            "skill_vs_base_rate": 1 - ll / ll0, "pred_sum": p.sum(), "actual_sum": y.sum()}


def calibration_table(y, p, bins=10):
    q = pd.qcut(p, bins, duplicates="drop")
    return (pd.DataFrame({"y": y, "p": p, "bin": q}).groupby("bin", observed=True)
            .agg(n=("y", "size"), predicted=("p", "mean"), actual=("y", "mean")).reset_index(drop=True))


def run(df, num, cat, target, name, groups="match_id", folds=5, benchmark=None):
    """Fit both models with grouped CV. Returns (metrics, oof dataframe, fitted
    full-data models). `benchmark` is an existing probability column to score on
    the same rows, for example StatsBomb's own xG."""
    X, y, g = df[num + cat], df[target].astype(int).values, df[groups].values
    oof = {"logistic": np.zeros(len(df)), "boosting": np.zeros(len(df))}
    for tr, te in GroupKFold(folds).split(X, y, g):
        for key, make in (("logistic", logistic), ("boosting", boosting)):
            m = make(num, cat).fit(X.iloc[tr], y[tr])
            oof[key][te] = m.predict_proba(X.iloc[te])[:, 1]
    rows = [{"model": k, **scores(y, v)} for k, v in oof.items()]
    if benchmark is not None:
        rows.append({"model": benchmark, **scores(y, df[benchmark].values)})
    metrics = pd.DataFrame(rows).assign(target=name, n=len(df), positives=int(y.sum()))
    full = {"logistic": logistic(num, cat).fit(X, y), "boosting": boosting(num, cat).fit(X, y)}
    out = pd.DataFrame({f"{name}_lr": oof["logistic"], f"{name}_gbm": oof["boosting"]}, index=df.index)
    return metrics, out, full


def logistic_effects(model, num, cat):
    """Standardised logistic coefficients. For numeric features this is the change
    in log odds for one standard deviation, so sizes are comparable."""
    pre, lr = model.named_steps["pre"], model.named_steps["lr"]
    names = pre.get_feature_names_out()
    return (pd.DataFrame({"feature": names, "coef": lr.coef_[0]})
            .assign(abs=lambda d: d["coef"].abs()).sort_values("abs", ascending=False).drop(columns="abs"))


def boosting_importance(df, num, cat, target, groups="match_id"):
    """Permutation importance on a held out set of matches. It answers how much
    worse the model gets when one input is shuffled, measured in log loss."""
    g = df[groups].values
    tr, te = next(GroupKFold(5).split(df, df[target], g))
    m = boosting(num, cat).fit(df.iloc[tr][num + cat], df.iloc[tr][target].astype(int))
    r = permutation_importance(m, df.iloc[te][num + cat], df.iloc[te][target].astype(int),
                               scoring="neg_log_loss", n_repeats=5, random_state=SEED, n_jobs=1)
    return (pd.DataFrame({"feature": num + cat, "importance": r.importances_mean, "sd": r.importances_std})
            .sort_values("importance", ascending=False))


def physical_columns(df, prefix=""):
    """Physical columns that exist and are filled for at least 30% of rows. Before
    heights are joined this returns nothing and the models run without them."""
    if os.environ.get("HQ_NO_PHYSICAL"):  # used to measure what height adds
        return []
    # main models use height only. EA ratings are tested separately in ea_ratings.py,
    # since an "expected" that already knows a player's heading rating would no longer
    # measure what the ranking is meant to measure.
    keys = ("height_cm",)
    if os.environ.get("HQ_WITH_EA"):
        keys = ("height_cm", "weight_kg", "ea_strength", "ea_jumping", "ea_heading", "ea_sprint")
    cols = [c for c in df.columns if c.startswith(prefix) and any(k in c for k in keys)
            and not c.startswith(prefix + "ea_height") and not c.startswith(prefix + "ea_weight")]
    return [c for c in cols if df[c].notna().mean() >= 0.3]


def attach_physical(df, id_col, prefix):
    p = PROC / "player_physical.csv.gz"
    if not p.exists():
        return df
    ph = pd.read_csv(p)
    keep = ["player_id", "height_cm", "weight_kg", "ea_strength", "ea_jumping", "ea_heading", "ea_sprint"]
    ph = ph[[c for c in keep if c in ph.columns]].rename(columns=lambda c: c if c == "player_id" else prefix + c)
    return df.merge(ph, how="left", left_on=id_col, right_on="player_id", suffixes=("", "_ph")).drop(
        columns=["player_id_ph"], errors="ignore")
