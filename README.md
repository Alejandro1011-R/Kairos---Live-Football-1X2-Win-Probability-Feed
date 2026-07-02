# Kairos — Live Football 1X2 Win-Probability Feed

A B2B sports-data product: a **calibrated, live win/draw/away-win probability
feed** for football matches, built for prediction-market operators and
sportsbooks pricing in-play markets. Built for the Harbour.Space *Industrial
Machine Learning* course (2026) around the course's core lesson — **business
goal ≠ math problem statement** — and validated end-to-end on real data,
including the live World Cup 2026.

## Overview

A live in-play market is priced continuously as a match unfolds, and every
mispriced minute is money left on the table against sharper bettors. Kairos
outputs a probability vector `P(home), P(draw), P(away)` at every match
minute/event, evaluated with **proper scoring rules (log-loss, Brier) and
calibration (ECE)** rather than accuracy — accuracy can't tell a well-priced
model from a badly-priced one with the same hit rate.

The model is a **Poisson goal-arrival process**: a swap-ready pre-match
strength prior (live de-vigged market odds when available, an Elo rating
otherwise) sets each team's baseline scoring rate; live match state (score,
red cards, real attacking intensity where it exists) modulates it; the
**Skellam distribution** (closed-form difference of two Poissons) turns the
two rates into `P(H/D/A)`; an out-of-fold calibration layer corrects the
model's structural under-pricing of the draw. This reproduces the
architecture used by the industry's own in-play systems (a market-anchored
prior + goal-arrival dynamics), measured piece by piece rather than assumed.

## Repository structure

**Data pipeline** (each cached; safe to re-run)
| Script | Produces |
|---|---|
| `build_dataset.py` | Club (StatsBomb) minute-snapshots → `data/snapshots.csv` |
| `build_odds.py` | Club Pinnacle closing odds → `data/odds_club.csv` |
| `build_dataset_intl.py` | International event data via KickoffAPI → `data/snapshots_intl.csv` |
| `build_dataset_sb_intl.py` | International full event streams via StatsBomb → `data/snapshots_sb_intl.csv` |
| `build_odds_intl.py` | Historical WC2018/22 closing odds → `data/odds_intl.csv` |
| `build_elo.py` | Team Elo history (eloratings.net) → `data/elo_history.csv` |

**Modeling**
| Script | Purpose |
|---|---|
| `train.py` | Club core lesson: M1 (baseline) / M2 (uncalibrated GBM) / M3 (calibrated) |
| `train_market.py` | Club ingredient test: what each feature (market prior, xG) is worth |
| `train_intl.py` | International `GoalProcessModel` — the production architecture |
| `experiment.py` | Shared CV / experiment-running utilities |

**Serving**
| Script | Purpose |
|---|---|
| `live_runner.py` | Fetches a live/finished match, runs the trained model, plots the live trajectory |
| `predict_prematch.py` | Pre-match sheets for upcoming fixtures, live market prior via `market_live.py` |
| `market_live.py` | Live de-vigged 1X2 odds (The Odds API) |

**Other**
- `data/` — cached raw + processed data (StatsBomb, KickoffAPI, football-data.co.uk, Elo, odds)
- `outputs/` — generated figures and metrics from the scripts above
- `Kairos_Pipeline.ipynb` — the full pipeline executed end to end as one notebook (data → EDA → training, both tracks → results/significance → live demo)

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install numpy pandas scikit-learn matplotlib scipy

# club football — core lesson + architecture/ingredient test
.venv/bin/python build_dataset.py
.venv/bin/python build_odds.py
.venv/bin/python train.py
.venv/bin/python train_market.py

# international — the real World Cup 2026 track
.venv/bin/python build_elo.py
.venv/bin/python build_dataset_intl.py
.venv/bin/python build_dataset_sb_intl.py
.venv/bin/python build_odds_intl.py
.venv/bin/python train_intl.py
.venv/bin/python live_runner.py --list
ODDS_API_KEY=... .venv/bin/python live_runner.py <fixture_id>
ODDS_API_KEY=... .venv/bin/python predict_prematch.py
```

## Presentation

- The pitch deck is a React/Vite app in `Build presentation for Opta/` — run it with `pnpm install && pnpm dev`.
