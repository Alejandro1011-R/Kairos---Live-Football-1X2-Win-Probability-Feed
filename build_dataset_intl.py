"""
Kairos — INTERNATIONAL dataset builder (national-team model for World Cup 2026).

Source: KickoffAPI (same provider as the live runner, so training and serving share
the exact same feature construction). We take the LATEST played edition of every major
senior international tournament — no friendlies (sparse xG + a 2023 data gap).

Per finished match:
  * events -> goals & red cards WITH exact minute => exact per-minute goal_diff,
              home/away goals, red_home/red_away. No proxies: every value in this
              dataset is a real, timestamped observation.
  * pre-match Elo ratings (data/elo_history.csv, built by build_elo.py from
    eloratings.net) -> elo_home / elo_away, the team-strength prior that both the
    Robberechts et al. (KDD 2021) and Clegg et al. (2026) in-play win-probability
    papers identify as the dominant driver of accuracy. This REPLACES the old
    linearly-ramped shots/xG proxy, which is dropped entirely (KickoffAPI's free
    plan only exposes match-FINAL shot/xG totals, never real per-minute values, so
    ramping them was never honest per-minute data).

1X2 label = REGULATION result (goal_diff at minute 90) — extra time / shootout do not
count for the 1X2 market.

Output: data/snapshots_intl.csv  (also .parquet if pyarrow is available)
"""
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "kickoffapi")
os.makedirs(CACHE, exist_ok=True)

API = "https://api.kickoffapi.com/api/v1"
API_KEY = os.environ.get("KICKOFF_KEY", "ft_kairos_7b7546bb385fe366dfb0a3f9c27137df1386374d")
MAX_MIN = 90
RED_DETAILS = {"Red Card", "Second Yellow card"}

# (league_id, season, label) — latest PLAYED edition of each major senior tournament
COMPETITIONS = [
    (1,  2022, "FIFA World Cup 2022"),
    (4,  2024, "UEFA Euro 2024"),
    (9,  2024, "Copa America 2024"),
    (6,  2025, "Africa Cup of Nations 2025"),
    (7,  2023, "AFC Asian Cup 2023"),
    (22, 2025, "CONCACAF Gold Cup 2025"),
    (5,  2024, "UEFA Nations League 2024"),
]


def api_get(path, cache_key=None, **params):
    """GET with caching, browser UA (Cloudflare), and retry/backoff on 429/5xx."""
    cache_path = os.path.join(CACHE, f"{cache_key}.json") if cache_key else None
    if cache_path and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    url = f"{API}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "x-api-key": API_KEY, "Accept": "application/json", "User-Agent": "curl/8.7.1",
    })
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
                remaining = r.headers.get("x-ratelimit-remaining")
            if remaining is not None and int(remaining) < 100:
                time.sleep(2)                       # stay clear of the window limit
            if cache_path:
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            raise


class EloBook:
    """As-of lookup: a team's Elo rating in effect just before a given match date,
    i.e. its rating-after from its most recent PRIOR match (built by build_elo.py
    from eloratings.net's own per-team match/rating history)."""

    DEFAULT = 1500.0  # eloratings.net's own baseline for a team with no history yet

    def __init__(self, path=None):
        path = path or os.path.join(DATA, "elo_history.csv")
        self.history = {}  # name -> sorted list of (date, elo_after)
        if not os.path.exists(path):
            return
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                self.history.setdefault(row["name"], []).append(
                    (row["date"], float(row["elo_after"])))
        for name in self.history:
            self.history[name].sort()

    def pre_match(self, name, date):
        """Rating in effect strictly before `date` (YYYY-MM-DD)."""
        rows = self.history.get(name)
        if not rows:
            return self.DEFAULT
        rating = self.DEFAULT
        for d, elo in rows:
            if d >= date:
                break
            rating = elo
        return rating


def match_to_rows(fx, events, elo, comp):
    home_id, away_id = fx["homeTeamId"], fx["awayTeamId"]
    hg_at, ag_at, rh_at, ra_at = {}, {}, {}, {}
    for e in events:
        m = e.get("time") or 0
        if m > MAX_MIN:
            continue
        tid = e.get("teamId")
        if e["type"] == "Goal" and e.get("detail") != "Missed Penalty":
            d = (ag_at if tid == home_id else hg_at) if e.get("detail") == "Own Goal" \
                else (hg_at if tid == home_id else ag_at)
            d[m] = d.get(m, 0) + 1
        elif e["type"] == "Card" and e.get("detail") in RED_DETAILS:
            d = rh_at if tid == home_id else ra_at
            d[m] = d.get(m, 0) + 1

    def cum(d, m):
        return sum(v for mn, v in d.items() if mn <= m)

    fhg, fag = cum(hg_at, MAX_MIN), cum(ag_at, MAX_MIN)
    result = "H" if fhg > fag else ("A" if fag > fhg else "D")   # regulation 1X2

    date = fx["date"][:10]
    elo_home = elo.pre_match(fx["homeTeam"]["name"], date)
    elo_away = elo.pre_match(fx["awayTeam"]["name"], date)

    rows = []
    for m in range(0, MAX_MIN + 1):
        hg, ag = cum(hg_at, m), cum(ag_at, m)
        rows.append({
            "match_id": fx["id"], "comp": comp, "minute": m,
            "date": date, "home": fx["homeTeam"]["name"], "away": fx["awayTeam"]["name"],
            "time_remaining": MAX_MIN - m, "goal_diff": hg - ag,
            "home_goals": hg, "away_goals": ag,
            "red_home": cum(rh_at, m), "red_away": cum(ra_at, m),
            "elo_home": elo_home, "elo_away": elo_away,
            "elo_diff": elo_home - elo_away, "result": result,
        })
    return rows


def process(fx, comp, elo):
    fid = fx["id"]
    events = api_get(f"fixtures/{fid}/events", f"ev_{fid}")["response"]
    return match_to_rows(fx, events, elo, comp)


def main():
    elo = EloBook()
    fixtures = []
    for lid, season, label in COMPETITIONS:
        resp = api_get("fixtures", f"fx_{lid}_{season}", league=lid, season=season)["response"]
        done = [f for f in resp if f.get("statusShort") in ("FT", "AET", "PEN")]
        print(f"{label}: {len(done)} finished matches", flush=True)
        fixtures += [(f, label) for f in done]

    print(f"Total finished matches: {len(fixtures)} (~{len(fixtures)} event requests — "
          f"no /statistics fetch needed anymore)", flush=True)
    all_rows, ok, bad = [], 0, 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(process, fx, comp, elo): fx["id"] for fx, comp in fixtures}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                all_rows.extend(fut.result())
                ok += 1
            except Exception as e:
                bad += 1
                if bad <= 5:
                    print(f"  bad {futs[fut]}: {e}", flush=True)
            if i % 50 == 0:
                print(f"  {i}/{len(fixtures)} (ok={ok}, bad={bad})", flush=True)

    import pandas as pd
    df = pd.DataFrame(all_rows)
    # ThreadPoolExecutor + as_completed() appends matches in network-completion
    # order, which is non-deterministic across runs. train.py's match-level
    # split shuffles df.match_id.unique() with a fixed seed, but relies on
    # match_id's *first-occurrence order* in the dataframe being stable — so
    # this row order has to be pinned, or the resulting train/test split
    # (and every downstream metric) silently changes on every re-run.
    df = df.sort_values(["match_id", "minute"]).reset_index(drop=True)
    out = os.path.join(DATA, "snapshots_intl.parquet")
    try:
        df.to_parquet(out, index=False)
    except Exception:
        out = os.path.join(DATA, "snapshots_intl.csv")
        df.to_csv(out, index=False)
    print(f"DONE. matches ok={ok} bad={bad} | rows={len(df)} | saved -> {out}", flush=True)
    kick = df[df.minute == 0]["result"].value_counts(normalize=True).round(3).to_dict()
    print("Kickoff base rates (H/D/A):", kick, flush=True)


if __name__ == "__main__":
    main()
