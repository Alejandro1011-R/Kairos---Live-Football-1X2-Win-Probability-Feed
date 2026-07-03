"""
Kairos — train & evaluate the NATIONAL-TEAM model (World Cup 2026 track).

M3 "Kairos" here is no longer a snapshot classifier. It recreates the model
FAMILY used in the actual in-play win-probability literature:

  * Robberechts, Van Haaren & Davis, "A Bayesian Approach to In-Game Win
    Probability in Soccer" (KDD 2021) — models the running score as a Poisson
    goal-arrival process per team, with a pre-match team-strength prior (Elo)
    and in-play covariates (score state, red cards) modulating the rate.
  * Clegg, Song & Cartlidge, "A market-calibrated accelerated failure time
    model for in-play football forecasting" (arXiv, May 2026) — same paradigm
    (continuous-time goal-arrival process), and their headline finding is that
    calibrating the pre-match team-strength prior matters MORE than the choice
    of model on top of it.

Neither paper's exact data is available to us for free (Robberechts needs a
full pass/xT event stream; Clegg needs live Betfair Exchange odds), so this is
a faithful adaptation of the shared mechanism to the data we DO have honestly:
exact goal & red-card timestamps from KickoffAPI, and a real pre-match Elo
prior scraped from eloratings.net (build_elo.py). No linear ramps, no proxies.

Mechanism — the same architecture the commercial systems (Opta supercomputer,
market makers) use, on free data:

1. PRIOR MODULE (swap-ready): pre-match team strength as two logit features.
   Default source is Elo (multinomial logistic fit on training kickoffs);
   whenever a row carries de-vigged market probabilities (mkt_pH/pD/pA, e.g.
   from market_live.py at serving time) those replace the Elo prior in the
   exact same feature space. The club track (train_market.py) proves the
   market prior is worth far more than any in-play covariate.
2. GOAL PROCESS: per side, a Poisson RATE regression (goals per minute of
   remaining time) on the prior logits + [goal_diff, red_diff] + real rolling
   attacking intensity (xg_roll_h/a over the last 12 minutes, from StatsBomb
   event streams) with a has_xg availability flag — matches without an event
   stream degrade gracefully, no proxies. GLM offset trick: target =
   remaining_goals / time_remaining, sample_weight = time_remaining. At any
   live minute the difference of the two Poisson remaining-goal counts is
   Skellam-distributed in closed form -> P(H/D/A), no simulation.
3. RECALIBRATION layer: multinomial logistic on the Skellam log-probabilities
   plus match context (time remaining, level-score indicator), fit on
   out-of-fold predictions grouped by match (prior refit per fold too). This
   corrects the Skellam independence assumption — independent home/away counts
   under-price the draw (the classic Dixon-Coles finding; this dataset is
   ~1/3 draws) — and residual time-varying over/under-confidence.

Every component earned its place by 5-fold match-level CV (never the single
holdout): expanded dataset -1.5%, prior module -0.8% vs raw elo_diff,
intensity -0.1%, recalibration the largest single piece.

M1/M2 keep the same "accuracy != money" story as the club track: a naive
scoreboard baseline, and an uncalibrated gradient-boosting "trap" (good
accuracy, bad log-loss/ECE because tree-leaf probabilities are overconfident
on autocorrelated snapshots).
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

import train as T   # reuse the metric/eval helpers so both tracks stay comparable

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "outputs")

MAX_MIN = 90
BASE_FEATURES = ["minute", "goal_diff"]
GBM_FEATURES = ["minute", "time_remaining", "goal_diff", "home_goals",
                "away_goals", "red_home", "red_away", "elo_diff"]
# in-play covariates of the rate model; the two prior logits (PriorModule) are
# prepended to these at fit/predict time
RATE_FEATURES = ["goal_diff", "red_diff", "xg_roll_h", "xg_roll_a", "has_xg"]

# tournaments present in BOTH sources — keep the StatsBomb copy (real per-minute
# shots/xG), drop the KickoffAPI copy, so no match is counted twice
OVERLAP_COMPS = {"FIFA World Cup 2022", "UEFA Euro 2024", "Copa America 2024"}
XG_ROLL_MIN = 12  # rolling attacking-intensity window (minutes)


def _add_live_features(df):
    df["red_diff"] = df.red_home - df.red_away
    if "xg_home" not in df.columns:
        df["xg_home"] = np.nan
        df["xg_away"] = np.nan
    df["has_xg"] = df.xg_home.notna().astype(float)
    g = df.groupby("match_id")
    for side in ("home", "away"):
        cum = df[f"xg_{side}"].fillna(0)
        roll = cum - g[f"xg_{side}"].shift(XG_ROLL_MIN).fillna(0).fillna(0)
        df[f"xg_roll_{side[0]}"] = roll.clip(lower=0).fillna(0)
    return df


def load_intl():
    """Combined national-team dataset: KickoffAPI (exact goal/card timestamps)
    + StatsBomb open data (same, plus real per-minute shots/xG), deduped.

    Where free historical closing odds exist (WC2018 + WC2022, football-data
    .co.uk via build_odds_intl.py) each match also carries de-vigged market
    probabilities (mkt_pH/pD/pA, constant across its 91 rows). A second wave
    (build_odds_intl_scraped.py — betexplorer.com "best odds" 1X2, personal/
    academic use, see that module's docstring on its ToS caveat) backfills
    the remaining tournaments (Euro 2020/24, Copa América 2024, AFCON 23/25,
    Asian Cup 2023, Gold Cup 2025, Nations League 2024) where WC-workbook
    odds don't exist; football-data.co.uk odds always take priority when a
    match happens to have both. PriorModule then uses whichever market prior
    is present and Elo on the rest, the same mixed regime the serving path
    runs."""
    a = pd.read_csv(os.path.join(DATA, "snapshots_intl.csv"))
    sb = os.path.join(DATA, "snapshots_sb_intl.csv")
    if os.path.exists(sb):
        b = pd.read_csv(sb)
        a = a[~a.comp.isin(OVERLAP_COMPS)]
        a, b = a.copy(), b.copy()
        a["source"] = "kickoff"
        b["source"] = "statsbomb"
        df = pd.concat([a, b], ignore_index=True)
    else:
        df = a.copy()
        df["source"] = "kickoff"
    odds = os.path.join(DATA, "odds_intl.csv")
    if os.path.exists(odds):
        o = pd.read_csv(odds)[["match_id", "comp", "mkt_pH", "mkt_pD", "mkt_pA"]]
        df = df.merge(o, on=["match_id", "comp"], how="left")
    scraped = os.path.join(DATA, "odds_intl_scraped.csv")
    if os.path.exists(scraped):
        s = pd.read_csv(scraped)[["match_id", "comp", "mkt_pH", "mkt_pD", "mkt_pA"]]
        s = s.rename(columns={c: f"{c}_scraped" for c in ("mkt_pH", "mkt_pD", "mkt_pA")})
        df = df.merge(s, on=["match_id", "comp"], how="left")
        for c in ("mkt_pH", "mkt_pD", "mkt_pA"):
            df[c] = df[c].fillna(df[f"{c}_scraped"])
        df = df.drop(columns=[f"{c}_scraped" for c in ("mkt_pH", "mkt_pD", "mkt_pA")])
    return _add_live_features(df)


class PriorModule:
    """Pre-match team-strength prior as two swap-ready logit features:
    logit_ha = log(pH/pA), logit_d = log(pD / sqrt(pH*pA)).

    Default source: Elo -> kickoff P(H/D/A) via a multinomial logistic fit on
    the training kickoffs. Swap source: if a row carries de-vigged market
    probabilities (mkt_pH/mkt_pD/mkt_pA — e.g. from market_live.py), those are
    used directly. Same feature space either way, which is exactly how the
    commercial systems work: the market prior does the heavy lifting whenever
    a market exists, the rating system covers everything else."""

    def fit(self, train):
        kick = train[train.minute == 0]
        self.elo_to_hda = make_pipeline(StandardScaler(),
                                        LogisticRegression(max_iter=3000))
        self.elo_to_hda.fit(kick[["elo_diff"]], kick.result.values)
        return self

    def features(self, df):
        p = T.proba_in_order(self.elo_to_hda, df[["elo_diff"]])
        if "mkt_pH" in df.columns:
            m = df[["mkt_pH", "mkt_pD", "mkt_pA"]].values
            has_mkt = ~np.isnan(m).any(axis=1)
            p[has_mkt] = m[has_mkt]
        p = np.clip(p, 1e-6, 1)
        return np.stack([np.log(p[:, 0] / p[:, 2]),
                         np.log(p[:, 1] / np.sqrt(p[:, 0] * p[:, 2]))], axis=1)


class GoalProcessModel:
    """Poisson goal-arrival process + swap-ready strength prior (market/Elo)
    + real attacking intensity where the event stream carries it + out-of-fold
    recalibration layer. See module docstring."""

    RECAL_FOLDS = 4

    @staticmethod
    def _ensure_cols(df):
        """Serving-time frames (live_runner) may lack the intensity columns —
        absent signal degrades gracefully to has_xg=0, never a fake value."""
        df = df.copy()
        for c, v in (("xg_roll_h", 0.0), ("xg_roll_a", 0.0), ("has_xg", 0.0)):
            if c not in df.columns:
                df[c] = v
        return df

    @staticmethod
    def _design(df, prior):
        return np.hstack([prior.features(df), df[RATE_FEATURES].values])

    def _fit_rates(self, train, prior):
        live = train[train.time_remaining > 0].copy()
        live["final_home"] = live.groupby("match_id").home_goals.transform("max")
        live["final_away"] = live.groupby("match_id").away_goals.transform("max")
        rem_home = (live.final_home - live.home_goals).clip(lower=0)
        rem_away = (live.final_away - live.away_goals).clip(lower=0)
        X = self._design(live, prior)
        w = live.time_remaining.values.astype(float)
        home_rate = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(
            X, (rem_home / live.time_remaining).values, sample_weight=w)
        away_rate = PoissonRegressor(alpha=1e-3, max_iter=2000).fit(
            X, (rem_away / live.time_remaining).values, sample_weight=w)
        return home_rate, away_rate

    def _raw_hda(self, rates, prior, df):
        """P(H/D/A) from the goal process alone. Vectorised, closed-form (Skellam)."""
        home_rate, away_rate = rates
        X = self._design(df, prior)
        time_remaining = df.time_remaining.values.astype(float)
        lam_h = np.clip(home_rate.predict(X) * time_remaining, 1e-6, None)
        lam_a = np.clip(away_rate.predict(X) * time_remaining, 1e-6, None)
        k = -df.goal_diff.values  # Delta needed for a draw: rem_home - rem_away == k
        p_draw = skellam.pmf(k, lam_h, lam_a)
        p_home = skellam.sf(k, lam_h, lam_a)
        p_away = skellam.cdf(k - 1, lam_h, lam_a)
        # minute 90 (time_remaining == 0): outcome is already fully realised
        done = time_remaining <= 0
        if done.any():
            gd = df.goal_diff.values[done]
            p_home[done] = (gd > 0).astype(float)
            p_draw[done] = (gd == 0).astype(float)
            p_away[done] = (gd < 0).astype(float)
        p = np.stack([p_home, p_draw, p_away], axis=1)
        return p / p.sum(axis=1, keepdims=True)

    @staticmethod
    def _recal_design(p, df):
        return np.hstack([
            np.log(np.clip(p, 1e-9, 1.0)),
            (df.time_remaining.values.astype(float) / MAX_MIN)[:, None],
            (df.goal_diff.values == 0).astype(float)[:, None],
        ])

    def fit(self, train):
        train = self._ensure_cols(train)
        self.prior = PriorModule().fit(train)
        self.rates = self._fit_rates(train, self.prior)
        # recalibration layer, fit on out-of-fold predictions (grouped by match
        # so it never scores probabilities from a model that saw the same match;
        # the prior module is refit per fold for the same reason)
        p_oof = np.empty((len(train), 3))
        gkf = GroupKFold(n_splits=self.RECAL_FOLDS)
        for tr_i, va_i in gkf.split(p_oof, groups=train.match_id.values):
            fold_train = train.iloc[tr_i]
            fold_prior = PriorModule().fit(fold_train)
            p_oof[va_i] = self._raw_hda(self._fit_rates(fold_train, fold_prior),
                                        fold_prior, train.iloc[va_i])
        live = (train.time_remaining.values > 0)
        self.recal = LogisticRegression(max_iter=3000, C=1.0).fit(
            self._recal_design(p_oof[live], train[live]),
            train.result.values[live])
        self._recal_col = [list(self.recal.classes_).index(c) for c in T.CLASSES]
        return self

    def predict_hda_raw(self, df):
        """Skellam probabilities without the recalibration layer (for ablation)."""
        return self._raw_hda(self.rates, self.prior, self._ensure_cols(df))

    def predict_hda(self, df):
        df = self._ensure_cols(df)
        p = self._raw_hda(self.rates, self.prior, df)
        live = df.time_remaining.values.astype(float) > 0
        if live.any():  # finished rows stay one-hot; recalibrate live rows only
            q = self.recal.predict_proba(self._recal_design(p[live], df[live]))
            p[live] = q[:, self._recal_col]
        return p


def main():
    df = load_intl()
    train, test = T.split_by_match(df)
    print(f"[INTL] train matches={train.match_id.nunique()} rows={len(train)} | "
          f"test matches={test.match_id.nunique()} rows={len(test)}")
    ytr, yte = train.result.values, test.result.values

    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    base.fit(train[BASE_FEATURES], ytr)
    p_base = T.proba_in_order(base, test[BASE_FEATURES])

    gbm = HistGradientBoostingClassifier(
        learning_rate=0.07, max_leaf_nodes=63, min_samples_leaf=80,
        l2_regularization=0.5, max_iter=2000, early_stopping=True,
        validation_fraction=0.15, n_iter_no_change=30, random_state=42)
    gbm.fit(train[GBM_FEATURES], ytr)
    p_gbm = T.proba_in_order(gbm, test[GBM_FEATURES])

    goalproc = GoalProcessModel().fit(train)
    p_raw = goalproc.predict_hda_raw(test)   # ablation: goal process alone
    p_main = goalproc.predict_hda(test)      # + recalibration layer (the product)

    results = [T.evaluate("M1 Scoreboard baseline", p_base, yte),
               T.evaluate("M2 Gradient boosting (uncalib., +Elo)", p_gbm, yte),
               T.evaluate("M3a Goal-process, raw Skellam (ablation)", p_raw, yte),
               T.evaluate("M3 Kairos (goal-process + recalibration)", p_main, yte)]

    print("\n=== [INTL] Overall metrics (test set) ===")
    print(f"{'model':40} {'log_loss':>9} {'brier':>7} {'accuracy':>9} {'ECE(H)':>7}")
    for r in results:
        print(f"{r['model']:40} {r['log_loss']:>9.4f} {r['brier']:>7.4f} "
              f"{r['accuracy']:>9.4f} {r['ece_homewin']:>7.4f}")

    print("\n=== [INTL] Log-loss by game state (test set) ===")
    print(f"{'state':28} {'n':>7} {'baseline':>9} {'Kairos':>9} {'uplift%':>8}")
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
        llm = T.logloss_hda(yte[mask], p_main[mask])
        up = (llb - llm) / llb * 100
        state_rows.append({"state": label, "n": int(mask.sum()),
                           "baseline": round(llb, 4), "kairos": round(llm, 4),
                           "uplift_pct": round(up, 2)})
        print(f"{label:28} {mask.sum():>7} {llb:>9.4f} {llm:>9.4f} {up:>8.1f}")

    uplift = (results[0]["log_loss"] - results[3]["log_loss"]) / results[0]["log_loss"] * 100
    print(f"\n[INTL] Overall log-loss reduction (Kairos vs baseline): {uplift:+.1f}%")

    fig, ax = plt.subplots(figsize=(6.2, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfectly calibrated")
    for p, lbl, col in [(p_base, "M1 Scoreboard baseline", "#888"),
                        (p_gbm, "M2 Gradient boosting (uncalib.)", "#e15759"),
                        (p_raw, "M3a Goal-process, raw Skellam", "#76b7b2"),
                        (p_main, "M3 Kairos (recalibrated)", "#1f77b4")]:
        xs, ys = T.reliability_points(p[:, 0], (yte == "H").astype(float))
        ax.plot(xs, ys, "o-", color=col, label=lbl, lw=2, ms=5)
    ax.set_xlabel("Predicted P(home win)"); ax.set_ylabel("Observed home-win frequency")
    ax.set_title("Calibration — international model (P home win)")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_reliability_intl.png")); plt.close(fig)

    payload = {
        "dataset": {
            "source": "KickoffAPI events + StatsBomb open-data event streams "
                       "(exact goal/red-card timestamps everywhere; real per-minute "
                       "shots/xG on the StatsBomb matches; no proxies) "
                       "+ eloratings.net pre-match Elo (build_elo.py) "
                       "+ football-data.co.uk closing odds for WC2018/WC2022 "
                       "(build_odds_intl.py — market prior in training where it exists)",
            "competitions": sorted(df.comp.unique().tolist()),
            "matches": int(df.match_id.nunique()), "snapshots": int(len(df)),
            "matches_with_xg": int(df[df.has_xg == 1].match_id.nunique()),
            "matches_with_market_prior": int(df[df.mkt_pH.notna()].match_id.nunique())
                                         if "mkt_pH" in df.columns else 0,
            "train_matches": int(train.match_id.nunique()),
            "test_matches": int(test.match_id.nunique()),
            "kickoff_base_rates": df[df.minute == 0].result.value_counts(normalize=True).round(4).to_dict(),
        },
        "method": "M3 = Poisson goal-arrival process (Skellam-distributed remaining "
                  "goal difference) with a swap-ready strength prior (de-vigged "
                  "market odds when a market exists, Elo otherwise), real rolling-xG "
                  "attacking intensity where the event stream carries it, plus a "
                  "multinomial recalibration layer fit on out-of-fold (by-match) "
                  "predictions, correcting the Skellam independence assumption's "
                  "draw under-pricing (Dixon-Coles effect). Following Robberechts "
                  "et al. KDD'21 and Clegg et al. 2026 — not a snapshot classifier.",
        "metrics": results,
        "logloss_reduction_pct_vs_baseline": round(uplift, 2),
        "by_game_state": state_rows,
    }
    with open(os.path.join(OUT, "metrics_intl.json"), "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved [INTL] metrics + reliability figure to {OUT}")


if __name__ == "__main__":
    main()
