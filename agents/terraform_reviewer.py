import os
import sys
import requests
from openai import OpenAI, RateLimitError, APIError, AuthenticationError

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ["GITHUB_TOKEN"]
pr_number = os.environ["PR_NUMBER"]
openai_key = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=openai_key)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

def post_comment(message):
    requests.post(
        comment_url,
        headers=headers,
        json={"body": message},
        timeout=30
    )

files_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
files = requests.get(files_url, headers=headers, timeout=30).json()

terraform_changes = []

for file in files:
    filename = file.get("filename", "")
    if filename.endswith(".tf"):
        terraform_changes.append(
            f"File: {filename}\nPatch:\n{file.get('patch', 'No patch available')}"
        )

if not terraform_changes:
    post_comment(
        "## AI Terraform Review\n\n"
        "No Terraform files were changed in this pull request."
    )
    print("No Terraform files changed.")
    sys.exit(0)

prompt = f"""
You are an AI Terraform security reviewer.

Review these Terraform changes.

Focus on:
- Public access
- Open security groups
- Weak IAM permissions
- Missing encryption
- Missing tagging
- Production deployment risk
- Recommended remediation

Terraform changes:
{chr(10).join(terraform_changes)}
"""

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    review = response.output_text

    post_comment(f"## AI Terraform Review\n\n{review}")

    print("AI Terraform Review posted successfully.")

except RateLimitError:
    post_comment(
        "## AI Terraform Review\n\n"
        "The Terraform AI review could not run because the OpenAI API quota or billing limit was reached. "
        "Please check OpenAI billing, usage limits, or available credits, then rerun the workflow."
    )
    print("OpenAI quota or rate limit reached.")
    sys.exit(0)

except AuthenticationError:
    post_comment(
        "## AI Terraform Review\n\n"
        "The Terraform AI review could not run because the OpenAI API key is invalid or missing. "
        "Please verify the OPENAI_API_KEY GitHub Actions secret."
    )
    print("OpenAI authentication failed.")
    sys.exit(1)

except APIError as error:
    post_comment(
        "## AI Terraform Review\n\n"
        f"The Terraform AI review could not run because of an OpenAI API error: {error}"
    )
    print(f"OpenAI API error: {error}")
    sys.exit(1)
