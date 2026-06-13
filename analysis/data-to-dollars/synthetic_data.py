"""synthetic_data.py - one week of fake telemetry.db data for testing cost_model.py
without hardware. Schema matches 06 Code - Vision Pipeline + env_readings (10)."""

import random
import sqlite3

DB_PATH = "telemetry.db"
DAYS = 7
MINUTES = DAYS * 1440


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    DROP TABLE IF EXISTS heatmap;
    DROP TABLE IF EXISTS zone_dwell;
    DROP TABLE IF EXISTS line_counts;
    DROP TABLE IF EXISTS env_readings;
    CREATE TABLE heatmap(ts_min INTEGER, gx INTEGER, gy INTEGER, weight REAL,
        PRIMARY KEY(ts_min,gx,gy));
    CREATE TABLE zone_dwell(ts_min INTEGER, zone TEXT, person_seconds REAL,
        unique_ids INTEGER, PRIMARY KEY(ts_min,zone));
    CREATE TABLE line_counts(ts_min INTEGER, line TEXT, dir_pos INTEGER,
        dir_neg INTEGER, PRIMARY KEY(ts_min,line));
    CREATE TABLE env_readings(ts_min INTEGER, zone TEXT, node TEXT,
        temp_c REAL, humidity REAL, vibration_anomaly REAL,
        PRIMARY KEY(ts_min,zone,node));
    """)
    cur = conn.cursor()
    for m in range(MINUTES):
        hour = (m // 60) % 24
        workday = ((m // 1440) % 7) < 5
        busy = workday and 7 <= hour < 16

        dock_people = (3 + random.randint(0, 3)) if busy else random.randint(0, 1)
        dock_ps = dock_people * 60
        cur.execute("INSERT INTO zone_dwell VALUES(?,?,?,?)",
                    (m, "dock", dock_ps, dock_people))

        pf_people = (2 + random.randint(0, 2)) if busy else 0
        cur.execute("INSERT INTO zone_dwell VALUES(?,?,?,?)",
                    (m, "pick_face", pf_people * 60, pf_people))

        if busy:
            cur.execute("INSERT INTO line_counts VALUES(?,?,?,?)",
                        (m, "main_aisle", random.randint(0, 2), random.randint(0, 2)))

        temp = 18 + (3 if busy else 1) + random.gauss(0, 0.3)
        humidity = 45 + random.gauss(0, 2)
        vib = 0.1 + (0.85 if (m % 1440 == 600) else 0) + random.gauss(0, 0.05)
        cur.execute("INSERT INTO env_readings VALUES(?,?,?,?,?,?)",
                    (m, "dock", "env1", temp, humidity, max(0.0, vib)))

    conn.commit()
    conn.close()
    print(f"wrote {MINUTES} minutes ({DAYS} days) of synthetic data -> {DB_PATH}")


if __name__ == "__main__":
    main()
