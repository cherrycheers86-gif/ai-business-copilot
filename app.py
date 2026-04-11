import streamlit as st
import pandas as pd
from groq import Groq

st.set_page_config(page_title="AI Business Copilot", layout="wide")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chart_data" not in st.session_state:
    st.session_state.chart_data = None

# ---------------- HEADER ----------------
st.title("🚀 AI Business Copilot")

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

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    df = df.dropna()

    df["profit"] = df["revenue"] - df["cost"]

    # ---------------- CHAT DISPLAY ----------------
    st.subheader("🤖 AI Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ---------------- INPUT ----------------
    user_input = st.chat_input("Ask your business question...")

    if user_input:

        # SHOW USER MESSAGE
        st.session_state.messages.append({"role": "user", "content": user_input})

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
        if any(x in q for x in ["chart","plot","graph"]):
            chart_data = data
            response = "Here is your chart 👇"

        # -------- CALCULATIONS --------
        elif "profit" in q:
            response = f"Total profit: ${data['profit'].sum():.2f}"

        elif "revenue" in q or "sales" in q:
            response = f"Total revenue: ${data['revenue'].sum():.2f}"

        elif "max profit" in q:
            row = data.loc[data["profit"].idxmax()]
            response = f"Max profit: {row['profit']} on {row['date'].date()}"

        elif "lowest profit" in q:
            row = data.loc[data["profit"].idxmin()]
            response = f"Lowest profit: {row['profit']} on {row['date'].date()}"

        # -------- AI INSIGHTS --------
        else:
            prompt = f"""
            You are a business analyst.

            DO NOT calculate numbers.
            DO NOT generate code.

            Explain insights from this data:

            {data.head(10).to_string()}

            Question: {user_input}
            """

            try:
                ai = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}],
                    temperature=0.3
                )
                response = ai.choices[0].message.content
            except:
                response = "AI unavailable"

        # SAVE AI MESSAGE
        st.session_state.messages.append({"role": "assistant", "content": response})

        # SAVE CHART
        if chart_data is not None:
            st.session_state.chart_data = chart_data

        # DISPLAY AI MESSAGE IMMEDIATELY
        with st.chat_message("assistant"):
            st.markdown(response)

    # ---------------- SHOW CHART ----------------
    if st.session_state.chart_data is not None:
        st.line_chart(
            st.session_state.chart_data.set_index("date")[["revenue","cost","profit"]]
        )

else:
    st.info("Upload data to start")
