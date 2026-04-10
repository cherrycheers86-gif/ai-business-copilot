import streamlit as st
import pandas as pd
from groq import Groq
import io

# Page config
st.set_page_config(page_title="AI Business Copilot", layout="wide")

# 🔐 Secure API Key
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Title
st.title("🚀 AI Business Copilot")
st.markdown("Analyze your business data and get smart insights instantly")

# Sidebar
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

# Chat memory
if "history" not in st.session_state:
    st.session_state.history = []

# Main logic
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Add Profit column
    df["Profit"] = df["Sales"] - df["Expenses"]

    # Layout
    col1, col2 = st.columns([2, 1])

    # LEFT SIDE → Data + Charts
    with col1:
        st.subheader("📊 Business Data")
        st.dataframe(df)

        st.subheader("📈 Trends")
        st.line_chart(df[["Sales", "Expenses", "Profit"]])

    # RIGHT SIDE → Metrics + Insights
    with col2:
        st.subheader("📌 Key Metrics")

        total_sales = df["Sales"].sum()
        total_expenses = df["Expenses"].sum()
        total_profit = df["Profit"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Sales", f"${total_sales}")
        c2.metric("💸 Expenses", f"${total_expenses}")
        c3.metric("📈 Profit", f"${total_profit}")

        st.divider()

        # 🚨 Problem Detection
        st.subheader("🚨 Detected Issues")

        if total_profit > 0:
            st.success("✅ Business is profitable")
        else:
            st.error("❌ Business is running at a loss")

        if total_expenses > total_sales * 0.7:
            st.warning("⚠️ Expenses are too high")

        if df["Sales"].iloc[-1] < df["Sales"].mean():
            st.warning("⚠️ Recent sales are below average")

        # 💡 Recommendations
        st.subheader("💡 Recommendations")

        if total_expenses > total_sales * 0.7:
            st.write("- Reduce supplier costs")
            st.write("- Optimize inventory")

        if df["Sales"].iloc[-1] < df["Sales"].mean():
            st.write("- Increase promotions")
            st.write("- Focus on best-selling products")

        if total_profit > 0:
            st.write("- Reinvest profits into growth")

        # 📥 Download Report
        st.subheader("📥 Download Report")

        report = f"""
Business Summary

Total Sales: {total_sales}
Total Expenses: {total_expenses}
Total Profit: {total_profit}
"""

        buffer = io.StringIO()
        buffer.write(report)

        st.download_button(
            label="Download Report",
            data=buffer.getvalue(),
            file_name="business_report.txt",
            mime="text/plain"
        )

    # 🤖 AI Chat Section
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

        Keep it simple and actionable.

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
        st.subheader("🧠 Conversation")
        for role, msg in st.session_state.history:
            if role == "You":
                st.markdown(f"**🧑 You:** {msg}")
            else:
                st.markdown(f"**🤖 AI:** {msg}")

else:
    st.info("👈 Upload a CSV file from the sidebar to get started")
