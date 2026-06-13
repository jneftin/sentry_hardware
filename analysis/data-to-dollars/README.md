# Data-to-Dollars Model (D12)

The analysis layer that turns warehouse telemetry into ranked dollar findings. Design rationale, schema, and the
full walkthrough live in the Obsidian vault: `C:\Brain\Hardware\10 Data-to-Dollars Model.md`.

## Files
- `cost_model.py` - reads `telemetry.db` + `client_config.yaml`, prints ranked weekly/annual findings
- `client_config.yaml` - client-supplied rates, thresholds, zone/line config (placeholder values - replace per client)
- `synthetic_data.py` - generates a week of fake `telemetry.db` for testing without hardware

`telemetry.db` is generated, not committed (see .gitignore).

## Run
```
pip install pyyaml
python synthetic_data.py
python cost_model.py
```

## Status (2026-06-13)
Validated against synthetic data. Found and fixed an AVG-vs-MAX aggregation bug on vibration anomaly scores (D18) -
weekly averaging was hiding daily spike events, which is exactly what the acoustic/vibration hero feature needs to
catch.

## Open items
- Utilization thresholds (0.30 / 0.85) and anomaly_to_failure_probability (0.05) in client_config.yaml are
  placeholders - validate against a real client's numbers.
- env_readings table is not yet written by any real ingest code (mqtt_ingest.py is a separate open gap).
