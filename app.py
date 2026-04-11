import streamlit as st
import pandas as pd
from groq import Groq

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Business Copilot", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------------- SESSION ----------------
if "page" not in st.session_state:
    st.session_state.page = "auth"

if "user" not in st.session_state:
    st.session_state.user = None

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- AUTH PAGE ----------------
if st.session_state.page == "auth":

    st.title("🔐 Login / Signup")

    mode = st.radio("Select", ["Login", "Signup"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Signup":
        name = st.text_input("Name")

        if st.button("Create Account"):
            st.session_state.user = {
                "name": name,
                "email": email,
                "industry": None,
                "size": None
            }
            st.session_state.page = "onboarding"
            st.rerun()

    else:
        if st.button("Login"):
            # Demo login (replace with DB later)
            st.session_state.user = {
                "name": "Demo User",
                "email": email,
                "industry": "Restaurant",
                "size": "Small"
            }
            st.session_state.page = "app"
            st.rerun()

    st.stop()

# ---------------- ONBOARDING ----------------
if st.session_state.page == "onboarding":

    st.title("🏢 Setup Your Business")

    industry = st.selectbox(
        "Industry",
        ["Restaurant", "Retail", "Gas Station", "Other"]
    )

    size = st.selectbox("Business Size", ["Small", "Medium", "Large"])

    if st.button("Continue"):
        st.session_state.user["industry"] = industry
        st.session_state.user["size"] = size
        st.session_state.page = "app"
        st.rerun()

    st.stop()

# ---------------- MAIN APP ----------------
user = st.session_state.user
industry = user["industry"]

st.title("🚀 AI Business Copilot")
st.success(f"Welcome {user['name']} 👋")

# Logout button
if st.sidebar.button("Logout"):
    st.session_state.page = "auth"
    st.session_state.user = None
    st.rerun()

# Sidebar
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
    sales_col = st.selectbox("Sales Column", cols)
    expense_col = st.selectbox("Expenses Column", cols)
    date_col = st.selectbox("Date Column", cols)

    # Map
    df["Sales"] = df[sales_col]
    df["Expenses"] = df[expense_col]
    df["Date"] = df[date_col]

    # ---------------- CLEANING ----------------
    df["Sales"] = df["Sales"].astype(str).str.replace("$","").str.replace(",","")
    df["Expenses"] = df["Expenses"].astype(str).str.replace("$","").str.replace(",","")

    df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
    df["Expenses"] = pd.to_numeric(df["Expenses"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df = df.dropna(subset=["Sales","Expenses","Date"])

    if len(df) == 0:
        st.error("❌ No valid data after cleaning")
        st.stop()

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
        st.warning("No data in selected range")
        st.stop()

    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Trends","🤖 AI"])

    # ---------------- DASHBOARD ----------------
    with tab1:

        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        c1,c2,c3 = st.columns(3)
        c1.metric("Sales", f"${total_sales:.2f}")
        c2.metric("Expenses", f"${total_expenses:.2f}")
        c3.metric("Profit", f"${total_profit:.2f}")

        st.subheader("📊 Industry KPIs")

        if industry == "Restaurant":
            food_cost = (total_expenses / total_sales)*100 if total_sales else 0
            st.metric("🍔 Food Cost %", f"{food_cost:.2f}%")

        elif industry == "Retail":
            margin = (total_profit / total_sales)*100 if total_sales else 0
            st.metric("🛒 Profit Margin", f"{margin:.2f}%")

        elif industry == "Gas Station":
            margin = (total_profit / total_sales)*100 if total_sales else 0
            st.metric("⛽ Margin %", f"{margin:.2f}%")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df[["Sales","Expenses","Profit"]])

    # ---------------- AI ----------------
    with tab3:

        user_input = st.text_input("Ask AI")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            Business: {user['name']}
            Industry: {industry}

            Data:
            {summary}

            Question: {user_input}
            """

            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}]
                )
                reply = response.choices[0].message.content
            except:
                reply = "AI unavailable"

            st.session_state.history.append(("You",user_input))
            st.session_state.history.append(("AI",reply))

        for role,msg in st.session_state.history:
            st.write(f"**{role}:** {msg}")

else:
    st.info("Upload data or use sample")
