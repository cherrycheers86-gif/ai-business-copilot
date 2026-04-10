import streamlit as st
import pandas as pd
from groq import Groq

# Page config
st.set_page_config(page_title="AI Business Copilot", layout="wide")

# API Key
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Title
st.title("🚀 AI Business Copilot")
st.markdown("Analyze your business data and get AI insights instantly")

# Sidebar
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

# Chat memory
if "history" not in st.session_state:
    st.session_state.history = []

# Main content
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Add Profit column
    df["Profit"] = df["Sales"] - df["Expenses"]

    # Layout with columns
    col1, col2 = st.columns([2, 1])

    # LEFT SIDE → DATA + CHARTS
    with col1:
        st.subheader("📊 Business Data")
        st.dataframe(df)

        st.subheader("📈 Trends")
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

    # RIGHT SIDE → INSIGHTS
    with col2:
        st.subheader("📌 Key Insights")

        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        st.metric("💰 Total Sales", f"${total_sales}")
        st.metric("💸 Total Expenses", f"${total_expenses}")
        st.metric("📈 Total Profit", f"${total_profit}")

        if total_profit > 0:
            st.success("✅ Profitable business")
        else:
            st.error("❌ Not profitable")

        if total_expenses > total_sales * 0.7:
            st.warning("⚠️ Expenses are high")

        if df["Sales"].iloc[-1] < df["Sales"].mean():
            st.warning("⚠️ Recent sales are low")

    # CHAT SECTION
    st.divider()
    st.subheader("💬 Ask AI about your business")

    user_input = st.text_input("Type your question here...")

    if user_input:
        summary = df.describe().to_string()

        prompt = f"""
        You are a professional business consultant.

        Analyze the data and provide:
        - Key insights
        - Problems
        - Suggestions

        Data:
        {summary}

        Question: {user_input}
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        ai_reply = response.choices[0].message.content

        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("AI", ai_reply))

    # Chat display
    if st.session_state.history:
        for role, msg in st.session_state.history:
            if role == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")

else:
    st.info("👈 Upload a CSV file from the sidebar to get started")
