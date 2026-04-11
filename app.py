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

    industry = st.selectbox("Industry", ["Restaurant", "Retail", "Other"])
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

    # Clean
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    if len(df) == 0:
        st.error("Invalid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- DASHBOARD ----------------
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Trends", "🤖 AI"])

    with tab1:
        st.metric("Sales", f"${df['revenue'].sum():.2f}")
        st.metric("Expenses", f"${df['cost'].sum():.2f}")
        st.metric("Profit", f"${df['profit'].sum():.2f}")

        st.dataframe(df)

    with tab2:
        st.line_chart(df.set_index("date")[["revenue","cost","profit"]])

    # ---------------- AI ----------------
    with tab3:

        st.subheader("🤖 AI Assistant")

        # 🔥 SCROLLABLE CHAT BOX
        st.markdown("""
        <div style="height:300px; overflow-y:scroll; border:1px solid gray; padding:10px;">
        """, unsafe_allow_html=True)

        for role, msg in st.session_state.history:
            st.markdown(f"**{role}:** {msg}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 🔥 FIXED INPUT (FORM)
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask your question")
            submit = st.form_submit_button("Send")

            if submit and user_input:

                q = user_input.lower()
                result = None

                # ---------------- PYTHON ENGINE ----------------

                if "max profit" in q:
                    row = df.loc[df["profit"].idxmax()]
                    result = f"Max profit: {row['profit']} on {row['date'].date()}"

                elif "min profit" in q or "lowest" in q:
                    row = df.loc[df["profit"].idxmin()]
                    result = f"Lowest profit: {row['profit']} on {row['date'].date()}"

                elif "total sales" in q:
                    result = f"Total sales: {df['revenue'].sum()}"

                elif "average profit" in q:
                    result = f"Average profit: {df['profit'].mean():.2f}"

                elif "january" in q:
                    jan = df[df["date"].dt.month == 1]
                    if len(jan) > 0:
                        row = jan.loc[jan["profit"].idxmax()]
                        result = f"January max profit: {row['profit']} on {row['date'].date()}"
                    else:
                        result = "No January data"

                # ---------------- CHARTS ----------------
                if "chart" in q or "graph" in q:
                    st.line_chart(df.set_index("date")[["revenue","cost","profit"]])
                    result = "Chart displayed"

                # ---------------- AI (ONLY INSIGHTS) ----------------
                if result is None:
                    prompt = f"""
                    You are a business analyst.

                    RULES:
                    - No calculations
                    - No code
                    - Only insights

                    Data:
                    {df.head(20).to_string()}

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

                # Save chat
                st.session_state.history.append(("You", user_input))
                st.session_state.history.append(("AI", result))

                st.rerun()

else:
    st.info("Upload data to start")
