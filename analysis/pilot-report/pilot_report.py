"""pilot_report.py - generates the one-week pilot diagnostic PDF.

Wraps cost_model.py's ranked findings + a heatmap render into the client-facing
deliverable. Reads telemetry.db + client_config.yaml from ../data-to-dollars/.
Run synthetic_data.py first if telemetry.db does not exist yet (no hardware needed).

Output: pilot_report.pdf in this directory.
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
)

# ../data-to-dollars holds the shared db/config and the finding functions
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data-to-dollars")
sys.path.insert(0, DATA_DIR)
from cost_model import (  # noqa: E402
    load_config, observed_span_minutes, labor_space_findings,
    chokepoint_findings, env_findings, q,
)

DB_PATH = os.path.join(DATA_DIR, "telemetry.db")
CONFIG_PATH = os.path.join(DATA_DIR, "client_config.yaml")
HEATMAP_PNG = os.path.join(os.path.dirname(__file__), "heatmap.png")
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), "pilot_report.pdf")


def render_heatmap(conn, out_path):
    """Render the heatmap table as a relative-density image. No floor-plan
    overlay yet (open gap: real floorplan.png + homography per [[07 Dashboard]]).
    """
    rows = q(conn, "SELECT gx, gy, SUM(weight) FROM heatmap GROUP BY gx, gy")
    if not rows:
        return None

    max_gx = max(r[0] for r in rows) + 1
    max_gy = max(r[1] for r in rows) + 1
    grid = np.zeros((max_gy, max_gx))
    for gx, gy, w in rows:
        grid[gy, gx] = w

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(grid, origin="lower", cmap="inferno", aspect="auto")
    ax.set_title("Occupancy Density (relative, anonymized aggregates only)")
    ax.set_xlabel("floor grid X")
    ax.set_ylabel("floor grid Y")
    fig.colorbar(im, ax=ax, label="relative dwell weight")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def build_findings(conn, cfg):
    span = observed_span_minutes(conn)
    findings = []
    findings += labor_space_findings(conn, cfg, span)
    findings += chokepoint_findings(conn, cfg, span)
    findings += env_findings(conn, cfg, span)
    findings.sort(key=lambda f: f.annual_dollars, reverse=True)
    return findings, span


def main():
    cfg = load_config(CONFIG_PATH)
    conn = sqlite3.connect(DB_PATH)

    findings, span_minutes = build_findings(conn, cfg)
    heatmap_path = render_heatmap(conn, HEATMAP_PNG)

    client = cfg.get("client", {})
    client_name = client.get("name", "[Client name]")
    site_name = client.get("site", "[Site name]")

    end_date = datetime.now()
    start_date = end_date - timedelta(minutes=span_minutes)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=22)
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8,
                            textColor=colors.grey)

    story = []

    # --- Cover ---
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Warehouse Movement &amp; Environmental Diagnostic",
                            title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Client: {client_name}", h2))
    story.append(Paragraph(f"Site: {site_name}", h2))
    story.append(Paragraph(
        f"Observation period: {start_date.strftime('%b %d')} - "
        f"{end_date.strftime('%b %d, %Y')} "
        f"({span_minutes/1440:.1f} days)", h2))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "Prepared by Sentry Trade. Anonymized movement and environmental "
        "telemetry only - no recognizable footage was recorded or stored.",
        body))
    story.append(PageBreak())

    # --- Executive summary ---
    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(
        "Sensors were installed for one week to quantify where labor time, "
        "space, and machine condition translate into avoidable cost. Figures "
        "below are annualized at the observed weekly rate - this is a "
        "diagnostic snapshot, not a predictive model. The top opportunities "
        "identified:", body))
    story.append(Spacer(1, 0.15 * inch))

    if findings:
        for i, f in enumerate(findings[:3], 1):
            story.append(Paragraph(
                f"{i}. <b>${f.annual_dollars:,.0f}/yr</b> - {f.detail}", body))
        total_top3 = sum(f.annual_dollars for f in findings[:3])
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f"<b>Combined top-3 annualized opportunity: "
            f"${total_top3:,.0f}/yr</b>", body))
    else:
        story.append(Paragraph(
            "No findings exceeded the configured thresholds this period. "
            "(Placeholder report run against synthetic/test data - check "
            "client_config.yaml thresholds and zone definitions.)", body))
    story.append(PageBreak())

    # --- Heatmap ---
    story.append(Paragraph("Occupancy Heatmap", h2))
    if heatmap_path:
        story.append(Image(heatmap_path, width=6 * inch, height=4 * inch))
    else:
        story.append(Paragraph("No heatmap data available for this period.", body))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Density is shown on a relative scale across the monitored zones. "
        "No video, images, or worker-identifiable data were captured at any "
        "point - all processing happens on-device and only anonymized counts "
        "and positions are recorded.", small))
    story.append(PageBreak())

    # --- Full findings table ---
    story.append(Paragraph("All Findings", h2))
    if findings:
        table_data = [["Category", "Zone / Line", "Weekly $", "Annual $", "Detail"]]
        for f in findings:
            table_data.append([
                Paragraph(f.category.replace("_", " "), small),
                Paragraph(f.zone, small),
                f"${f.weekly_dollars:,.0f}", f"${f.annual_dollars:,.0f}",
                Paragraph(f.detail, small),
            ])
        tbl = Table(table_data, colWidths=[1.6*inch, 0.85*inch, 0.65*inch,
                                            0.65*inch, 2.0*inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph("No findings to report.", body))
    story.append(PageBreak())

    # --- Methodology & assumptions ---
    story.append(Paragraph("Methodology &amp; Assumptions", h2))
    story.append(Paragraph(
        "Findings are derived from anonymized aggregates: per-zone person-seconds "
        "and unique-visitor counts, chokepoint crossing counts, and per-zone "
        "temperature/humidity/vibration-anomaly scores. Raw video, audio, and "
        "identity data are never stored or transmitted - only these aggregates "
        "exist. Vibration anomaly scoring covers the audible band only and "
        "indicates 'worth a maintenance look', not a confirmed fault.", body))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Rates and thresholds used for this report:", body))
    rates = cfg.get("rates", {})
    thresholds = cfg.get("thresholds", {})
    rate_rows = [["Parameter", "Value"]]
    for k, v in rates.items():
        rate_rows.append([k.replace("_", " "), str(v)])
    for k, v in thresholds.items():
        rate_rows.append([k.replace("_", " ") + " (threshold)", str(v)])
    rtbl = Table(rate_rows, colWidths=[3.5*inch, 1.5*inch])
    rtbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(rtbl)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "These values are placeholders pending a client intake conversation "
        "and should be replaced with the client's actual fully-loaded labor "
        "rate, space cost, energy rate, and equipment downtime costs.", small))

    doc = SimpleDocTemplate(OUTPUT_PDF, pagesize=letter,
                             topMargin=0.75*inch, bottomMargin=0.75*inch)
    doc.build(story)
    conn.close()
    print(f"wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
