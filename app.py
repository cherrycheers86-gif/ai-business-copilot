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

if "quick_q" not in st.session_state:
    st.session_state.quick_q = ""

# ---------------- AUTH ----------------
if st.session_state.page == "auth":

    st.title("🔐 Login / Signup")

    mode = st.radio("Select", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Signup":
        name = st.text_input("Name")
        if st.button("Create Account"):
            st.session_state.user = {"name": name, "email": email}
            st.session_state.page = "onboarding"
            st.rerun()

    else:
        if st.button("Login"):
            st.session_state.user = {"name": "User", "email": email}
            st.session_state.page = "app"
            st.rerun()

    st.stop()

# ---------------- ONBOARDING ----------------
if st.session_state.page == "onboarding":

    st.title("🏢 Setup Your Business")

    industry = st.selectbox("Industry", ["Restaurant", "Retail", "Gas Station", "Other"])
    size = st.selectbox("Business Size", ["Small", "Medium", "Large"])

    if st.button("Continue"):
        st.session_state.user["industry"] = industry
        st.session_state.user["size"] = size
        st.session_state.page = "app"
        st.rerun()

    st.stop()

# ---------------- MAIN ----------------
user = st.session_state.user

st.title("🚀 AI Business Copilot")
st.success(f"Welcome {user['name']} 👋")

if st.sidebar.button("Logout"):
    st.session_state.page = "auth"
    st.session_state.user = None
    st.session_state.history = []
    st.rerun()

# ---------------- DATA ----------------
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=60),
            "revenue": [1000 + i*50 for i in range(60)],
            "cost": [600 + i*30 for i in range(60)]
        })
    else:
        df = pd.read_csv(uploaded_file)

    # Clean
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    if len(df) == 0:
        st.error("Invalid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- FILTER ----------------
    st.sidebar.subheader("📅 Filter")

    start = st.sidebar.date_input("Start", df["date"].min().date())
    end = st.sidebar.date_input("End", df["date"].max().date())

    df = df[(df["date"].dt.date >= start) & (df["date"].dt.date <= end)]

    if len(df) == 0:
        st.warning("No data")
        st.stop()

    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Trends","🤖 AI"])

    # ---------------- DASHBOARD ----------------
    with tab1:

        total_sales = df["revenue"].sum()
        total_expenses = df["cost"].sum()
        total_profit = df["profit"].sum()

        margin = (total_profit / total_sales) * 100 if total_sales else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Sales", f"${total_sales:.2f}")
        c2.metric("Expenses", f"${total_expenses:.2f}")
        c3.metric("Profit", f"${total_profit:.2f}")
        c4.metric("Margin", f"{margin:.2f}%")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df.set_index("date")[["revenue","cost","profit"]])

    # ---------------- AI ----------------
    with tab3:

        st.subheader("🤖 AI Assistant")

        # -------- AUTO INSIGHTS --------
        best = df.loc[df["profit"].idxmax()]
        worst = df.loc[df["profit"].idxmin()]

        st.success(f"Best Day: {best['date'].date()} (${best['profit']:.2f})")
        st.error(f"Worst Day: {worst['date'].date()} (${worst['profit']:.2f})")

        # -------- ALERTS --------
        margin = (df["profit"].sum() / df["revenue"].sum()) * 100

        if margin < 20:
            st.warning("Low profit margin")

        if df["cost"].mean() > df["revenue"].mean() * 0.7:
            st.warning("High expenses")

        # -------- SUGGESTIONS --------
        st.markdown("### 💡 Suggestions")

        col1,col2,col3 = st.columns(3)

        if col1.button("Best Day"):
            st.session_state.quick_q = "best day"

        if col2.button("Worst Day"):
            st.session_state.quick_q = "worst day"

        if col3.button("Top 3 Profit Days"):
            st.session_state.quick_q = "top 3 profit"

        # -------- CHAT --------
        for role, msg in st.session_state.history:
            st.markdown(f"**{role}:** {msg}")

        st.markdown("---")

        user_input = st.chat_input("Ask your business question...")

        if user_input:
            q = user_input.lower()
            result = None

            # -------- CHARTS --------
            if "chart" in q or "graph" in q:

                if "january" in q:
                    data = df[df["date"].dt.month == 1]
                elif "february" in q or "feb" in q:
                    data = df[df["date"].dt.month == 2]
                else:
                    data = df

                if len(data) > 0:
                    st.line_chart(data.set_index("date")[["revenue","cost","profit"]])
                    result = "Chart displayed"
                else:
                    result = "No data available"

            # -------- CALCULATIONS --------
            elif "top 3" in q:
                top3 = df.nlargest(3,"profit")[["date","profit"]]
                result = top3.to_string(index=False)

            elif "best day" in q:
                result = f"{best['date'].date()} (${best['profit']:.2f})"

            elif "worst day" in q:
                result = f"{worst['date'].date()} (${worst['profit']:.2f})"

            elif "max profit" in q:
                row = df.loc[df["profit"].idxmax()]
                result = f"{row['profit']} on {row['date'].date()}"

            elif "lowest profit" in q:
                row = df.loc[df["profit"].idxmin()]
                result = f"{row['profit']} on {row['date'].date()}"

            elif "total sales" in q:
                result = f"{df['revenue'].sum():.2f}"

            elif "average profit" in q:
                result = f"{df['profit'].mean():.2f}"

            # -------- BLOCK AI CALCULATIONS --------
            if any(x in q for x in ["profit","sales","max","min","average","top"]):
                if result is None:
                    result = "Calculation not supported yet"

            # -------- AI INSIGHTS ONLY --------
            if result is None:
                prompt = f"""
                You are a business analyst.

                Give insights only. No numbers calculation.

                Data:
                {df.head(30).to_string()}

                Question:
                {user_input}
                """

                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content":prompt}]
                    )
                    result = response.choices[0].message.content
                except:
                    result = "AI unavailable"

            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("AI", result))

            st.rerun()

else:
    st.info("Upload data to start")
