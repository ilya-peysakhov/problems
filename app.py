import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        
        fig = px.line(
            df,
            x="date",
            y="count",
            hover_data=["description", "severity"],
            labels={"count": "Issue Count", "date": "Date"},
            title="📊 History of Issues Over Time",
            height=1000,
            line_shape='spline',  # Smooth curves
            markers=True  # Add markers to data points
        )
        
        # Enhanced styling
        fig.update_traces(
            line=dict(width=4, color='#FF6B6B'),  # Thicker line with vibrant color
            marker=dict(
                size=10,
                color='#4ECDC4',
                line=dict(width=2, color='#FFFFFF'),
                symbol='circle'
            ),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                          '<b>Issue Count:</b> %{y}<br>' +
                          '<b>Description:</b> %{customdata[0]}<br>' +
                          '<b>Severity:</b> %{customdata[1]}<br>' +
                          '<extra></extra>'
        )
        
        # Add text annotations for descriptions
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['count'],
                mode='text',
                text=df['description'],
                textposition="top center",
                textfont=dict(
                    size=11,
                    color='#2C3E50',
                    family="Arial, sans-serif"
                ),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        
        # Enhanced layout styling
        fig.update_layout(
            # Title styling
            title=dict(
                text="📊 History of Issues Over Time",
                x=0.5,
                xanchor='center',
                font=dict(size=28, color='#2C3E50', family="Arial Black, sans-serif"),
                pad=dict(t=20, b=20)
            ),
            
            # Background and grid
            plot_bgcolor='rgba(248, 249, 250, 0.8)',
            paper_bgcolor='white',
            
            # Axes styling
            xaxis=dict(
                title=dict(
                    text="📅 Date",
                    font=dict(size=16, color='#34495E', family="Arial, sans-serif")
                ),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linewidth=2,
                linecolor='#BDC3C7',
                tickfont=dict(size=12, color='#2C3E50')
            ),
            
            yaxis=dict(
                title=dict(
                    text="🔢 Issue Count",
                    font=dict(size=16, color='#34495E', family="Arial, sans-serif")
                ),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                showline=True,
                linewidth=2,
                linecolor='#BDC3C7',
                tickfont=dict(size=12, color='#2C3E50'),
                zeroline=True,
                zerolinecolor='rgba(128, 128, 128, 0.4)',
                zerolinewidth=2
            ),
            
            # Hover styling
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="#2C3E50",
                font_size=14,
                font_family="Arial, sans-serif"
            ),
            
            # Margin adjustments for better text visibility
            margin=dict(l=60, r=60, t=100, b=60),
            
            # Add subtle shadow effect
            shapes=[
                dict(
                    type="rect",
                    xref="paper", yref="paper",
                    x0=0, y0=0, x1=1, y1=1,
                    fillcolor="rgba(0,0,0,0.02)",
                    layer="below",
                    line_width=0
                )
            ]
        )

    else:
        st.info("✅ No issues found or no structured data returned.")

elif run_check and not name:
    st.warning("Please enter a name before analyzing.")
