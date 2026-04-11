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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chart_data" not in st.session_state:
    st.session_state.chart_data = None

# ---------------- AUTH ----------------
if st.session_state.page == "auth":

    st.title("🔐 Login / Signup")

    mode = st.radio("Select", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Signup":
        name = st.text_input("Name")
        if st.button("Create Account"):
            st.session_state.user = {"name": name}
            st.session_state.page = "onboarding"
            st.rerun()

    else:
        if st.button("Login"):
            st.session_state.user = {"name": "User"}
            st.session_state.page = "app"
            st.rerun()

    st.stop()

# ---------------- ONBOARDING ----------------
if st.session_state.page == "onboarding":

    st.title("🏢 Setup Business")

    industry = st.selectbox("Industry", ["Restaurant", "Retail", "Gas Station", "Other"])
    size = st.selectbox("Size", ["Small", "Medium", "Large"])

    if st.button("Continue"):
        st.session_state.page = "app"
        st.rerun()

    st.stop()

# ---------------- MAIN ----------------
st.title("🚀 AI Business Copilot")
st.success(f"Welcome {st.session_state.user['name']} 👋")

if st.sidebar.button("Logout"):
    st.session_state.page = "auth"
    st.session_state.messages = []
    st.session_state.chart_data = None
    st.rerun()

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

# ---------------- DATA ----------------
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=60),
            "revenue": [1000 + i*50 for i in range(60)],
            "cost": [600 + i*30 for i in range(60)]
        })
    else:
        df = pd.read_csv(uploaded_file)

    # -------- CLEAN --------
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    if len(df) == 0:
        st.error("Invalid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- TABS ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Trends","🤖 AI"])

    # ---------------- DASHBOARD ----------------
    with tab1:
        st.metric("Sales", f"${df['revenue'].sum():.2f}")
        st.metric("Profit", f"${df['profit'].sum():.2f}")
        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df.set_index("date")[["revenue","cost","profit"]])

    # ---------------- AI ----------------
    with tab3:

        st.subheader("🤖 AI Assistant")

        # -------- INPUT FIRST (IMPORTANT FIX) --------
        user_input = st.chat_input("Ask anything about your data...")

        if user_input:

            q = user_input.lower()
            response = ""
            chart_data = None

            # -------- MONTH FILTER --------
            if "january" in q:
                data = df[df["date"].dt.month == 1]
            elif "february" in q or "feb" in q:
                data = df[df["date"].dt.month == 2]
            else:
                data = df

            # -------- CHART --------
            if any(x in q for x in ["chart", "plot", "graph"]):
                chart_data = data
                response = "Here is your chart 👇"

            # -------- STRONG CALCULATIONS --------
            elif "max" in q and ("sale" in q or "revenue" in q):
                row = data.loc[data["revenue"].idxmax()]
                response = f"Max revenue: {row['revenue']} on {row['date'].date()}"

            elif "max profit" in q:
                row = data.loc[data["profit"].idxmax()]
                response = f"Max profit: {row['profit']} on {row['date'].date()}"

            elif "lowest profit" in q or "min profit" in q:
                row = data.loc[data["profit"].idxmin()]
                response = f"Lowest profit: {row['profit']} on {row['date'].date()}"

            elif "total profit" in q:
                response = f"Total profit: ${data['profit'].sum():.2f}"

            elif "total revenue" in q or "total sales" in q:
                response = f"Total revenue: ${data['revenue'].sum():.2f}"

            elif "average profit" in q:
                response = f"Average profit: ${data['profit'].mean():.2f}"

            elif "average revenue" in q:
                response = f"Average revenue: ${data['revenue'].mean():.2f}"

            # -------- AI INSIGHTS --------
            else:
                prompt = f"""
                You are a business analyst.

                RULES:
                - Do NOT calculate numbers
                - Do NOT generate code
                - Give clear business insights

                Data:
                {data.head(10).to_string()}

                Question:
                {user_input}
                """

                try:
                    ai = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content":prompt}],
                        temperature=0.3
                    )
                    response = ai.choices[0].message.content
                except:
                    response = "AI unavailable. Try again."

            # -------- SAVE ONCE (CRITICAL FIX) --------
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response})

            if chart_data is not None:
                st.session_state.chart_data = chart_data

        # -------- DISPLAY CHAT (ONLY ONCE) --------
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # -------- DISPLAY CHART --------
        if st.session_state.chart_data is not None:
            st.line_chart(
                st.session_state.chart_data.set_index("date")[["revenue","cost","profit"]]
            )

else:
    st.info("Upload data to start")
