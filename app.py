import streamlit as st
import pandas as pd
from groq import Groq
import io

# Page config
st.set_page_config(page_title="AI Business Copilot", layout="wide")

# API Key
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Title
st.title("🚀 AI Business Copilot")
st.markdown("### Analyze your business and get AI insights instantly")

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

    # Convert Date
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Add Profit
    df["Profit"] = df["Sales"] - df["Expenses"]

    # FILTER
    if "Date" in df.columns:
        st.sidebar.subheader("📅 Filter Data")

        start_date = st.sidebar.date_input("Start Date", df["Date"].min().date())
        end_date = st.sidebar.date_input("End Date", df["Date"].max().date())

        mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
        df = df.loc[mask]

    # VIEW TYPE
    st.sidebar.subheader("📊 View Type")
    view_type = st.sidebar.selectbox("Select View", ["Daily", "Monthly"])

    if "Date" in df.columns:
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        if view_type == "Monthly":
            df = df.groupby("Month").sum(numeric_only=True).reset_index()

    # Tabs
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

            # Best Day
            if "Date" in df.columns and len(df) > 0:
                best_day = df.loc[df["Sales"].idxmax()]
                st.success(f"🏆 Best Sales Day: {best_day['Date']} (${best_day['Sales']})")

        with col2:
            st.subheader("🚨 Issues")

            if total_profit > 0:
                st.success("Profitable")
            else:
                st.error("Loss detected")

            if total_expenses > total_sales * 0.7:
                st.warning("High expenses")

            if len(df) > 0 and df["Sales"].iloc[-1] < df["Sales"].mean():
                st.warning("Sales dropping")

            st.subheader("💡 Recommendations")

            if total_expenses > total_sales * 0.7:
                st.write("- Reduce supplier cost")

            if len(df) > 0 and df["Sales"].iloc[-1] < df["Sales"].mean():
                st.write("- Increase marketing")

            if total_profit > 0:
                st.write("- Reinvest profits")

        # Profit Margin
        st.subheader("📊 Profit Margin")

        if total_sales > 0:
            profit_margin = (total_profit / total_sales) * 100
            st.metric("Profit Margin", f"{profit_margin:.2f}%")

        # Smart Alert
        st.subheader("⚡ Smart Alert")

        if total_profit < 0:
            st.error("🔥 You're losing money!")
        elif total_profit < total_sales * 0.1:
            st.warning("⚠️ Low profit margin")
        else:
            st.success("🚀 Healthy business")

    # ---------------- TRENDS ----------------
    with tab2:
        st.subheader("📈 Trends")
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

        # Bar Chart
        chart_df = pd.DataFrame({
            "Category": ["Sales", "Expenses"],
            "Amount": [total_sales, total_expenses]
        })
        st.bar_chart(chart_df.set_index("Category"))

    # ---------------- AI CHAT ----------------
    with tab3:
        st.subheader("🤖 Ask AI")

        user_input = st.text_input("Ask a business question")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            You are a business expert.

            Analyze the data and provide:
            - Key insights
            - Problems
            - Suggestions

            Data:
            {summary}

            Question: {user_input}
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
