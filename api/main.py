"""
TuniGoal API — FastAPI backend for the React dashboard.
Endpoints:
  GET  /health
  GET  /matches
  GET  /standings
  GET  /scorers
  GET  /teams
  POST /predict        { home_team, away_team }  → win/draw/loss probs + xG
  POST /pipeline/trigger                          → fires Airflow DAG
  GET  /pipeline/status                           → last DAG run state
  GET  /warehouse/summary                         → star schema row counts
"""
import os, time, requests as req
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_URL       = os.getenv("DATABASE_URL", "postgresql://admin:admin123@tunigoal-dw:5432/tunigoal_db")
AIRFLOW_URL  = os.getenv("AIRFLOW_URL",  "http://airflow-webserver:8080")
AIRFLOW_USER = os.getenv("AIRFLOW_USER", "airflow")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASS", "airflow")
DAG_ID       = "tunigoal_pipeline"

app = FastAPI(title="TuniGoal API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _load_team_stats_from_db(conn) -> dict:
    """Compute per-team home/away win rates and goal averages from raw_matches."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            team,
            is_home,
            ROUND(COUNT(*) FILTER (WHERE pts=3)::numeric / NULLIF(COUNT(*),0), 4) AS win_rate,
            ROUND(AVG(gf)::numeric, 3) AS avg_gf,
            ROUND(AVG(ga)::numeric, 3) AS avg_ga,
            COUNT(*) AS played
        FROM (
            SELECT home_team AS team, home_goals AS gf, away_goals AS ga, TRUE  AS is_home,
                   CASE WHEN home_goals>away_goals THEN 3
                        WHEN home_goals=away_goals THEN 1 ELSE 0 END AS pts
            FROM raw_matches
            UNION ALL
            SELECT away_team,        away_goals,       home_goals,       FALSE AS is_home,
                   CASE WHEN away_goals>home_goals THEN 3
                        WHEN away_goals=home_goals THEN 1 ELSE 0 END
            FROM raw_matches
        ) t
        GROUP BY team, is_home
        HAVING COUNT(*) >= 5
    """)
    rows = cur.fetchall()
    stats = {}
    for r in rows:
        t = r["team"]
        if t not in stats:
            stats[t] = {"hw": 0.33, "aw": 0.25, "hg": 1.0, "ag": 1.0}
        if r["is_home"]:
            stats[t]["hw"] = float(r["win_rate"] or 0.33)
            stats[t]["hg"] = float(r["avg_gf"] or 1.0)
        else:
            stats[t]["aw"] = float(r["win_rate"] or 0.25)
            stats[t]["ag"] = float(r["avg_gf"] or 1.0)
    return stats


def _predict(home: str, away: str, stats: dict) -> dict:
    h = stats.get(home, {"hw": 0.40, "aw": 0.30, "hg": 1.2, "ag": 1.0})
    a = stats.get(away, {"hw": 0.40, "aw": 0.30, "hg": 1.2, "ag": 1.0})

    home_score = h["hw"] * 0.55 + (h["hg"] / 4.0) * 0.35 + 0.10
    away_score = a["aw"] * 0.55 + (a["ag"] / 4.0) * 0.35

    diff = home_score - away_score
    if diff > 0.12:
        hw = _clamp(0.50 + diff * 0.65, 0.10, 0.80)
        dr = 0.22
        aw = 1.0 - hw - dr
    elif diff < -0.08:
        aw = _clamp(0.50 + abs(diff) * 0.65, 0.10, 0.80)
        dr = 0.22
        hw = 1.0 - aw - dr
    else:
        dr = 0.32
        hw = _clamp(0.38 + diff * 0.50, 0.10, 0.70)
        aw = 1.0 - hw - dr

    hw = _clamp(hw, 0.05, 0.80)
    aw = _clamp(aw, 0.05, 0.80)
    dr = _clamp(dr, 0.10, 0.40)
    total = hw + dr + aw
    hw, dr, aw = hw / total, dr / total, aw / total
    max_p = max(hw, dr, aw)
    outcome = "home_win" if max_p == hw else ("away_win" if max_p == aw else "draw")
    xg_home = round(h["hg"] * 0.70 + a["ag"] * 0.30 * 0.85, 1)
    xg_away = round(a["ag"] * 0.70 + h["hg"] * 0.30 * 0.85, 1)
    return {
        "home_team": home, "away_team": away,
        "outcome": outcome, "confidence": round(max_p, 3),
        "probabilities": {"home_win": round(hw, 3), "draw": round(dr, 3), "away_win": round(aw, 3)},
        "expected_goals": {"home": xg_home, "away": xg_away},
        "model_note": f"Computed from {len(stats)} teams × real match data (raw_matches table)",
    }


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


def _table_exists(cur, name):
    cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{name}",))
    return cur.fetchone()[0]


def _count(cur, table):
    try:
        cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
        return cur.fetchone()["c"]
    except Exception:
        return 0


def init_db():
    for attempt in range(10):
        try:
            conn = get_conn()
            cur = conn.cursor()
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
                    team_name     VARCHAR(255) PRIMARY KEY,
                    rank          INT, played INT,
                    wins INT, draws INT, losses INT,
                    goals_for INT, goals_against INT,
                    goal_diff INT, points INT,
                    fetched_at TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS raw_topscorers (
                    player_id   INT PRIMARY KEY,
                    player_name VARCHAR(255),
                    team VARCHAR(255), goals INT, assists INT, appearances INT,
                    fetched_at TIMESTAMP DEFAULT NOW()
                );
            """)
            # No seed fixtures — data comes from the Airflow pipeline (extract_api.py)
            conn.commit()
            conn.close()
            print("DB ready.")
            return
        except Exception as e:
            print(f"DB not ready ({attempt+1}/10): {e}")
            time.sleep(3)


init_db()


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    try:
        conn = get_conn(); conn.cursor().execute("SELECT 1"); conn.close(); pg = "ok"
    except Exception as e:
        pg = str(e)
    return {"status": "healthy", "postgres": pg, "version": "2.0.0"}


@app.get("/teams")
def get_teams():
    """Returns teams that have enough match data for the predictor (>=5 home games)."""
    conn = get_conn()
    stats = _load_team_stats_from_db(conn)
    conn.close()
    return sorted(stats.keys())


@app.get("/matches")
def get_matches():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
        SELECT match_id AS id, match_date::date::text AS date,
               home_team AS home, away_team AS away,
               home_goals AS hg, away_goals AS ag
        FROM raw_matches ORDER BY match_date DESC LIMIT 20
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows


@app.get("/standings")
def get_standings():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM raw_standings")
    if cur.fetchone()["c"] > 0:
        cur.execute("""
            SELECT rank AS pos, team_name AS team, played AS p,
                   wins AS w, draws AS d, losses AS l,
                   CONCAT(CASE WHEN goal_diff>=0 THEN '+' ELSE '' END, goal_diff) AS gd,
                   points AS pts
            FROM raw_standings ORDER BY rank
        """)
        rows = [dict(r) for r in cur.fetchall()]; conn.close(); return rows
    cur.execute("""
        WITH all_results AS (
            SELECT home_team AS team, home_goals AS gf, away_goals AS ga,
                   CASE WHEN home_goals>away_goals THEN 3 WHEN home_goals=away_goals THEN 1 ELSE 0 END AS pts
            FROM raw_matches
            UNION ALL
            SELECT away_team, away_goals, home_goals,
                   CASE WHEN away_goals>home_goals THEN 3 WHEN away_goals=home_goals THEN 1 ELSE 0 END
            FROM raw_matches
        )
        SELECT ROW_NUMBER() OVER (ORDER BY SUM(pts) DESC, SUM(gf)-SUM(ga) DESC) AS pos,
               team, COUNT(*) AS p,
               COUNT(*) FILTER (WHERE pts=3) AS w,
               COUNT(*) FILTER (WHERE pts=1) AS d,
               COUNT(*) FILTER (WHERE pts=0) AS l,
               CONCAT(CASE WHEN SUM(gf)-SUM(ga)>=0 THEN '+' ELSE '' END, SUM(gf)-SUM(ga)) AS gd,
               SUM(pts) AS pts
        FROM all_results GROUP BY team
        ORDER BY SUM(pts) DESC, SUM(gf)-SUM(ga) DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]; conn.close(); return rows


@app.get("/scorers")
def get_scorers():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM raw_topscorers")
    if cur.fetchone()["c"] == 0:
        conn.close(); return []
    cur.execute("""
        SELECT ROW_NUMBER() OVER (ORDER BY goals DESC, assists DESC) AS rank,
               player_name AS name, team, goals, assists, appearances
        FROM raw_topscorers ORDER BY goals DESC LIMIT 10
    """)
    rows = [dict(r) for r in cur.fetchall()]; conn.close(); return rows


# ── Match Predictor ───────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    home_team: str
    away_team: str


@app.post("/predict")
def predict(body: PredictRequest):
    if body.home_team == body.away_team:
        raise HTTPException(400, "Teams must be different")
    conn = get_conn()
    stats = _load_team_stats_from_db(conn)
    conn.close()
    if body.home_team not in stats:
        raise HTTPException(400, f"Not enough match data for: {body.home_team}")
    if body.away_team not in stats:
        raise HTTPException(400, f"Not enough match data for: {body.away_team}")
    return _predict(body.home_team, body.away_team, stats)


# ── Pipeline Control (Airflow) ────────────────────────────────────────────────
def _airflow(method, path, **kwargs):
    url = f"{AIRFLOW_URL}/api/v1/{path}"
    try:
        r = getattr(req, method)(url, auth=(AIRFLOW_USER, AIRFLOW_PASS),
                                  timeout=8, **kwargs)
        return r.status_code, r.json() if r.content else {}
    except Exception as e:
        return 0, {"error": str(e)}


@app.post("/pipeline/trigger")
def trigger_pipeline():
    import datetime
    run_id = f"manual__{datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}"
    status, data = _airflow("post", f"dags/{DAG_ID}/dagRuns",
                             json={"dag_run_id": run_id})
    if status in (200, 409):
        return {"triggered": True, "run_id": run_id, "detail": data}
    return {"triggered": False, "status_code": status, "detail": data}


@app.get("/pipeline/status")
def pipeline_status():
    status, data = _airflow("get", f"dags/{DAG_ID}/dagRuns",
                             params={"limit": 1, "order_by": "-execution_date"})
    if status != 200:
        return {"available": False, "detail": "Airflow unreachable — check http://localhost:8080"}
    runs = data.get("dag_runs", [])
    if not runs:
        return {"available": True, "last_run": None, "state": "never_run"}
    r = runs[0]
    return {
        "available": True,
        "dag_id": DAG_ID,
        "run_id": r.get("dag_run_id"),
        "state": r.get("state"),
        "started": r.get("start_date"),
        "ended": r.get("end_date"),
        "execution_date": r.get("execution_date"),
    }


@app.get("/warehouse/summary")
def warehouse_summary():
    conn = get_conn(); cur = conn.cursor()
    tables = ["raw_matches", "raw_standings", "raw_topscorers",
              "fact_matches", "dim_teams", "dim_dates", "dim_leagues"]
    result = {}
    for t in tables:
        result[t] = _count(cur, t)
    conn.close()
    gold_built = result.get("fact_matches", 0) > 0
    return {**result, "gold_layer_built": gold_built}
