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

    # -------- CLEAN DATA --------
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    if df.empty:
        st.error("Invalid data")
        st.stop()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- AI ----------------
    st.subheader("🤖 AI Assistant (Universal Engine)")

    user_input = st.chat_input("Ask anything about your business...")

    if user_input:

        # -------- STEP 1: INTENT ENGINE --------
        intent_prompt = f"""
        Convert the question into structured JSON.

        Return ONLY JSON:

        {{
          "type": "data | general",
          "tasks": [
            {{
              "action": "max | min | total | average | median | top | bottom | trend",
              "metric": "revenue | profit | cost",
              "limit": number,
              "filters": {{
                "month": "january | february | march | none"
              }},
              "chart": "yes | no"
            }}
          ]
        }}

        Question: {user_input}
        """

        try:
            ai = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0
            )
            parsed = json.loads(ai.choices[0].message.content)
        except:
            parsed = {"type": "general"}

        responses = []
        chart_df = None

        # ---------------- DATA ENGINE ----------------
        if parsed.get("type") == "data":

            for task in parsed.get("tasks", []):

                data = df.copy()

                # -------- FILTER --------
                month = task.get("filters", {}).get("month")

                if month == "january":
                    data = data[data["date"].dt.month == 1]
                elif month == "february":
                    data = data[data["date"].dt.month == 2]
                elif month == "march":
                    data = data[data["date"].dt.month == 3]

                metric = task.get("metric", "revenue")
                action = task.get("action", "total")
                limit = int(task.get("limit", 5))

                try:
                    if action == "max":
                        row = data.loc[data[metric].idxmax()]
                        responses.append(f"Max {metric}: {row[metric]} on {row['date'].date()}")

                    elif action == "min":
                        row = data.loc[data[metric].idxmin()]
                        responses.append(f"Min {metric}: {row[metric]} on {row['date'].date()}")

                    elif action == "total":
                        responses.append(f"Total {metric}: ${data[metric].sum():.2f}")

                    elif action == "average":
                        responses.append(f"Average {metric}: ${data[metric].mean():.2f}")

                    elif action == "median":
                        responses.append(f"Median {metric}: ${data[metric].median():.2f}")

                    elif action == "top":
                        top_df = data.sort_values(metric, ascending=False).head(limit)
                        responses.append(f"Top {limit} {metric} records:")
                        responses.append(top_df.to_string(index=False))
                        chart_df = top_df

                    elif action == "bottom":
                        bot_df = data.sort_values(metric).head(limit)
                        responses.append(f"Bottom {limit} {metric} records:")
                        responses.append(bot_df.to_string(index=False))
                        chart_df = bot_df

                    elif action == "trend":
                        responses.append(f"{metric.capitalize()} trend shown below")
                        chart_df = data

                    if task.get("chart") == "yes":
                        chart_df = data

                except:
                    responses.append("⚠️ Could not compute this task")

        # ---------------- GENERAL AI ----------------
        else:

            general_prompt = f"""
            You are a helpful business assistant.

            Answer clearly and professionally.

            Question: {user_input}
            """

            try:
                ai = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": general_prompt}],
                    temperature=0.5
                )
                responses.append(ai.choices[0].message.content)
            except:
                responses.append("AI unavailable")

        # -------- FINAL RESPONSE --------
        final_response = "\n\n".join(responses)

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
