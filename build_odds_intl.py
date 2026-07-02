"""
Kairos — market odds builder (international track).

Downloads football-data.co.uk's free World Cup workbook (WorldCup2026.xlsx —
one sheet per tournament, 1X2 closing odds per match) and joins the WC2018 and
WC2022 sheets to the StatsBomb international match index by date + teams.
That backfills a real historical market prior for 128 of the 636 training
matches — the two tournaments in our dataset for which free closing odds exist.
(The other intl tournaments — Euro, Copa América, AFCON, Nations League, Asian
Cup, Gold Cup — have no free odds archive; those matches keep the Elo prior,
which is exactly the mixed regime PriorModule was built for.)

Odds preference per match, sharpest first: Pinnacle (WC2018), Betfair Exchange,
bet365, then the market average. De-vig is proportional normalisation, same as
the club track (build_odds.py).

Output: data/odds_intl.csv with one row per matched StatsBomb match_id:
  match_id, date, home, away, comp, book, mkt_pH, mkt_pD, mkt_pA

Every value is a real, recorded market price; nothing is interpolated.
"""
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FD_URL = "https://www.football-data.co.uk/WorldCup2026.xlsx"
CACHE = os.path.join(DATA, "fd_worldcup.xlsx")

SHEETS = {"WorldCup2018": "FIFA World Cup 2018",
          "WorldCup2022": "FIFA World Cup 2022"}

# StatsBomb team name -> football-data.co.uk team name (identity if absent)
NAME_MAP = {"United States": "USA"}

# 1X2 column prefixes, sharpest book first; ("H-Avg", ...) is the market average
BOOK_COLS = [
    (("Pinny-H", "Pinny-D", "Pinny-A"), "pinnacle"),
    (("Betfair_Exch-H", "Betfair_Exch-D", "Betfair_Exch-A"), "betfair_exchange"),
    (("bet365-H", "bet365-D", "bet365-A"), "bet365"),
    (("H-Avg", "D-Avg", "A-Avg"), "market_average"),
]


def fetch_workbook():
    if not os.path.exists(CACHE):
        req = urllib.request.Request(FD_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        with open(CACHE, "wb") as f:
            f.write(raw)
    return pd.ExcelFile(CACHE)


def pick_odds(row):
    for cols, label in BOOK_COLS:
        if all(c in row.index and pd.notna(row[c]) and row[c] > 1.0 for c in cols):
            return float(row[cols[0]]), float(row[cols[1]]), float(row[cols[2]]), label
    return None


def devig(oh, od, oa):
    inv = np.array([1.0 / oh, 1.0 / od, 1.0 / oa])
    return inv / inv.sum()


def main():
    xl = fetch_workbook()
    fd_key = {}
    for sheet in SHEETS:
        d = xl.parse(sheet)
        d["date"] = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")
        # keep rows as Series so odds columns keep their real names
        # (itertuples would mangle 'bet365-H' etc. into positional fields)
        for _, row in d.iterrows():
            fd_key[(row["date"], row["Home"], row["Away"])] = row

    sb = (pd.read_csv(os.path.join(DATA, "snapshots_sb_intl.csv"))
          .drop_duplicates("match_id"))
    sb = sb[sb.comp.isin(SHEETS.values())]

    out_rows, missed = [], 0
    for m in sb.itertuples():
        key = (m.date, NAME_MAP.get(m.home, m.home), NAME_MAP.get(m.away, m.away))
        r = fd_key.get(key)
        picked = pick_odds(r) if r is not None else None
        if picked is None:
            missed += 1
            print(f"  [MISS] {m.comp} {m.date} {m.home} vs {m.away}")
            continue
        oh, od, oa, book = picked
        p = devig(oh, od, oa)
        out_rows.append({
            "match_id": m.match_id, "date": m.date,
            "home": m.home, "away": m.away, "comp": m.comp, "book": book,
            "mkt_pH": round(p[0], 5), "mkt_pD": round(p[1], 5),
            "mkt_pA": round(p[2], 5),
        })

    df = pd.DataFrame(out_rows)
    out = os.path.join(DATA, "odds_intl.csv")
    df.to_csv(out, index=False)
    print(f"DONE. {len(df)}/{len(sb)} World Cup matches with market odds -> {out} "
          f"({missed} missed)")
    print(df.book.value_counts().to_dict())


if __name__ == "__main__":
    main()
