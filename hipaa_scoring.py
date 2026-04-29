from hipaa_questions import hipaa_questions


# ----------------------------------
# SEVERITY WEIGHTS (ENTERPRISE GRADE)
# ----------------------------------
SEVERITY_WEIGHTS = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 2,
    "LOW": 1
}


# ----------------------------------
# NORMALIZE ANSWERS
# ----------------------------------
def normalize_answer(value):
    if not value:
        return "no"
    return str(value).strip().lower()


# ----------------------------------
# GET QUESTION WEIGHT (SMART)
# ----------------------------------
def get_weight(q):
    severity = (q.get("severity") or "MEDIUM").upper()
    base_weight = q.get("weight", 1)

    severity_weight = SEVERITY_WEIGHTS.get(severity, 2)

    return base_weight * severity_weight


# ----------------------------------
# TOTAL SCORE (ADVANCED WEIGHTED)
# ----------------------------------
def calculate_score(answers):

    total_weight = 0
    earned_weight = 0

    for q in hipaa_questions:

        weight = get_weight(q)
        total_weight += weight

        answer = normalize_answer(answers.get(q["id"]))

        if answer == "yes":
            earned_weight += weight

        elif answer == "partial":
            earned_weight += weight * 0.5  # partial credit

    if total_weight == 0:
        return 0

    return round((earned_weight / total_weight) * 100, 2)


# ----------------------------------
# CATEGORY SCORES (SMART WEIGHTED)
# ----------------------------------
def calculate_category_scores(answers):

    categories = {}

    for q in hipaa_questions:

        category = q.get("category", "Other")
        weight = get_weight(q)

        if category not in categories:
            categories[category] = {
                "earned": 0,
                "total": 0
            }

        categories[category]["total"] += weight

        answer = normalize_answer(answers.get(q["id"]))

        if answer == "yes":
            categories[category]["earned"] += weight

        elif answer == "partial":
            categories[category]["earned"] += weight * 0.5

    results = {}

    for cat, values in categories.items():

        total = values["total"]
        earned = values["earned"]

        if total == 0:
            results[cat] = 0
        else:
            results[cat] = round((earned / total) * 100, 2)

    return results


# ----------------------------------
# RISK CLASSIFICATION (IMPROVED)
# ----------------------------------
def determine_risk(score):

    if score >= 90:
        return "LOW RISK"

    elif score >= 75:
        return "MODERATE RISK"

    elif score >= 60:
        return "HIGH RISK"

    else:
        return "CRITICAL RISK"


# ----------------------------------
# COMPLIANCE MATURITY LEVEL (NEW 🔥)
# ----------------------------------
def determine_maturity(score):

    if score >= 90:
        return "Optimized"

    elif score >= 75:
        return "Managed"

    elif score >= 60:
        return "Defined"

    elif score >= 40:
        return "Developing"

    else:
        return "Initial"


# ----------------------------------
# RISK BREAKDOWN (FOR REPORTS)
# ----------------------------------
def calculate_risk_breakdown(answers):

    breakdown = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for q in hipaa_questions:

        severity = (q.get("severity") or "MEDIUM").upper()
        answer = normalize_answer(answers.get(q["id"]))

        if answer == "no":
            breakdown[severity] += 1

    return breakdown