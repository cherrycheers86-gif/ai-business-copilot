import streamlit as st
import pandas as pd
from groq import Groq

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Business Copilot", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🚀 AI Business Copilot")

# ---------------- SESSION ----------------
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

if "customer" not in st.session_state:
    st.session_state.customer = {}

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- CUSTOMER FORM ----------------
if not st.session_state.form_submitted:

    st.header("👤 Enter Business Details")

    with st.form("customer_form"):
        name = st.text_input("Your Name")
        business = st.text_input("Business Name")

        industry = st.selectbox(
            "Industry",
            ["Restaurant", "Retail", "Gas Station", "Other"]
        )

        size = st.selectbox("Business Size", ["Small", "Medium", "Large"])

        submit = st.form_submit_button("Continue")

    if submit:
        st.session_state.customer = {
            "name": name,
            "business": business,
            "industry": industry,
            "size": size
        }
        st.session_state.form_submitted = True
        st.rerun()

    st.warning("Please fill your details to continue")
    st.stop()

# ---------------- CUSTOMER ----------------
customer = st.session_state.customer
industry = customer["industry"]

st.success(f"Welcome {customer['name']} 🚀")

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Controls")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

# ---------------- LOAD DATA ----------------
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=10),
            "revenue": [1000,1200,900,1500,1100,1300,1400,1600,1700,1800],
            "cost": [600,700,500,800,650,750,900,950,1000,1100]
        })
    else:
        df = pd.read_csv(uploaded_file)

    st.subheader("🔧 Map Your Data")

    cols = df.columns
    sales_col = st.selectbox("Select Sales Column", cols)
    expense_col = st.selectbox("Select Expense Column", cols)
    date_col = st.selectbox("Select Date Column", cols)

    # Map columns
    df["Sales"] = df[sales_col]
    df["Expenses"] = df[expense_col]
    df["Date"] = df[date_col]

    # ---------------- ROBUST CLEANING ----------------
    df["Sales"] = (
        df["Sales"].astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["Expenses"] = (
        df["Expenses"].astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
    df["Expenses"] = pd.to_numeric(df["Expenses"], errors="coerce")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Debug info
    st.subheader("🔍 Data Check")
    st.write("Null values:")
    st.write(df[["Sales", "Expenses", "Date"]].isna().sum())

    # Drop invalid
    df = df.dropna(subset=["Sales", "Expenses", "Date"])

    if len(df) == 0:
        st.error("❌ No valid data after cleaning. Please check your mapping or file.")
        st.stop()

    # Profit
    df["Profit"] = df["Sales"] - df["Expenses"]

    # ---------------- FILTER ----------------
    st.sidebar.subheader("📅 Filter")

    min_date = df["Date"].min()
    max_date = df["Date"].max()

    start = st.sidebar.date_input("Start", min_date.date())
    end = st.sidebar.date_input("End", max_date.date())

    df = df[(df["Date"].dt.date >= start) &
            (df["Date"].dt.date <= end)]

    if len(df) == 0:
        st.warning("⚠️ No data in selected range")
        st.stop()

    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Trends", "🤖 AI"])

    # ---------------- DASHBOARD ----------------
    with tab1:

        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Sales", f"${total_sales:.2f}")
        c2.metric("Expenses", f"${total_expenses:.2f}")
        c3.metric("Profit", f"${total_profit:.2f}")

        # ---------------- KPI ENGINE ----------------
        st.subheader("📊 Industry KPIs")

        if industry == "Restaurant":
            food_cost = (total_expenses / total_sales) * 100 if total_sales else 0
            st.metric("🍔 Food Cost %", f"{food_cost:.2f}%")

            if food_cost > 30:
                st.error("Food cost too high (>30%)")
            else:
                st.success("Healthy food cost")

        elif industry == "Retail":
            margin = (total_profit / total_sales) * 100 if total_sales else 0
            st.metric("🛒 Profit Margin", f"{margin:.2f}%")

            if margin < 20:
                st.warning("Low margin")

        elif industry == "Gas Station":
            margin = (total_profit / total_sales) * 100 if total_sales else 0
            st.metric("⛽ Margin %", f"{margin:.2f}%")

            if margin < 10:
                st.warning("Very low margin")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

    # ---------------- AI ----------------
    with tab3:

        user_input = st.text_input("Ask a business question")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            Business: {customer['business']}
            Industry: {industry}

            Data:
            {summary}

            Question: {user_input}

            Give insights and suggestions.
            """

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content
            except:
                reply = "AI is temporarily unavailable."

            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("AI", reply))

        for role, msg in st.session_state.history:
            st.write(f"**{role}:** {msg}")

else:
    st.info("Upload a CSV or use sample data")
