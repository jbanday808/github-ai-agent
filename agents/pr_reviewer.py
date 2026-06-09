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

changed_files = []

for file in files:
    changed_files.append(
        f"File: {file.get('filename')}\nPatch:\n{file.get('patch', 'No patch available')}"
    )

prompt = f"""
You are an AI pull request reviewer.

Review the following pull request changes.

Focus on:
- Code quality
- Security risks
- Test coverage
- Deployment risk
- Clear recommendations

Changes:
{chr(10).join(changed_files)}
"""

try:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    review = response.output_text

    post_comment(f"## AI Pull Request Review\n\n{review}")

    print("AI Pull Request Review posted successfully.")

except RateLimitError:
    post_comment(
        "## AI Pull Request Review\n\n"
        "The AI review could not run because the OpenAI API quota or billing limit was reached. "
        "Please check OpenAI billing, usage limits, or available credits, then rerun the workflow."
    )
    print("OpenAI quota or rate limit reached.")
    sys.exit(0)

except AuthenticationError:
    post_comment(
        "## AI Pull Request Review\n\n"
        "The AI review could not run because the OpenAI API key is invalid or missing. "
        "Please verify the OPENAI_API_KEY GitHub Actions secret."
    )
    print("OpenAI authentication failed.")
    sys.exit(1)

except APIError as error:
    post_comment(
        "## AI Pull Request Review\n\n"
        f"The AI review could not run because of an OpenAI API error: {error}"
    )
    print(f"OpenAI API error: {error}")
    sys.exit(1)
