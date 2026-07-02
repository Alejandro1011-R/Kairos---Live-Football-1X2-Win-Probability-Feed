"""
Kairos — live market prior for serving (WC2026 track).

Fetches current 1X2 odds for upcoming/live World Cup 2026 fixtures from
The Odds API (free tier: 500 credits/month, https://the-odds-api.com — set
ODDS_API_KEY in the environment), de-vigs them, and hands the result to
PriorModule as mkt_pH/mkt_pD/mkt_pA columns — the swap-ready feature space
the model was trained on (club track proves the swap is worth ~5% log-loss).

Everything degrades gracefully: no key, no market for a fixture, or a team
name we can't match -> live_runner falls back to the Elo prior and says so.
No odds are ever fabricated or cached beyond one process run.
"""
import json
import os
import urllib.parse
import urllib.request

SPORT_KEY = "soccer_fifa_world_cup"
API = "https://api.the-odds-api.com/v4/sports/{sport}/odds"
PREFERRED_BOOKS = ["pinnacle", "betfair_ex_eu", "bet365"]  # sharpest first

_cache = {}


_ALIASES = {
    "cape verde islands": "cape verde",
    "korea republic": "south korea",
    "usa": "united states",
    "türkiye": "turkey",
    "côte d'ivoire": "ivory coast",
}


def _norm(name):
    """Normalise a national-team name enough to match across feeds."""
    s = (name or "").lower().replace("republic of ", "").replace("ir ", "").strip()
    return _ALIASES.get(s, s)


def fetch_market_prior(home, away, api_key=None):
    """De-vigged (pH, pD, pA) for one fixture, or None if unavailable."""
    api_key = api_key or os.environ.get("ODDS_API_KEY")
    if not api_key:
        return None
    if "events" not in _cache:
        url = API.format(sport=SPORT_KEY) + "?" + urllib.parse.urlencode({
            "apiKey": api_key, "regions": "eu", "markets": "h2h",
            "oddsFormat": "decimal",
        })
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                _cache["events"] = json.load(r)
        except Exception as e:
            print(f"  market prior: The Odds API unavailable ({e}) — Elo fallback")
            _cache["events"] = []
    for ev in _cache["events"]:
        if {_norm(ev.get("home_team")), _norm(ev.get("away_team"))} != {_norm(home), _norm(away)}:
            continue
        books = {b["key"]: b for b in ev.get("bookmakers", [])}
        for key in PREFERRED_BOOKS + list(books):
            book = books.get(key)
            if not book:
                continue
            for mkt in book.get("markets", []):
                if mkt["key"] != "h2h":
                    continue
                prices = {_norm(o["name"]): o["price"] for o in mkt["outcomes"]}
                oh = prices.get(_norm(ev["home_team"]))
                oa = prices.get(_norm(ev["away_team"]))
                od = prices.get("draw")
                if not all(x and x > 1.0 for x in (oh, od, oa)):
                    continue
                inv = [1.0 / oh, 1.0 / od, 1.0 / oa]
                s = sum(inv)
                print(f"  market prior: {book['title']} "
                      f"H/D/A = {inv[0]/s:.3f}/{inv[1]/s:.3f}/{inv[2]/s:.3f}")
                return inv[0] / s, inv[1] / s, inv[2] / s
    return None
