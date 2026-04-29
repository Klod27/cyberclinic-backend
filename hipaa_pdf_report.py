# ----------------------------------
# CYBERCLINIC ENTERPRISE PDF REPORT
# ----------------------------------

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

import os
from datetime import datetime
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ----------------------------------
# CONFIG
# ----------------------------------
LOGO_PATH = "assets/logo.png"


# ----------------------------------
# UTIL
# ----------------------------------
def safe(val):
    return "" if val is None else str(val)


def get_color(score):
    if score >= 85:
        return "#16a34a"
    elif score >= 70:
        return "#f59e0b"
    return "#dc2626"


# ----------------------------------
# CHARTS
# ----------------------------------
def generate_score_chart(score):
    fig, ax = plt.subplots(figsize=(6, 2))

    ax.barh(["Compliance Score"], [score], color=get_color(score))
    ax.set_xlim(0, 100)

    ax.text(score + 1, 0, f"{score}%", va="center")

    ax.spines[['top', 'right', 'left']].set_visible(False)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, bbox_inches='tight')
    plt.close()

    return tmp.name


def generate_category_chart(scores):
    fig, ax = plt.subplots(figsize=(6, 3))

    names = list(scores.keys())
    values = list(scores.values())

    ax.bar(names, values, color=[get_color(v) for v in values])
    ax.set_ylim(0, 100)

    for i, v in enumerate(values):
        ax.text(i, v + 2, f"{int(v)}%", ha='center')

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(tmp.name, bbox_inches='tight')
    plt.close()

    return tmp.name


# ----------------------------------
# EXECUTIVE SUMMARY
# ----------------------------------
def build_summary(score):

    if score >= 85:
        level = "LOW RISK"
    elif score >= 60:
        level = "MODERATE RISK"
    else:
        level = "HIGH RISK"

    exposure = (100 - score) * 500

    return f"""
Your organization is classified as <b>{level}</b> with a compliance score of <b>{score}%</b>.

Estimated financial exposure is approximately <b>${exposure:,}</b> based on current compliance gaps.

Failure to address identified issues may result in regulatory fines, legal liability, and loss of patient trust.

Immediate remediation is strongly recommended.
"""


# ----------------------------------
# MAIN PDF GENERATOR
# ----------------------------------
def generate_pdf(data, file_path="reports/hipaa_report.pdf"):

    os.makedirs("reports", exist_ok=True)

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    content = []

    score = data.get("score", 0)
    findings = data.get("findings", [])
    category_scores = data.get("category_scores", {})
    org = data.get("organization", "Unknown")

    # ======================================
    # COVER PAGE
    # ======================================
    if os.path.exists(LOGO_PATH):
        content.append(Image(LOGO_PATH, width=150, height=50))

    content.append(Spacer(1, 40))

    content.append(Paragraph(
        "<b>CyberClinic Compliance Report</b>", styles["Title"]
    ))

    content.append(Spacer(1, 20))

    content.append(Paragraph(
        "HIPAA Security & Risk Assessment", styles["Heading2"]
    ))

    content.append(Spacer(1, 30))

    content.append(Paragraph(f"<b>Organization:</b> {org}", styles["Normal"]))
    content.append(Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}", styles["Normal"]))

    content.append(Spacer(1, 60))

    content.append(Paragraph(
        "<i>Confidential – Internal Use Only</i>", styles["Italic"]
    ))

    content.append(PageBreak())

    # ======================================
    # EXECUTIVE SUMMARY
    # ======================================
    content.append(Paragraph("<b>Executive Summary</b>", styles["Heading1"]))
    content.append(Spacer(1, 15))
    content.append(Paragraph(build_summary(score), styles["Normal"]))
    content.append(Spacer(1, 20))

    # SCORE CHART
    try:
        chart = generate_score_chart(score)
        content.append(Image(chart, width=420, height=120))
    except:
        pass

    content.append(PageBreak())

    # ======================================
    # CATEGORY PERFORMANCE
    # ======================================
    if category_scores:
        content.append(Paragraph("<b>Category Performance</b>", styles["Heading1"]))
        content.append(Spacer(1, 15))

        try:
            chart = generate_category_chart(category_scores)
            content.append(Image(chart, width=420, height=220))
            content.append(Spacer(1, 20))
        except:
            pass

        table_data = [["Category", "Score"]]
        for k, v in category_scores.items():
            table_data.append([k, f"{v}%"])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey)
        ]))

        content.append(table)
        content.append(PageBreak())

    # ======================================
    # FINDINGS
    # ======================================
    content.append(Paragraph("<b>Top Risk Findings</b>", styles["Heading1"]))
    content.append(Spacer(1, 15))

    for f in findings[:10]:
        content.append(Paragraph(
            f"<b>{safe(f.get('title') or f.get('issue'))}</b>",
            styles["Heading3"]
        ))

        content.append(Paragraph(
            f"<b>Risk Level:</b> {safe(f.get('risk_level'))}",
            styles["Normal"]
        ))

        content.append(Paragraph(
            f"<b>Impact:</b> {safe(f.get('impact'))}",
            styles["Normal"]
        ))

        content.append(Paragraph(
            f"<b>Business Impact:</b> {safe(f.get('business_impact'))}",
            styles["Normal"]
        ))

        content.append(Paragraph(
            f"<b>Recommendation:</b> {safe(f.get('recommendation'))}",
            styles["Normal"]
        ))

        content.append(Spacer(1, 15))

    content.append(PageBreak())

    # ======================================
    # CONCLUSION
    # ======================================
    content.append(Paragraph("<b>Conclusion</b>", styles["Heading1"]))
    content.append(Spacer(1, 15))

    content.append(Paragraph(
        "This report provides a structured overview of compliance risks and recommended actions. "
        "Organizations should act promptly to mitigate exposure and ensure regulatory compliance.",
        styles["Normal"]
    ))

    content.append(Spacer(1, 30))

    content.append(Paragraph(
        "CyberClinic AI Compliance Engine", styles["Italic"]
    ))

    # BUILD PDF
    doc.build(content)

    return file_path