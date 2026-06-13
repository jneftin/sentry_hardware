"""test_ingest.py - exercises mqtt_ingest.dispatch() against sample payloads from
09 MQTT Contract, with no broker required. Run before any satellite hardware
exists to validate the schema + handler logic, and again once real nodes are
publishing (point DB_PATH at the real telemetry.db and watch row counts grow).
"""

import json
import sqlite3

from mqtt_ingest import init_db, dispatch

DB_PATH = "test_telemetry.db"


SAMPLES = [
    # vision (XIAO ESP32-S3 Sense)
    ("warehouse/site1/dock/xiao01/vision",
     {"ts": 1749600000, "count": 3, "w": 96, "h": 96,
      "centroids": [[42, 30], [55, 61], [12, 80]]}),

    # env (ESP32-C3 + BME280 + LIS3DH) - two messages, same minute, last wins
    ("warehouse/site1/dock/envc3-02/env",
     {"ts": 1749600000, "temp_c": 22.4, "humidity": 47.1, "vib_rms": 0.0123}),
    ("warehouse/site1/dock/envc3-02/env",
     {"ts": 1749600030, "temp_c": 22.6, "humidity": 47.0, "vib_rms": 0.91}),

    # status
    ("warehouse/site1/dock/xiao01/status",
     {"ts": 1749600000, "node": "xiao01", "online": True,
      "rssi": -61, "uptime_s": 3840, "fw": "0.1"}),
]

# malformed / edge cases - should be logged and skipped, not raise
BAD_SAMPLES = [
    ("warehouse/site1/dock/xiao01/vision", b"not json"),
    ("warehouse/site1/dock/unknownstream/zzz", json.dumps({"ts": 1})),
    ("too/few/parts", json.dumps({"ts": 1})),
    ("warehouse/site1/dock/envc3-02/env", json.dumps({"temp_c": 20})),  # missing ts
]


def main():
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    ok = 0
    for topic, payload in SAMPLES:
        if dispatch(conn, topic, json.dumps(payload)):
            ok += 1
    print(f"good samples handled: {ok}/{len(SAMPLES)}")

    skipped = 0
    for topic, raw in BAD_SAMPLES:
        if not dispatch(conn, topic, raw):
            skipped += 1
    print(f"bad samples correctly skipped: {skipped}/{len(BAD_SAMPLES)}")

    print("\nvision_counts:")
    for row in conn.execute("SELECT * FROM vision_counts"):
        print(" ", row)

    print("\nenv (raw):")
    for row in conn.execute("SELECT * FROM env"):
        print(" ", row)

    print("\nenv_readings (per-minute, what cost_model.py reads):")
    for row in conn.execute("SELECT * FROM env_readings"):
        print(" ", row)

    print("\nnode_status:")
    for row in conn.execute("SELECT * FROM node_status"):
        print(" ", row)

    conn.close()


if __name__ == "__main__":
    main()
