import os
import sys
from openai import OpenAI, RateLimitError, APIError, AuthenticationError

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

input_file = "compliance/sample/sample-scap-results.xml"
output_file = "compliance/reports/stig-remediation-report.md"

with open(input_file, "r", encoding="utf-8") as file:
    scap_results = file.read()

prompt = f"""
You are an AI STIG compliance analyst supporting a DoD-style Linux environment.

Review the following SCAP/STIG results.

Return:
- Executive summary
- Failed controls
- Severity level
- Risk explanation
- Recommended remediation
- Validation command
- RMF impact
- Change control notes

SCAP/STIG Results:
{scap_results}
"""

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    report = response.output_text

except RateLimitError:
    report = """
## AI STIG Compliance Report

The STIG review could not run because the OpenAI API quota or billing limit was reached.

### Recommended Action
Check OpenAI billing, usage limits, or available credits, then rerun the workflow.
"""

except AuthenticationError:
    print("OpenAI authentication failed. Check OPENAI_API_KEY.")
    sys.exit(1)

except APIError as error:
    print(f"OpenAI API error: {error}")
    sys.exit(1)

os.makedirs("compliance/reports", exist_ok=True)

with open(output_file, "w", encoding="utf-8") as file:
    file.write("# AI STIG Remediation Report\n\n")
    file.write(report)

print(f"STIG remediation report generated: {output_file}")
