import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# -------------------------
# Configuration from secrets
# -------------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GEMINI_API_URL = st.secrets["GEMINI_API_URL"]

# -------------------------
# Helper Functions
# -------------------------
def fetch_issues(name):
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    params = {"name": name}
    try:
        response = requests.get(GEMINI_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("issues", [])
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return []

def assess_risk(issues):
    count = len(issues)
    if count == 0:
        return "🟢 Green", "No known issues."
    elif count < 3:
        return "🟡 Yellow", "Some minor issues."
    else:
        return "🔴 Red", "Multiple or severe issues detected."

def preprocess_issues(issues):
    df = pd.DataFrame(issues)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["count"] = 1  # For bar chart
    return df

# -------------------------
# Streamlit App Layout
# -------------------------
st.set_page_config(page_title="Problem Profile Analyzer", layout="wide")
st.title("🕵️ Problem Profile Analyzer")
st.caption("Enter a name to evaluate their public issue history using Gemini AI.")

name = st.text_input("🔍 Name to investigate", placeholder="e.g., John Doe")

if name:
    with st.spinner("Querying Gemini..."):
        issues = fetch_issues(name)

    if issues:
        df = preprocess_issues(issues)

        col1, col2, col3 = st.columns([1, 2, 2])

        with col1:
            st.metric("Total Issues", len(issues))

        with col2:
            st.subheader("📊 Issue Timeline")
            fig = px.bar(
                df,
                x="date",
                y="count",
                hover_data=["description", "severity"],
                text="description",
                labels={"count": "Issue"},
                title="History of Issues",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(xaxis_title="Date", yaxis_title="Issue Count")
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            risk_color, message = assess_risk(issues)
            st.subheader("🚨 Risk Assessment")
            st.markdown(f"### {risk_color}\n{message}")

    else:
        st.info("✅ No issues found for this name.")
