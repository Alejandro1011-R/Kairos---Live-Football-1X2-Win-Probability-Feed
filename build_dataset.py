"""
Kairos — dataset builder.

Pulls StatsBomb open event data for selected competitions and builds a
minute-by-minute "match state -> final result" table for live 1X2
(home win / draw / away win) win-probability modelling.

All raw JSON is cached under data/ so re-runs are fast.
"""
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
EVDIR = os.path.join(DATA, "events")
os.makedirs(EVDIR, exist_ok=True)

# (competition_id, season_id, label) — men's top leagues, full 2015/16 seasons
COMPETITIONS = [
    (2, 27, "Premier League 2015/16"),
    (11, 27, "La Liga 2015/16"),
]
MAX_MIN = 90  # snapshot elapsed minutes 0..90


def _get(url, cache_path, timeout=60):
    if cache_path and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                data = json.load(r)
            if cache_path:
                with open(cache_path, "w") as f:
                    json.dump(data, f)
            return data
        except Exception as e:
            if attempt == 2:
                raise
    return None


def list_matches():
    matches = []
    for cid, sid, name in COMPETITIONS:
        idx = _get(f"{BASE}/matches/{cid}/{sid}.json",
                   os.path.join(DATA, f"matches_{cid}_{sid}.json"))
        for m in idx:
            matches.append({
                "match_id": m["match_id"],
                "comp": name,
                "home": m["home_team"]["home_team_name"],
                "away": m["away_team"]["away_team_name"],
                "home_score": m["home_score"],
                "away_score": m["away_score"],
            })
    return matches


def fetch_events(match_id):
    return _get(f"{BASE}/events/{match_id}.json",
                os.path.join(EVDIR, f"{match_id}.json"))


def _card_red(card_name):
    return card_name in ("Red Card", "Second Yellow")


def match_to_rows(meta, events):
    home, away = meta["home"], meta["away"]
    # per-minute deltas
    g = {home: {}, away: {}}          # goals
    s = {home: {}, away: {}}          # shots (count)
    xg = {home: {}, away: {}}         # cumulative xG
    rc = {home: {}, away: {}}         # red cards

    def add(d, team, minute, val):
        if team not in (home, away):
            return
        d[team][minute] = d[team].get(minute, 0) + val

    for ev in events:
        t = ev.get("type", {}).get("name")
        team = ev.get("team", {}).get("name")
        minute = ev.get("minute", 0)
        if t == "Shot":
            shot = ev.get("shot", {})
            add(s, team, minute, 1)
            add(xg, team, minute, float(shot.get("statsbomb_xg", 0.0) or 0.0))
            if shot.get("outcome", {}).get("name") == "Goal":
                add(g, team, minute, 1)
        elif t == "Own Goal For":
            add(g, team, minute, 1)
        elif t == "Bad Behaviour":
            if _card_red(ev.get("bad_behaviour", {}).get("card", {}).get("name", "")):
                add(rc, team, minute, 1)
        elif t == "Foul Committed":
            if _card_red(ev.get("foul_committed", {}).get("card", {}).get("name", "")):
                add(rc, team, minute, 1)

    # final result label from official score
    hs, as_ = meta["home_score"], meta["away_score"]
    result = "H" if hs > as_ else ("A" if as_ > hs else "D")

    def cum_at(d, team, m):
        return sum(v for mn, v in d[team].items() if mn < m)

    rows = []
    for m in range(0, MAX_MIN + 1):
        hg = cum_at(g, home, m); ag = cum_at(g, away, m)
        rows.append({
            "match_id": meta["match_id"],
            "comp": meta["comp"],
            "minute": m,
            "time_remaining": MAX_MIN - m,
            "goal_diff": hg - ag,
            "home_goals": hg,
            "away_goals": ag,
            "red_home": cum_at(rc, home, m),
            "red_away": cum_at(rc, away, m),
            "shots_home": cum_at(s, home, m),
            "shots_away": cum_at(s, away, m),
            "xg_home": round(cum_at(xg, home, m), 4),
            "xg_away": round(cum_at(xg, away, m), 4),
            "xg_diff": round(cum_at(xg, home, m) - cum_at(xg, away, m), 4),
            "result": result,
        })
    return rows


def main(limit=None):
    matches = list_matches()
    if limit:
        matches = matches[:limit]
    print(f"Matches to process: {len(matches)}", flush=True)

    # download concurrently (cached)
    def dl(meta):
        try:
            return meta, fetch_events(meta["match_id"])
        except Exception as e:
            return meta, None

    all_rows = []
    ok = bad = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(dl, m) for m in matches]
        for i, fut in enumerate(as_completed(futs), 1):
            meta, events = fut.result()
            if not events:
                bad += 1
                continue
            try:
                all_rows.extend(match_to_rows(meta, events))
                ok += 1
            except Exception as e:
                bad += 1
            if i % 50 == 0:
                print(f"  {i}/{len(matches)} processed (ok={ok}, bad={bad})", flush=True)

    import pandas as pd
    df = pd.DataFrame(all_rows)
    out = os.path.join(DATA, "snapshots.parquet")
    try:
        df.to_parquet(out, index=False)
    except Exception:
        out = os.path.join(DATA, "snapshots.csv")
        df.to_csv(out, index=False)
    print(f"DONE. matches ok={ok} bad={bad} | rows={len(df)} | saved -> {out}", flush=True)
    # quick label balance at kickoff
    kick = df[df.minute == 0]["result"].value_counts(normalize=True).round(3).to_dict()
    print("Kickoff base rates (H/D/A):", kick, flush=True)


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(lim)
