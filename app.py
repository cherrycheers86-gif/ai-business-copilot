import streamlit as st
import pandas as pd
import re
from groq import Groq
 
# CONFIG
st.set_page_config(page_title="AI Business Copilot", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
 
# SESSION DEFAULTS
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
    st.title("Login / Signup")
    mode = st.radio("Select", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
 
    if mode == "Signup":
        name = st.text_input("Full Name")
        if st.button("Create Account"):
            if not name or not email or not password:
                st.error("Please fill in all fields.")
            else:
                st.session_state.user = {"name": name, "email": email}
                st.session_state.page = "onboarding"
                st.rerun()
    else:
        if st.button("Login"):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                st.session_state.user = {"name": email.split("@")[0].capitalize(), "email": email}
                st.session_state.page = "app"
                st.rerun()
    st.stop()
 
# ================================================================
# ONBOARDING PAGE
# ================================================================
if st.session_state.page == "onboarding":
    st.title("Set Up Your Business")
    st.write("Welcome, " + st.session_state.user["name"] + "! Tell us about your business.")
    industry = st.selectbox("Industry", ["Restaurant", "Retail", "Gas Station", "Services", "Other"])
    size = st.selectbox("Business Size", ["Small (1-10 employees)", "Medium (11-50)", "Large (50+)"])
    business_name = st.text_input("Business Name (optional)", placeholder="e.g. Joe's Diner")
 
    if st.button("Continue to Dashboard"):
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
    # Try ISO format first
    m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(1))
        except Exception:
            pass
    # Try "Month DD, YYYY" or "Month DD YYYY"
    m = re.search(
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'\s+(\d{1,2})[,\s]+(\d{4})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    # Try "jan 1 2026" short forms
    m = re.search(
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})[,\s]+(\d{4})\b', text)
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    return None
 
# FIX 3: after/before uses full dataset, not month-filtered data
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
 
# FIX 2 & 6: richer AI context - full monthly summary + all data stats
def build_ai_context(df, full_df=None):
    if full_df is None:
        full_df = df
 
    # Monthly breakdown
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
 
    # Recent 10 rows
    recent = full_df.tail(10)[["date", "revenue", "cost", "profit"]].copy()
    recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
    recent_str = recent.to_string(index=False)
 
    total_rev = full_df["revenue"].sum()
    total_cost = full_df["cost"].sum()
    total_profit = full_df["profit"].sum()
    avg_margin = full_df["margin_pct"].mean() if "margin_pct" in full_df.columns else 0
    min_date = str(full_df["date"].min().date())
    max_date = str(full_df["date"].max().date())
 
    business = st.session_state.business
    context = (
        "You are an AI business analyst for a " + business.get("industry", "small") +
        " business called " + business.get("name", "this business") +
        " (" + business.get("size", "") + ").\n\n"
        "DATA RANGE: " + min_date + " to " + max_date + " (" + str(len(full_df)) + " days)\n\n"
        "OVERALL TOTALS:\n"
        "- Total Revenue: $" + f"{total_rev:,.2f}" + "\n"
        "- Total Costs:   $" + f"{total_cost:,.2f}" + "\n"
        "- Total Profit:  $" + f"{total_profit:,.2f}" + "\n"
        "- Avg Margin:    " + f"{avg_margin:.1f}" + "%\n\n"
        "MONTHLY BREAKDOWN:\n" + monthly_str + "\n"
        "RECENT 10 RECORDS:\n" + recent_str + "\n\n"
        "Rules for your response:\n"
        "1. Do NOT use LaTeX, dollar signs inside math, or code formatting for numbers.\n"
        "2. Write all numbers plainly: $36,450 not $36450 or code-formatted values.\n"
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
 
# FIX 2: detect multiple distinct intents in one message
def detect_multi_intent(text):
    intents = []
    sentences = re.split(r'[?.!]+', text)
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        intents.append(s)
    return intents if len(intents) > 1 else []
 
def answer_single_intent(sentence, df, full_df):
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
    data = df.copy()
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
 
st.title("AI Business Copilot")
st.success("Welcome back, " + user["name"] + " - " + business.get("name", "") + "!")
 
with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
 
    if uploaded_file:
        try:
            raw_df = pd.read_csv(uploaded_file)
            cleaned = clean_dataframe(raw_df)
            if cleaned is not None:
                st.session_state.df = cleaned
                st.success("Loaded " + str(len(cleaned)) + " rows")
        except Exception as e:
            st.error("Could not read file: " + str(e))
 
    if st.button("Use Sample Data"):
        st.session_state.df = get_sample_data()
        st.success("Sample data loaded")
 
    if st.session_state.df is not None:
        df = st.session_state.df
        st.write("Rows: " + str(len(df)))
        st.write("From: " + str(df["date"].min().date()) + " to " + str(df["date"].max().date()))
 
    st.divider()
 
    if st.button("Logout"):
        for key in ["page", "user", "business", "messages", "df"]:
            del st.session_state[key]
        st.rerun()
 
if st.session_state.df is None:
    st.info("Upload a CSV or click Use Sample Data to get started.")
    st.stop()
 
df = st.session_state.df
 
# KPI Row
st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", "$" + f"{df['revenue'].sum():,.2f}")
col2.metric("Total Costs", "$" + f"{df['cost'].sum():,.2f}")
col3.metric("Total Profit", "$" + f"{df['profit'].sum():,.2f}")
if "margin_pct" in df.columns:
    col4.metric("Avg Margin", str(round(df["margin_pct"].mean(), 1)) + "%")
 
st.subheader("Trend")
metric_choice = st.selectbox("Chart metric", ["revenue", "cost", "profit"], label_visibility="collapsed")
st.line_chart(df.set_index("date")[[metric_choice]])
 
with st.expander("Raw Data"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)
 
st.divider()
st.subheader("AI Assistant")
 
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
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
                    st.bar_chart(chart_data[cols_to_show])
                else:
                    st.line_chart(chart_data[cols_to_show])
            except Exception:
                st.dataframe(msg["chart"])
 
user_input = st.chat_input("Ask anything about your data...")
 
if user_input:
    text = user_input.lower()
    full_df = df.copy()
    data = df.copy()
    response = ""
    chart_df_out = None
    chart_metric_out = "revenue"
    chart_type_out = "line"
    show_multi = False
 
    # FIX 1: specific date lookup runs first, before AI or any other logic
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
 
    # FIX 2: multi-intent detection - multiple questions in one message
    multi_intents = detect_multi_intent(text)
    if len(multi_intents) > 1:
        parts = []
        for sentence in multi_intents:
            ans = answer_single_intent(sentence, data, full_df)
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
 
    # FIX 3: after/before filter uses full_df, not month-filtered
    data, date_filter_note = extract_date_filter(full_df, text)
 
    # Month filter (only if no after/before)
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
            response = "Top " + str(n) + " days by " + metric + ":\n\n```\n" + top_df.to_string(index=False) + "\n```"
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
