def generate_report(findings, score):

    critical = 0
    high = 0
    medium = 0
    low = 0

    for f in findings:

        severity = f["severity"].upper()

        if severity == "CRITICAL":
            critical += 1

        elif severity == "HIGH":
            high += 1

        elif severity == "MEDIUM":
            medium += 1

        elif severity == "LOW":
            low += 1

    report = {
        "executive_summary": {
            "security_score": score,
            "total_findings": len(findings),
            "critical_risks": critical,
            "high_risks": high,
            "medium_risks": medium,
            "low_risks": low
        }
    }

    return report