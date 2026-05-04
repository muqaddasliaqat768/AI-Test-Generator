import os
import requests
import sys
from github import Github, Auth

# 1. Configuration
SOURCE_REPO_NAME = "schoolgram/schoolgram-web"  # Update this!
GITHUB_TOKEN = os.getenv('EXTERNAL_REPO_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ISSUE_ID_STR = os.getenv('ISSUE_ID')

def get_ai_test_cases(title, body):
    if not GROQ_API_KEY:
        return "❌ Error: GROQ_API_KEY is missing."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    # Updated Prompt for Positive/Negative/Edge Cases
    prompt = f"""
    Act as a Senior QA Automation Engineer. Based on the GitHub Issue below, 
    generate a list of high-level Use Cases.

    STRICT FORMATTING RULES:
    1. Header: "### 🤖 AI-Generated Use Cases"
    2. Sub-header: "UseCases:"
    3. Group into three sections: "Positive Cases", "Negative Cases", and "Edge Cases".
    4. Format every case as: Check "[Brief description of the scenario]"
    5. Be concise. No steps, no preconditions, no expected results.
    6. End with a single line: "**Cross-Browser Testing**"

    TICKET TITLE: {title}
    TICKET DESCRIPTION: {body}
    """

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1 # Keep it low for consistent formatting
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ AI Generation Failed: {str(e)}"

if __name__ == "__main__":
    try:
        if not GITHUB_TOKEN or not ISSUE_ID_STR:
            print("❌ Error: Missing GITHUB_TOKEN or ISSUE_ID.")
            sys.exit(1)

        print(f"Connecting to: {SOURCE_REPO_NAME}")
        
        # New Auth Method (Stable)
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        
        repo = g.get_repo(SOURCE_REPO_NAME)
        issue = repo.get_issue(number=int(ISSUE_ID_STR))
        
        print(f"Generating tests for Ticket #{ISSUE_ID_STR}...")
        test_results = get_ai_test_cases(issue.title, issue.body)
        
        print("Posting comment...")
        issue.create_comment(test_results)
        
        print(f"✓ Success: Use cases posted to {SOURCE_REPO_NAME} Issue #{ISSUE_ID_STR}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        sys.exit(1)
