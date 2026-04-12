import streamlit as st
import pandas as pd
import re
from groq import Groq
 
# CONFIG
st.set_page_config(page_title="BizCopilot", layout="wide", page_icon="chart_with_upwards_trend")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
 
# ================================================================
# GLOBAL CSS - Premium dark UI + sticky chat input
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
 
/* -- Reset & Base -- */
*, *::before, *::after { box-sizing: border-box; }
 
html, body, [data-testid="stAppViewContainer"] {
    background: #13151f !important;
    color: #e2e8f0 !important;
    font-family: 'Outfit', sans-serif !important;
}
 
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #13151f 0%, #181b26 50%, #13151f 100%) !important;
}
 
/* -- Hide Streamlit chrome -- */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
 
/* -- Sidebar -- */
[data-testid="stSidebar"] {
    background: #1a1d2e !important;
    border-right: 1px solid rgba(99,102,241,0.35) !important;
}
 
[data-testid="stSidebar"] * {
    font-family: 'Outfit', sans-serif !important;
}
 
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    color: #a5b4fc !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    padding: 0.5rem 1rem !important;
}
 
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.2) !important;
    border-color: rgba(99,102,241,0.5) !important;
    transform: translateY(-1px) !important;
}
 
/* -- Main content area -- */
[data-testid="stMain"] {
    background: transparent !important;
}
 
.block-container {
    padding: 2rem 2.5rem 0 2.5rem !important;
    max-width: 100% !important;
}
 
/* -- Title -- */
h1 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.9rem !important;
    background: linear-gradient(135deg, #e2e8f0 0%, #a5b4fc 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0 !important;
    letter-spacing: -0.5px !important;
}
 
h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    font-size: 1rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
 
/* -- Success / info banners -- */
[data-testid="stAlert"] {
    background: rgba(99,102,241,0.08) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 12px !important;
    color: #a5b4fc !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.875rem !important;
}
 
/* -- Metric cards -- */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.05) 100%) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 16px !important;
    padding: 1.25rem 1.5rem !important;
    transition: transform 0.2s, border-color 0.2s !important;
}
 
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    border-color: rgba(99,102,241,0.3) !important;
}
 
[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
 
[data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
    color: #f1f5f9 !important;
}
 
/* -- Charts -- */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}
 
/* -- Selectbox -- */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Outfit', sans-serif !important;
}
 
/* -- Expander -- */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
}
 
/* -- Divider -- */
hr {
    border-color: rgba(255,255,255,0.15) !important;
    margin: 1rem 0 !important;
}
 
/* -- File uploader -- */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px dashed rgba(99,102,241,0.5) !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
}
 
/* ================================================================
   CHAT LAYOUT - ChatGPT / Claude style
   ================================================================ */
 
/* The chat messages scroll area */
.chat-scroll-area {
    height: calc(100vh - 340px);
    overflow-y: auto;
    padding: 1rem 0 1.5rem 0;
    display: flex;
    flex-direction: column;
    gap: 0;
    scrollbar-width: thin;
    scrollbar-color: rgba(99,102,241,0.3) transparent;
}
 
.chat-scroll-area::-webkit-scrollbar {
    width: 4px;
}
 
.chat-scroll-area::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.3);
    border-radius: 4px;
}
 
/* Sticky input container pinned to bottom */
.chat-input-sticky {
    position: sticky;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(to top, #13151f 85%, transparent);
    padding: 1rem 0 1.5rem 0;
    z-index: 100;
}
 
/* Chat bubbles */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.75rem;
    animation: slideUp 0.25s ease;
}
 
.msg-user .bubble {
    max-width: 70%;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: #fff;
    border-radius: 20px 20px 4px 20px;
    padding: 0.75rem 1.1rem;
    font-size: 0.925rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(99,102,241,0.25);
}
 
.msg-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 0.75rem;
    gap: 0.6rem;
    align-items: flex-start;
    animation: slideUp 0.25s ease;
}
 
.bot-avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0ea5e9, #6366f1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    flex-shrink: 0;
    margin-top: 2px;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
}
 
.msg-bot .bubble {
    max-width: 75%;
    background: rgba(255,255,255,0.09);
    border: 1px solid rgba(255,255,255,0.18);
    color: #e2e8f0;
    border-radius: 4px 20px 20px 20px;
    padding: 0.75rem 1.1rem;
    font-size: 0.925rem;
    line-height: 1.7;
}
 
.msg-bot .bubble pre {
    background: rgba(0,0,0,0.3);
    border-radius: 8px;
    padding: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    overflow-x: auto;
    margin: 0.5rem 0 0 0;
    border: 1px solid rgba(255,255,255,0.08);
}
 
.msg-bot .bubble code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #a5b4fc;
    background: rgba(99,102,241,0.12);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
}
 
/* Typing indicator */
.typing-indicator {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 0.5rem 0;
}
 
.typing-indicator span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #6366f1;
    animation: typingBounce 1.2s infinite ease-in-out;
}
 
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
 
@keyframes typingBounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
}
 
@keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
 
/* -- Streamlit chat input override -- */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 16px !important;
    box-shadow: 0 0 0 0 rgba(99,102,241,0) !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
 
[data-testid="stChatInput"]:focus-within {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
 
[data-testid="stChatInput"] textarea {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important;
    color: #e2e8f0 !important;
    background: transparent !important;
}
 
[data-testid="stChatInput"] textarea::placeholder {
    color: #475569 !important;
}
 
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border-radius: 10px !important;
    border: none !important;
    color: white !important;
}
 
/* -- Chat message overrides (streamlit native) -- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
 
/* -- Auth / Onboarding forms -- */
.auth-card {
    max-width: 420px;
    margin: 5vh auto;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 24px;
    padding: 2.5rem;
}
 
[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Outfit', sans-serif !important;
}
 
[data-testid="stTextInput"] input:focus {
    border-color: rgba(99,102,241,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}
 
.stRadio label {
    color: #94a3b8 !important;
    font-family: 'Outfit', sans-serif !important;
}
 
/* Primary buttons */
.stButton > button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    transition: opacity 0.2s, transform 0.2s !important;
}
 
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}
 
/* Sidebar specific buttons keep their style */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    color: #a5b4fc !important;
}
 
/* Tag chips for onboarding */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 1rem;
}
 
/* Empty state */
.empty-chat {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 280px;
    color: #64748b;
    text-align: center;
    gap: 1rem;
}
 
.empty-chat-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    margin: 0 auto;
}
 
.empty-chat-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #94a3b8;
    margin: 0;
}
 
.empty-chat-sub {
    font-size: 0.85rem;
    color: #64748b;
    max-width: 320px;
    line-height: 1.6;
    margin: 0;
}
 
.pill-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 440px;
}
 
.pill {
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.35);
    color: #6366f1;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 0.8rem;
    font-family: 'Outfit', sans-serif;
    cursor: pointer;
    transition: all 0.15s;
}
 
.pill:hover {
    background: rgba(99,102,241,0.15);
    color: #a5b4fc;
}
 
/* Sidebar logo */
.sidebar-logo {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    background: linear-gradient(135deg, #e2e8f0, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25rem;
}
 
.sidebar-sub {
    font-size: 0.7rem;
    color: #475569;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 1.5rem;
}
 
.sidebar-stat {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    padding: 0.6rem 0.85rem;
    margin-bottom: 0.5rem;
    font-size: 0.78rem;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
}
 
.sidebar-stat span {
    color: #a5b4fc;
    font-weight: 500;
}
 
/* Force sidebar text to be clearly visible */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}
 
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #cbd5e1 !important;
}
 
/* Sidebar always expanded */
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { min-width: 240px !important; }
 
/* Make sure all body text is visible */
p, span, div, label {
    color: #e2e8f0;
}
 
/* Stronger metric label color */
[data-testid="stMetricLabel"] > div {
    color: #94a3b8 !important;
}
 
/* Make sidebar stat box text fully visible */
.sidebar-stat {
    color: #94a3b8 !important;
}
 
.sidebar-sub {
    color: #94a3b8 !important;
}
 
</style>
""", unsafe_allow_html=True)
 
# ================================================================
# SESSION DEFAULTS
# ================================================================
for key, default in {
    "page": "auth",
    "user": None,
    "business": {},
    "messages": [],
    "df": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default
 
# ================================================================
# AUTH PAGE
# ================================================================
if st.session_state.page == "auth":
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-bottom:2rem;">'
                '<div style="font-family:Outfit,sans-serif;font-weight:800;font-size:2rem;'
                'background:linear-gradient(135deg,#e2e8f0,#a5b4fc);-webkit-background-clip:text;'
                '-webkit-text-fill-color:transparent;background-clip:text;">BizCopilot</div>'
                '<div style="color:#94a3b8;font-size:0.85rem;margin-top:4px;font-family:JetBrains Mono,monospace;">'
                'AI-powered business intelligence</div></div>', unsafe_allow_html=True)
 
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        mode = st.radio("", ["Login", "Signup"], horizontal=True, label_visibility="collapsed")
        email = st.text_input("Email address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Your password")
 
        if mode == "Signup":
            name = st.text_input("Full Name", placeholder="Your name")
            if st.button("Create Account", use_container_width=True):
                if not name or not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    st.session_state.user = {"name": name, "email": email}
                    st.session_state.page = "onboarding"
                    st.rerun()
        else:
            if st.button("Sign In", use_container_width=True):
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    st.session_state.user = {"name": email.split("@")[0].capitalize(), "email": email}
                    st.session_state.page = "app"
                    st.rerun()
    st.stop()
 
# ================================================================
# ONBOARDING PAGE
# ================================================================
if st.session_state.page == "onboarding":
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown('<div style="font-family:Outfit,sans-serif;font-weight:700;font-size:1.5rem;color:#e2e8f0;margin-bottom:0.5rem;">Tell us about your business</div>', unsafe_allow_html=True)
        st.markdown('<div style="color:#94a3b8;font-size:0.875rem;margin-bottom:1.5rem;">We will personalize your dashboard and AI insights.</div>', unsafe_allow_html=True)
 
        industry = st.selectbox("Industry", ["Restaurant", "Retail", "Gas Station", "Services", "Other"])
        size = st.selectbox("Business Size", ["Small (1-10 employees)", "Medium (11-50)", "Large (50+)"])
        business_name = st.text_input("Business Name (optional)", placeholder="e.g. Joe's Diner")
 
        if st.button("Launch Dashboard", use_container_width=True):
            st.session_state.business = {
                "industry": industry,
                "size": size,
                "name": business_name if business_name else ("My " + industry + " Business"),
            }
            st.session_state.page = "app"
            st.rerun()
    st.stop()
 
# ================================================================
# HELPERS
# ================================================================
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
 
def has_word(text, word):
    return bool(re.search(r'\b' + word + r'\b', text))
 
def get_sample_data():
    dates = pd.date_range("2026-01-01", periods=60)
    revenue = [1000 + i * 50 for i in range(60)]
    cost = [600 + i * 30 for i in range(60)]
    df = pd.DataFrame({"date": dates, "revenue": revenue, "cost": cost})
    df["profit"] = df["revenue"] - df["cost"]
    df["margin_pct"] = (df["profit"] / df["revenue"] * 100).round(1)
    return df
 
def clean_dataframe(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    if "date" not in df.columns:
        st.error("CSV must have a date column.")
        return None
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["revenue", "cost"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date"])
    if "revenue" in df.columns and "cost" in df.columns:
        df["profit"] = df["revenue"] - df["cost"]
        df["margin_pct"] = (df["profit"] / df["revenue"].replace(0, pd.NA) * 100).round(1)
    return df
 
def get_months_from_text(text):
    found = []
    for month_name, month_num in MONTH_MAP.items():
        if month_name in text:
            found.append((month_name.capitalize(), month_num))
    return found
 
def filter_by_year(df, text):
    years = re.findall(r'\b(20\d{2})\b', text)
    if not years:
        return df, None
    year = int(years[0])
    filtered = df[df["date"].dt.year == year]
    if filtered.empty:
        return None, str(year)
    return filtered, str(year)
 
def extract_specific_date(text):
    m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(1))
        except Exception:
            pass
    m = re.search(
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'\s+(\d{1,2})[,\s]+(\d{4})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    m = re.search(
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})[,\s]+(\d{4})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    return None
 
def extract_date_filter(df, text):
    after_match = re.search(r'\bafter\b\s+([\w\s,]+?\d{4})', text)
    before_match = re.search(r'\bbefore\b\s+([\w\s,]+?\d{4})', text)
    filtered = df.copy()
    note = ""
    try:
        if after_match:
            dt = pd.to_datetime(after_match.group(1).strip(), infer_datetime_format=True)
            filtered = filtered[filtered["date"] > dt]
            note = "after " + str(dt.date())
        if before_match:
            dt = pd.to_datetime(before_match.group(1).strip(), infer_datetime_format=True)
            filtered = filtered[filtered["date"] < dt]
            note = ("before " + str(dt.date())) if not note else (note + " before " + str(dt.date()))
    except Exception:
        pass
    return filtered, note
 
def build_ai_context(df, full_df=None):
    if full_df is None:
        full_df = df
    monthly = full_df.groupby(full_df["date"].dt.to_period("M")).agg(
        revenue=("revenue", "sum"),
        cost=("cost", "sum"),
        profit=("profit", "sum"),
        days=("revenue", "count")
    ).reset_index()
    monthly_str = ""
    for _, row in monthly.iterrows():
        monthly_str += (
            str(row["date"]) + ": revenue=$" + str(int(row["revenue"])) +
            ", cost=$" + str(int(row["cost"])) +
            ", profit=$" + str(int(row["profit"])) +
            ", days=" + str(int(row["days"])) + "\n"
        )
    recent = full_df.tail(10)[["date", "revenue", "cost", "profit"]].copy()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    recent_str = recent.to_string(index=False)
    total_rev = full_df["revenue"].sum()
    total_cost = full_df["cost"].sum()
    total_profit = full_df["profit"].sum()
    avg_margin = full_df["margin_pct"].mean() if "margin_pct" in full_df.columns else 0
    business = st.session_state.business
    context = (
        "You are an AI business analyst for a " + business.get("industry", "small") +
        " business called " + business.get("name", "this business") +
        " (" + business.get("size", "") + ").\n\n"
        "DATA RANGE: " + str(full_df["date"].min().date()) + " to " + str(full_df["date"].max().date()) + " (" + str(len(full_df)) + " days)\n\n"
        "OVERALL TOTALS:\n"
        "- Total Revenue: $" + f"{total_rev:,.2f}" + "\n"
        "- Total Costs:   $" + f"{total_cost:,.2f}" + "\n"
        "- Total Profit:  $" + f"{total_profit:,.2f}" + "\n"
        "- Avg Margin:    " + f"{avg_margin:.1f}" + "%\n\n"
        "MONTHLY BREAKDOWN:\n" + monthly_str + "\n"
        "RECENT 10 RECORDS:\n" + recent_str + "\n\n"
        "Rules:\n"
        "1. Do NOT use LaTeX, dollar signs in math expressions, or code formatting for numbers.\n"
        "2. Write all money values plainly: $36,450\n"
        "3. Be concise, specific, and data-driven.\n"
        "4. End with one actionable recommendation.\n"
        "5. If asked to group or compare by month, use the MONTHLY BREAKDOWN above.\n"
    )
    return context
 
AI_INTENT_PHRASES = [
    "how to", "how can", "ways to", "best way", "best approach",
    "ideas to", "suggestions", "recommend", "advice", "strategy",
    "improve", "grow", "increase my", "help me", "what should",
    "explain", "tell me about", "performance metric", "performance matrix",
    "kpi", "key performance", "remember", "last question",
    "where is", "who is", "located", "president",
    "varies", "relationship", "compare", "correlation",
    "why", "how is", "is my", "group", "rolling", "risky",
    "sustainable", "trend", "pattern", "sql", "query",
    "give me", "give top", "top 3 days and explain",
]
 
def is_ai_intent(text):
    for phrase in AI_INTENT_PHRASES:
        if phrase in text:
            return True
    return False
 
def detect_multi_intent(text):
    sentences = re.split(r'[?.!]+', text)
    return [s.strip() for s in sentences if s.strip()]
 
def answer_single_intent(sentence, full_df):
    text = sentence.lower()
    if has_word(text, "profit") or has_word(text, "loss") or has_word(text, "gain"):
        metric = "profit"
    elif has_word(text, "cost") or has_word(text, "expense") or has_word(text, "costs"):
        metric = "cost"
    elif has_word(text, "margin"):
        metric = "margin_pct"
    else:
        metric = "revenue"
    months_found = get_months_from_text(text)
    data = full_df.copy()
    if months_found:
        ml, mn = months_found[0]
        data = full_df[full_df["date"].dt.month == mn]
        period = "in " + ml
    else:
        period = "overall"
    if data.empty:
        return period + ": no data"
    if has_word(text, "total") or has_word(text, "sum"):
        return "Total " + metric + " " + period + ": $" + f"{data[metric].sum():,.2f}"
    elif has_word(text, "average") or has_word(text, "avg") or has_word(text, "mean"):
        return "Average " + metric + " " + period + ": $" + f"{data[metric].mean():,.2f}"
    elif has_word(text, "max") or has_word(text, "highest") or has_word(text, "maximum"):
        row = data.loc[data[metric].idxmax()]
        return "Highest " + metric + " " + period + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())
    elif has_word(text, "min") or has_word(text, "lowest") or has_word(text, "minimum"):
        row = data.loc[data[metric].idxmin()]
        return "Lowest " + metric + " " + period + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())
    return None
 
# ================================================================
# MAIN APP
# ================================================================
user = st.session_state.user
business = st.session_state.business
 
# -- Sidebar ------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo">BizCopilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">' + business.get("industry", "Business") + " / " + business.get("size", "") + '</div>', unsafe_allow_html=True)
 
    st.markdown("**Data**")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
 
    if uploaded_file:
        try:
            raw_df = pd.read_csv(uploaded_file)
            cleaned = clean_dataframe(raw_df)
            if cleaned is not None:
                st.session_state.df = cleaned
                st.success("Loaded " + str(len(cleaned)) + " rows")
        except Exception as e:
            st.error("Could not read file: " + str(e))
 
    if st.button("Use Sample Data", use_container_width=True):
        st.session_state.df = get_sample_data()
        st.success("Sample data loaded")
 
    if st.session_state.df is not None:
        _df = st.session_state.df
        st.markdown(
            '<div class="sidebar-stat">Rows: <span>' + str(len(_df)) + '</span></div>'
            '<div class="sidebar-stat">From: <span>' + str(_df["date"].min().date()) + '</span></div>'
            '<div class="sidebar-stat">To: <span>' + str(_df["date"].max().date()) + '</span></div>',
            unsafe_allow_html=True
        )
 
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Logout", use_container_width=True):
        for key in ["page", "user", "business", "messages", "df"]:
            del st.session_state[key]
        st.rerun()
 
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.7rem;color:#94a3b8;font-family:JetBrains Mono,monospace;">'
        'Signed in as<br><span style="color:#6366f1;">' + user["name"] + '</span></div>',
        unsafe_allow_html=True
    )
 
# -- No data guard ------------------------------------------------
if st.session_state.df is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;padding:3rem;">'
        '<div style="font-size:3rem;margin-bottom:1rem;"></div>'
        '<div style="font-family:Outfit,sans-serif;font-size:1.2rem;font-weight:600;color:#94a3b8;margin-bottom:0.5rem;">No data loaded</div>'
        '<div style="color:#94a3b8;font-size:0.875rem;">Upload a CSV or use Sample Data from the sidebar to get started.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()
 
df = st.session_state.df
 
# -- Header -------------------------------------------------------
st.markdown(
    '<h1>AI Business Copilot</h1>'
    '<div style="color:#94a3b8;font-size:0.875rem;margin-top:2px;margin-bottom:1.25rem;">'
    'Welcome back, <span style="color:#a5b4fc;font-weight:600;">' + user["name"] + '</span>'
    ' &nbsp;&bull;&nbsp; ' + business.get("name", "") + '</div>',
    unsafe_allow_html=True
)
 
# -- KPI Row ------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", "$" + f"{df['revenue'].sum():,.2f}")
col2.metric("Total Costs", "$" + f"{df['cost'].sum():,.2f}")
col3.metric("Total Profit", "$" + f"{df['profit'].sum():,.2f}")
if "margin_pct" in df.columns:
    col4.metric("Avg Margin", str(round(df["margin_pct"].mean(), 1)) + "%")
 
# -- Trend chart --------------------------------------------------
c1, c2 = st.columns([1, 3])
with c1:
    metric_choice = st.selectbox("", ["revenue", "cost", "profit"], label_visibility="collapsed")
with c2:
    pass
st.line_chart(df.set_index("date")[[metric_choice]], height=200)
 
with st.expander("Raw Data"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
 
st.markdown('<hr style="margin:1.25rem 0;">', unsafe_allow_html=True)
 
# ================================================================
# CHAT SECTION - ChatGPT/Claude style layout
# ================================================================
st.markdown('<h2 style="margin-bottom:0.75rem;">AI Assistant</h2>', unsafe_allow_html=True)
 
# -- Render chat history in a scrollable area ------------------
msgs_html = '<div class="chat-scroll-area" id="chatArea">'
 
if not st.session_state.messages:
    msgs_html += '''
    <div class="empty-chat">
        <div class="empty-chat-icon">*</div>
        <p class="empty-chat-title">Ask anything about your data</p>
        <p class="empty-chat-sub">Try: "What are my top 5 profit days?" or "Compare January and February performance"</p>
        <div class="pill-grid">
            <span class="pill">Total revenue?</span>
            <span class="pill">Top 10 profit days</span>
            <span class="pill">How is my business?</span>
            <span class="pill">Show revenue trend</span>
            <span class="pill">Ways to reduce costs</span>
        </div>
    </div>
    '''
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            msgs_html += (
                '<div class="msg-user"><div class="bubble">' +
                msg["content"].replace("\n", "<br>") +
                '</div></div>'
            )
        else:
            content = msg["content"].replace("\n", "<br>")
            msgs_html += (
                '<div class="msg-bot">'
                '<div class="bot-avatar">AI</div>'
                '<div class="bubble">' + content + '</div>'
                '</div>'
            )
 
msgs_html += '</div>'
 
# Auto-scroll JS
msgs_html += '''
<script>
    const area = document.getElementById("chatArea");
    if (area) { area.scrollTop = area.scrollHeight; }
</script>
'''
 
st.markdown(msgs_html, unsafe_allow_html=True)
 
# -- Render charts for messages that have them ------------------
for msg in st.session_state.messages:
    if msg.get("chart") is not None:
        try:
            chart_data = msg["chart"].set_index("date")
            allowed = [c for c in ["revenue", "cost", "profit"] if c in chart_data.columns]
            if msg.get("show_multi"):
                cols_to_show = allowed
            elif msg.get("chart_metric") and msg["chart_metric"] in chart_data.columns:
                cols_to_show = [msg["chart_metric"]]
            else:
                cols_to_show = allowed
            if msg.get("chart_type") == "bar":
                st.bar_chart(chart_data[cols_to_show], height=220)
            else:
                st.line_chart(chart_data[cols_to_show], height=220)
        except Exception:
            pass
 
# -- Sticky chat input (always visible at bottom) --------------
st.markdown('<div class="chat-input-sticky">', unsafe_allow_html=True)
user_input = st.chat_input("Ask anything about your data...")
st.markdown('</div>', unsafe_allow_html=True)
 
# ================================================================
# MESSAGE PROCESSING
# ================================================================
if user_input:
    text = user_input.lower()
    full_df = df.copy()
    data = df.copy()
    response = ""
    chart_df_out = None
    chart_metric_out = "revenue"
    chart_type_out = "line"
    show_multi = False
 
    # Specific date lookup
    specific_date = extract_specific_date(text)
    is_asking_total_month = (has_word(text, "total") or has_word(text, "sum")) and any(m in text for m in MONTH_MAP)
    if specific_date is not None and not is_asking_total_month:
        row = full_df[full_df["date"].dt.date == specific_date.date()]
        if row.empty:
            response = (
                "No data found for " + str(specific_date.date()) +
                ". Data covers " + str(full_df["date"].min().date()) +
                " to " + str(full_df["date"].max().date()) + "."
            )
        else:
            r = row.iloc[0]
            response = (
                "On " + str(r["date"].date()) + ":\n"
                "- Revenue: $" + f"{r['revenue']:,.2f}" + "\n"
                "- Cost:    $" + f"{r['cost']:,.2f}" + "\n"
                "- Profit:  $" + f"{r['profit']:,.2f}"
            )
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
 
    # AI intent check
    if is_ai_intent(text):
        context = build_ai_context(data, full_df)
        try:
            ai_resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            response = ai_resp.choices[0].message.content
        except Exception as e:
            response = "Something went wrong with AI: " + str(e)
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
 
    # Multi-intent detection
    multi_intents = detect_multi_intent(text)
    if len(multi_intents) > 1:
        parts = []
        for sentence in multi_intents:
            ans = answer_single_intent(sentence, full_df)
            if ans:
                parts.append(ans)
        if parts:
            response = "\n\n".join(parts)
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
 
    # Year filter
    data, matched_year = filter_by_year(data, text)
    if data is None:
        response = "No data found for " + matched_year + ". Data covers " + str(full_df["date"].min().date()) + " to " + str(full_df["date"].max().date()) + "."
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
 
    # After/before date filter
    data, date_filter_note = extract_date_filter(full_df, text)
 
    # Month filter
    months_found = get_months_from_text(text)
    matched_month = None
    if not date_filter_note and months_found:
        ml, mn = months_found[0]
        month_data = full_df[full_df["date"].dt.month == mn]
        if not month_data.empty:
            data = month_data
            matched_month = ml
 
    # Metric detection
    if has_word(text, "profit") or has_word(text, "loss") or has_word(text, "gain"):
        metric = "profit"
    elif has_word(text, "cost") or has_word(text, "expense") or has_word(text, "costs") or has_word(text, "expenses"):
        metric = "cost"
    elif has_word(text, "margin"):
        metric = "margin_pct"
    elif has_word(text, "sales") or has_word(text, "revenue") or has_word(text, "income"):
        metric = "revenue"
    else:
        metric = "revenue"
 
    chart_metric_out = metric if metric in ["revenue", "cost", "profit"] else "revenue"
    if "bar" in text:
        chart_type_out = "bar"
 
    is_chart = any(k in text for k in ["chart", "graph", "trend", "plot", "visualize", "draw", "display"])
    is_total = (has_word(text, "total") or has_word(text, "sum")) and not is_chart
    is_avg = (has_word(text, "average") or has_word(text, "avg") or has_word(text, "mean")) and not is_chart
    is_max = has_word(text, "max") or has_word(text, "highest") or has_word(text, "maximum")
    is_min = has_word(text, "min") or has_word(text, "lowest") or has_word(text, "minimum")
    is_top = has_word(text, "top") and not is_ai_intent(text)
 
    if date_filter_note:
        period_label = date_filter_note
    elif matched_month:
        period_label = "in " + matched_month
    elif matched_year:
        period_label = "in " + matched_year
    else:
        period_label = "overall"
 
    try:
        if (is_max or is_min) and len(months_found) > 1:
            parts = []
            for mlabel, mnum in months_found:
                md = full_df[full_df["date"].dt.month == mnum]
                if md.empty:
                    parts.append(mlabel + ": no data")
                    continue
                if is_max:
                    row = md.loc[md[metric].idxmax()]
                    parts.append(mlabel + " - Highest " + metric + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date()))
                else:
                    row = md.loc[md[metric].idxmin()]
                    parts.append(mlabel + " - Lowest " + metric + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date()))
            response = "\n\n".join(parts)
 
        elif is_max:
            if data.empty:
                response = "No data found for that period."
            else:
                row = data.loc[data[metric].idxmax()]
                response = "Highest " + metric + " " + period_label + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())
 
        elif is_min:
            if data.empty:
                response = "No data found for that period."
            else:
                row = data.loc[data[metric].idxmin()]
                response = "Lowest " + metric + " " + period_label + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())
 
        elif is_total:
            if data.empty:
                response = "No data found for that period."
            else:
                response = "Total " + metric + " " + period_label + ": $" + f"{data[metric].sum():,.2f}"
 
        elif is_avg:
            if data.empty:
                response = "No data found for that period."
            else:
                response = "Average " + metric + " " + period_label + ": $" + f"{data[metric].mean():,.2f}"
 
        elif is_top:
            n = next((int(w) for w in text.split() if w.isdigit()), 5)
            top_df = data.sort_values(metric, ascending=False).head(n)[["date", "revenue", "cost", "profit"]]
            response = "Top " + str(n) + " days by " + metric + ":\n\n" + top_df.to_string(index=False)
            chart_df_out = top_df.sort_values("date")[["date", metric]]
            chart_metric_out = metric if metric in ["revenue", "cost", "profit"] else "revenue"
 
        elif is_chart:
            show_both = any(p in text for p in ["and expense", "and cost", "versus", "vs", "and revenue", "and sales", "and profit"])
            if show_both:
                cols = []
                if has_word(text, "sales") or has_word(text, "revenue"):
                    cols.append("revenue")
                if has_word(text, "expense") or has_word(text, "cost") or has_word(text, "expenses"):
                    cols.append("cost")
                if has_word(text, "profit"):
                    cols.append("profit")
                cols = cols if cols else ["revenue", "cost"]
                response = "Chart: " + " & ".join(cols) + " " + period_label
                chart_df_out = data[["date"] + cols]
                chart_metric_out = cols[0]
                show_multi = True
            else:
                response = metric.capitalize() + " trend " + period_label
                chart_df_out = data[["date", metric]]
                chart_metric_out = metric if metric in ["revenue", "cost", "profit"] else "revenue"
 
        else:
            context = build_ai_context(data, full_df)
            ai_resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            response = ai_resp.choices[0].message.content
 
    except KeyError as e:
        response = "Column not found: " + str(e) + ". Available: " + ", ".join(df.columns.tolist())
    except Exception as e:
        response = "Something went wrong: " + str(e)
 
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "chart": chart_df_out,
        "chart_metric": chart_metric_out,
        "chart_type": chart_type_out,
        "show_multi": show_multi,
    })
    st.rerun()
