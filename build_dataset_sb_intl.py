"""
Kairos — international dataset expansion from StatsBomb open data.

Adds every men's senior international tournament available in StatsBomb's free
open-data release to the national-team track: full event streams, so unlike
the KickoffAPI feed these matches carry REAL per-minute shots and xG (per-shot
StatsBomb xG, the same quality of signal Opta sells) in addition to exact
goal/red-card timestamps.

Tournaments (≈314 matches): WC2018, WC2022, Euro2020, Euro2024,
Copa América 2024, AFCON 2023.

Three of these (WC2022, Euro2024, Copa América 2024) overlap the KickoffAPI
dataset — the combined loader in train_intl.py prefers the StatsBomb version
of those matches (richer features) and drops the KickoffAPI copies, so no
match is ever counted twice.

Elo prior: same as the rest of the intl track — eloratings.net as-of ratings
via EloBook (build_elo.py). StatsBomb team names are mapped to the KickoffAPI
naming that elo_history.csv is keyed by; the build FAILS LOUDLY if any team
can't be resolved (no silent 1500-default leaks into the dataset).

Output: data/snapshots_sb_intl.csv — same schema as snapshots_intl.csv plus
shots/xG columns and home/away/date metadata.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

import build_dataset as B                      # StatsBomb fetch + match_to_rows
from build_dataset_intl import EloBook

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# (competition_id, season_id, label) — men's senior internationals with events
COMPETITIONS = [
    (43, 3, "FIFA World Cup 2018"),
    (43, 106, "FIFA World Cup 2022"),
    (55, 43, "UEFA Euro 2020"),
    (55, 282, "UEFA Euro 2024"),
    (223, 282, "Copa America 2024"),
    (1267, 107, "African Cup of Nations 2023"),
]

# StatsBomb team name -> elo_history.csv (KickoffAPI) team name.
# Only names that differ; identity otherwise. Verified against both sources.
NAME_MAP = {
    "United States": "USA",
    "Turkey": "Türkiye",
    "Czech Republic": "Czechia",
    "Côte d'Ivoire": "Ivory Coast",
    "DR Congo": "Congo DR",
    "North Macedonia": "FYR Macedonia",
}


def list_matches():
    matches = []
    for cid, sid, label in COMPETITIONS:
        idx = B._get(f"{B.BASE}/matches/{cid}/{sid}.json",
                     os.path.join(DATA, f"matches_{cid}_{sid}.json"))
        for m in idx:
            matches.append({
                "match_id": m["match_id"],
                "comp": label,
                "date": m["match_date"],
                "home": m["home_team"]["home_team_name"],
                "away": m["away_team"]["away_team_name"],
                "home_score": m["home_score"],
                "away_score": m["away_score"],
            })
        print(f"{label}: {len(idx)} matches")
    return matches


def main():
    matches = list_matches()
    print(f"Total: {len(matches)} matches")

    elo = EloBook()
    unresolved = set()
    for m in matches:
        for side in ("home", "away"):
            name = NAME_MAP.get(m[side], m[side])
            if name not in elo.history:
                unresolved.add(m[side])
            m[f"elo_{side}"] = elo.pre_match(name, m["date"])
    if unresolved:
        sys.exit(f"FATAL: no Elo history for teams: {sorted(unresolved)} — "
                 f"extend NAME_MAP/build_elo.py instead of defaulting to 1500.")

    def dl(meta):
        try:
            return meta, B.fetch_events(meta["match_id"])
        except Exception:
            return meta, None

    def regulation_score(meta, events):
        """Goals inside periods 1-2 only. The 1X2 label must be the
        REGULATION-TIME result (same convention as the KickoffAPI track) —
        StatsBomb's official home_score/away_score includes extra time, which
        would silently flip the label of every match decided in ET (9 of the
        314 matches here, e.g. the Copa América 2024 final)."""
        hg = ag = 0
        for ev in events:
            t = ev.get("type", {}).get("name")
            team = ev.get("team", {}).get("name")
            scored = (t == "Shot" and
                      ev.get("shot", {}).get("outcome", {}).get("name") == "Goal") \
                     or t == "Own Goal For"
            if scored:
                if team == meta["home"]:
                    hg += 1
                elif team == meta["away"]:
                    ag += 1
        return hg, ag

    all_rows, ok, bad = [], 0, 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = [ex.submit(dl, m) for m in matches]
        for i, fut in enumerate(as_completed(futs), 1):
            meta, events = fut.result()
            if not events:
                bad += 1
                continue
            # regulation time only: drop extra-time periods entirely (goals,
            # cards and shots in ET belong to neither the snapshots nor the label)
            events = [ev for ev in events if ev.get("period", 1) <= 2]
            meta["home_score"], meta["away_score"] = regulation_score(meta, events)
            rows = B.match_to_rows(meta, events)
            for r in rows:
                r["date"] = meta["date"]
                r["home"] = meta["home"]
                r["away"] = meta["away"]
                r["elo_home"] = meta["elo_home"]
                r["elo_away"] = meta["elo_away"]
                r["elo_diff"] = meta["elo_home"] - meta["elo_away"]
            all_rows.extend(rows)
            ok += 1
            if i % 50 == 0:
                print(f"  {i}/{len(matches)} (ok={ok}, bad={bad})", flush=True)

    df = pd.DataFrame(all_rows)
    out = os.path.join(DATA, "snapshots_sb_intl.csv")
    df.to_csv(out, index=False)
    print(f"DONE. matches ok={ok} bad={bad} | rows={len(df)} -> {out}")
    kick = df[df.minute == 0].result.value_counts(normalize=True).round(3).to_dict()
    print("Kickoff base rates:", kick)


if __name__ == "__main__":
    main()
