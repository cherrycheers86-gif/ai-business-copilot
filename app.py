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

# ---------------- AUTH ----------------
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
                "email": email
            }
            st.session_state.page = "onboarding"
            st.rerun()

    else:
        if st.button("Login"):
            st.session_state.user = {
                "name": "User",
                "email": email
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

st.title("🚀 AI Business Copilot")
st.success(f"Welcome {user['name']} 👋")

# Logout
if st.sidebar.button("Logout"):
    st.session_state.page = "auth"
    st.session_state.user = None
    st.rerun()

# Sidebar
st.sidebar.header("📁 Upload Data")
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

    # ---------------- VALIDATION ----------------
    required_cols = ["date", "revenue", "cost"]

    if not all(col in df.columns for col in required_cols):
        st.error("❌ CSV must contain: date, revenue, cost")
        st.stop()

    # Convert types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")

    df = df.dropna()

    if len(df) == 0:
        st.error("❌ No valid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- FILTER ----------------
    st.sidebar.subheader("📅 Filter")

    min_date = df["date"].min()
    max_date = df["date"].max()

    start = st.sidebar.date_input("Start", min_date.date())
    end = st.sidebar.date_input("End", max_date.date())

    df = df[(df["date"].dt.date >= start) &
            (df["date"].dt.date <= end)]

    if len(df) == 0:
        st.warning("No data in selected range")
        st.stop()

    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Trends", "🤖 AI"])

    # ---------------- DASHBOARD ----------------
    with tab1:

        total_sales = df["revenue"].sum()
        total_expenses = df["cost"].sum()
        total_profit = df["profit"].sum()

        margin = (total_profit / total_sales) * 100 if total_sales else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sales", f"${total_sales:.2f}")
        c2.metric("Expenses", f"${total_expenses:.2f}")
        c3.metric("Profit", f"${total_profit:.2f}")
        c4.metric("Profit Margin", f"{margin:.2f}%")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df[["revenue", "cost", "profit"]])

    # ---------------- AI ----------------
    with tab3:

        user_input = st.text_input("Ask AI")

        if user_input:
            summary = df.describe().to_string()

            prompt = f"""
            Analyze this business data and give insights.

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

            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("AI", reply))

        for role, msg in st.session_state.history:
            st.write(f"**{role}:** {msg}")

else:
    st.info("Upload a CSV file or use sample data")
