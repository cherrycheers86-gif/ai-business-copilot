import streamlit as st
import pandas as pd
from groq import Groq
import io

# Page config
st.set_page_config(page_title="AI Business Copilot", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🚀 AI Business Copilot")
st.markdown("### Analyze your business and get AI insights instantly")

# Sidebar
st.sidebar.header("⚙️ Controls")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

use_sample = st.sidebar.button("Use Sample Data")

# Chat memory
if "history" not in st.session_state:
    st.session_state.history = []

# Load data
if uploaded_file or use_sample:
    
    if use_sample:
        df = pd.DataFrame({
            "Date": pd.date_range(start="2026-01-01", periods=7),
            "Sales": [1000,1200,900,1500,1100,1300,1400],
            "Expenses": [600,700,500,800,650,750,900]
        })
    else:
        df = pd.read_csv(uploaded_file)

    # Convert date if exists
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    df["Profit"] = df["Sales"] - df["Expenses"]

    # FILTER
    st.sidebar.subheader("📅 Filter Data")

    if "Date" in df.columns:
        start_date = st.sidebar.date_input("Start Date", df["Date"].min())
        end_date = st.sidebar.date_input("End Date", df["Date"].max())

        df = df[(df["Date"] >= pd.to_datetime(start_date)) & 
                (df["Date"] <= pd.to_datetime(end_date))]

    # TABS (clean UI)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Trends", "🤖 AI Chat", "📥 Report"])

    # ---------------- DASHBOARD ----------------
    with tab1:
        st.subheader("📊 Business Overview")

        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Sales", f"${total_sales}")
        c2.metric("💸 Expenses", f"${total_expenses}")
        c3.metric("📈 Profit", f"${total_profit}")

        st.divider()

        col1, col2 = st.columns([2,1])

        with col1:
            st.dataframe(df)

        with col2:
            st.subheader("🚨 Issues")

            if total_profit > 0:
                st.success("Profitable")
            else:
                st.error("Loss detected")

            if total_expenses > total_sales * 0.7:
                st.warning("High expenses")

            if df["Sales"].iloc[-1] < df["Sales"].mean():
                st.warning("Sales dropping")

            st.subheader("💡 Recommendations")

            if total_expenses > total_sales * 0.7:
                st.write("- Reduce supplier cost")

            if df["Sales"].iloc[-1] < df["Sales"].mean():
                st.write("- Increase marketing")

    # ---------------- TRENDS ----------------
    with tab2:
        st.subheader("📈 Trends")

        st.line_chart(df[["Sales", "Expenses", "Profit"]])

    # ---------------- AI CHAT ----------------
    with tab3:
        st.subheader("🤖 Ask AI")

        user_input = st.text_input("Ask a business question")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            You are a business expert.

            Data:
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

    # ---------------- REPORT ----------------
    with tab4:
        st.subheader("📥 Download Report")

        report = f"""
Total Sales: {total_sales}
Total Expenses: {total_expenses}
Total Profit: {total_profit}
"""

        buffer = io.StringIO()
        buffer.write(report)

        st.download_button(
            "Download Report",
            data=buffer.getvalue(),
            file_name="report.txt"
        )

else:
    st.info("👈 Upload a file or use sample data to start")
