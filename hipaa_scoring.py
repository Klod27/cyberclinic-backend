from hipaa_questions import hipaa_questions

SEVERITY_WEIGHTS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 2,
    "LOW": 1
}


def normalize_answer(value):
    """
    Supports both formats:
    - "Yes"
    - {"answer": "Yes", "weight": 5, "category": "Administrative"}
    """
    if not value:
        return "no"

    if isinstance(value, dict):
        value = value.get("answer", "no")

    return str(value).strip().lower()


def get_weight(q):
    severity = (q.get("severity") or "MEDIUM").upper()
    base_weight = q.get("weight", 1)
    severity_weight = SEVERITY_WEIGHTS.get(severity, 2)
    return base_weight * severity_weight


def calculate_score(answers):
    total_weight = 0
    earned_weight = 0

    for q in hipaa_questions:
        qid = q.get("id")
        weight = get_weight(q)
        total_weight += weight

        answer = normalize_answer(answers.get(qid))

        if answer == "yes":
            earned_weight += weight
        elif answer == "partial":
            earned_weight += weight * 0.5

    if total_weight == 0:
        return 0

    return round((earned_weight / total_weight) * 100, 2)


def calculate_category_scores(answers):
    categories = {}

    for q in hipaa_questions:
        category = q.get("category", "Other")
        qid = q.get("id")
        weight = get_weight(q)

        if category not in categories:
          categories[category] = {"earned": 0, "total": 0}

        categories[category]["total"] += weight

        answer = normalize_answer(answers.get(qid))

        if answer == "yes":
            categories[category]["earned"] += weight
        elif answer == "partial":
            categories[category]["earned"] += weight * 0.5

    return {
        cat: round((values["earned"] / values["total"]) * 100, 2)
        if values["total"] else 0
        for cat, values in categories.items()
    }


def determine_risk(score):
    if score >= 90:
        return "LOW RISK"
    elif score >= 75:
        return "MODERATE RISK"
    elif score >= 60:
        return "HIGH RISK"
    return "CRITICAL RISK"


def determine_maturity(score):
    if score >= 90:
        return "Optimized"
    elif score >= 75:
        return "Managed"
    elif score >= 60:
        return "Defined"
    elif score >= 40:
        return "Developing"
    return "Initial"


def calculate_risk_breakdown(answers):
    breakdown = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for q in hipaa_questions:
        severity = (q.get("severity") or "MEDIUM").upper()
        answer = normalize_answer(answers.get(q.get("id")))

        if answer == "no":
            breakdown[severity] += 1

    return breakdown