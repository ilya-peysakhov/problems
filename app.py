import streamlit as st
import requests

def fetch_issues(name):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": st.secrets["GEMINI_API_KEY"]
    }

    prompt = (
        f"List any known legal or problematic issues involving {name}. "
        "Provide each issue with a date and short description. "
        "Use JSON format like this:\n"
        "[\n"
        "  {\"date\": \"YYYY-MM-DD\", \"description\": \"...\", \"severity\": \"low|medium|high\"},\n"
        "  ...\n"
        "]"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        st.error(f"Gemini API error {response.status_code}: {response.text}")
        return []

    try:
        text_output = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        # Try to parse the result as JSON
        import json
        issues = json.loads(text_output)
        return issues
    except Exception as e:
        st.error("Could not parse response from Gemini. Try again or check the prompt format.")
        return []
