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

    # CLEAN
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    if df.empty:
        st.error("Invalid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- AI SECTION ----------------
    st.subheader("🤖 AI Assistant")

    # -------- INPUT --------
    user_input = st.chat_input("Ask anything about your data...")

    if user_input:

        q = user_input.lower().strip()

        # -------- INVALID INPUT --------
        if len(q) < 3 or not any(c.isalpha() for c in q):
            response = "Please ask a valid business question."
            chart_df = None

        else:

            # -------- STEP 1: ASK AI FOR CODE --------
            prompt = f"""
            You are a data analyst.

            Convert the question into pandas code.

            RULES:
            - Use ONLY dataframe df
            - No imports
            - One line of code
            - Must return a value
            - If chart needed → return dataframe

            Columns: {list(df.columns)}

            Question: {user_input}
            """

            try:
                ai = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0
                )

                code = ai.choices[0].message.content.strip()

                # -------- SECURITY --------
                unsafe = ["import", "os", "sys", "open", "__", "exec", "eval"]

                if any(x in code.lower() for x in unsafe):
                    response = "❌ Unsafe query blocked."
                    chart_df = None

                else:
                    try:
                        result = eval(code, {"df": df})

                        # -------- HANDLE RESULT --------
                        if isinstance(result, pd.DataFrame):
                            response = "Here is your chart 👇"
                            chart_df = result

                        elif isinstance(result, (int, float)):
                            response = f"Result: {round(result,2)}"
                            chart_df = None

                        else:
                            response = f"Result: {result}"
                            chart_df = None

                    except:
                        response = "⚠️ Could not compute. Try rephrasing."
                        chart_df = None

            except:
                response = "AI unavailable"
                chart_df = None

        # -------- SAVE --------
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "chart": chart_df
        })

        st.rerun()

    # -------- DISPLAY CHAT --------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg.get("chart") is not None:
                try:
                    st.line_chart(msg["chart"].set_index("date"))
                except:
                    st.dataframe(msg["chart"])

else:
    st.info("Upload data to start")
