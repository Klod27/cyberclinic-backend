import boto3


def scan_s3():

    findings = []

    s3 = boto3.client("s3")

    buckets = s3.list_buckets()["Buckets"]

    for bucket in buckets:

        name = bucket["Name"]

        try:

            acl = s3.get_bucket_acl(Bucket=name)

            for grant in acl["Grants"]:

                grantee = grant.get("Grantee", {})

                if grantee.get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers":

                    findings.append({
                        "issue": "S3 Bucket Public Access",
                        "service": "AWS S3",
                        "severity": "HIGH",
                        "resource": name
                    })

        except Exception:
            pass

    return findings



def scan_iam():

    findings = []

    iam = boto3.client("iam")

    policies = iam.list_policies(Scope="Local")["Policies"]

    for policy in policies:

        name = policy["PolicyName"]

        if "*" in name:

            findings.append({
                "issue": "Overly Permissive IAM Policy",
                "service": "AWS IAM",
                "severity": "MEDIUM",
                "resource": name
            })

    return findings



def run_aws_scan():

    findings = []

    findings.extend(scan_s3())
    findings.extend(scan_iam())

    return findings