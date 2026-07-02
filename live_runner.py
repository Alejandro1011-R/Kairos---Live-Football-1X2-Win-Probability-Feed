"""
Kairos — live runner (World Cup 2026, KickoffAPI).

Proves the live pipeline end to end against the CURRENT World Cup:

    KickoffAPI fixture  ->  per-minute match-state snapshots (Kairos schema)
                        ->  trained Kairos model  ->  live P(H/D/A) trajectory

Data source: KickoffAPI (https://kickoffapi.com) — genuine free tier, 100 req/day,
no credit card. It carries WORLD CUP 2026 (league id 1, season 2026) up to date, and
its free plan even exposes expected_goals — so Kairos runs with its FULL feature set
on real 2026 matches. Header auth: `x-api-key`. Base: /api/v1.

Free-plan fields confirmed against a WC2026 match (France 3-0 Sweden):
  * events                 -> goals & red cards WITH minute => goal_diff, red_diff EXACT
  * fixtures/{id}/statistics -> Total Shots, Shots on Goal, Red Cards, expected_goals
                                (final totals for a finished match; live-cumulative
                                 when polled during a match in play)

The model is trained by train.py's calibrated-logistic pipeline on the StatsBomb
snapshots. Regulation time only (0..90'); extra time / shootout is ignored.

Usage:
    .venv/bin/python live_runner.py                 # auto: live match, else latest FT
    .venv/bin/python live_runner.py <fixture_id>
    .venv/bin/python live_runner.py --list          # list WC2026 fixtures + ids
"""
import json
import os
import sys
import urllib.request
import urllib.parse

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from build_dataset_intl import EloBook
from train_intl import GoalProcessModel, load_intl

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "kickoffapi")
OUT = os.path.join(HERE, "outputs")
os.makedirs(CACHE, exist_ok=True)

API = "https://api.kickoffapi.com/api/v1"
API_KEY = os.environ.get("KICKOFF_KEY", "ft_kairos_7b7546bb385fe366dfb0a3f9c27137df1386374d")
LEAGUE_WORLD_CUP = 1
SEASON = 2026
MAX_MIN = 90
LIVE_STATUS = {"1H", "2H", "HT", "ET", "BT", "P", "LIVE", "INT"}
RED_DETAILS = {"Red Card", "Second Yellow card"}


def api_get(path, cache_key=None, **params):
    """GET a KickoffAPI endpoint. Finished-match data is cached (0 req on re-run);
    live data is never cached so each poll is fresh."""
    cache_path = os.path.join(CACHE, f"{cache_key}.json") if cache_key else None
    if cache_path and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "x-api-key": API_KEY,
        "Accept": "application/json",
        "User-Agent": "curl/8.7.1",  # Cloudflare blocks the default urllib UA
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if cache_path:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    return data


def wc_fixtures():
    return api_get("fixtures", None, league=LEAGUE_WORLD_CUP, season=SEASON)["response"]


def pick_fixture(fixtures):
    """A live match if one exists, else the most recently finished one."""
    live = [f for f in fixtures if f.get("statusShort") in LIVE_STATUS]
    if live:
        return sorted(live, key=lambda f: f.get("elapsed") or 0)[-1], True
    done = [f for f in fixtures if f.get("statusShort") in ("FT", "AET", "PEN")]
    return sorted(done, key=lambda f: f.get("date", ""))[-1], False


def build_snapshots(fx, events, elo_home, elo_away, live_minute=None):
    """Convert one fixture into Kairos's per-minute snapshot table (0..cap).
    No shots/xG proxy: every column here is either an exact event timestamp
    or the pre-match Elo prior (constant for the match)."""
    home_id, away_id = fx["homeTeamId"], fx["awayTeamId"]
    cap = min(MAX_MIN, live_minute) if live_minute else MAX_MIN

    hg_at, ag_at, rh_at, ra_at = {}, {}, {}, {}
    for e in events:
        m = e.get("time") or 0
        if m > MAX_MIN:
            continue
        tid = e.get("teamId")
        if e["type"] == "Goal" and e.get("detail") != "Missed Penalty":
            if e.get("detail") == "Own Goal":                 # counts for opponent
                d = ag_at if tid == home_id else hg_at
            else:
                d = hg_at if tid == home_id else ag_at
            d[m] = d.get(m, 0) + 1
        elif e["type"] == "Card" and e.get("detail") in RED_DETAILS:
            d = rh_at if tid == home_id else ra_at
            d[m] = d.get(m, 0) + 1

    def cum(d, m):
        return sum(v for mn, v in d.items() if mn <= m)

    import pandas as pd
    rows = []
    for m in range(0, cap + 1):
        hg, ag = cum(hg_at, m), cum(ag_at, m)
        red_h, red_a = cum(rh_at, m), cum(ra_at, m)
        rows.append({
            "minute": m,
            "time_remaining": MAX_MIN - m,
            "goal_diff": hg - ag,
            "home_goals": hg,
            "away_goals": ag,
            "red_home": red_h,
            "red_away": red_a,
            "red_diff": red_h - red_a,
            "elo_home": elo_home,
            "elo_away": elo_away,
            "elo_diff": elo_home - elo_away,
        })
    return pd.DataFrame(rows)


def train_kairos():
    """Fit the Poisson goal-process model (see train_intl.py) on the full
    national-team dataset — the same mechanism used to train/serve is used
    to evaluate it, so live probabilities and the reported metrics match."""
    df = load_intl()
    print(f"  model: Poisson goal-process, market/Elo prior + recalibration, "
          f"trained on {df.match_id.nunique()} international matches")
    return GoalProcessModel().fit(df)


def main():
    args = sys.argv[1:]
    fixtures = wc_fixtures()

    if args and args[0] == "--list":
        for f in sorted(fixtures, key=lambda z: z.get("date", "")):
            print(f"{f['id']:>8} | {f.get('date','')[:16]} | {f.get('statusShort'):>3} | "
                  f"{(f.get('homeTeam') or {}).get('name')} {f.get('goalsHome')}-"
                  f"{f.get('goalsAway')} {(f.get('awayTeam') or {}).get('name')}")
        return

    if args:
        fid = int(args[0])
        fx = next(f for f in fixtures if f["id"] == fid)
        is_live = fx.get("statusShort") in LIVE_STATUS
    else:
        fx, is_live = pick_fixture(fixtures)
        fid = fx["id"]

    home = (fx.get("homeTeam") or {}).get("name")
    away = (fx.get("awayTeam") or {}).get("name")
    status = fx.get("statusShort")
    live_minute = fx.get("elapsed") if is_live else None
    tag = f"LIVE {live_minute}'" if is_live else f"{status} {fx.get('goalsHome')}-{fx.get('goalsAway')}"
    print(f"Kairos live runner — WC2026 fixture {fid}")
    print(f"Match: {home} vs {away}  ({tag})")

    goalproc = train_kairos()
    elo = EloBook()
    match_date = (fx.get("date") or "")[:10]
    elo_home = elo.pre_match(home, match_date)
    elo_away = elo.pre_match(away, match_date)
    print(f"Pre-match Elo: {home} {elo_home:.0f}  vs  {away} {elo_away:.0f}  "
          f"(diff {elo_home - elo_away:+.0f})")

    # cache only finished matches; live polls stay fresh
    ck = None if is_live else f"ev_{fid}"
    events = api_get(f"fixtures/{fid}/events", ck)["response"]

    snaps = build_snapshots(fx, events, elo_home, elo_away, live_minute)

    # swap-ready strength prior: live de-vigged market odds when a market
    # exists (The Odds API free tier — market_live.py), Elo otherwise
    from market_live import fetch_market_prior
    mkt = fetch_market_prior(home, away)
    if mkt:
        snaps["mkt_pH"], snaps["mkt_pD"], snaps["mkt_pA"] = mkt
    else:
        print("  prior: Elo (no live market odds available)")

    p = goalproc.predict_hda(snaps)
    snaps = snaps.assign(pH=p[:, 0], pD=p[:, 1], pA=p[:, 2])

    goal_min = snaps.index[snaps.goal_diff.diff().fillna(0) != 0].tolist()
    show = sorted(set([0, 15, 30, 45, 60, 75, int(snaps.minute.max())] + goal_min))
    print(f"\n{'min':>4} {'score':>7} {'P(H)':>7} {'P(D)':>7} {'P(A)':>7}   {home} / {away}")
    for m in show:
        r = snaps.loc[m]
        print(f"{m:>4} {int(r.home_goals)}-{int(r.away_goals):<5} "
              f"{r.pH:>7.3f} {r.pD:>7.3f} {r.pA:>7.3f}")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(snaps.minute, snaps.pH, color="#1f77b4", lw=2.5, label=f"P({home} win)")
    ax.plot(snaps.minute, snaps.pD, color="#7f7f7f", lw=2.5, label="P(draw)")
    ax.plot(snaps.minute, snaps.pA, color="#e15759", lw=2.5, label=f"P({away} win)")
    hd = snaps.home_goals.diff().fillna(0)
    ad = snaps.away_goals.diff().fillna(0)
    for m in snaps.index[(hd > 0) | (ad > 0)]:
        r = snaps.loc[m]
        side = home if hd[m] > 0 else away
        ax.axvline(m, color="green", ls=":", alpha=0.6)
        ax.plot(m, 1.04, marker="v", color="green", ms=8, clip_on=False)
        ax.text(m, 1.075, f"{side.split()[0]} {int(r.home_goals)}-{int(r.away_goals)}",
                ha="center", fontsize=8, color="green")
    ax.set_ylim(0, 1.16); ax.set_xlim(0, MAX_MIN)
    ax.set_xlabel("Match minute"); ax.set_ylabel("Probability")
    ax.set_title(f"Kairos live 1X2 — {home} vs {away}  (World Cup 2026 · {tag})")
    ax.legend(loc="center left", fontsize=9)
    fig.tight_layout()
    out = os.path.join(OUT, f"fig_wc2026_{fid}.png")
    fig.savefig(out); plt.close(fig)
    print(f"\nSaved trajectory figure -> {out}")


if __name__ == "__main__":
    main()
