"""
TuniGoal — Load to PostgreSQL
Reads raw JSON files and inserts into tunigoal-dw.
Tables: raw_matches, raw_standings, raw_topscorers
"""
import json
import os
import psycopg2

RAW_DIR = "/opt/airflow/data/raw"

conn = psycopg2.connect(
    dbname="tunigoal_db", user="admin", password="admin123",
    host="tunigoal-dw", port="5432"
)
cur = conn.cursor()

# ── Create tables ─────────────────────────────────────────────────────────
cur.execute("""
CREATE TABLE IF NOT EXISTS raw_matches (
    match_id   INT PRIMARY KEY,
    league_id  INT,
    home_team  VARCHAR(255),
    away_team  VARCHAR(255),
    home_goals INT,
    away_goals INT,
    match_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw_standings (
    team_name    VARCHAR(255) PRIMARY KEY,
    rank         INT,
    played       INT,
    wins         INT,
    draws        INT,
    losses       INT,
    goals_for    INT,
    goals_against INT,
    goal_diff    INT,
    points       INT,
    fetched_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_topscorers (
    player_id   INT PRIMARY KEY,
    player_name VARCHAR(255),
    team        VARCHAR(255),
    goals       INT,
    assists     INT,
    appearances INT,
    fetched_at  TIMESTAMP DEFAULT NOW()
);
""")
conn.commit()
print("Tables ready.")

# ── Load fixtures ─────────────────────────────────────────────────────────
fixture_files = sorted(f for f in os.listdir(RAW_DIR) if f.startswith("fixtures_") and f.endswith(".json"))
for fname in fixture_files:
    with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
        matches = json.load(f)
    loaded = 0
    for m in matches:
        try:
            cur.execute("""
                INSERT INTO raw_matches (match_id,league_id,home_team,away_team,home_goals,away_goals,match_date)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (match_id) DO NOTHING
            """, (
                m["fixture"]["id"],
                m["league"]["id"],
                m["teams"]["home"]["name"],
                m["teams"]["away"]["name"],
                m["goals"]["home"],
                m["goals"]["away"],
                m["fixture"]["date"],
            ))
            loaded += cur.rowcount
        except Exception as e:
            print(f"  skip fixture {m.get('fixture',{}).get('id')}: {e}")
    conn.commit()
    print(f"Fixtures: {loaded} new rows from {fname}")

# ── Load standings ────────────────────────────────────────────────────────
standing_files = sorted(f for f in os.listdir(RAW_DIR) if f.startswith("standings_") and f.endswith(".json"))
for fname in standing_files:
    with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
        data = json.load(f)
    loaded = 0
    # api-sports nests: data[0]["league"]["standings"][0] → list of teams
    groups = data[0]["league"]["standings"] if data else []
    for group in groups:
        for entry in group:
            try:
                cur.execute("""
                    INSERT INTO raw_standings
                    (team_name,rank,played,wins,draws,losses,goals_for,goals_against,goal_diff,points)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (team_name) DO UPDATE SET
                        rank=EXCLUDED.rank, played=EXCLUDED.played, wins=EXCLUDED.wins,
                        draws=EXCLUDED.draws, losses=EXCLUDED.losses, goals_for=EXCLUDED.goals_for,
                        goals_against=EXCLUDED.goals_against, goal_diff=EXCLUDED.goal_diff,
                        points=EXCLUDED.points, fetched_at=NOW()
                """, (
                    entry["team"]["name"],
                    entry["rank"],
                    entry["all"]["played"],
                    entry["all"]["win"],
                    entry["all"]["draw"],
                    entry["all"]["lose"],
                    entry["all"]["goals"]["for"],
                    entry["all"]["goals"]["against"],
                    entry["goalsDiff"],
                    entry["points"],
                ))
                loaded += cur.rowcount
            except Exception as e:
                print(f"  skip standing {entry.get('team',{}).get('name')}: {e}")
    conn.commit()
    print(f"Standings: {loaded} rows from {fname}")

# ── Load top scorers ──────────────────────────────────────────────────────
scorer_files = sorted(f for f in os.listdir(RAW_DIR) if f.startswith("topscorers_") and f.endswith(".json"))
for fname in scorer_files:
    with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
        data = json.load(f)
    loaded = 0
    for entry in data:
        try:
            p       = entry["player"]
            stats   = entry["statistics"][0]
            cur.execute("""
                INSERT INTO raw_topscorers (player_id,player_name,team,goals,assists,appearances)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (player_id) DO UPDATE SET
                    goals=EXCLUDED.goals, assists=EXCLUDED.assists,
                    appearances=EXCLUDED.appearances, fetched_at=NOW()
            """, (
                p["id"],
                p["name"],
                stats["team"]["name"],
                stats["goals"]["total"] or 0,
                stats["goals"]["assists"] or 0,
                stats["games"]["appearences"] or 0,
            ))
            loaded += cur.rowcount
        except Exception as e:
            print(f"  skip scorer: {e}")
    conn.commit()
    print(f"Top scorers: {loaded} rows from {fname}")

cur.close()
conn.close()
print("Done.")
