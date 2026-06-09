import os
import requests
from openai import OpenAI

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ["GITHUB_TOKEN"]
pr_number = os.environ["PR_NUMBER"]
openai_key = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=openai_key)

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

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

response = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt
)

review = response.output_text

comment_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

requests.post(
    comment_url,
    headers=headers,
    json={"body": f"## AI Pull Request Review\n\n{review}"},
    timeout=30
)

print("AI Pull Request Review posted successfully.")
