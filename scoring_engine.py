def calculate_compliance_score(findings):

    total = len(findings)

    if total == 0:
        return 100

    failed = len([f for f in findings if f["status"] == "FAIL"])

    passed = total - failed

    score = int((passed / total) * 100)

    return score