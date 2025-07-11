import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

# -------------------------
# Config from Streamlit secrets
# -------------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# -------------------------
# Helper functions
# -------------------------
def fetch_issues(name):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    prompt = (
        f"List any known legal or problematic issues involving {name}. "
        "Provide each issue with a date and short description. "
        "Respond ONLY with valid JSON in the following format. Do not include any commentary, titles, or markdown:\n\n"
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

    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        st.error(f"Gemini API error {response.status_code}: {response.text}")
        return []

    try:
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        # st.subheader("🧪 Raw Gemini Response")
        # st.code(raw_text, language="json")

        # Attempt to extract JSON from markdown or extra lines
        # Strip markdown and any wrapping code block
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.strip("```").strip()

        # Parse the JSON
        issues = json.loads(raw_text)
        return issues
    except Exception as e:
        st.error(f"❌ Could not parse response from Gemini: {e}")
        return []

def preprocess_issues(issues):
    df = pd.DataFrame(issues)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["count"] = 1
    return df
    
def assess_risk(issues):
    count = len(issues)

    high_severity = sum(1 for i in issues if i.get("severity", "").lower() == "high")

    if count == 0:
        return "🟢 Green", "No known issues."
    elif high_severity > 0 or count >= 5:
        return "🔴 Red", "Multiple or severe issues detected."
    else:
        return "🟡 Yellow", "Some minor issues found."
# -------------------------
# Streamlit App
# -------------------------
st.set_page_config(page_title="Problem Profile Analyzer", layout="wide")
st.title("🕵️ Problem Profile Analyzer")
st.caption("Enter a name and click the button to analyze their legal/problematic history using Gemini AI.")

name = st.text_input("🔍 Name to investigate", placeholder="e.g., John Doe")
run_check = st.button("Analyze")

if run_check and name:
    with st.spinner("Querying Gemini..."):
        issues = fetch_issues(name)

    if issues:
        df = preprocess_issues(issues)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Issues", len(issues))

        with col2:           
            risk_color, message = assess_risk(issues)
            st.subheader("🚨 Risk Assessment")
            st.markdown(f"### {risk_color}\n{message}")
         
        
        st.subheader("📊 Issue Timeline")
        fig = px.bar(
            df,
            x="date",
            y="count",
            text="description",
            hover_data=["description", "severity"],
            labels={"count": "Issue"},
            title="History of Issues",
        )
        fig.update_traces(textposition="inside")
        fig.update_layout(xaxis_title="Date", yaxis_title="Issue Count")
        st.plotly_chart(fig, use_container_width=True)

        with col2:
    else:
        st.info("✅ No issues found or no structured data returned.")

elif run_check and not name:
    st.warning("Please enter a name before analyzing.")
