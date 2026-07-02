"""
Kairos — train & evaluate live 1X2 win-probability models.

Two models, deliberately:
  * Scoreboard baseline : multinomial logistic on [minute, goal_diff]
                          ("the obvious approach")
  * Kairos (main)     : gradient boosting on full match-state features,
                          probability-calibrated (isotonic)

We evaluate with metrics that match the BUSINESS, not just accuracy:
  log-loss + Brier + calibration (reliability / ECE), with accuracy shown
  only for contrast (to demonstrate accuracy != the right objective).
"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import log_loss, accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

CLASSES = ["H", "D", "A"]          # report order (home win / draw / away win)
# raw features the "black-box" gradient boosting model sees
GBM_FEATURES = ["minute", "time_remaining", "goal_diff", "home_goals",
                "away_goals", "red_home", "red_away", "shots_home",
                "shots_away", "xg_home", "xg_away", "xg_diff"]
# the naive "scoreboard" baseline
BASE_FEATURES = ["minute", "goal_diff"]
# Kairos: game-state features with the key interactions
#   mxgd = minute x goal_diff, tr_gd = time_remaining x goal_diff
#   (a one-goal lead is worth far more at minute 85 than minute 15)
LIVE_FEATURES = ["minute", "time_remaining", "goal_diff", "mxgd", "tr_gd",
                 "xg_diff", "red_diff", "shots_home", "shots_away"]
RNG = np.random.RandomState(42)


def add_engineered(df):
    df = df.copy()
    df["mxgd"] = df.minute * df.goal_diff
    df["tr_gd"] = df.time_remaining * df.goal_diff
    df["red_diff"] = df.red_home - df.red_away
    return df


def load():
    f = os.path.join(DATA, "snapshots.parquet")
    if os.path.exists(f):
        return pd.read_parquet(f)
    return pd.read_csv(os.path.join(DATA, "snapshots.csv"))


def split_by_match(df, test_frac=0.2, seed=42):
    # fresh RNG per call: the split for a given dataset is identical no matter
    # how many other splits were drawn before it in the same process (keeps
    # notebook results equal to each script's standalone results)
    ids = df.match_id.unique()
    np.random.RandomState(seed).shuffle(ids)
    n_test = int(len(ids) * test_frac)
    test_ids = set(ids[:n_test])
    test = df[df.match_id.isin(test_ids)].copy()
    train = df[~df.match_id.isin(test_ids)].copy()
    return train, test


def proba_in_order(model, X):
    """Return probabilities as columns [H, D, A] regardless of model class order."""
    p = model.predict_proba(X)
    idx = [list(model.classes_).index(c) for c in CLASSES]
    return p[:, idx]


# sklearn's log_loss expects probability columns in lexicographic class order
# (A, D, H). Our matrices are in [H, D, A] order, so reorder before scoring.
_LEX = ["A", "D", "H"]
_HDA_TO_LEX = [2, 1, 0]  # [H,D,A] -> [A,D,H]


def logloss_hda(y_true, p_hda):
    return float(log_loss(y_true, p_hda[:, _HDA_TO_LEX], labels=_LEX))


def brier_multiclass(y_true_oh, p):
    return float(np.mean(np.sum((p - y_true_oh) ** 2, axis=1)))


def ece_homewin(p_home, y_home, n_bins=10):
    """Expected Calibration Error for the P(home win) probability."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(p_home)
    for i in range(n_bins):
        m = (p_home >= bins[i]) & (p_home < bins[i + 1] if i < n_bins - 1 else p_home <= bins[i + 1])
        if m.sum() == 0:
            continue
        conf = p_home[m].mean()
        acc = y_home[m].mean()
        ece += (m.sum() / n) * abs(acc - conf)
    return float(ece)


def reliability_points(p_home, y_home, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    xs, ys = [], []
    for i in range(n_bins):
        m = (p_home >= bins[i]) & (p_home < bins[i + 1] if i < n_bins - 1 else p_home <= bins[i + 1])
        if m.sum() < 20:
            continue
        xs.append(p_home[m].mean())
        ys.append(y_home[m].mean())
    return np.array(xs), np.array(ys)


def evaluate(name, p, y_true):
    y_oh = np.stack([(y_true == c).astype(float) for c in CLASSES], axis=1)
    return {
        "model": name,
        "log_loss": logloss_hda(y_true, p),
        "brier": brier_multiclass(y_oh, p),
        "accuracy": float(accuracy_score(y_true, np.array(CLASSES)[p.argmax(1)])),
        "ece_homewin": ece_homewin(p[:, 0], (y_true == "H").astype(float)),
    }


def main():
    df = load()
    train, test = split_by_match(df)
    print(f"train matches={train.match_id.nunique()} rows={len(train)} | "
          f"test matches={test.match_id.nunique()} rows={len(test)}")

    train, test = add_engineered(train), add_engineered(test)
    ytr, yte = train.result.values, test.result.values

    # --- M1: Scoreboard baseline (logistic on minute + goal_diff) -----------
    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    base.fit(train[BASE_FEATURES], ytr)
    p_base = proba_in_order(base, test[BASE_FEATURES])

    # --- M2: "Black-box" gradient boosting, UNCALIBRATED (the trap) ---------
    # Powerful model, decent accuracy, but trees emit near-deterministic leaf
    # probabilities on autocorrelated in-match data -> overconfident -> the
    # probabilities (what a market is priced on) are poor.
    gbm = HistGradientBoostingClassifier(
        learning_rate=0.07, max_leaf_nodes=63, min_samples_leaf=80,
        l2_regularization=0.5, max_iter=2000, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30, random_state=42)
    gbm.fit(train[GBM_FEATURES], ytr)
    p_gbm = proba_in_order(gbm, test[GBM_FEATURES])

    # --- M3: Kairos — calibrated logistic with game-state interactions ----
    main_clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    main_clf.fit(train[LIVE_FEATURES], ytr)
    p_main = proba_in_order(main_clf, test[LIVE_FEATURES])

    results = [evaluate("M1 Scoreboard baseline", p_base, yte),
               evaluate("M2 Gradient boosting (uncalib.)", p_gbm, yte),
               evaluate("M3 Kairos (calibrated)", p_main, yte)]

    print("\n=== Overall metrics (test set) ===")
    hdr = f"{'model':34} {'log_loss':>9} {'brier':>7} {'accuracy':>9} {'ECE(H)':>7}"
    print(hdr)
    for r in results:
        print(f"{r['model']:34} {r['log_loss']:>9.4f} {r['brier']:>7.4f} "
              f"{r['accuracy']:>9.4f} {r['ece_homewin']:>7.4f}")

    # --- state-conditional: where does the richer model add value? ----------
    print("\n=== Log-loss by game state (test set) ===")
    print(f"{'state':28} {'n':>7} {'baseline':>9} {'Kairos':>9} {'uplift%':>8}")
    states = {
        "All snapshots": np.ones(len(test), bool),
        "Level score (goal_diff=0)": (test.goal_diff == 0).values,
        "Level & 0-0": ((test.goal_diff == 0) & (test.home_goals == 0)).values,
        "1-goal margin": (test.goal_diff.abs() == 1).values,
        "Has a red card": ((test.red_home + test.red_away) > 0).values,
        "Last 30 min, level": ((test.goal_diff == 0) & (test.minute >= 60)).values,
    }
    state_rows = []
    for label, mask in states.items():
        if mask.sum() < 50:
            continue
        yb = yte[mask]
        if len(set(yb)) < 2:
            continue
        llb = logloss_hda(yb, p_base[mask])
        llm = logloss_hda(yb, p_main[mask])
        up = (llb - llm) / llb * 100
        state_rows.append({"state": label, "n": int(mask.sum()),
                           "baseline": round(llb, 4), "liveedge": round(llm, 4),
                           "uplift_pct": round(up, 2)})
        print(f"{label:28} {mask.sum():>7} {llb:>9.4f} {llm:>9.4f} {up:>8.1f}")

    ll_base = results[0]["log_loss"]
    ll_main = results[2]["log_loss"]
    uplift = (ll_base - ll_main) / ll_base * 100
    print(f"\nOverall log-loss reduction (Kairos vs baseline): {uplift:+.1f}%")
    p_cal = p_main  # alias used below for figures/by-minute

    # --- by-minute log-loss --------------------------------------------------
    test = test.assign(_pbH=p_base[:, 0], _pbD=p_base[:, 1], _pbA=p_base[:, 2],
                       _pmH=p_cal[:, 0], _pmD=p_cal[:, 1], _pmA=p_cal[:, 2])
    minutes = sorted(test.minute.unique())
    ll_b_min, ll_m_min = [], []
    for mn in minutes:
        sub = test[test.minute == mn]
        ysub = sub.result.values
        ll_b_min.append(logloss_hda(ysub, sub[["_pbH", "_pbD", "_pbA"]].values)
                        if len(set(ysub)) > 1 else np.nan)
        ll_m_min.append(logloss_hda(ysub, sub[["_pmH", "_pmD", "_pmA"]].values)
                        if len(set(ysub)) > 1 else np.nan)

    # ============================ FIGURES ===================================
    plt.rcParams.update({"figure.dpi": 130, "font.size": 11, "axes.grid": True,
                         "grid.alpha": 0.3})

    # Fig 1 — hero: example match probability trajectory (Kairos model)
    plot_example_match(train, test, main_clf, df, LIVE_FEATURES)

    # Fig 2 — reliability diagram (P home win)
    fig, ax = plt.subplots(figsize=(6.2, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfectly calibrated")
    for p, lbl, col in [(p_base, "M1 Scoreboard baseline", "#888"),
                        (p_gbm, "M2 Gradient boosting (uncalib.)", "#e15759"),
                        (p_main, "M3 Kairos (calibrated)", "#1f77b4")]:
        xs, ys = reliability_points(p[:, 0], (yte == "H").astype(float))
        ax.plot(xs, ys, "o-", color=col, label=lbl, lw=2, ms=5)
    ax.set_xlabel("Predicted P(home win)")
    ax.set_ylabel("Observed home-win frequency")
    ax.set_title("Calibration / reliability diagram — P(home win)")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_reliability.png")); plt.close(fig)

    # Fig 3 — log-loss vs minute
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(minutes, ll_b_min, color="#888", lw=2, label="Scoreboard baseline")
    ax.plot(minutes, ll_m_min, color="#1f77b4", lw=2, label="Kairos (calibrated)")
    ax.set_xlabel("Match minute"); ax.set_ylabel("Log-loss (lower = better)")
    ax.set_title("Live prediction quality through the match")
    ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_logloss_by_minute.png")); plt.close(fig)

    # --- save metrics --------------------------------------------------------
    payload = {
        "dataset": {
            "competitions": ["Premier League 2015/16", "La Liga 2015/16"],
            "matches": int(df.match_id.nunique()),
            "snapshots": int(len(df)),
            "train_matches": int(train.match_id.nunique()),
            "test_matches": int(test.match_id.nunique()),
            "kickoff_base_rates": df[df.minute == 0].result.value_counts(normalize=True).round(4).to_dict(),
        },
        "features_liveedge": LIVE_FEATURES,
        "features_gbm": GBM_FEATURES,
        "features_baseline": BASE_FEATURES,
        "metrics": results,
        "logloss_reduction_pct_vs_baseline": round(uplift, 2),
        "by_game_state": state_rows,
    }
    with open(os.path.join(OUT, "metrics.json"), "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved metrics + 3 figures to {OUT}")


def plot_example_match(train, test, model, df, feats):
    """Pick a dramatic test match (a comeback) and plot the live 1X2 curves."""
    # comeback = team losing at minute 60 still does not lose
    cand = []
    for mid, g in test.groupby("match_id"):
        g = g.sort_values("minute")
        gd60 = g[g.minute == 60].goal_diff.values
        res = g.result.iloc[0]
        if len(gd60) == 0:
            continue
        gd60 = gd60[0]
        # losing at 60 but wins (home), or leading at 60 but loses
        if (gd60 < 0 and res == "H") or (gd60 > 0 and res == "A"):
            final_gd = g[g.minute == 90].goal_diff.values[0]
            cand.append((mid, abs(final_gd), g))
    if not cand:
        cand = [(mid, 0, g) for mid, g in list(test.groupby("match_id"))[:1]]
    mid, _, g = sorted(cand, key=lambda x: -x[1])[0]
    g = g.sort_values("minute")
    p = proba_in_order(model, g[feats])

    home = test  # only for label text fallback
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(g.minute, p[:, 0], color="#1f77b4", lw=2.5, label="P(home win)")
    ax.plot(g.minute, p[:, 1], color="#7f7f7f", lw=2.5, label="P(draw)")
    ax.plot(g.minute, p[:, 2], color="#e15759", lw=2.5, label="P(away win)")
    # mark goals (which side scored + running score)
    g = g.assign(hg_d=g.home_goals.diff(), ag_d=g.away_goals.diff())
    goals = g[(g.hg_d > 0) | (g.ag_d > 0)]
    for _, row in goals.iterrows():
        side = "Home" if row.hg_d > 0 else "Away"
        score = f"{int(row.home_goals)}-{int(row.away_goals)}"
        ax.axvline(row.minute, color="green", ls=":", alpha=0.6)
        ax.plot(row.minute, 1.04, marker="v", color="green", ms=8, clip_on=False)
        ax.text(row.minute, 1.075, f"{side} {score}", ha="center", fontsize=8, color="green")
    ax.set_ylim(0, 1.16); ax.set_xlim(0, 90)
    ax.set_xlabel("Match minute"); ax.set_ylabel("Probability")
    ax.set_title(f"Live 1X2 win-probability trajectory — example match (final result: {g.result.iloc[0]})")
    ax.legend(loc="center left")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_match_trajectory.png")); plt.close(fig)
    # stash some context for the writeup
    with open(os.path.join(OUT, "example_match.json"), "w") as f:
        json.dump({"match_id": int(mid), "final_goal_diff": int(g[g.minute == 90].goal_diff.values[0]),
                   "result": g.result.iloc[0], "n_goals": int(len(goals))}, f, indent=2)


if __name__ == "__main__":
    main()
