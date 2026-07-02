"""
Kairos — pre-match prediction sheets for upcoming World Cup 2026 fixtures.

Prices the kickoff 1X2 of every not-yet-started WC2026 fixture twice through
the production GoalProcessModel: once with the LIVE de-vigged market prior
(The Odds API via market_live.py — the real swap, not a synthetic test) and
once with the Elo fallback, i.e. exactly the two paths PriorModule serves.

Writes:
  outputs/predictions_wc2026_live.md     summary — every upcoming fixture, both priors
  outputs/prediction_wc2026_<slug>.md    full sheet for the next fixture with a market
                                         (fair odds, scorelines, live what-if states)

Each saved sheet is scoreable after full time with `live_runner.py <fixture_id>`.

Usage:  ODDS_API_KEY=... .venv/bin/python predict_prematch.py
"""
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.stats import poisson

import live_runner
from build_dataset_intl import EloBook
from market_live import fetch_market_prior

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

def state_row(minute, goal_diff, red_diff, elo_home, elo_away, mkt=None,
              home_goals=0, away_goals=0):
    row = {
        "minute": minute, "time_remaining": live_runner.MAX_MIN - minute,
        "goal_diff": goal_diff, "home_goals": home_goals, "away_goals": away_goals,
        "red_diff": red_diff, "red_home": max(red_diff, 0), "red_away": max(-red_diff, 0),
        "elo_home": elo_home, "elo_away": elo_away, "elo_diff": elo_home - elo_away,
    }
    if mkt:
        row["mkt_pH"], row["mkt_pD"], row["mkt_pA"] = mkt
    return row


def predict_states(goalproc, rows):
    return goalproc.predict_hda(pd.DataFrame(rows))


def expected_goals(goalproc, row):
    """Regulation-time expected goals per side from the fitted rate models."""
    df = goalproc._ensure_cols(pd.DataFrame([row]))
    X = goalproc._design(df, goalproc.prior)
    lam_h = float(goalproc.rates[0].predict(X)[0]) * live_runner.MAX_MIN
    lam_a = float(goalproc.rates[1].predict(X)[0]) * live_runner.MAX_MIN
    return lam_h, lam_a


def top_scorelines(lam_h, lam_a, k=5):
    grid = [((h, a), poisson.pmf(h, lam_h) * poisson.pmf(a, lam_a))
            for h in range(8) for a in range(8)]
    return sorted(grid, key=lambda t: -t[1])[:k]


def pct(p):
    return "/".join(f"{x*100:.0f}%" for x in p)


def detailed_sheet(goalproc, fx, elo_home, elo_away, mkt, now_utc):
    home = fx["homeTeam"]["name"]; away = fx["awayTeam"]["name"]
    ko = (fx.get("date") or "")[:16].replace("T", " ")
    k0 = state_row(0, 0, 0, elo_home, elo_away, mkt)
    p_mkt, = predict_states(goalproc, [k0])
    p_elo, = predict_states(goalproc, [state_row(0, 0, 0, elo_home, elo_away)])
    lam_h, lam_a = expected_goals(goalproc, k0)

    whatif = [
        ("Kickoff (0')", state_row(0, 0, 0, elo_home, elo_away, mkt)),
        (f"{home} lead 1-0 at 30'", state_row(30, 1, 0, elo_home, elo_away, mkt, 1, 0)),
        (f"{away} lead 0-1 at 30'", state_row(30, -1, 0, elo_home, elo_away, mkt, 0, 1)),
        ("Still 0-0 at 60'", state_row(60, 0, 0, elo_home, elo_away, mkt)),
        (f"{home} lead 1-0 at 75'", state_row(75, 1, 0, elo_home, elo_away, mkt, 1, 0)),
        (f"{away} red card at 55', 0-0", state_row(55, 0, 1, elo_home, elo_away, mkt)),
    ]
    pw = predict_states(goalproc, [r for _, r in whatif])

    md = [
        f"# Kairos pre-match prediction — {home} vs {away}",
        f"### FIFA World Cup 2026 · fixture {fx['id']} · kickoff {ko} UTC · "
        f"generated {now_utc:%Y-%m-%d %H:%M} UTC (pre-kickoff)",
        "",
        "Model: production `GoalProcessModel` (Poisson goal process + swap-ready prior + OOF recalibration),",
        f"trained on all 636 international matches. **Out-of-sample** — WC2026 is not in the training data.",
        "Strength prior source: **live de-vigged market odds (The Odds API)** — the real",
        "market swap, with the Elo fallback shown for comparison.",
        f"Pre-match Elo: **{home} {elo_home:.0f}** vs **{away} {elo_away:.0f}** "
        f"(gap **{elo_home - elo_away:+.0f}**). "
        f"Market prior (de-vig): **{pct(mkt)}**.",
        "",
        "## Kickoff 1X2 (regulation time — for a knockout, a draw = goes to extra time)",
        "",
        "| Outcome | Market prior | Fair odds | Elo fallback |",
        "|---|---|---|---|",
        f"| **{home} win (90')** | **{p_mkt[0]*100:.1f}%** | {1/p_mkt[0]:.2f} | {p_elo[0]*100:.1f}% |",
        f"| Draw (90') | {p_mkt[1]*100:.1f}% | {1/p_mkt[1]:.2f} | {p_elo[1]*100:.1f}% |",
        f"| {away} win (90') | {p_mkt[2]*100:.1f}% | {1/p_mkt[2]:.2f} | {p_elo[2]*100:.1f}% |",
        "",
        f"Expected regulation goals (market prior): **{home} {lam_h:.2f} — {lam_a:.2f} {away}**.",
        "",
        "## Most likely regulation scorelines (independent-Poisson, pre-recalibration)",
        "",
        "| Score | Probability |",
        "|---|---|",
    ]
    md += [f"| {h}-{a} | {p*100:.1f}% |" for (h, a), p in top_scorelines(lam_h, lam_a)]
    md += [
        "",
        "## How the price moves — live what-if states (market prior)",
        "",
        f"| State | P({home}) | P(draw) | P({away}) |",
        "|---|---|---|---|",
    ]
    md += [f"| {label} | {p[0]*100:.1f}% | {p[1]*100:.1f}% | {p[2]*100:.1f}% |"
           for (label, _), p in zip(whatif, pw)]
    md += [
        "",
        "---",
        "*Every number above is produced by the same pipeline that trains and serves the",
        "model (`train_intl.py` / `live_runner.py` / `market_live.py`); nothing is",
        f"hand-adjusted. To score this prediction after the match: "
        f"`python live_runner.py {fx['id']}`.*",
    ]
    slug = f"{home}_{away}".lower().replace(" & ", "_").replace(" ", "_")
    path = os.path.join(OUT, f"prediction_wc2026_{slug}.md")
    with open(path, "w") as f:
        f.write("\n".join(md) + "\n")
    return path


def main():
    now_utc = datetime.now(timezone.utc)
    fixtures = live_runner.wc_fixtures()
    upcoming = sorted([f for f in fixtures if f.get("statusShort") == "NS"],
                      key=lambda f: f.get("date", ""))
    if not upcoming:
        print("No upcoming WC2026 fixtures — tournament over?")
        return

    goalproc = live_runner.train_kairos()
    elo = EloBook()

    lines = [
        "# Kairos live feed — upcoming World Cup 2026 fixtures",
        f"### Generated {now_utc:%Y-%m-%d %H:%M} UTC · production model "
        "(636 training matches, out-of-sample for WC2026)",
        "",
        "**The market-anchored prior, running live**: for every upcoming fixture with a betting",
        "market, the strength prior is the de-vigged 1X2 consensus fetched from The Odds API",
        "(free tier); the Elo-prior column shows what the feed would emit without a market —",
        "the fallback path for uncovered competitions. All probabilities are regulation-time",
        "(a draw in a knockout = extra time).",
        "",
        "| Kickoff (UTC) | Match | Elo gap | Market prior (de-vig) | **Kairos P(H/D/A) — market prior** | Kairos P(H/D/A) — Elo fallback |",
        "|---|---|---|---|---|---|",
    ]

    n_mkt = 0
    sheet = None
    for fx in upcoming:
        home = fx["homeTeam"]["name"]; away = fx["awayTeam"]["name"]
        date = (fx.get("date") or "")[:10]
        elo_h, elo_a = elo.pre_match(home, date), elo.pre_match(away, date)
        mkt = fetch_market_prior(home, away)
        p_elo, = predict_states(goalproc, [state_row(0, 0, 0, elo_h, elo_a)])
        if mkt:
            n_mkt += 1
            p_mkt, = predict_states(goalproc, [state_row(0, 0, 0, elo_h, elo_a, mkt)])
            lines.append(f"| {(fx.get('date') or '')[:16].replace('T',' ')} | {home} vs {away} "
                         f"| {elo_h - elo_a:+.0f} | {pct(mkt)} | **{pct(p_mkt)}** | {pct(p_elo)} |")
            if sheet is None:
                sheet = detailed_sheet(goalproc, fx, elo_h, elo_a, mkt, now_utc)
        else:
            lines.append(f"| {(fx.get('date') or '')[:16].replace('T',' ')} | {home} vs {away} "
                         f"| {elo_h - elo_a:+.0f} | — (no market) | — | {pct(p_elo)} |")
        print(f"{home} vs {away}: market={'yes' if mkt else 'no'}")

    lines += [
        "",
        f"*{n_mkt}/{len(upcoming)} fixtures priced with a live market prior; the rest fall "
        "back to Elo (logged, never silent).*",
        "*Same `GoalProcessModel` that produced every number in the deck; market data: "
        "The Odds API, sharpest available book per fixture.*",
    ]

    path = os.path.join(OUT, "predictions_wc2026_live.md")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSaved {path}")
    if sheet:
        print(f"Saved {sheet}")


if __name__ == "__main__":
    main()
