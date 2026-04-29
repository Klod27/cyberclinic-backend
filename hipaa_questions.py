hipaa_questions = [

# -------------------------------
# ADMINISTRATIVE SAFEGUARDS
# -------------------------------

{"id":"HIPAA-AS-01","category":"Administrative","hipaa_reference":"164.308(a)(1)","question":"Has your organization conducted a HIPAA security risk analysis within the past 12 months?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-AS-02","category":"Administrative","hipaa_reference":"164.308(a)(1)","question":"Do you maintain documented HIPAA security policies and procedures?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-03","category":"Administrative","hipaa_reference":"164.308(a)(5)","question":"Do employees receive HIPAA security awareness training annually?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-04","category":"Administrative","hipaa_reference":"164.308(a)(2)","question":"Is there a designated HIPAA security officer responsible for compliance?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-AS-05","category":"Administrative","hipaa_reference":"164.308(a)(4)","question":"Are user access permissions reviewed periodically?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-06","category":"Administrative","hipaa_reference":"164.308(a)(3)","question":"Are terminated employees immediately removed from system access?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-AS-07","category":"Administrative","hipaa_reference":"164.308(a)(6)","question":"Do you maintain documented incident response procedures?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-08","category":"Administrative","hipaa_reference":"164.308(a)(6)","question":"Are security incidents documented and investigated?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-09","category":"Administrative","hipaa_reference":"164.308(a)(1)","question":"Are risk management plans updated regularly?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-10","category":"Administrative","hipaa_reference":"164.308(b)","question":"Are third-party vendors evaluated for HIPAA compliance?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-11","category":"Administrative","hipaa_reference":"164.308(b)","question":"Do you maintain Business Associate Agreements with all vendors handling PHI?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-AS-12","category":"Administrative","hipaa_reference":"164.308(a)(7)","question":"Do you maintain contingency and disaster recovery plans?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-13","category":"Administrative","hipaa_reference":"164.308(a)(7)","question":"Are data backup procedures documented and tested regularly?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-AS-14","category":"Administrative","hipaa_reference":"164.308(a)(5)","question":"Are phishing awareness and cybersecurity trainings conducted for staff?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-AS-15","category":"Administrative","hipaa_reference":"164.308(a)(8)","question":"Are internal HIPAA compliance audits performed periodically?","weight":4,"severity":"High","answer_type":"yes_no"},

# -------------------------------
# TECHNICAL SAFEGUARDS
# -------------------------------

{"id":"HIPAA-TS-01","category":"Technical","hipaa_reference":"164.312(d)","question":"Is multi-factor authentication enabled for system access?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-TS-02","category":"Technical","hipaa_reference":"164.312(a)(2)(iv)","question":"Is patient data encrypted at rest?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-TS-03","category":"Technical","hipaa_reference":"164.312(e)(1)","question":"Is patient data encrypted during transmission (TLS)?","weight":5,"severity":"Critical","answer_type":"yes_no"},
{"id":"HIPAA-TS-04","category":"Technical","hipaa_reference":"164.312(b)","question":"Are system audit logs maintained for PHI access?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-05","category":"Technical","hipaa_reference":"164.312(d)","question":"Are login attempts limited to prevent brute-force attacks?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-06","category":"Technical","hipaa_reference":"164.312(a)(2)(iii)","question":"Are automatic session timeouts enforced?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-TS-07","category":"Technical","hipaa_reference":"164.312(a)","question":"Are privileged accounts restricted and monitored?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-08","category":"Technical","hipaa_reference":"164.312(a)(2)(iv)","question":"Are backups encrypted?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-09","category":"Technical","hipaa_reference":"164.312(b)","question":"Is intrusion detection or security monitoring deployed?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-10","category":"Technical","hipaa_reference":"164.308(a)(1)","question":"Are system patches and security updates applied regularly?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-11","category":"Technical","hipaa_reference":"164.312(b)","question":"Are audit logs reviewed regularly for suspicious activity?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-12","category":"Technical","hipaa_reference":"164.312(c)(1)","question":"Are mechanisms in place to ensure PHI integrity and detect tampering?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-13","category":"Technical","hipaa_reference":"164.312(e)(1)","question":"Are secure VPNs used for remote access to internal systems?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-TS-14","category":"Technical","hipaa_reference":"164.312(d)","question":"Are strong password policies enforced across systems?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-TS-15","category":"Technical","hipaa_reference":"164.312(b)","question":"Are automated alerts triggered for suspicious login attempts?","weight":4,"severity":"High","answer_type":"yes_no"},

# -------------------------------
# PHYSICAL SAFEGUARDS
# -------------------------------

{"id":"HIPAA-PS-01","category":"Physical","hipaa_reference":"164.310(a)","question":"Is access to server rooms restricted to authorized personnel?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-PS-02","category":"Physical","hipaa_reference":"164.310(b)","question":"Are workstations locked when unattended?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-03","category":"Physical","hipaa_reference":"164.310(d)","question":"Are devices securely disposed of before reuse or disposal?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-PS-04","category":"Physical","hipaa_reference":"164.310(d)","question":"Are mobile devices encrypted?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-PS-05","category":"Physical","hipaa_reference":"164.310(a)","question":"Are facility access logs maintained?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-06","category":"Physical","hipaa_reference":"164.310(d)","question":"Are portable storage devices restricted or encrypted?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-07","category":"Physical","hipaa_reference":"164.310(b)","question":"Are printed patient records stored securely?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-08","category":"Physical","hipaa_reference":"164.310(d)","question":"Are lost or stolen devices reported immediately?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-09","category":"Physical","hipaa_reference":"164.310(d)","question":"Is device inventory maintained?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-PS-10","category":"Physical","hipaa_reference":"164.310(a)","question":"Are security cameras used in sensitive areas?","weight":2,"severity":"Low","answer_type":"yes_no"},

# -------------------------------
# NETWORK / CYBERSECURITY PRACTICES
# -------------------------------

{"id":"HIPAA-EX-01","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Are firewall rules reviewed regularly?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-EX-02","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Are network intrusion alerts monitored?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-EX-03","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Are endpoint protection systems installed on all devices?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-EX-04","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Is vulnerability scanning performed periodically?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-EX-05","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Is network segmentation used to protect sensitive systems?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-EX-06","category":"Network","hipaa_reference":"164.308(a)(1)","question":"Is security logging retained for audit purposes?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-EX-07","category":"Network","hipaa_reference":"164.308(a)(7)","question":"Are disaster recovery exercises performed periodically?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-EX-08","category":"Network","hipaa_reference":"164.312(a)","question":"Is access to patient databases restricted by role?","weight":4,"severity":"High","answer_type":"yes_no"},
{"id":"HIPAA-EX-09","category":"Network","hipaa_reference":"164.308(a)(7)","question":"Are emergency access procedures documented?","weight":3,"severity":"Medium","answer_type":"yes_no"},
{"id":"HIPAA-EX-10","category":"Network","hipaa_reference":"164.308(a)(8)","question":"Are security assessments performed annually?","weight":4,"severity":"High","answer_type":"yes_no"}

]