"""
Kairos — pre-match Elo ratings for the national-team model.

Source: eloratings.net (World Football Elo Ratings) — free, no key, no login.
The site's own frontend (scripts/ratings.js) pulls each team's full match/rating
history as a plain TSV file at https://www.eloratings.net/<Team_Name>.tsv (same
name as the team's page, spaces -> underscores). We reuse that endpoint directly.

TSV row layout (space/tab separated, one row per match for that team):
    year  month  day  home_code  away_code  home_goals  away_goals  tourn_code
    <blank>  elo_change  home_elo_after  away_elo_after  ...(rank/extra cols)

We only need: date, home_code, away_code, home_elo_after, away_elo_after —
that's enough to reconstruct each team's rating immediately AFTER every match
it has played, which is exactly the value in effect (as its next "pre-match"
rating) until its next match.

Output: data/elo_history.csv with columns [name, date, elo_after]  (one row per
team per match date, so build_dataset_intl.py can look up "team's rating as of
strictly-before this match" via an as-of join).
"""
import csv
import glob
import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "elo")
os.makedirs(CACHE, exist_ok=True)

BASE = "https://www.eloratings.net"

# eloratings.net page-name overrides where it diverges from KickoffAPI's team name
ALIASES = {
    "USA": "United_States",
    "Congo DR": "DR_Congo",
    "FYR Macedonia": "North_Macedonia",
    "Rep. Of Ireland": "Ireland",
    "Türkiye": "Turkey",
    "Bosnia & Herzegovina": "Bosnia_and_Herzegovina",
    "Curaçao": "Curacao",
    "Cape Verde Islands": "Cape_Verde",
    "Guinea-Bissau": "Guinea-Bissau",  # keep the hyphen — slug() would break it
}

# teams that appear only in the StatsBomb tournaments (build_dataset_sb_intl.py),
# not in any KickoffAPI fixture — fetched under their StatsBomb names
EXTRA_TEAMS = [
    "Cape Verde Islands", "Gambia", "Guinea", "Guinea-Bissau",
    "Mauritania", "Namibia", "Russia",
]

# only use recent-era rows to fingerprint a team's own eloratings.net code — several
# teams changed code/name decades ago (West Germany->Germany, Zaire->Congo DR, etc.)
# which would otherwise make the "common code across ALL rows" trick fail
CODE_ERA_START = "2010-01-01"

# manual fallback for the handful of teams whose own code still isn't a clean
# intersection even in the recent era (e.g. a rename mid-window)
MANUAL_CODE = {"FYR Macedonia": "NM", "Curaçao": "CW"}


def slug(name):
    if name in ALIASES:
        return ALIASES[name]
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s


def fetch_tsv(name):
    cache_path = os.path.join(CACHE, f"{slug(name)}.tsv")
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return f.read()
    url = f"{BASE}/{slug(name)}.tsv"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def main():
    names = set()
    for f in glob.glob(os.path.join(DATA, "kickoffapi", "fx_*.json")):
        d = json.load(open(f))
        for r in d["response"]:
            names.add(r["homeTeam"]["name"])
            names.add(r["awayTeam"]["name"])
    names.update(EXTRA_TEAMS)
    names = sorted(names)
    print(f"{len(names)} distinct teams to fetch Elo history for")

    out_rows = []
    missing = []

    def work(name):
        text = fetch_tsv(name)
        return name, text

    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(work, n): n for n in names}
        for i, fut in enumerate(as_completed(futs), 1):
            name = futs[fut]
            try:
                _, text = fut.result()
            except Exception as e:
                missing.append((name, str(e)))
                continue
            if text is None:
                missing.append((name, "404"))
                continue

            parsed = []
            code_pairs = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                cols = line.split("\t")
                if len(cols) < 12:
                    continue
                try:
                    yr, mo, da = int(cols[0]), int(cols[1]), int(cols[2])
                    home_after, away_after = float(cols[10]), float(cols[11])
                except ValueError:
                    continue
                date = f"{yr:04d}-{mo:02d}-{da:02d}"
                home_code, away_code = cols[3], cols[4]
                parsed.append((date, home_code, away_code, home_after, away_after))
                code_pairs.append({home_code, away_code})

            if not parsed:
                missing.append((name, "no parsable rows"))
                continue

            # every row's {home_code, away_code} pair contains this team's own code,
            # since eloratings.net's per-team tsv only lists matches that team played;
            # the code common to ALL rows is this team's own code. Restrict to the
            # recent era so decades-old code/name changes don't break the intersection.
            if name in MANUAL_CODE:
                team_code = MANUAL_CODE[name]
            else:
                recent_pairs = [cp for (d, *_), cp in zip(parsed, code_pairs) if d >= CODE_ERA_START]
                pairs_for_code = recent_pairs or code_pairs
                common = set.intersection(*pairs_for_code) if pairs_for_code else set()
                if len(common) != 1:
                    missing.append((name, f"ambiguous code {common}"))
                    continue
                team_code = next(iter(common))

            for date, home_code, away_code, home_after, away_after in parsed:
                elo_after = home_after if home_code == team_code else away_after
                out_rows.append({"name": name, "date": date, "elo_after": elo_after})

            if i % 20 == 0:
                print(f"  {i}/{len(names)} fetched", flush=True)

    if missing:
        print(f"\n{len(missing)} teams had no eloratings.net page (add to ALIASES if needed):")
        for n, err in missing:
            print(f"  {n}: {err}")

    out_rows.sort(key=lambda r: (r["name"], r["date"]))
    out = os.path.join(DATA, "elo_history.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "date", "elo_after"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"\nSaved {len(out_rows)} (team, match-date, rating-after) rows for "
          f"{len(names) - len(missing)}/{len(names)} teams -> {out}")


if __name__ == "__main__":
    main()
