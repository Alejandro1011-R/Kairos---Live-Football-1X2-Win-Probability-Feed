"""
Kairos — market odds builder, second wave (scraped).

Backfills a market-derived pre-match prior for the 6 international competitions
that have no free structured odds archive (UEFA Euro 2020/2024, Copa América
2024, Africa Cup of Nations 2023/2025, AFC Asian Cup 2023, CONCACAF Gold Cup
2025, UEFA Nations League 2024) — the ~508 matches that otherwise train on the
Elo prior. Source: the "best odds" 1X2 columns already published on each
match's row on betexplorer.com's public results-listing pages (no per-match
page visit needed — date, teams, score and 1X2 odds are all in one row).

*** Personal / academic research use only — read this before reusing. ***
betexplorer.com's Terms of Service (Art. 2.11) explicitly prohibit scraping
and automated requests ("You may not use our content ... by embedding,
aggregating, scraping or recreating it without our express consent" / "You
must not burden our server ... with automated requests"). This script exists
because of an explicit, informed decision made in the project conversation
record to proceed anyway for personal/academic use — it is not this
project's default recommendation. The ToS-compliant path (documented in
RESULTS.md) is a paid The-Odds-API plan, which already covers 5 of these 6
competitions and is already integrated via market_live.py. Do not
redistribute data/odds_intl_scraped.csv, do not raise the request rate below,
and do not use this for anything commercial.

Output: data/odds_intl_scraped.csv, same schema as odds_intl.csv:
  match_id, date, home, away, comp, book, mkt_pH, mkt_pD, mkt_pA
"""
import datetime as dt
import os
import re
import sys
import time
import unicodedata
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE_DIR = os.path.join(DATA, "betexplorer_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REQUEST_DELAY_S = 1.8  # politeness delay between requests, even though scraping
                        # itself is against ToS — do not lower this.

# comp label (must match train_intl.load_intl()'s `comp` column) -> betexplorer path
TOURNAMENTS = {
    "UEFA Euro 2020": "football/europe/euro-2020/",
    "UEFA Euro 2024": "football/europe/euro-2024/",
    "Copa America 2024": "football/south-america/copa-america/",
    "African Cup of Nations 2023": "football/africa/africa-cup-of-nations-2023/",
    "Africa Cup of Nations 2025": "football/africa/africa-cup-of-nations-2025/",
    "AFC Asian Cup 2023": "football/asia/asian-cup-2023/",
    "CONCACAF Gold Cup 2025": "football/north-central-america/gold-cup/",
    "UEFA Nations League 2024": "football/europe/uefa-nations-league-2024-2025/",
}

# Aliases applied AFTER accent-stripping/lowercasing/de-punctuating, so accented
# and unaccented spellings of the same alias key are handled uniformly (e.g.
# "Côte d'Ivoire" and "Cote d'Ivoire" both normalize to "cotedivoire" before
# this lookup runs). Keys/values are normalized (lowercase, alnum-only) forms.
ALIASES = {
    "usa": "unitedstates",
    "turkiye": "turkey",
    "fyrmacedonia": "northmacedonia",
    "repofireland": "ireland",
    "republicofireland": "ireland",
    "cotedivoire": "ivorycoast",
    "congodr": "drcongo",
    "bosniaherzegovina": "bosniaandherzegovina",
    "koreidrepublic": "southkorea",
    "korearepublic": "southkorea",
    "czechia": "czechrepublic",
    "capeverdeislands": "capeverde",
    "stkittsandnevis": "saintkittsandnevis",
}


def _get(url, cache_key):
    """Cached, rate-limited GET. Idempotent — re-runs never re-hit the server
    for a URL already on disk."""
    cache_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    time.sleep(REQUEST_DELAY_S)
    return html


def normalize(name):
    if not isinstance(name, str):
        return ""
    name = name.replace("&", " and ")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    return ALIASES.get(key, key)


STAGE_RE = re.compile(r'stage=([A-Za-z0-9_-]+)"[^>]*class="list-tabs__item__in')

# Row parsing is done in two steps — first split the page into individual
# <tr> chunks with a plain string split (zero backtracking risk), then run a
# small, bounded regex on each chunk (a few KB at most). A single combined
# regex spanning the whole page with re.S caused catastrophic backtracking
# (multi-minute hangs) on a handful of pages with irregular markup.
ANCHOR_RE = re.compile(
    r'<a data-test="\d+" href="/football/[a-z0-9-]+/[a-z0-9-]+/[a-z0-9-]+/([A-Za-z0-9]{6,})/"'
    r'\s*class="in-match"><span>(?:<strong>)?([^<]+?)(?:</strong>)?</span>\s*-\s*'
    r'<span>(?:<strong>)?([^<]+?)(?:</strong>)?</span></a>'
)
ODDS_RE = re.compile(r'data-odd="([0-9]+\.[0-9]+)"')
DATE_RE = re.compile(r'<td class="h-text-right h-text-no-wrap">(\d{2}\.\d{2}\.\d{4})</td>')


def parse_stage_ids(html):
    return sorted(set(STAGE_RE.findall(html)))


def parse_results_rows(html):
    rows = []
    for chunk in html.split("<tr>")[1:]:
        chunk = chunk.split("</tr>", 1)[0]
        if "in-match" not in chunk or len(chunk) > 6000:
            continue
        am = ANCHOR_RE.search(chunk)
        dm = DATE_RE.search(chunk)
        odds = ODDS_RE.findall(chunk)
        if not (am and dm and len(odds) >= 3):
            continue
        match_id, home, away = am.groups()
        oh, od, oa = (float(x) for x in odds[:3])
        dd, mm, yyyy = dm.group(1).split(".")
        rows.append({
            "match_id_be": match_id,
            "home_be": home.strip(), "away_be": away.strip(),
            "date": f"{yyyy}-{mm}-{dd}",
            "oh": oh, "od": od, "oa": oa,
        })
    return rows


def devig(oh, od, oa):
    inv = np.array([1.0 / oh, 1.0 / od, 1.0 / oa])
    return inv / inv.sum()


def scrape_tournament(comp, path):
    base = f"https://www.betexplorer.com/{path}"
    slug = path.strip("/").split("/")[-1]
    home_html = _get(base, f"{slug}__home.html")
    stage_ids = parse_stage_ids(home_html)
    if not stage_ids:
        stage_ids = [None]  # single-stage tournament, no tab needed

    all_rows, seen_ids = [], set()
    for i, stage in enumerate(stage_ids):
        url = f"{base}results/" + (f"?stage={stage}" if stage else "")
        html = _get(url, f"{slug}__results_{stage or 'default'}.html")
        for row in parse_results_rows(html):
            if row["match_id_be"] in seen_ids:
                continue
            seen_ids.add(row["match_id_be"])
            row["comp"] = comp
            all_rows.append(row)
    print(f"  {comp}: {len(stage_ids)} stage(s), {len(all_rows)} match rows scraped")
    return all_rows


def main():
    sys.path.insert(0, HERE)
    from train_intl import load_intl  # reuses the project's own dedupe logic

    target = load_intl()
    target = target[target.minute == 0].drop_duplicates("match_id")
    target = target[target.comp.isin(TOURNAMENTS)]
    target = target.dropna(subset=["home", "away", "date"])
    if "mkt_pH" in target.columns:
        target = target[target.mkt_pH.isna()]
    print(f"Target: {len(target)} matches across {target.comp.nunique()} competitions "
          f"need a scraped market prior.")

    be_key = {}
    for comp, path in TOURNAMENTS.items():
        for row in scrape_tournament(comp, path):
            key = (row["date"], normalize(row["home_be"]), normalize(row["away_be"]))
            be_key[key] = row

    out_rows, missed, shifted = [], [], 0
    for m in target.itertuples():
        h, a = normalize(m.home), normalize(m.away)
        base_date = dt.date.fromisoformat(m.date)
        r = None
        # betexplorer's listed match date is occasionally +/-1 day off ours
        # (a timezone-of-record artifact, e.g. a US/Africa evening kickoff
        # rendered as the next calendar day) — try the exact date first,
        # then a one-day window before falling back to a genuine miss.
        for delta in (0, 1, -1):
            d = (base_date + dt.timedelta(days=delta)).isoformat()
            r = be_key.get((d, h, a))
            if r is not None:
                if delta != 0:
                    shifted += 1
                break
        if r is None:
            missed.append((m.comp, m.date, m.home, m.away))
            continue
        p = devig(r["oh"], r["od"], r["oa"])
        out_rows.append({
            "match_id": m.match_id, "date": m.date,
            "home": m.home, "away": m.away, "comp": m.comp,
            "book": "betexplorer_best",
            "mkt_pH": round(p[0], 5), "mkt_pD": round(p[1], 5),
            "mkt_pA": round(p[2], 5),
        })

    df = pd.DataFrame(out_rows)
    out = os.path.join(DATA, "odds_intl_scraped.csv")
    df.to_csv(out, index=False)
    print(f"\nDONE. {len(df)}/{len(target)} matched -> {out} "
          f"({len(missed)} missed, {shifted} matched via a +/-1 day date shift)")
    if missed:
        print("Missed (needs an ALIASES entry, wider date window, or a stage-discovery gap):")
        for comp, date, home, away in missed:
            print(f"  [MISS] {comp} {date} {home} vs {away}")


if __name__ == "__main__":
    main()
