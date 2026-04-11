import streamlit as st
import pandas as pd
from groq import Groq
import io

# CONFIG
st.set_page_config(page_title="AI Business Copilot", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🚀 AI Business Copilot")
st.markdown("Advanced Business Analytics + AI Insights")

# SIDEBAR
st.sidebar.header("⚙️ Controls")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

if "history" not in st.session_state:
    st.session_state.history = []

# LOAD DATA
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "Date": pd.date_range(start="2026-01-01", periods=15),
            "Sales": [1000,1200,900,1500,1100,1300,1400,1600,1700,1800,1750,1650,1550,1450,1350],
            "Expenses": [600,700,500,800,650,750,900,950,1000,1100,1050,1000,950,900,850]
        })
    else:
        df = pd.read_csv(uploaded_file)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Profit"] = df["Sales"] - df["Expenses"]

    # FILTER
    if "Date" in df.columns:
        st.sidebar.subheader("📅 Date Filter")
        start = st.sidebar.date_input("Start", df["Date"].min().date())
        end = st.sidebar.date_input("End", df["Date"].max().date())
        df = df[(df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)]

    # VIEW
    view = st.sidebar.selectbox("View", ["Daily", "Monthly"])
    if "Date" in df.columns:
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        if view == "Monthly":
            df = df.groupby("Month").sum(numeric_only=True).reset_index()

    # SEARCH
    search = st.sidebar.text_input("🔍 Search")
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

    # SORT
    sort_col = st.sidebar.selectbox("Sort by", df.columns)
    order = st.sidebar.radio("Order", ["Asc", "Desc"])
    df = df.sort_values(by=sort_col, ascending=(order == "Asc"))

    # COLUMN SELECT
    st.sidebar.subheader("📊 Select Columns")
    selected_cols = st.sidebar.multiselect("Columns", df.columns, default=df.columns)
    df = df[selected_cols]

    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Trends", "🤖 AI", "📥 Report"])

    # DASHBOARD
    with tab1:
        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Sales", f"${total_sales}")
        c2.metric("Expenses", f"${total_expenses}")
        c3.metric("Profit", f"${total_profit}")

        # Profit Margin
        if total_sales > 0:
            margin = (total_profit / total_sales) * 100
            st.metric("Profit Margin", f"{margin:.2f}%")

        # Growth
        if len(df) > 1:
            growth = ((df["Sales"].iloc[-1] - df["Sales"].iloc[0]) / df["Sales"].iloc[0]) * 100
            st.metric("Growth", f"{growth:.2f}%")

        st.divider()

        col1, col2 = st.columns([2,1])

        with col1:
            st.dataframe(df)

            if len(df) > 0:
                st.success(f"Best Sales: {df['Sales'].max()}")
                st.warning(f"Lowest Sales: {df['Sales'].min()}")

        with col2:
            st.subheader("🚨 Alerts")

            if total_profit < 0:
                st.error("Loss detected")
            elif total_profit < total_sales * 0.1:
                st.warning("Low margin")
            else:
                st.success("Healthy business")

            if total_expenses > total_sales * 0.7:
                st.warning("High expenses")

            st.subheader("💡 Recommendations")

            if total_expenses > total_sales * 0.7:
                st.write("- Reduce cost")

            if total_profit > 0:
                st.write("- Reinvest profits")

    # TRENDS
    with tab2:
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

        # Moving average
        df["MA"] = df["Sales"].rolling(3).mean()
        st.line_chart(df[["Sales", "MA"]])

    # AI
    with tab3:
        user_input = st.text_input("Ask business question")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            Analyze business data and give insights + suggestions.

            {summary}

            Question: {user_input}
            """

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )

            reply = response.choices[0].message.content

            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("AI", reply))

        for role, msg in st.session_state.history:
            st.write(f"**{role}:** {msg}")

    # REPORT
    with tab4:
        report = f"""
Sales: {total_sales}
Expenses: {total_expenses}
Profit: {total_profit}
"""

        st.download_button("Download", report, "report.txt")

else:
    st.info("Upload file or use sample")
