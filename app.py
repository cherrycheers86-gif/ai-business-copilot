import streamlit as st
import pandas as pd
import re
from groq import Groq

# CONFIG
st.set_page_config(page_title="BizCopilot", layout="wide", page_icon="chart_with_upwards_trend")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --cream:   #FAF7F2;
  --sand:    #F0EBE1;
  --linen:   #E8E0D0;
  --stone:   #C4BAA8;
  --ink:     #1C1917;
  --ink-mid: #44403C;
  --ink-soft:#78716C;
  --teal:    #0D9488;
  --teal-lt: #14B8A6;
  --amber:   #D97706;
  --rose:    #E11D48;
  --card-bg: rgba(255,255,255,0.82);
  --border:  rgba(196,186,168,0.55);
  --shadow:  0 4px 24px rgba(28,25,23,0.08);
  --shadow-lg: 0 12px 48px rgba(28,25,23,0.13);
  --radius:  20px;
  --font-display: 'Playfair Display', serif;
  --font-body:    'DM Sans', sans-serif;
  --font-mono:    'DM Mono', monospace;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--cream) !important;
  color: var(--ink) !important;
  font-family: var(--font-body) !important;
}

[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 10% 0%,  rgba(13,148,136,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 90% 100%, rgba(217,119,6,0.07)  0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 50%,  rgba(225,29,72,0.03)  0%, transparent 70%);
  pointer-events: none; z-index: 0;
}

[data-testid="stMain"] { background: transparent !important; position: relative; z-index: 1; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

.block-container { padding: 2rem 2.5rem 0 2.5rem !important; max-width: 100% !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
  background: rgba(240,235,225,0.92) !important;
  backdrop-filter: blur(20px) !important;
  border-right: 1.5px solid var(--border) !important;
}
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { min-width: 250px !important; }
[data-testid="stSidebar"] * { font-family: var(--font-body) !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label { color: var(--ink-mid) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--ink-mid) !important; }

[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  background: rgba(13,148,136,0.08) !important;
  border: 1px solid rgba(13,148,136,0.3) !important;
  color: var(--teal) !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  transition: all 0.2s ease !important;
  padding: 0.55rem 1rem !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(13,148,136,0.15) !important;
  border-color: rgba(13,148,136,0.5) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(13,148,136,0.15) !important;
}

/* HEADINGS */
h1 {
  font-family: var(--font-display) !important;
  font-weight: 800 !important; font-size: 2rem !important;
  color: var(--ink) !important; letter-spacing: -0.03em !important;
  -webkit-text-fill-color: unset !important; background: none !important;
}
h2, h3 {
  font-family: var(--font-body) !important; font-weight: 600 !important;
  color: var(--ink-soft) !important; font-size: 0.7rem !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important;
}

/* METRIC CARDS */
[data-testid="stMetric"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.4rem 1.6rem !important;
  transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1) !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(12px) !important;
  position: relative !important; overflow: hidden !important;
}
[data-testid="stMetric"]::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--teal), var(--teal-lt));
  opacity: 0; transition: opacity 0.3s;
}
[data-testid="stMetric"]:hover { transform: translateY(-4px) !important; box-shadow: var(--shadow-lg) !important; border-color: rgba(13,148,136,0.3) !important; }
[data-testid="stMetric"]:hover::before { opacity: 1; }
[data-testid="stMetricLabel"] { font-family: var(--font-mono) !important; font-size: 0.6rem !important; color: var(--ink-soft) !important; text-transform: uppercase !important; letter-spacing: 0.12em !important; }
[data-testid="stMetricLabel"] > div { color: var(--ink-soft) !important; }
[data-testid="stMetricValue"] { font-family: var(--font-display) !important; font-weight: 700 !important; font-size: 1.75rem !important; color: var(--ink) !important; letter-spacing: -0.02em !important; }

/* CHARTS */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.25rem !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(12px) !important;
}

/* SELECTBOX */
[data-testid="stSelectbox"] > div > div {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important; color: var(--ink) !important;
  box-shadow: var(--shadow) !important;
}

/* EXPANDER */
[data-testid="stExpander"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  backdrop-filter: blur(12px) !important;
}

/* DIVIDER */
hr { border-color: var(--linen) !important; margin: 1.25rem 0 !important; }

/* FILE UPLOADER */
[data-testid="stFileUploader"] {
  background: rgba(255,255,255,0.6) !important;
  border: 1.5px dashed rgba(13,148,136,0.4) !important;
  border-radius: 14px !important; padding: 0.5rem !important;
}

/* ALERT */
[data-testid="stAlert"] {
  background: rgba(13,148,136,0.07) !important;
  border: 1px solid rgba(13,148,136,0.25) !important;
  border-radius: 12px !important; color: var(--teal) !important;
  font-size: 0.875rem !important;
}

/* TEXT INPUTS */
[data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.8) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important; color: var(--ink) !important;
  font-family: var(--font-body) !important; font-size: 0.95rem !important;
}
[data-testid="stTextInput"] input:focus {
  border-color: rgba(13,148,136,0.5) !important;
  box-shadow: 0 0 0 3px rgba(13,148,136,0.1) !important; outline: none !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--stone) !important; }

/* RADIO */
.stRadio label { color: var(--ink-mid) !important; font-family: var(--font-body) !important; }

/* BUTTONS */
.stButton > button {
  background: linear-gradient(135deg, var(--teal) 0%, #0A7C72 100%) !important;
  border: none !important; border-radius: 12px !important;
  color: #fff !important; font-weight: 600 !important;
  font-size: 0.9rem !important; letter-spacing: 0.02em !important;
  padding: 0.6rem 1.5rem !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 4px 14px rgba(13,148,136,0.3) !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(13,148,136,0.35) !important;
  filter: brightness(1.05) !important;
}

/* ======================================================
   CHAT  - ChatGPT/Claude style
   ====================================================== */
.chat-scroll-area {
  overflow-y: auto; padding: 1rem 0 1.5rem 0;
  scrollbar-width: thin; scrollbar-color: var(--stone) transparent;
}
.chat-scroll-area::-webkit-scrollbar { width: 4px; }
.chat-scroll-area::-webkit-scrollbar-thumb { background: var(--stone); border-radius: 4px; }

/* sticky input wrapper */
.chat-input-sticky {
  position: sticky; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, var(--cream) 80%, transparent);
  padding: 1rem 0 1.5rem 0; z-index: 100;
}

/* bubbles */
.msg-user {
  display: flex; justify-content: flex-end;
  margin-bottom: 1rem;
  animation: msgIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
.msg-user .bubble {
  max-width: 68%;
  background: linear-gradient(135deg, var(--teal) 0%, #0A7C72 100%);
  color: #fff; border-radius: 22px 22px 5px 22px;
  padding: 0.85rem 1.2rem; font-size: 0.92rem; line-height: 1.65;
  box-shadow: 0 6px 24px rgba(13,148,136,0.25); font-family: var(--font-body);
}
.msg-bot {
  display: flex; justify-content: flex-start;
  margin-bottom: 1rem; gap: 0.7rem; align-items: flex-start;
  animation: msgIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
.bot-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), var(--amber));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
  margin-top: 2px; color: white; font-family: var(--font-mono);
  box-shadow: 0 4px 12px rgba(13,148,136,0.3);
}
.msg-bot .bubble {
  max-width: 74%; background: var(--card-bg);
  border: 1px solid var(--border); color: var(--ink);
  border-radius: 5px 22px 22px 22px;
  padding: 0.85rem 1.2rem; font-size: 0.92rem; line-height: 1.75;
  box-shadow: var(--shadow); backdrop-filter: blur(12px);
  font-family: var(--font-body);
}
.msg-bot .bubble pre {
  background: var(--sand); border-radius: 10px; padding: 0.85rem;
  font-family: var(--font-mono); font-size: 0.8rem; overflow-x: auto;
  margin: 0.6rem 0 0 0; border: 1px solid var(--linen);
}
.msg-bot .bubble code {
  font-family: var(--font-mono); font-size: 0.83rem; color: var(--teal);
  background: rgba(13,148,136,0.08); padding: 0.1rem 0.4rem; border-radius: 5px;
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)  scale(1); }
}

/* CHAT INPUT */
[data-testid="stChatInput"] {
  background: var(--card-bg) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 18px !important; box-shadow: var(--shadow) !important;
  backdrop-filter: blur(16px) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stChatInput"]:focus-within {
  border-color: rgba(13,148,136,0.5) !important;
  box-shadow: 0 0 0 4px rgba(13,148,136,0.1), var(--shadow) !important;
}
[data-testid="stChatInput"] textarea {
  font-family: var(--font-body) !important; font-size: 0.95rem !important;
  color: var(--ink) !important; background: transparent !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--stone) !important; }
[data-testid="stChatInput"] button {
  background: linear-gradient(135deg, var(--teal), #0A7C72) !important;
  border-radius: 12px !important; border: none !important; color: white !important;
}
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 0 !important; }

/* EMPTY CHAT */
.empty-chat {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; min-height: 300px; text-align: center; gap: 1.2rem;
}
.empty-chat-icon {
  width: 72px; height: 72px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(13,148,136,0.12), rgba(217,119,6,0.12));
  border: 1.5px solid rgba(13,148,136,0.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.8rem; margin: 0 auto;
  box-shadow: 0 8px 24px rgba(13,148,136,0.12);
}
.empty-chat-title {
  font-family: var(--font-display); font-size: 1.15rem; font-weight: 700;
  color: var(--ink-mid); margin: 0; letter-spacing: -0.02em;
}
.empty-chat-sub {
  font-size: 0.875rem; color: var(--ink-soft);
  max-width: 320px; line-height: 1.65; margin: 0;
}
.pill-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 480px; }
.pill {
  background: rgba(255,255,255,0.75); border: 1px solid var(--border); color: var(--teal);
  border-radius: 50px; padding: 7px 16px; font-size: 0.8rem; font-family: var(--font-body);
  cursor: pointer; transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(28,25,23,0.06); backdrop-filter: blur(8px);
}
.pill:hover { background: rgba(13,148,136,0.08); border-color: rgba(13,148,136,0.35); transform: translateY(-1px); }

/* SIDEBAR ELEMENTS */
.sidebar-logo { font-family: var(--font-display); font-weight: 800; font-size: 1.4rem; color: var(--ink); letter-spacing: -0.03em; margin-bottom: 0.2rem; }
.sidebar-sub { font-size: 0.68rem; color: var(--ink-soft) !important; font-family: var(--font-mono); margin-bottom: 1.5rem; letter-spacing: 0.05em; }
.sidebar-stat {
  background: rgba(255,255,255,0.65); border: 1px solid var(--border);
  border-radius: 12px; padding: 0.65rem 0.9rem; margin-bottom: 0.5rem;
  font-size: 0.75rem; color: var(--ink-soft) !important; font-family: var(--font-mono);
  box-shadow: 0 2px 8px rgba(28,25,23,0.05); backdrop-filter: blur(8px);
}
.sidebar-stat span { color: var(--teal); font-weight: 600; }

/* SECTION LABEL */
.section-label {
  font-size: 0.65rem; font-family: var(--font-mono); color: var(--ink-soft);
  text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 0.75rem;
  display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--linen); }

/* HEADER */
.header-welcome { font-size: 0.875rem; color: var(--ink-soft); font-family: var(--font-body); margin-top: 2px; margin-bottom: 1.25rem; }
.header-welcome strong { color: var(--teal); }
.status-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(13,148,136,0.08); border: 1px solid rgba(13,148,136,0.22);
  border-radius: 50px; padding: 5px 14px; font-size: 0.75rem;
  color: var(--teal); font-family: var(--font-mono); font-weight: 500;
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--teal);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { transform: scale(1); opacity: 1; }
  50%      { transform: scale(1.4); opacity: 0.6; }
}

/* AI SECTION HEADER */
.ai-section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.ai-orb {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), var(--amber));
  box-shadow: 0 4px 12px rgba(13,148,136,0.3); flex-shrink: 0;
}
.ai-section-title { font-family: var(--font-display); font-weight: 700; font-size: 1.1rem; color: var(--ink); letter-spacing: -0.02em; }

/* ONBOARDING */
.onboard-title { font-family: var(--font-display); font-weight: 800; font-size: 1.7rem; color: var(--ink); letter-spacing: -0.03em; margin-bottom: 0.4rem; }
.onboard-sub { color: var(--ink-soft); font-size: 0.875rem; margin-bottom: 1.75rem; }

/* AUTH */
.auth-logo { font-family: var(--font-display); font-weight: 900; font-size: 2.4rem; color: var(--ink); letter-spacing: -0.04em; margin-bottom: 4px; }
.auth-tagline { font-size: 0.8rem; color: var(--ink-soft); font-family: var(--font-mono); margin-bottom: 2rem; letter-spacing: 0.04em; }

p, span, div, label { color: var(--ink); }
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
    st.markdown("""
    <div style="text-align:center;padding:3rem 0 1.5rem 0;">
      <div class="auth-logo">BizCopilot</div>
      <div class="auth-tagline">AI-powered business intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.1, 1])
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
        st.markdown('<div class="onboard-title">Tell us about<br>your business.</div>', unsafe_allow_html=True)
        st.markdown('<div class="onboard-sub">We will personalize your dashboard and AI insights.</div>', unsafe_allow_html=True)
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
        m_data = full_df[full_df["date"].dt.to_period("M") == row["date"]]
        avg_rev = m_data["revenue"].mean()
        avg_profit = m_data["profit"].mean()
        max_p_row = m_data.loc[m_data["profit"].idxmax()]
        min_p_row = m_data.loc[m_data["profit"].idxmin()]
        monthly_str += (
            str(row["date"]) +
            f": total_revenue=${int(row['revenue']):,}" +
            f", total_cost=${int(row['cost']):,}" +
            f", total_profit=${int(row['profit']):,}" +
            f", avg_daily_revenue=${avg_rev:,.2f}" +
            f", avg_daily_profit=${avg_profit:,.2f}" +
            f", max_profit_day=${max_p_row['profit']:,.2f} on {max_p_row['date'].date()}" +
            f", min_profit_day=${min_p_row['profit']:,.2f} on {min_p_row['date'].date()}" +
            f", days={int(row['days'])}\n"
        )
    top5_profit = full_df.nlargest(5, "profit")[["date", "revenue", "cost", "profit"]]
    top5_str = ""
    for _, r in top5_profit.iterrows():
        top5_str += f"  {r['date'].date()}: revenue=${r['revenue']:,}, cost=${r['cost']:,}, profit=${r['profit']:,}\n"
    corr = full_df["revenue"].corr(full_df["cost"])
    total_rev = full_df["revenue"].sum()
    total_cost = full_df["cost"].sum()
    total_profit = full_df["profit"].sum()
    avg_profit = full_df["profit"].mean()
    avg_margin = full_df["margin_pct"].mean() if "margin_pct" in full_df.columns else 0
    max_p = full_df.loc[full_df["profit"].idxmax()]
    min_p = full_df.loc[full_df["profit"].idxmin()]
    max_r = full_df.loc[full_df["revenue"].idxmax()]
    business = st.session_state.business
    context = (
        "You are an AI business analyst for a " + business.get("industry", "small") +
        " business called " + business.get("name", "this business") +
        " (" + business.get("size", "") + ").\n\n"
        "DATA RANGE: " + str(full_df["date"].min().date()) + " to " + str(full_df["date"].max().date()) + " (" + str(len(full_df)) + " days)\n\n"
        "CRITICAL: Use ONLY the pre-computed numbers below. Do NOT recalculate.\n\n"
        "OVERALL TOTALS:\n"
        f"- Total Revenue: ${total_rev:,.2f}\n"
        f"- Total Costs:   ${total_cost:,.2f}\n"
        f"- Total Profit:  ${total_profit:,.2f}\n"
        f"- Avg Daily Profit: ${avg_profit:,.2f}\n"
        f"- Avg Margin:    {avg_margin:.1f}%\n"
        f"- Max Profit: ${max_p['profit']:,.2f} on {max_p['date'].date()}\n"
        f"- Min Profit: ${min_p['profit']:,.2f} on {min_p['date'].date()}\n"
        f"- Highest Revenue Day: {max_r['date'].date()} with ${max_r['revenue']:,.2f}\n"
        f"- Revenue/Cost Correlation: {corr:.4f}\n\n"
        "TOP 5 PROFIT DAYS:\n" + top5_str + "\n"
        "MONTHLY BREAKDOWN:\n" + monthly_str + "\n"
        "Rules:\n"
        "1. ONLY use the numbers provided. Do NOT recalculate.\n"
        "2. Write money values plainly: $36,450\n"
        "3. Be concise, specific, data-driven.\n"
        "4. End with one actionable recommendation.\n"
        "5. For month-specific questions, use the MONTHLY BREAKDOWN above.\n"
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
    "why", "how is", "is my", "group", "risky",
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

# SIDEBAR
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">BizCopilot</div>'
        '<div class="sidebar-sub">' +
        business.get("industry", "Business").upper() + " / " +
        business.get("size", "").split(" ")[0].upper() +
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
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
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-stat">Records <span>' + str(len(_df)) + '</span></div>'
            '<div class="sidebar-stat">From <span>' + str(_df["date"].min().date()) + '</span></div>'
            '<div class="sidebar-stat">To <span>' + str(_df["date"].max().date()) + '</span></div>',
            unsafe_allow_html=True
        )
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        for key in ["page", "user", "business", "messages", "df"]:
            del st.session_state[key]
        st.rerun()
    st.markdown(
        '<div style="margin-top:1rem;font-size:0.7rem;color:var(--ink-soft);font-family:var(--font-mono);">'
        + user["name"] + '</div>',
        unsafe_allow_html=True
    )

# NO DATA STATE
if st.session_state.df is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1.2rem;">&#128202;</div>'
        '<div style="font-family:Playfair Display,serif;font-size:1.4rem;font-weight:700;'
        'color:#44403C;margin-bottom:0.6rem;">No data loaded</div>'
        '<div style="color:#78716C;font-size:0.9rem;line-height:1.6;max-width:360px;margin:0 auto;">'
        'Upload a CSV file or click <strong>Use Sample Data</strong> in the sidebar to begin.</div>'
        '</div>',
        unsafe_allow_html=True
    )
    st.stop()

df = st.session_state.df

# HEADER
row_h1, row_h2 = st.columns([3, 1])
with row_h1:
    st.markdown(
        '<h1>AI Business Copilot</h1>'
        '<div class="header-welcome">Welcome back, <strong>' + user["name"] + '</strong>'
        ' &nbsp;&mdash;&nbsp; ' + business.get("name", "") + '</div>',
        unsafe_allow_html=True
    )
with row_h2:
    st.markdown(
        '<div style="display:flex;justify-content:flex-end;align-items:center;height:100%;padding-top:0.5rem;">'
        '<div class="status-badge"><div class="status-dot"></div>Live</div>'
        '</div>',
        unsafe_allow_html=True
    )

# KPI ROW
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", "$" + f"{df['revenue'].sum():,.2f}")
col2.metric("Total Costs", "$" + f"{df['cost'].sum():,.2f}")
col3.metric("Total Profit", "$" + f"{df['profit'].sum():,.2f}")
if "margin_pct" in df.columns:
    col4.metric("Avg Margin", str(round(df["margin_pct"].mean(), 1)) + "%")

# TREND CHART
st.markdown('<div class="section-label" style="margin-top:1.5rem;">Performance Trend</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 5])
with c1:
    metric_choice = st.selectbox("", ["revenue", "cost", "profit"], label_visibility="collapsed")
st.line_chart(df.set_index("date")[[metric_choice]], height=210)

with st.expander("View Raw Data"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

st.markdown('<hr>', unsafe_allow_html=True)

# AI SECTION HEADER
st.markdown(
    '<div class="ai-section-header">'
    '<div class="ai-orb"></div>'
    '<div class="ai-section-title">AI Business Analyst</div>'
    '</div>',
    unsafe_allow_html=True
)

# CHAT MESSAGES
if not st.session_state.messages:
    st.markdown('''
    <div class="empty-chat">
      <div class="empty-chat-icon">&#10022;</div>
      <p class="empty-chat-title">Ask anything about your data</p>
      <p class="empty-chat-sub">Your AI analyst is ready. Ask a question or pick a prompt below.</p>
      <div class="pill-grid">
        <span class="pill">Total revenue?</span>
        <span class="pill">Top 5 profit days</span>
        <span class="pill">How is my business doing?</span>
        <span class="pill">Revenue trend chart</span>
        <span class="pill">Ways to reduce costs</span>
        <span class="pill">Compare Jan and Feb</span>
      </div>
    </div>
    ''', unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                '<div class="msg-user"><div class="bubble">' +
                msg["content"].replace("\n", "<br>") + '</div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="msg-bot"><div class="bot-avatar">AI</div>'
                '<div class="bubble">' + msg["content"].replace("\n", "<br>") + '</div></div>',
                unsafe_allow_html=True
            )
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

# STICKY INPUT
st.markdown('<div class="chat-input-sticky">', unsafe_allow_html=True)
user_input = st.chat_input("Ask anything about your business data...")
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

    # Specific date
    specific_date = extract_specific_date(text)
    is_asking_total_month = (has_word(text, "total") or has_word(text, "sum")) and any(m in text for m in MONTH_MAP)
    if specific_date is not None and not is_asking_total_month:
        row = full_df[full_df["date"].dt.date == specific_date.date()]
        if row.empty:
            response = ("No data for " + str(specific_date.date()) +
                ". Data covers " + str(full_df["date"].min().date()) +
                " to " + str(full_df["date"].max().date()) + ".")
        else:
            r = row.iloc[0]
            response = ("On " + str(r["date"].date()) + ":\n"
                "- Revenue: $" + f"{r['revenue']:,.2f}" + "\n"
                "- Cost:    $" + f"{r['cost']:,.2f}" + "\n"
                "- Profit:  $" + f"{r['profit']:,.2f}")
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # AI intent
    if is_ai_intent(text):
        context = build_ai_context(data, full_df)
        try:
            ai_resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": context}, {"role": "user", "content": user_input}],
                temperature=0.5, max_tokens=600,
            )
            response = ai_resp.choices[0].message.content
        except Exception as e:
            response = "Something went wrong: " + str(e)
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Multi-intent
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
        response = ("No data for " + matched_year + ". Data covers " +
            str(full_df["date"].min().date()) + " to " + str(full_df["date"].max().date()) + ".")
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # After/before filter
    data, date_filter_note = extract_date_filter(full_df, text)

    # Month filter
    months_found = get_months_from_text(text)
    matched_month = None
    if not date_filter_note and months_found:
        ml, mn = months_found[0]
        month_data = full_df[full_df["date"].dt.month == mn]
        if month_data.empty:
            avail = sorted(full_df["date"].dt.strftime("%B %Y").unique())
            response = "No data for " + ml + ". Available: " + ", ".join(avail) + "."
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        else:
            data = month_data
            matched_month = ml

    # Metric
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
    is_rolling = "rolling" in text

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
            row = data.loc[data[metric].idxmax()]
            response = "Highest " + metric + " " + period_label + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())

        elif is_min:
            row = data.loc[data[metric].idxmin()]
            response = "Lowest " + metric + " " + period_label + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())

        elif is_total:
            response = "Total " + metric + " " + period_label + ": $" + f"{data[metric].sum():,.2f}"

        elif is_avg:
            response = "Average " + metric + " " + period_label + ": $" + f"{data[metric].mean():,.2f}"

        elif is_rolling:
            window = next((int(w) for w in text.split() if w.isdigit()), 7)
            roll_col = "rolling_avg"
            roll_df = data.copy()
            roll_df[roll_col] = roll_df["profit"].rolling(window).mean().round(2)
            last_val = roll_df[roll_col].dropna().iloc[-1] if not roll_df[roll_col].dropna().empty else 0
            response = (f"{window}-day rolling avg profit {period_label}:\n"
                f"- Latest: ${last_val:,.2f}\n"
                f"- Overall avg: ${data['profit'].mean():,.2f}")
            chart_df_out = roll_df[["date", roll_col]].rename(columns={roll_col: "revenue"})
            chart_metric_out = "revenue"

        elif is_top:
            n = next((int(w) for w in text.split() if w.isdigit()), 5)
            top_df = data.sort_values(metric, ascending=False).head(n)[["date", "revenue", "cost", "profit"]]
            response = "Top " + str(n) + " days by " + metric + " " + period_label + ":\n\n" + top_df.to_string(index=False)
            chart_df_out = data[["date", metric]].copy()
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
                messages=[{"role": "system", "content": context}, {"role": "user", "content": user_input}],
                temperature=0.5, max_tokens=600,
            )
            response = ai_resp.choices[0].message.content

    except KeyError as e:
        response = "Column not found: " + str(e) + ". Available: " + ", ".join(df.columns.tolist())
    except Exception as e:
        response = "Something went wrong: " + str(e)

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({
        "role": "assistant", "content": response,
        "chart": chart_df_out, "chart_metric": chart_metric_out,
        "chart_type": chart_type_out, "show_multi": show_multi,
    })
    st.rerun()
