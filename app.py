import streamlit as st
import pandas as pd
import json
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

    # ---------------- AI ----------------
    st.subheader("🤖 AI Assistant (Enterprise Mode)")

    user_input = st.chat_input("Ask anything about your business...")

    if user_input:

        # -------- STEP 1: INTENT SPLIT --------
        intent_prompt = f"""
        Break this into tasks.

        Return JSON:
        {{
          "tasks":[
            {{"type":"calculation","metric":"profit","operation":"max","month":"january"}},
            {{"type":"chart","metric":"profit","month":"january"}},
            {{"type":"insight"}}
          ]
        }}

        Question: {user_input}
        """

        try:
            ai = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role":"user","content":intent_prompt}],
                temperature=0
            )
            parsed = json.loads(ai.choices[0].message.content)
            tasks = parsed.get("tasks", [])
        except:
            tasks = [{"type":"insight"}]

        responses = []
        chart_df = None

        # -------- STEP 2: EXECUTION --------
        for task in tasks:

            data = df.copy()

            month = task.get("month")
            if month == "january":
                data = data[data["date"].dt.month == 1]
            elif month == "february":
                data = data[data["date"].dt.month == 2]
            elif month == "march":
                data = data[data["date"].dt.month == 3]

            if task["type"] == "calculation":

                metric = task.get("metric", "revenue")
                op = task.get("operation", "total")

                try:
                    if op == "max":
                        row = data.loc[data[metric].idxmax()]
                        responses.append(f"Max {metric}: {row[metric]} on {row['date'].date()}")

                    elif op == "min":
                        row = data.loc[data[metric].idxmin()]
                        responses.append(f"Min {metric}: {row[metric]} on {row['date'].date()}")

                    elif op == "total":
                        responses.append(f"Total {metric}: ${data[metric].sum():.2f}")

                    elif op == "average":
                        responses.append(f"Average {metric}: ${data[metric].mean():.2f}")

                    elif op == "median":
                        responses.append(f"Median {metric}: ${data[metric].median():.2f}")

                except:
                    responses.append("⚠️ Calculation failed")

            elif task["type"] == "chart":
                chart_df = data

            elif task["type"] == "insight":

                insight_prompt = f"""
                Give business insights only.

                Data:
                {data.head(10).to_string()}

                Question:
                {user_input}
                """

                try:
                    ai = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role":"user","content":insight_prompt}],
                        temperature=0.3
                    )
                    responses.append(ai.choices[0].message.content)
                except:
                    responses.append("⚠️ Insight failed")

        final_response = "\n\n".join(responses)

        # -------- SAVE --------
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_response,
            "chart": chart_df
        })

        st.rerun()

    # -------- DISPLAY --------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg.get("chart") is not None:
                st.line_chart(
                    msg["chart"].set_index("date")[["revenue","cost","profit"]]
                )

else:
    st.info("Upload data to start")
