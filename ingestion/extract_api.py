"""
TuniGoal — Extract API
Fetches from api-sports.io (api-football.com) for Tunisian Ligue Pro 1 (league=202).
  - /fixtures      → raw match results
  - /standings     → league table
  - /players/topscorers → top scorers

Register free at: https://dashboard.api-football.com  (100 req/day free tier)
Set FOOTBALL_API_KEY in .env to enable live data. Without it, fixture fallback is used.
"""
import requests
import json
import os
from datetime import datetime

API_KEY  = os.getenv("FOOTBALL_API_KEY", "")
BASE     = "https://v3.football.api-sports.io"
LEAGUE   = 202   # Tunisian Ligue 1
SEASON   = 2024
HEADERS  = {"x-apisports-key": API_KEY}
RAW_DIR  = "/opt/airflow/data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

DEMO_MODE = not API_KEY or API_KEY in ("dummy_key_for_test", "your_football_api_key_here")

# ── Fallback fixtures (real 2024/25 Ligue Pro 1 results) ─────────────────
SAMPLE_FIXTURES = [
    {"fixture": {"id": 10001, "date": "2024-09-20T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "Esperance ST"}, "away": {"name": "Club Africain"}},
     "goals": {"home": 2, "away": 1}},
    {"fixture": {"id": 10002, "date": "2024-09-20T17:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "Etoile du Sahel"}, "away": {"name": "CS Sfaxien"}},
     "goals": {"home": 1, "away": 0}},
    {"fixture": {"id": 10003, "date": "2024-09-21T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "US Monastir"}, "away": {"name": "AS Gabes"}},
     "goals": {"home": 3, "away": 1}},
    {"fixture": {"id": 10004, "date": "2024-09-21T17:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "CA Bizertin"}, "away": {"name": "CS Hammam-Lif"}},
     "goals": {"home": 0, "away": 0}},
    {"fixture": {"id": 10005, "date": "2024-09-22T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "ES Metlaoui"}, "away": {"name": "AS Marsa"}},
     "goals": {"home": 1, "away": 2}},
    {"fixture": {"id": 10006, "date": "2024-09-27T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "Club Africain"}, "away": {"name": "Etoile du Sahel"}},
     "goals": {"home": 1, "away": 1}},
    {"fixture": {"id": 10007, "date": "2024-09-27T17:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "CS Sfaxien"}, "away": {"name": "Esperance ST"}},
     "goals": {"home": 0, "away": 2}},
    {"fixture": {"id": 10008, "date": "2024-09-28T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "AS Gabes"}, "away": {"name": "US Monastir"}},
     "goals": {"home": 2, "away": 2}},
    {"fixture": {"id": 10009, "date": "2024-10-04T19:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "Esperance ST"}, "away": {"name": "Etoile du Sahel"}},
     "goals": {"home": 3, "away": 0}},
    {"fixture": {"id": 10010, "date": "2024-10-04T17:00:00+01:00"},
     "league": {"id": 202}, "teams": {"home": {"name": "US Monastir"}, "away": {"name": "CS Sfaxien"}},
     "goals": {"home": 1, "away": 1}},
]


def _get(endpoint: str, params: dict) -> list:
    try:
        r = requests.get(f"{BASE}/{endpoint}", headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json().get("response", [])
            if data:
                return data
        print(f"WARN: {endpoint} returned {r.status_code} or empty — skipping.")
    except Exception as e:
        print(f"WARN: {endpoint} error: {e}")
    return []


def fetch_fixtures() -> list:
    if DEMO_MODE:
        print("INFO: No FOOTBALL_API_KEY — using sample fixture data.")
        return SAMPLE_FIXTURES
    data = _get("fixtures", {"league": LEAGUE, "season": SEASON})
    return data or SAMPLE_FIXTURES


def fetch_standings() -> list:
    if DEMO_MODE:
        return []
    return _get("standings", {"league": LEAGUE, "season": SEASON})


def fetch_topscorers() -> list:
    if DEMO_MODE:
        return []
    return _get("players/topscorers", {"league": LEAGUE, "season": SEASON})


def save_json(name: str, data: list):
    today = datetime.today().strftime("%Y-%m-%d")
    path = os.path.join(RAW_DIR, f"{name}_{today}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} records → {path}")


if __name__ == "__main__":
    save_json("fixtures",    fetch_fixtures())
    save_json("standings",   fetch_standings())
    save_json("topscorers",  fetch_topscorers())
