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
    st.session_state.history = []
    st.rerun()

# Sidebar
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
use_sample = st.sidebar.button("Use Sample Data")

# ---------------- LOAD DATA ----------------
if uploaded_file or use_sample:

    if use_sample:
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=30),
            "revenue": [1000 + i*50 for i in range(30)],
            "cost": [600 + i*30 for i in range(30)]
        })
    else:
        df = pd.read_csv(uploaded_file)

    # ---------------- VALIDATION ----------------
    required_cols = ["date", "revenue", "cost"]

    if not all(col in df.columns for col in required_cols):
        st.error("❌ CSV must contain: date, revenue, cost")
        st.stop()

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
        c4.metric("Profit Margin", f"{margin:.2f}%")

        st.dataframe(df)

    # ---------------- TRENDS ----------------
    with tab2:
        st.line_chart(df[["revenue","cost","profit"]])

    # ---------------- AI ----------------
    with tab3:

        st.subheader("🤖 AI Assistant")

        # ---------------- AUTO INSIGHTS ----------------
        st.markdown("### 📊 Auto Insights")

        best_day = df.loc[df["profit"].idxmax()]
        worst_day = df.loc[df["profit"].idxmin()]

        st.success(f"🏆 Best Day: {best_day['date'].date()} (Profit: ${best_day['profit']:.2f})")
        st.error(f"📉 Worst Day: {worst_day['date'].date()} (Profit: ${worst_day['profit']:.2f})")

        avg_profit = df["profit"].mean()
        st.info(f"📊 Average Profit: ${avg_profit:.2f}")

        # ---------------- ALERTS ----------------
        st.markdown("### 🚨 Alerts")

        margin = (df["profit"].sum() / df["revenue"].sum()) * 100

        if margin < 20:
            st.warning("⚠️ Profit margin is low")

        if df["cost"].mean() > df["revenue"].mean() * 0.7:
            st.warning("⚠️ Expenses are high")

        # ---------------- QUICK QUESTIONS ----------------
        st.markdown("### 💡 Suggested Questions")

        col1, col2, col3 = st.columns(3)

        if col1.button("Best Day"):
            st.session_state.quick_q = "What is my best day?"

        if col2.button("Worst Day"):
            st.session_state.quick_q = "What is my worst day?"

        if col3.button("Improve Profit"):
            st.session_state.quick_q = "How can I improve profit?"

        # ---------------- CHAT HISTORY ----------------
        for role, msg in st.session_state.history:
            if role == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")

        st.markdown("---")

        # ---------------- CHAT INPUT ----------------
        with st.form("chat_form", clear_on_submit=True):

            user_input = st.text_input("Ask AI", value=st.session_state.quick_q)
            submitted = st.form_submit_button("Send")

            if submitted and user_input:

                q = user_input.lower()

                # ---------------- SMART LOGIC ----------------
                if "best day" in q:
                    row = df.loc[df["profit"].idxmax()]
                    result = f"Best day is {row['date'].date()} with profit {row['profit']:.2f}"

                elif "worst day" in q:
                    row = df.loc[df["profit"].idxmin()]
                    result = f"Worst day is {row['date'].date()} with profit {row['profit']:.2f}"

                elif "improve" in q:
                    result = "Reduce costs, optimize pricing, and focus on high-margin days."

                else:
                    result = None

                # ---------------- AI RESPONSE ----------------
                if result:
                    prompt = f"Explain this clearly: {result}"
                else:
                    prompt = f"""
                    Analyze this business data:
                    {df.head(20).to_string()}

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
                st.session_state.quick_q = ""

                st.rerun()

else:
    st.info("Upload a CSV file or use sample data")
