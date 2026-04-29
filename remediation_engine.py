def generate_remediation(f):

    remediation = f"""
CyberClinic AI Remediation Recommendation

Issue: {f.get('issue')}
Service: {f.get('service')}
Severity: {f.get('severity')}

Recommended Actions:

1. Review the configuration of the affected service.
2. Apply security best practices and least-privilege access.
3. Disable any public or unnecessary access.
4. Enable monitoring and logging.
5. Ensure the configuration aligns with HIPAA and NIST security standards.

CyberClinic Security Guidance:
Implement continuous monitoring and periodic compliance scans to prevent recurrence.
"""

    return remediation