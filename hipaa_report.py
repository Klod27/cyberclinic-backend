from datetime import datetime


def generate_hipaa_report(results):

    score = results.get("score", 0)

    if score >= 90:
        risk = "LOW RISK"
    elif score >= 70:
        risk = "MODERATE RISK"
    elif score >= 50:
        risk = "HIGH RISK"
    else:
        risk = "CRITICAL RISK"

    return {
        "report_title": "CyberClinic HIPAA Security Risk Assessment",
        "generated_on": datetime.utcnow().strftime("%Y-%m-%d"),

        "overall_score": score,
        "risk_level": risk,

        "executive_summary": build_executive_summary(score),

        "category_scores": results.get("category_scores", {}),

        "top_risks": get_top_risks(results.get("findings", [])),

        "findings": results.get("findings", []),

        "remediation_plan": build_remediation_plan(results.get("findings", [])),

        "compliance_status": build_compliance_status(score)
    }


# ----------------------------------
# EXECUTIVE SUMMARY
# ----------------------------------
def build_executive_summary(score):

    if score >= 85:
        status = "LOW RISK"
    elif score >= 60:
        status = "MODERATE RISK"
    else:
        status = "HIGH RISK"

    return f"""
Your organization is currently classified as {status} with a compliance score of {score}%.

Several gaps were identified across administrative, technical, and physical safeguards.

Immediate remediation is recommended to reduce exposure to HIPAA violations, financial penalties, and reputational damage.
"""


# ----------------------------------
# TOP RISKS
# ----------------------------------
def get_top_risks(findings):
    critical = [f for f in findings if f.get("risk_level") == "CRITICAL"]
    return critical[:5]


# ----------------------------------
# REMEDIATION PLAN
# ----------------------------------
def build_remediation_plan(findings):

    plan = []

    for f in findings:
        if f.get("risk_level") in ["CRITICAL", "HIGH"]:
            plan.append({
                "issue": f.get("title"),
                "action": f.get("recommendation"),
                "priority": f.get("risk_level")
            })

    return plan


# ----------------------------------
# COMPLIANCE STATUS
# ----------------------------------
def build_compliance_status(score):

    if score >= 90:
        return "Compliant"
    elif score >= 70:
        return "Partially Compliant"
    else:
        return "Non-Compliant"