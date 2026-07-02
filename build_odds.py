"""
Kairos — market odds builder (club track).

Downloads free historical closing odds from football-data.co.uk for the exact
two seasons covered by the StatsBomb club dataset (Premier League 2015/16 and
La Liga 2015/16), joins them to the StatsBomb match index by date + home team,
and converts bookmaker prices into a de-vigged market-implied probability
prior — the same "market anchor" that commercial systems (Opta supercomputer,
market makers) use as their strongest pre-match input.

Odds preference order per match: Pinnacle closing (PSCH/PSCD/PSCA — the
sharpest widely-available free price), then Pinnacle (PSH/PSD/PSA), then
Bet365 (B365H/B365D/B365A). De-vig is proportional normalisation: divide each
implied probability by the overround so they sum to 1.

Output: data/odds_club.csv with one row per StatsBomb match_id:
  match_id, date, home, away, book,
  mkt_pH, mkt_pD, mkt_pA           de-vigged market probabilities
  mkt_logit_ha, mkt_logit_d        log(pH/pA) and log(pD/sqrt(pH*pA)) — the
                                   prior features the rate model consumes

Every value is a real, recorded market price; nothing is interpolated.
"""
import io
import json
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FD_BASE = "https://www.football-data.co.uk/mmz4281/1516"

# (football-data file, StatsBomb match index cache, label)
SOURCES = [
    ("E0", "matches_2_27.json", "Premier League 2015/16"),
    ("SP1", "matches_11_27.json", "La Liga 2015/16"),
]

# StatsBomb team name -> football-data.co.uk team name (identity if absent)
NAME_MAP = {
    # Premier League
    "AFC Bournemouth": "Bournemouth",
    "Leicester City": "Leicester",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Norwich City": "Norwich",
    "Stoke City": "Stoke",
    "Swansea City": "Swansea",
    "Tottenham Hotspur": "Tottenham",
    "West Bromwich Albion": "West Brom",
    "West Ham United": "West Ham",
    # La Liga
    "Athletic Club": "Ath Bilbao",
    "Atlético Madrid": "Ath Madrid",
    "Celta Vigo": "Celta",
    "Espanyol": "Espanol",
    "Levante UD": "Levante",
    "Málaga": "Malaga",
    "RC Deportivo La Coruña": "La Coruna",
    "Rayo Vallecano": "Vallecano",
    "Real Betis": "Betis",
    "Real Sociedad": "Sociedad",
    "Sporting Gijón": "Sp Gijon",
}

BOOKS = [("PSC", "pinnacle_closing"), ("PS", "pinnacle"), ("B365", "bet365")]


def fetch_fd(code):
    """Download (and cache) one football-data.co.uk season CSV."""
    cache = os.path.join(DATA, f"fd_{code}_1516.csv")
    if not os.path.exists(cache):
        url = f"{FD_BASE}/{code}.csv"
        with urllib.request.urlopen(url, timeout=60) as r:
            raw = r.read()
        with open(cache, "wb") as f:
            f.write(raw)
    return pd.read_csv(cache)


def devig(oh, od, oa):
    """Proportional de-vig: bookmaker prices -> probabilities summing to 1."""
    inv = np.array([1.0 / oh, 1.0 / od, 1.0 / oa])
    return inv / inv.sum()


def pick_odds(row):
    """Best available 1X2 price for one football-data row."""
    for prefix, label in BOOKS:
        cols = [f"{prefix}H", f"{prefix}D", f"{prefix}A"]
        if all(c in row.index and pd.notna(row[c]) and row[c] > 1.0 for c in cols):
            return row[cols[0]], row[cols[1]], row[cols[2]], label
    return None


def main():
    out_rows = []
    for code, sb_cache, label in SOURCES:
        fd = fetch_fd(code)
        fd["date"] = pd.to_datetime(fd["Date"], dayfirst=True).dt.strftime("%Y-%m-%d")
        fd_key = {(r.date, r.HomeTeam): r for r in fd.itertuples()}

        sb = json.load(open(os.path.join(DATA, sb_cache)))
        matched = missed = 0
        for m in sb:
            home = m["home_team"]["home_team_name"]
            away = m["away_team"]["away_team_name"]
            key = (m["match_date"], NAME_MAP.get(home, home))
            r = fd_key.get(key)
            if r is None:
                missed += 1
                print(f"  [MISS] {label} {m['match_date']} {home} vs {away}")
                continue
            picked = pick_odds(pd.Series(r._asdict()))
            if picked is None:
                missed += 1
                print(f"  [NO ODDS] {label} {m['match_date']} {home}")
                continue
            oh, od, oa, book = picked
            p = devig(oh, od, oa)
            out_rows.append({
                "match_id": m["match_id"],
                "date": m["match_date"],
                "home": home, "away": away, "comp": label, "book": book,
                "mkt_pH": round(p[0], 5), "mkt_pD": round(p[1], 5),
                "mkt_pA": round(p[2], 5),
                # prior features for the goal-process rate model:
                #   logit_ha : home-vs-away strength axis
                #   logit_d  : draw-propensity axis (vs geometric mean of H/A)
                "mkt_logit_ha": round(float(np.log(p[0] / p[2])), 5),
                "mkt_logit_d": round(float(np.log(p[1] / np.sqrt(p[0] * p[2]))), 5),
            })
            matched += 1
        print(f"{label}: matched {matched}, missed {missed}")

    df = pd.DataFrame(out_rows)
    out = os.path.join(DATA, "odds_club.csv")
    df.to_csv(out, index=False)
    print(f"DONE. {len(df)} matches with market odds -> {out}")
    print(df.book.value_counts().to_dict())


if __name__ == "__main__":
    main()
