import streamlit as st
import pandas as pd
from groq import Groq

# ================================
# CONFIG
# ================================
st.set_page_config(page_title="AI Business Copilot", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ================================
# SESSION STATE
# ================================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "user" not in st.session_state:
    st.session_state.user = None

if "business" not in st.session_state:
    st.session_state.business = {}

if "df" not in st.session_state:
    st.session_state.df = None

# ================================
# DARK THEME
# ================================
st.markdown("""
<style>
body {background-color:#0f172a;color:white;}
</style>
""", unsafe_allow_html=True)

# ================================
# SAMPLE DATA
# ================================
def get_sample_data():
    dates = pd.date_range("2026-01-01", periods=60)
    revenue = [1000 + i * 50 for i in range(60)]
    cost = [600 + i * 30 for i in range(60)]
    df = pd.DataFrame({"date": dates, "revenue": revenue, "cost": cost})
    df["profit"] = df["revenue"] - df["cost"]
    df["margin"] = (df["profit"] / df["revenue"] * 100).round(1)
    return df

# ================================
# KPI CARD
# ================================
def kpi_card(title, value):
    st.markdown(f"""
    <div style="background:#111827;padding:20px;border-radius:12px;">
    <h4 style="color:#9CA3AF;">{title}</h4>
    <h2>{value}</h2>
    </div>
    """, unsafe_allow_html=True)

# ================================
# LOGIN PAGE
# ================================
if st.session_state.page == "login":
    st.title("🔐 Login / Signup")

    mode = st.radio("Select", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Signup":
        name = st.text_input("Full Name")

        if st.button("Create Account"):
            st.session_state.user = {"name": name, "email": email}
            st.session_state.page = "onboarding"
            st.rerun()

    else:
        if st.button("Login"):
            st.session_state.user = {"name": email.split("@")[0]}
            st.session_state.page = "dashboard"
            st.rerun()

    st.stop()

# ================================
# ONBOARDING
# ================================
if st.session_state.page == "onboarding":
    st.title("🏢 Setup Your Business")

    name = st.text_input("Business Name")
    industry = st.selectbox("Industry", ["Retail", "Restaurant", "Gas Station", "Other"])
    size = st.selectbox("Size", ["Small", "Medium", "Large"])

    if st.button("Continue"):
        st.session_state.business = {
            "name": name,
            "industry": industry,
            "size": size
        }
        st.session_state.page = "dashboard"
        st.rerun()

    st.stop()

# ================================
# DASHBOARD
# ================================
user = st.session_state.user
business = st.session_state.business

# Sidebar
with st.sidebar:
    st.markdown(f"👤 {user['name']}")
    st.markdown(f"🏢 {business.get('name','')}")

    uploaded_file = st.file_uploader("Upload CSV")

    if st.button("Use Sample Data"):
        st.session_state.df = get_sample_data()

    if st.button("Logout"):
        st.session_state.page = "login"
        st.rerun()

# Load data
if st.session_state.df is None:
    st.session_state.df = get_sample_data()

df = st.session_state.df

# Header
st.title("🚀 AI Business Copilot")

# KPI
col1, col2, col3, col4 = st.columns(4)

with col1: kpi_card("Revenue", f"${df['revenue'].sum():,.0f}")
with col2: kpi_card("Cost", f"${df['cost'].sum():,.0f}")
with col3: kpi_card("Profit", f"${df['profit'].sum():,.0f}")
with col4: kpi_card("Margin", f"{df['margin'].mean():.1f}%")

# Chart
st.markdown("## 📈 Trends")
metric = st.selectbox("Metric", ["revenue", "cost", "profit"])
st.line_chart(df.set_index("date")[[metric]])

# Insights
st.markdown("## 💡 Insights")

if df["cost"].sum() > df["revenue"].sum() * 0.7:
    st.warning("Costs are high")

if df["profit"].mean() > 300:
    st.success("Good profitability")

# AI Assistant
st.markdown("## 🤖 AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.text_input("Ask something...")

if user_input:
    context = f"""
    Revenue: {df['revenue'].sum()}
    Cost: {df['cost'].sum()}
    Profit: {df['profit'].sum()}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": user_input}
        ]
    )

    answer = response.choices[0].message.content

    st.session_state.messages.append(("You", user_input))
    st.session_state.messages.append(("AI", answer))

for role, msg in st.session_state.messages:
    st.write(f"**{role}:** {msg}")
