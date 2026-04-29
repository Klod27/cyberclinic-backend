from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# ----------------------------------
# LOAD ENV VARIABLES
# ----------------------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is not set. Check your .env file.")

client = OpenAI(api_key=api_key)


# ----------------------------------
# FALLBACK ENGINE (CRITICAL)
# ----------------------------------

def fallback_recommendations(issues):
    """
    If AI fails, we still return usable recommendations.
    """

    fallback = []

    for issue in issues:
        fallback.append({
            "issue": issue,
            "recommendation": f"Review and implement appropriate safeguards for: {issue}",
            "hipaa_reference": "Refer to HIPAA Security Rule",
            "priority": "High"
        })

    return fallback


# ----------------------------------
# GENERATE AI RECOMMENDATIONS
# ----------------------------------

def generate_recommendations(risk_data):
    """
    Always returns a LIST:
    [
        {
            "issue": "...",
            "recommendation": "...",
            "hipaa_reference": "...",
            "priority": "High | Medium | Low"
        }
    ]
    """

    try:
        issues = risk_data.get("issues", [])

        # ✅ Ensure valid input
        if not isinstance(issues, list) or len(issues) == 0:
            return []

        # ----------------------------------
        # PROMPT (UPGRADED)
        # ----------------------------------

        prompt = f"""
        You are a HIPAA compliance and cybersecurity expert.

        Analyze the following compliance issues:
        {issues}

        For EACH issue:
        - Provide a clear remediation action
        - Assign a priority (High, Medium, Low)
        - Include the most relevant HIPAA Security Rule reference if possible

        Return ONLY valid JSON in this format:

        [
          {{
            "issue": "...",
            "recommendation": "...",
            "hipaa_reference": "...",
            "priority": "High | Medium | Low"
          }}
        ]
        """

        # ----------------------------------
        # OPENAI CALL
        # ----------------------------------

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON. No explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()

        # ----------------------------------
        # PARSE RESPONSE SAFELY
        # ----------------------------------

        try:
            parsed = json.loads(content)

            if isinstance(parsed, list):
                return parsed

            if isinstance(parsed, dict):
                if "data" in parsed:
                    return parsed["data"]
                return [parsed]

            return fallback_recommendations(issues)

        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed:", content)
            return fallback_recommendations(issues)

    except Exception as e:
        print("❌ AI ERROR:", str(e))
        return fallback_recommendations(issues)