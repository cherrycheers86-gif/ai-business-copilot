import streamlit as st
import pandas as pd
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

# FIX 2: full-word keyword matching to avoid "pro" triggering "profit"
def has_word(text, word):
    import re
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

def filter_by_month(df, text):
    for month_name, month_num in MONTH_MAP.items():
        if month_name in text:
            filtered = df[df["date"].dt.month == month_num]
            if filtered.empty:
                return None, month_name.capitalize()
            return filtered, month_name.capitalize()
    return df, None

# FIX 4: year filter - if a year is mentioned and not in data, return None
def filter_by_year(df, text):
    import re
    years = re.findall(r'\b(20\d{2})\b', text)
    if not years:
        return df, None
    year = int(years[0])
    filtered = df[df["date"].dt.year == year]
    if filtered.empty:
        return None, str(year)
    return filtered, str(year)

def build_ai_context(df):
    summary_rows = df.tail(10)[["date", "revenue", "cost", "profit"]].copy()
    summary_rows["date"] = summary_rows["date"].dt.strftime("%Y-%m-%d")
    summary_str = summary_rows.to_string(index=False)
    total_rev = df["revenue"].sum()
    total_cost = df["cost"].sum()
    total_profit = df["profit"].sum()
    avg_margin = df["margin_pct"].mean() if "margin_pct" in df.columns else 0
    business = st.session_state.business
    context = (
        "You are an AI business analyst for a " + business.get("industry", "small") +
        " business called " + business.get("name", "this business") +
        " (" + business.get("size", "") + ").\n\n"
        "OVERALL SUMMARY (" + str(len(df)) + " days of data):\n"
        "- Total Revenue: $" + str(round(total_rev, 2)) + "\n"
        "- Total Costs:   $" + str(round(total_cost, 2)) + "\n"
        "- Total Profit:  $" + str(round(total_profit, 2)) + "\n"
        "- Avg Margin:    " + str(round(avg_margin, 1)) + "%\n\n"
        "RECENT DATA (last 10 records):\n" + summary_str + "\n\n"
        "Answer the user's question using this data. Be concise and specific. "
        "Do NOT use LaTeX, dollar signs inside math expressions, or any special formatting. "
        "Write numbers plainly like: $36,450. Give at least one actionable recommendation."
    )
    return context

# ================================================================
# MAIN APP
# ================================================================
user = st.session_state.user
business = st.session_state.business

st.title("AI Business Copilot")
st.success("Welcome back, " + user["name"] + " - " + business.get("name", "") + "!")

# Sidebar
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

# Load data
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

# Chart
st.subheader("Trend")
metric_choice = st.selectbox("Chart metric", ["revenue", "cost", "profit"], label_visibility="collapsed")
chart_df = df.set_index("date")[[metric_choice]]
st.line_chart(chart_df)

# Data Table
with st.expander("Raw Data"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

st.divider()

# AI Chat
st.subheader("AI Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart") is not None:
            try:
                col = msg.get("chart_metric", "revenue")
                chart_data = msg["chart"].set_index("date")[[col]]
                # FIX 3: use bar chart when user asked for bar
                if msg.get("chart_type") == "bar":
                    st.bar_chart(chart_data)
                else:
                    st.line_chart(chart_data)
            except Exception:
                st.dataframe(msg["chart"])

user_input = st.chat_input("Ask anything about your data...")

if user_input:
    text = user_input.lower()
    data = df.copy()
    response = ""
    chart_df_out = None
    chart_metric_out = "revenue"
    chart_type_out = "line"

    # FIX 4: year filter first
    data, matched_year = filter_by_year(data, text)
    if data is None:
        response = "No data found for " + matched_year + ". Your data covers " + str(df["date"].min().date()) + " to " + str(df["date"].max().date()) + "."
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Month filter
    data, matched_month = filter_by_month(data, text)
    if data is None:
        response = "No data found for " + matched_month + ". Try another month or check your dataset."
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # FIX 2: use whole-word matching for metric detection
    # FIX 2: also detect "sales" as revenue
    if has_word(text, "profit") or has_word(text, "loss"):
        metric = "profit"
    elif has_word(text, "cost") or has_word(text, "expense") or has_word(text, "costs"):
        metric = "cost"
    elif has_word(text, "margin"):
        metric = "margin_pct"
    elif has_word(text, "sales") or has_word(text, "revenue") or has_word(text, "income"):
        metric = "revenue"
    else:
        metric = "revenue"

    chart_metric_out = metric if metric in ["revenue", "cost", "profit"] else "revenue"

    # FIX 3: detect bar chart request
    if "bar" in text:
        chart_type_out = "bar"

    period_label = ""
    if matched_month:
        period_label = "in " + matched_month
    elif matched_year:
        period_label = "in " + matched_year
    else:
        period_label = "overall"

    try:
        if has_word(text, "max") or has_word(text, "highest") or has_word(text, "best") or has_word(text, "maximum"):
            row = data.loc[data[metric].idxmax()]
            response = "Highest " + metric + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())

        elif has_word(text, "min") or has_word(text, "lowest") or has_word(text, "worst") or has_word(text, "minimum"):
            row = data.loc[data[metric].idxmin()]
            response = "Lowest " + metric + ": $" + f"{row[metric]:,.2f}" + " on " + str(row["date"].date())

        elif has_word(text, "total") or has_word(text, "sum"):
            response = "Total " + metric + " " + period_label + ": $" + f"{data[metric].sum():,.2f}"

        elif has_word(text, "average") or has_word(text, "avg") or has_word(text, "mean"):
            response = "Average " + metric + " " + period_label + ": $" + f"{data[metric].mean():,.2f}"

        elif has_word(text, "top"):
            n = next((int(w) for w in text.split() if w.isdigit()), 5)
            top_df = data.sort_values(metric, ascending=False).head(n)[["date", "revenue", "cost", "profit"]]
            # FIX 1: use to_string instead of to_markdown to avoid tabulate dependency
            response = "Top " + str(n) + " days by " + metric + ":\n\n```\n" + top_df.to_string(index=False) + "\n```"
            chart_df_out = top_df.sort_values("date")

        elif any(k in text for k in ["chart", "graph", "trend", "show", "plot", "visualize", "draw", "display"]):
            response = metric.capitalize() + " trend " + period_label
            chart_df_out = data[["date", metric]].rename(columns={metric: chart_metric_out})

        else:
            context = build_ai_context(data)
            ai_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.5,
                max_tokens=500,
            )
            response = ai_response.choices[0].message.content

    except KeyError as e:
        response = "Column not found: " + str(e) + ". Available columns: " + ", ".join(df.columns.tolist())
    except Exception as e:
        response = "Something went wrong: " + str(e)

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "chart": chart_df_out,
        "chart_metric": chart_metric_out,
        "chart_type": chart_type_out,
    })
    st.rerun()
