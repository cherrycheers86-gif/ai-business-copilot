import streamlit as st
import pandas as pd
from groq import Groq
import io

# Page config
st.set_page_config(page_title="ProfitLens AI", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ----------- CUSTOM STYLE -----------
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: white;
    }
    .stMetric {
        background-color: #1c1f26;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------- HEADER -----------
st.markdown("## 🚀 ProfitLens AI")
st.markdown("### 📊 Smart Business Insights Dashboard")

# Sidebar
st.sidebar.header("⚙️ Controls")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

# Chat memory
if "history" not in st.session_state:
    st.session_state.history = []

# Load Data
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "Date": pd.date_range(start="2026-01-01", periods=7),
            "Sales": [1000,1200,900,1500,1100,1300,1400],
            "Expenses": [600,700,500,800,650,750,900]
        })
    else:
        df = pd.read_csv(uploaded_file)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Profit"] = df["Sales"] - df["Expenses"]

    # FILTER
    if "Date" in df.columns:
        st.sidebar.subheader("📅 Filter Data")
        start_date = st.sidebar.date_input("Start", df["Date"].min().date())
        end_date = st.sidebar.date_input("End", df["Date"].max().date())

        df = df[(df["Date"].dt.date >= start_date) & 
                (df["Date"].dt.date <= end_date)]

    # VIEW TYPE
    view_type = st.sidebar.selectbox("View", ["Daily", "Monthly"])

    if "Date" in df.columns:
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        if view_type == "Monthly":
            df = df.groupby("Month").sum(numeric_only=True).reset_index()

    # ----------- METRICS -----------
    total_sales = df["Sales"].sum()
    total_expenses = df["Expenses"].sum()
    total_profit = df["Profit"].sum()

    st.markdown("### 📊 Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Sales", f"${total_sales}")
    c2.metric("💸 Expenses", f"${total_expenses}")
    c3.metric("📈 Profit", f"${total_profit}")

    # ----------- MAIN LAYOUT -----------
    left, right = st.columns([2, 1])

    with left:
        st.markdown("### 📈 Performance Trends")
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

        st.markdown("### 📋 Data Table")
        st.dataframe(df, use_container_width=True)

    with right:
        st.markdown("### 🚨 Alerts")

        if total_profit < 0:
            st.error("🔥 Loss detected")
        elif total_profit < total_sales * 0.1:
            st.warning("⚠️ Low profit margin")
        else:
            st.success("🚀 Strong performance")

        if total_expenses > total_sales * 0.7:
            st.warning("High expenses")

        if len(df) > 0 and df["Sales"].iloc[-1] < df["Sales"].mean():
            st.warning("Sales dropping")

        st.markdown("### 💡 Recommendations")

        if total_expenses > total_sales * 0.7:
            st.write("• Reduce supplier cost")

        if len(df) > 0 and df["Sales"].iloc[-1] < df["Sales"].mean():
            st.write("• Increase promotions")

        if total_profit > 0:
            st.write("• Reinvest profits")

    # ----------- AI CHAT -----------
    st.markdown("---")
    st.markdown("### 🤖 AI Assistant")

    user_input = st.text_input("Ask anything about your business")

    if user_input:
        summary = df.describe().to_string()

        prompt = f"""
        You are a business consultant.

        Analyze:
        {summary}

        Question: {user_input}

        Give insights + suggestions.
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_reply = response.choices[0].message.content

        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("AI", ai_reply))

    for role, msg in st.session_state.history:
        if role == "You":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 AI:** {msg}")

    # ----------- DOWNLOAD -----------
    st.markdown("---")
    st.markdown("### 📥 Export Report")

    report = f"""
Sales: {total_sales}
Expenses: {total_expenses}
Profit: {total_profit}
"""

    buffer = io.StringIO()
    buffer.write(report)

    st.download_button("Download Report", buffer.getvalue(), "report.txt")

else:
    st.info("👈 Upload data or use sample to begin")
