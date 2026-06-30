# TuniGoal — Audit Log

## Project Overview

End-to-end ELT data pipeline for Tunisian Ligue Professionnelle 1 football analytics.
Ingests live match data from API-Football (api-sports.io v3, league=202, season=2024),
stages into PostgreSQL, transforms to a Star Schema via PySpark, and serves a React 18 dashboard.

## Stack

- Python 3.9+
- Apache Spark / PySpark 3.5.0 — distributed transformation
- Apache Airflow 2.8.1 — DAG orchestration (CeleryExecutor + Redis)
- PostgreSQL 15 (tunigoal_db, port 5433) — staging + star schema warehouse
- PostgreSQL 13 — Airflow metadata DB
- Redis — Celery broker for Airflow workers
- Docker / Docker Compose — full containerization
- FastAPI 0.115 + uvicorn — REST API backend
- React 18 + Vite + nginx — analytics dashboard
- psycopg2-binary 2.9.9 — Python PostgreSQL driver
- api-sports.io v3 REST API (league=202, Tunisian Ligue Pro 1)

## Changes Applied

- Renamed: bundesliga-data-pipeline → TuniGoal
- Fixed league ID: 202 = Tunisian Ligue Pro 1 (was wrong)
- Removed all hardcoded match data and fake player names
- Built FastAPI backend (api/main.py) with dynamic predictor from real DB stats
- Added classic football SVG logo (black-and-white ball, green accent ring) + favicon
- Ingested 240 real fixtures from 2024/25 season via API-Football
- Wired nginx reverse proxy: /api/ → tunigoal-api:8000
- Removed Morocco/Botola Pro assets (Power BI .pbix, PDF, PNG screenshots, Excel data)

## Live Data (2024/25 season)

| Endpoint | Records |
|----------|---------|
| /fixtures?league=202&season=2024&status=FT | 240 fixtures |
| /standings?league=202&season=2024 | 16 teams |
| /players/topscorers?league=202&season=2024 | 20 scorers |
