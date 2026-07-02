"""
Kairos — club track, market-prior proof (the "what Opta actually does" test).

The commercial in-play systems (Opta supercomputer, market makers) anchor
their match probabilities on the betting market's own pre-match price and add
an in-play model on top. This script tests that recipe on the club dataset,
where everything is freely available at once: real per-minute shots/xG
(StatsBomb events), exact goal/card timestamps, AND Pinnacle closing odds for
all 760 matches (build_odds.py).

Models (all goal-process variants share the Poisson-rate -> Skellam ->
out-of-fold recalibration architecture of train_intl.py):

  M1   scoreboard baseline        logistic on [minute, goal_diff]
  M4a  goal process, no prior     rates on [goal_diff, red_diff]
  M4b  + intensity                rates + rolling 12-min real xG per side
  M4   + market prior (Kairos-M)  rates + de-vigged Pinnacle closing logits

Headline findings this script reproduces (5-fold match-level CV was used for
selection; the canonical seed-42 split is reported for continuity):
  * the market prior is worth ~4% log-loss on its own — more than every
    in-play covariate combined;
  * once the market prior is in, rolling-xG intensity adds ~nothing — the
    market price already embeds team quality. Weeks of feature engineering
    vs one free CSV of closing odds: the CSV wins. That IS Clegg et al.'s
    headline finding, reproduced independently on our own pipeline.
"""
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scipy.stats import skellam
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

import train as T

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")

XG_ROLL_MIN = 12

F_GP = ["goal_diff", "red_diff"]
F_GPX = F_GP + ["xg_roll_h", "xg_roll_a"]
F_MKT = ["mkt_logit_ha", "mkt_logit_d"]


def load_club_market():
    df = T.load()
    odds = pd.read_csv(os.path.join(DATA, "odds_club.csv"))
    df = df.merge(odds[["match_id", "mkt_logit_ha", "mkt_logit_d"]],
                  on="match_id", how="inner")
    df["red_diff"] = df.red_home - df.red_away
    g = df.groupby("match_id")
    for side in ("home", "away"):
        roll = df[f"xg_{side}"] - g[f"xg_{side}"].shift(XG_ROLL_MIN).fillna(0)
        df[f"xg_roll_{side[0]}"] = roll.clip(lower=0)
    return df


class ClubGoalProcess:
    """Same architecture as train_intl.GoalProcessModel, parametrised by the
    rate-feature list (the club track swaps prior/intensity variants in and
    out to measure what each is worth)."""

    RECAL_FOLDS = 4

    def __init__(self, feats):
        self.feats = feats

    def _fit_rates(self, train):
        live = train[train.time_remaining > 0].copy()
        live["final_home"] = live.groupby("match_id").home_goals.transform("max")
        live["final_away"] = live.groupby("match_id").away_goals.transform("max")
        rem_h = (live.final_home - live.home_goals).clip(lower=0)
        rem_a = (live.final_away - live.away_goals).clip(lower=0)
        X = live[self.feats].values
        w = live.time_remaining.values.astype(float)
        mh = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(
            X, (rem_h / live.time_remaining).values, sample_weight=w)
        ma = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(
            X, (rem_a / live.time_remaining).values, sample_weight=w)
        return mh, ma

    def _raw_hda(self, rates, df):
        mh, ma = rates
        X = df[self.feats].values
        tr_ = df.time_remaining.values.astype(float)
        lam_h = np.clip(mh.predict(X) * tr_, 1e-6, None)
        lam_a = np.clip(ma.predict(X) * tr_, 1e-6, None)
        k = -df.goal_diff.values
        p = np.stack([skellam.sf(k, lam_h, lam_a),
                      skellam.pmf(k, lam_h, lam_a),
                      skellam.cdf(k - 1, lam_h, lam_a)], axis=1)
        done = tr_ <= 0
        if done.any():
            gd = df.goal_diff.values[done]
            p[done] = np.stack([(gd > 0), (gd == 0), (gd < 0)], axis=1).astype(float)
        return p / p.sum(axis=1, keepdims=True)

    @staticmethod
    def _recal_design(p, df):
        return np.hstack([
            np.log(np.clip(p, 1e-9, 1.0)),
            (df.time_remaining.values.astype(float) / 90.0)[:, None],
            (df.goal_diff.values == 0).astype(float)[:, None],
        ])

    def fit(self, train):
        self.rates = self._fit_rates(train)
        p_oof = np.empty((len(train), 3))
        gkf = GroupKFold(n_splits=self.RECAL_FOLDS)
        for tr_i, va_i in gkf.split(p_oof, groups=train.match_id.values):
            p_oof[va_i] = self._raw_hda(self._fit_rates(train.iloc[tr_i]),
                                        train.iloc[va_i])
        live = train.time_remaining.values > 0
        self.recal = LogisticRegression(max_iter=3000, C=1.0).fit(
            self._recal_design(p_oof[live], train[live]),
            train.result.values[live])
        self._col = [list(self.recal.classes_).index(c) for c in T.CLASSES]
        return self

    def predict_hda(self, df):
        p = self._raw_hda(self.rates, df)
        live = df.time_remaining.values.astype(float) > 0
        if live.any():
            q = self.recal.predict_proba(self._recal_design(p[live], df[live]))
            p[live] = q[:, self._col]
        return p


def main():
    df = load_club_market()
    train, test = T.split_by_match(df)
    print(f"[MKT] {df.match_id.nunique()} matches with Pinnacle closing odds | "
          f"train={train.match_id.nunique()} test={test.match_id.nunique()}")
    ytr, yte = train.result.values, test.result.values

    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    base.fit(train[T.BASE_FEATURES], ytr)
    p_base = T.proba_in_order(base, test[T.BASE_FEATURES])

    p_gp = ClubGoalProcess(F_GP).fit(train).predict_hda(test)
    p_gpx = ClubGoalProcess(F_GPX).fit(train).predict_hda(test)
    kairos_m = ClubGoalProcess(F_GP + F_MKT).fit(train)
    p_mkt = kairos_m.predict_hda(test)

    results = [
        T.evaluate("M1 Scoreboard baseline", p_base, yte),
        T.evaluate("M4a Goal-process, no prior", p_gp, yte),
        T.evaluate("M4b Goal-process + xG intensity", p_gpx, yte),
        T.evaluate("M4 Kairos-M (+ market prior)", p_mkt, yte),
    ]
    print("\n=== [MKT] Overall metrics (test set) ===")
    print(f"{'model':36} {'log_loss':>9} {'brier':>7} {'accuracy':>9} {'ECE(H)':>7}")
    for r in results:
        print(f"{r['model']:36} {r['log_loss']:>9.4f} {r['brier']:>7.4f} "
              f"{r['accuracy']:>9.4f} {r['ece_homewin']:>7.4f}")

    print("\n=== [MKT] Log-loss by game state (test set) ===")
    print(f"{'state':28} {'n':>7} {'baseline':>9} {'Kairos-M':>9} {'uplift%':>8}")
    states = {
        "All snapshots": np.ones(len(test), bool),
        "Level score (goal_diff=0)": (test.goal_diff == 0).values,
        "1-goal margin": (test.goal_diff.abs() == 1).values,
        "Has a red card": ((test.red_home + test.red_away) > 0).values,
        "Last 30 min, level": ((test.goal_diff == 0) & (test.minute >= 60)).values,
    }
    state_rows = []
    for label, mask in states.items():
        if mask.sum() < 50 or len(set(yte[mask])) < 2:
            continue
        llb = T.logloss_hda(yte[mask], p_base[mask])
        llm = T.logloss_hda(yte[mask], p_mkt[mask])
        up = (llb - llm) / llb * 100
        state_rows.append({"state": label, "n": int(mask.sum()),
                           "baseline": round(llb, 4), "kairos_m": round(llm, 4),
                           "uplift_pct": round(up, 2)})
        print(f"{label:28} {mask.sum():>7} {llb:>9.4f} {llm:>9.4f} {up:>8.1f}")

    uplift = (results[0]["log_loss"] - results[3]["log_loss"]) / results[0]["log_loss"] * 100
    mkt_worth = (results[1]["log_loss"] - results[3]["log_loss"]) / results[1]["log_loss"] * 100
    xg_worth = (results[1]["log_loss"] - results[2]["log_loss"]) / results[1]["log_loss"] * 100
    print(f"\n[MKT] Kairos-M vs baseline: {uplift:+.1f}% | market prior worth "
          f"{mkt_worth:+.1f}% | xG intensity worth {xg_worth:+.1f}%")

    fig, ax = plt.subplots(figsize=(6.2, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfectly calibrated")
    for p, lbl, col in [(p_base, "M1 Scoreboard baseline", "#888"),
                        (p_gp, "M4a Goal-process, no prior", "#76b7b2"),
                        (p_mkt, "M4 Kairos-M (market prior)", "#1f77b4")]:
        xs, ys = T.reliability_points(p[:, 0], (yte == "H").astype(float))
        ax.plot(xs, ys, "o-", color=col, label=lbl, lw=2, ms=5)
    ax.set_xlabel("Predicted P(home win)"); ax.set_ylabel("Observed home-win frequency")
    ax.set_title("Calibration — club track with market prior")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_market_reliability.png")); plt.close(fig)

    payload = {
        "dataset": {
            "source": "StatsBomb open events + football-data.co.uk Pinnacle "
                       "closing odds (760/760 matched, de-vigged)",
            "matches": int(df.match_id.nunique()), "snapshots": int(len(df)),
        },
        "method": "Poisson goal process + Skellam + OOF recalibration; prior = "
                  "de-vigged market closing odds as two logit features — the "
                  "same market-anchored recipe as the commercial systems.",
        "metrics": results,
        "kairos_m_vs_baseline_pct": round(uplift, 2),
        "market_prior_worth_pct": round(mkt_worth, 2),
        "xg_intensity_worth_pct": round(xg_worth, 2),
        "by_game_state": state_rows,
    }
    with open(os.path.join(OUT, "metrics_market.json"), "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Saved [MKT] metrics + reliability figure to {OUT}")


if __name__ == "__main__":
    main()
