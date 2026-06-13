"""server.py - read-only API over telemetry.db. Anonymized aggregates only.
From 07 Dashboard. Reads the same telemetry.db produced by synthetic_data.py
(analysis/data-to-dollars/) or by pipeline.py + mqtt_ingest.py in production."""

import os
import sqlite3
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = os.environ.get(
    "TELEMETRY_DB",
    os.path.join(os.path.dirname(__file__), "..", "data-to-dollars", "telemetry.db"))
GRID_CELL_M = 0.5   # must match pipeline.py / synthetic_data.py

app = FastAPI(title="Warehouse Intelligence API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def q(sql, args=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def window(minutes):
    now_min = int(time.time() // 60)
    return now_min - int(minutes), now_min


@app.get("/health")
def health():
    return {"ok": True, "db": DB_PATH, "exists": os.path.exists(DB_PATH)}


@app.get("/heatmap")
def heatmap(minutes: int = 10080):
    lo, hi = window(minutes)
    cells = q("""SELECT gx, gy, SUM(weight) AS weight FROM heatmap
                 WHERE ts_min BETWEEN ? AND ? GROUP BY gx, gy""", (lo, hi))
    return {"cell_m": GRID_CELL_M, "cells": cells}


@app.get("/zones")
def zones(minutes: int = 10080):
    lo, hi = window(minutes)
    return q("""SELECT zone, SUM(person_seconds) AS person_seconds,
                       MAX(unique_ids) AS peak_unique
                FROM zone_dwell WHERE ts_min BETWEEN ? AND ?
                GROUP BY zone ORDER BY person_seconds DESC""", (lo, hi))


@app.get("/lines")
def lines(minutes: int = 10080):
    lo, hi = window(minutes)
    return q("""SELECT line, SUM(dir_pos) AS dir_pos, SUM(dir_neg) AS dir_neg
                FROM line_counts WHERE ts_min BETWEEN ? AND ?
                GROUP BY line""", (lo, hi))


@app.get("/env")
def env(minutes: int = 10080):
    lo, hi = window(minutes)
    return q("""SELECT zone, node, AVG(temp_c) AS avg_temp_c,
                       AVG(humidity) AS avg_humidity,
                       MAX(vibration_anomaly) AS peak_vibration_anomaly
                FROM env_readings WHERE ts_min BETWEEN ? AND ?
                GROUP BY zone, node""", (lo, hi))
