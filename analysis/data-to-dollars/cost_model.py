"""cost_model.py - data-to-dollars layer (D12). Reads telemetry.db + client_config.yaml,
outputs ranked dollar findings. Run against synthetic_data.py output to validate without
hardware. No raw telemetry leaves this script - aggregates in, dollars out."""

import sqlite3
import yaml
from dataclasses import dataclass

DB_PATH = "telemetry.db"
CONFIG_PATH = "client_config.yaml"


@dataclass
class Finding:
    category: str
    zone: str
    weekly_dollars: float
    annual_dollars: float
    detail: str


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def q(conn, sql, args=()):
    return conn.execute(sql, args).fetchall()


def observed_span_minutes(conn):
    row = q(conn, "SELECT MIN(ts_min), MAX(ts_min) FROM zone_dwell")[0]
    if row[0] is None:
        return 7 * 1440
    return max(row[1] - row[0], 1)


def labor_space_findings(conn, cfg, span_minutes):
    findings = []
    rows = q(conn, "SELECT zone, SUM(person_seconds), MAX(unique_ids) "
                   "FROM zone_dwell GROUP BY zone")
    span_hours = span_minutes / 60
    for zone, ps, peak in rows:
        zcfg = cfg["zones"].get(zone, {})
        capacity = zcfg.get("design_capacity_people")
        sqft = zcfg.get("sqft")
        if not capacity:
            continue
        hours_observed = (ps or 0) / 3600
        utilization = hours_observed / (span_hours * capacity)

        if sqft and utilization < cfg["thresholds"]["underutilized_below"]:
            weekly = sqft * cfg["rates"]["space_cost_per_sqft_per_year"] / 52 \
                     * (1 - utilization)
            findings.append(Finding(
                "space_underutilization", zone, weekly, weekly * 52,
                f"{zone}: {utilization:.0%} of capacity used ({sqft} sqft) "
                f"-> excess space cost"))

        if utilization > cfg["thresholds"]["overutilized_above"]:
            extra_hours = hours_observed * (utilization - 1)
            weekly = extra_hours * cfg["rates"]["labor_cost_per_hour"]
            findings.append(Finding(
                "labor_bottleneck", zone, weekly, weekly * 52,
                f"{zone}: {utilization:.0%} of capacity used "
                f"-> ~{extra_hours:.1f} extra labor-hrs/wk"))
    return findings


def chokepoint_findings(conn, cfg, span_minutes):
    findings = []
    rows = q(conn, "SELECT line, SUM(dir_pos), SUM(dir_neg) "
                   "FROM line_counts GROUP BY line")
    for line, p, n in rows:
        total = (p or 0) + (n or 0)
        lcfg = cfg["lines"].get(line, {})
        delay_sec = lcfg.get("avg_delay_seconds_per_crossing", 0)
        if delay_sec and total:
            weekly_hours = total * delay_sec / 3600
            weekly = weekly_hours * cfg["rates"]["labor_cost_per_hour"]
            findings.append(Finding(
                "chokepoint_delay", line, weekly, weekly * 52,
                f"{line}: {total} crossings/wk x {delay_sec}s delay "
                f"-> {weekly_hours:.1f} labor-hrs/wk"))
    return findings


def env_findings(conn, cfg, span_minutes):
    findings = []
    try:
        rows = q(conn, "SELECT zone, AVG(temp_c), AVG(humidity), "
                       "MAX(vibration_anomaly) FROM env_readings GROUP BY zone")
    except sqlite3.OperationalError:
        return findings

    span_hours = span_minutes / 60
    for zone, t, h, v_max in rows:
        zcfg = cfg["zones"].get(zone, {})

        setpoint = zcfg.get("hvac_setpoint_c")
        if setpoint is not None and t is not None:
            delta = abs(t - setpoint)
            if delta > cfg["thresholds"]["hvac_delta_alert_c"]:
                kwh_excess = delta * zcfg.get("hvac_kw_per_degree", 0) * span_hours
                weekly = kwh_excess * cfg["rates"]["energy_rate_per_kwh"]
                findings.append(Finding(
                    "hvac_waste", zone, weekly, weekly * 52,
                    f"{zone}: avg {t:.1f}C vs {setpoint}C setpoint "
                    f"-> ~{kwh_excess:.0f} kWh/wk excess"))

        if v_max is not None and v_max > cfg["thresholds"]["vibration_anomaly_alert"]:
            ecfg = zcfg.get("equipment", {})
            p_fail = cfg["rates"].get("anomaly_to_failure_probability", 0)
            downtime_hrs = ecfg.get("downtime_hours_per_failure", 0)
            cost_per_hr = ecfg.get("downtime_cost_per_hour", 0)
            weekly = p_fail * downtime_hrs * cost_per_hr
            if weekly:
                findings.append(Finding(
                    "predictive_maintenance", zone, weekly, weekly * 52,
                    f"{zone}: peak anomaly score {v_max:.2f} this week (audible-band, D14) "
                    f"-> est downtime-avoided value"))
    return findings


def main():
    cfg = load_config(CONFIG_PATH)
    conn = sqlite3.connect(DB_PATH)
    span = observed_span_minutes(conn)

    findings = []
    findings += labor_space_findings(conn, cfg, span)
    findings += chokepoint_findings(conn, cfg, span)
    findings += env_findings(conn, cfg, span)
    findings.sort(key=lambda f: f.annual_dollars, reverse=True)

    print(f"Observed span: {span} minutes ({span/1440:.1f} days)")
    print(f"Annualized at observed rate (x52). Diagnostic snapshot, not a model.\n")

    print("Top 3 (annualized):")
    for f in findings[:3]:
        print(f"  ${f.annual_dollars:,.0f}/yr  [{f.category}] {f.detail}")

    print("\nAll findings:")
    for f in findings:
        print(f"  ${f.weekly_dollars:,.0f}/wk  ${f.annual_dollars:,.0f}/yr  "
              f"[{f.category}] {f.detail}")

    conn.close()


if __name__ == "__main__":
    main()
