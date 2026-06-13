"""mqtt_ingest.py - hub-side MQTT subscriber per [[09 MQTT Contract]].

Subscribes to warehouse/{site}/{zone}/{node}/{stream} and lands messages into
telemetry.db. The per-message handlers are pure functions (conn, site, zone,
node, payload) -> None so they can be unit-tested without a broker
(see test_ingest.py).

Writes:
- vision_counts(ts, site, zone, node, count, w, h, centroids) - raw, append-only.
  Not yet consumed by cost_model.py - satellite-vision -> zone_dwell aggregation
  is a separate open item (see 00 Index / Gaps and Backlog).
- env(ts, site, zone, node, temp_c, humidity, vib_rms) - raw, append-only audit trail.
- env_readings(ts_min, zone, node, temp_c, humidity, vibration_anomaly) - per-minute,
  last-value-wins. This is the shape cost_model.py (10 Data-to-Dollars Model) reads.
  vib_rms is written into vibration_anomaly directly: v1 is the RMS proxy (D9),
  later replaced by an Edge Impulse anomaly score on the same MQTT field (09
  MQTT Contract), so no ingest change is needed when that swap happens.
- node_status(node, site, zone, online, rssi, uptime_s, fw, last_seen) - latest per node.
"""

import json
import sqlite3

DB_PATH = "telemetry.db"
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_FILTER = "warehouse/+/+/+/+"  # site/zone/node/stream


def init_db(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS vision_counts(
        ts INTEGER, site TEXT, zone TEXT, node TEXT,
        count INTEGER, w INTEGER, h INTEGER, centroids TEXT,
        PRIMARY KEY(ts, zone, node));
    CREATE TABLE IF NOT EXISTS env(
        ts INTEGER, site TEXT, zone TEXT, node TEXT,
        temp_c REAL, humidity REAL, vib_rms REAL,
        PRIMARY KEY(ts, zone, node));
    CREATE TABLE IF NOT EXISTS env_readings(
        ts_min INTEGER, zone TEXT, node TEXT,
        temp_c REAL, humidity REAL, vibration_anomaly REAL,
        PRIMARY KEY(ts_min, zone, node));
    CREATE TABLE IF NOT EXISTS node_status(
        node TEXT PRIMARY KEY, site TEXT, zone TEXT, online INTEGER,
        rssi INTEGER, uptime_s INTEGER, fw TEXT, last_seen INTEGER);
    """)
    conn.commit()


def handle_vision(conn, site, zone, node, payload):
    centroids = json.dumps(payload.get("centroids", []))
    conn.execute(
        "INSERT OR REPLACE INTO vision_counts VALUES(?,?,?,?,?,?,?,?)",
        (payload.get("ts"), site, zone, node, payload.get("count"),
         payload.get("w"), payload.get("h"), centroids))


def handle_env(conn, site, zone, node, payload):
    ts = payload.get("ts")
    temp_c = payload.get("temp_c")
    humidity = payload.get("humidity")
    vib = payload.get("vib_rms")

    conn.execute(
        "INSERT OR REPLACE INTO env VALUES(?,?,?,?,?,?,?)",
        (ts, site, zone, node, temp_c, humidity, vib))

    ts_min = ts // 60
    conn.execute(
        "INSERT INTO env_readings VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(ts_min,zone,node) DO UPDATE SET "
        "temp_c=excluded.temp_c, humidity=excluded.humidity, "
        "vibration_anomaly=excluded.vibration_anomaly",
        (ts_min, zone, node, temp_c, humidity, vib))


def handle_status(conn, site, zone, node, payload):
    conn.execute(
        "INSERT OR REPLACE INTO node_status VALUES(?,?,?,?,?,?,?,?)",
        (payload.get("node", node), site, zone,
         int(bool(payload.get("online"))), payload.get("rssi"),
         payload.get("uptime_s"), payload.get("fw"), payload.get("ts")))


HANDLERS = {
    "vision": handle_vision,
    "env": handle_env,
    "status": handle_status,
}


def dispatch(conn, topic, raw_payload):
    """topic: 'warehouse/{site}/{zone}/{node}/{stream}', raw_payload: bytes/str.
    Returns True if handled, False if the message was skipped (logged, not raised) -
    a malformed message from one node should never take down the ingest loop."""
    parts = topic.split("/")
    if len(parts) != 5 or parts[0] != "warehouse":
        print(f"[mqtt_ingest] unexpected topic shape: {topic}")
        return False

    _, site, zone, node, stream = parts
    handler = HANDLERS.get(stream)
    if handler is None:
        print(f"[mqtt_ingest] unknown stream '{stream}' on {topic}")
        return False

    try:
        payload = json.loads(raw_payload)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as e:
        print(f"[mqtt_ingest] bad payload on {topic}: {e}")
        return False

    if "ts" not in payload:
        print(f"[mqtt_ingest] payload missing 'ts' on {topic}: {payload}")
        return False

    handler(conn, site, zone, node, payload)
    conn.commit()
    return True


def main():
    import paho.mqtt.client as mqtt

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"[mqtt_ingest] connected rc={rc}, subscribing {TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER, qos=1)

    def on_message(client, userdata, msg):
        dispatch(userdata, msg.topic, msg.payload)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=conn)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    print("[mqtt_ingest] running. Ctrl-C to stop.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()


if __name__ == "__main__":
    main()
