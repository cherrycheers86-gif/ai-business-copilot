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

if "last_chart" not in st.session_state:
    st.session_state.last_chart = None

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
st.success(f"Welcome {st.session_state.user['name']}")

if st.sidebar.button("Logout"):
    st.session_state.page = "auth"
    st.session_state.history = []
    st.rerun()

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

# ---------------- LOAD DATA ----------------
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=60),
            "revenue": [1000 + i*50 for i in range(60)],
            "cost": [600 + i*30 for i in range(60)]
        })
    else:
        df = pd.read_csv(uploaded_file)

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
        total_profit = df["profit"].sum()

        c1, c2 = st.columns(2)
        c1.metric("Sales", f"${total_sales:.2f}")
        c2.metric("Profit", f"${total_profit:.2f}")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df.set_index("date")[["revenue","cost","profit"]])

    # ---------------- AI ----------------
    with tab3:

        st.subheader("🤖 AI Assistant")

        # Auto insights
        best = df.loc[df["profit"].idxmax()]
        worst = df.loc[df["profit"].idxmin()]

        st.success(f"Best Day: {best['date'].date()} (${best['profit']:.2f})")
        st.error(f"Worst Day: {worst['date'].date()} (${worst['profit']:.2f})")

        # Chat history
        for role, msg in st.session_state.history:
            st.markdown(f"**{role}:** {msg}")

        st.markdown("---")

        user_input = st.chat_input("Ask your business question...")

        if user_input:

            q = user_input.lower()
            result_parts = []
            chart_data = None
            need_ai = False

            # -------- MONTH FILTER --------
            if "january" in q:
                data = df[df["date"].dt.month == 1]
            elif "february" in q or "feb" in q:
                data = df[df["date"].dt.month == 2]
            else:
                data = df

            # -------- CHART --------
            if any(x in q for x in ["chart","graph","plot","visualize"]):
                if len(data) > 0:
                    chart_data = data
                    result_parts.append("Chart generated below")
                else:
                    result_parts.append("No data available")

            # -------- CALCULATIONS --------
            if "max profit" in q:
                row = data.loc[data["profit"].idxmax()]
                result_parts.append(f"Max profit: {row['profit']} on {row['date'].date()}")

            if "lowest profit" in q:
                row = data.loc[data["profit"].idxmin()]
                result_parts.append(f"Lowest profit: {row['profit']} on {row['date'].date()}")

            if "total sales" in q:
                result_parts.append(f"Total sales: {data['revenue'].sum():.2f}")

            if "average profit" in q:
                result_parts.append(f"Average profit: {data['profit'].mean():.2f}")

            if "top 3" in q:
                top3 = data.nlargest(3,"profit")
                formatted = "\n".join(
                    [f"{row['date'].date()} → ${row['profit']}" for _, row in top3.iterrows()]
                )
                result_parts.append(f"Top 3 days:\n{formatted}")

            # -------- INSIGHT DETECTION --------
            if any(x in q for x in ["how","why","trend","explain","performance"]):
                need_ai = True

            # -------- AI INSIGHTS --------
            if need_ai:
                prompt = f"""
                Give business insights only.

                Data:
                {data.head(30).to_string()}

                Question:
                {user_input}
                """

                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content":prompt}]
                    )
                    result_parts.append(response.choices[0].message.content)
                except:
                    result_parts.append("AI unavailable")

            # -------- FINAL RESULT --------
            if not result_parts:
                result_parts.append("I couldn't understand the query clearly.")

            final_result = "\n\n".join(result_parts)

            st.session_state.history.append(("You", user_input))
            st.session_state.history.append(("AI", final_result))

            if chart_data is not None:
                st.session_state.last_chart = chart_data

        # -------- RENDER CHART --------
        if st.session_state.last_chart is not None:
            st.markdown("### 📊 Chart")
            st.line_chart(
                st.session_state.last_chart.set_index("date")[["revenue","cost","profit"]]
            )

else:
    st.info("Upload data to start")
