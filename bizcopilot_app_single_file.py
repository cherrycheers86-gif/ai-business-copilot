# BizCopilot — single-file Streamlit app (tool-grounded Groq analyst).
# Run: streamlit run bizcopilot_app_single_file.py
# Secrets: .streamlit/secrets.toml → GROQ_API_KEY = "..."  (optional GROQ_MODEL)
# Deps: pip install streamlit pandas groq

from __future__ import annotations

import html as html_module
import json
import re
from typing import Any

import pandas as pd
import streamlit as st
from groq import Groq

# =============================================================================
# UI (CSS)
# =============================================================================
STYLES = """
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

h1 {
  font-family: var(--font-display) !important;
  font-weight: 800 !important; font-size: 2rem !important;
  color: var(--ink) !important; letter-spacing: -0.03em !important;
}
h2, h3 {
  font-family: var(--font-body) !important; font-weight: 600 !important;
  color: var(--ink-soft) !important; font-size: 0.7rem !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important;
}

[data-testid="stMetric"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.4rem 1.6rem !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(12px) !important;
}

[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.25rem !important;
  box-shadow: var(--shadow) !important;
}

[data-testid="stSelectbox"] > div > div {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

[data-testid="stExpander"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

hr { border-color: var(--linen) !important; margin: 1.25rem 0 !important; }

[data-testid="stFileUploader"] {
  background: rgba(255,255,255,0.6) !important;
  border: 1.5px dashed rgba(13,148,136,0.4) !important;
  border-radius: 14px !important;
}

.stButton > button {
  background: linear-gradient(135deg, var(--teal) 0%, #0A7C72 100%) !important;
  border: none !important; border-radius: 12px !important;
  color: #fff !important; font-weight: 600 !important;
}

.chat-input-sticky {
  position: sticky; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, var(--cream) 80%, transparent);
  padding: 1rem 0 1.5rem 0; z-index: 100;
}

.msg-user { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
.msg-user .bubble {
  max-width: 68%;
  background: linear-gradient(135deg, var(--teal) 0%, #0A7C72 100%);
  color: #fff; border-radius: 22px 22px 5px 22px;
  padding: 0.85rem 1.2rem; font-size: 0.92rem; line-height: 1.65;
}
.msg-bot {
  display: flex; justify-content: flex-start;
  margin-bottom: 1rem; gap: 0.7rem; align-items: flex-start;
}
.bot-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), var(--amber));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; color: white; font-family: var(--font-mono);
}
.msg-bot .bubble {
  max-width: 74%; background: var(--card-bg);
  border: 1px solid var(--border); color: var(--ink);
  border-radius: 5px 22px 22px 22px;
  padding: 0.85rem 1.2rem; font-size: 0.92rem; line-height: 1.75;
}

[data-testid="stChatInput"] {
  background: var(--card-bg) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 18px !important;
}

.section-label {
  font-size: 0.65rem; font-family: var(--font-mono); color: var(--ink-soft);
  text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 0.75rem;
  display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--linen); }

.sidebar-logo { font-family: var(--font-display); font-weight: 800; font-size: 1.4rem; color: var(--ink); }
.sidebar-sub { font-size: 0.68rem; color: var(--ink-soft) !important; font-family: var(--font-mono); }
.sidebar-stat {
  background: rgba(255,255,255,0.65); border: 1px solid var(--border);
  border-radius: 12px; padding: 0.65rem 0.9rem; margin-bottom: 0.5rem;
  font-size: 0.75rem; color: var(--ink-soft) !important; font-family: var(--font-mono);
}
.sidebar-stat span { color: var(--teal); font-weight: 600; }

.ai-section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.ai-orb {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, var(--teal), var(--amber));
}
.ai-section-title { font-family: var(--font-display); font-weight: 700; font-size: 1.1rem; color: var(--ink); }

.onboard-title { font-family: var(--font-display); font-weight: 800; font-size: 1.7rem; color: var(--ink); }
.onboard-sub { color: var(--ink-soft); font-size: 0.875rem; margin-bottom: 1.75rem; }

.auth-logo { font-family: var(--font-display); font-weight: 900; font-size: 2.4rem; color: var(--ink); }
.auth-tagline { font-size: 0.8rem; color: var(--ink-soft); font-family: var(--font-mono); }

p, span, div, label { color: var(--ink); }
</style>
"""


# =============================================================================
# Fact sheet (precomputed context)
# =============================================================================
def ensure_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "profit" not in out.columns and "revenue" in out.columns and "cost" in out.columns:
        out["profit"] = out["revenue"] - out["cost"]
    if "margin_pct" not in out.columns and "profit" in out.columns and "revenue" in out.columns:
        out["margin_pct"] = (out["profit"] / out["revenue"].replace(0, pd.NA) * 100).round(1)
    return out


def build_fact_sheet(df: pd.DataFrame) -> dict[str, Any]:
    d = ensure_derived_columns(df)
    d = d.dropna(subset=["date"])
    if d.empty:
        return {"error": "no_rows_after_cleaning"}

    d = d.sort_values("date")
    corr = None
    if "revenue" in d.columns and "cost" in d.columns:
        corr = float(d["revenue"].corr(d["cost"]))

    monthly_rows: list[dict[str, Any]] = []
    g = d.groupby(d["date"].dt.to_period("M"), sort=True)
    for period, chunk in g:
        if chunk.empty:
            continue
        max_p = chunk.loc[chunk["profit"].idxmax()]
        min_p = chunk.loc[chunk["profit"].idxmin()]
        monthly_rows.append(
            {
                "period": str(period),
                "total_revenue": float(chunk["revenue"].sum()) if "revenue" in chunk else None,
                "total_cost": float(chunk["cost"].sum()) if "cost" in chunk else None,
                "total_profit": float(chunk["profit"].sum()) if "profit" in chunk else None,
                "avg_daily_revenue": float(chunk["revenue"].mean()) if "revenue" in chunk else None,
                "avg_daily_profit": float(chunk["profit"].mean()) if "profit" in chunk else None,
                "avg_margin_pct": float(chunk["margin_pct"].mean()) if "margin_pct" in chunk else None,
                "days_count": int(len(chunk)),
                "max_profit_day": {"date": str(max_p["date"].date()), "profit": float(max_p["profit"])},
                "min_profit_day": {"date": str(min_p["date"].date()), "profit": float(min_p["profit"])},
            }
        )

    top5 = []
    if "profit" in d.columns:
        for _, r in d.nlargest(5, "profit").iterrows():
            top5.append(
                {
                    "date": str(r["date"].date()),
                    "revenue": float(r["revenue"]) if "revenue" in d.columns else None,
                    "cost": float(r["cost"]) if "cost" in d.columns else None,
                    "profit": float(r["profit"]),
                }
            )

    max_p = d.loc[d["profit"].idxmax()] if "profit" in d.columns else None
    min_p = d.loc[d["profit"].idxmin()] if "profit" in d.columns else None
    max_r = d.loc[d["revenue"].idxmax()] if "revenue" in d.columns else None

    return {
        "date_range": {"min": str(d["date"].min().date()), "max": str(d["date"].max().date())},
        "row_count": int(len(d)),
        "columns_present": [c for c in d.columns.tolist()],
        "totals": {
            "revenue": float(d["revenue"].sum()) if "revenue" in d.columns else None,
            "cost": float(d["cost"].sum()) if "cost" in d.columns else None,
            "profit": float(d["profit"].sum()) if "profit" in d.columns else None,
            "avg_daily_profit": float(d["profit"].mean()) if "profit" in d.columns else None,
            "avg_margin_pct": float(d["margin_pct"].mean()) if "margin_pct" in d.columns else None,
        },
        "extrema": {
            "max_profit": (
                {"value": float(max_p["profit"]), "date": str(max_p["date"].date())} if max_p is not None else None
            ),
            "min_profit": (
                {"value": float(min_p["profit"]), "date": str(min_p["date"].date())} if min_p is not None else None
            ),
            "max_revenue": (
                {"value": float(max_r["revenue"]), "date": str(max_r["date"].date())} if max_r is not None else None
            ),
        },
        "revenue_cost_correlation": corr,
        "monthly": monthly_rows,
        "top_5_profit_days": top5,
    }


# =============================================================================
# Analytics tool (deterministic numbers for the LLM)
# =============================================================================
def _slice_df(
    df: pd.DataFrame,
    year: int | None = None,
    month: int | None = None,
    date_after: str | None = None,
    date_before: str | None = None,
) -> pd.DataFrame:
    d = ensure_derived_columns(df)
    d = d.dropna(subset=["date"])
    if year is not None:
        d = d[d["date"].dt.year == year]
    if month is not None:
        d = d[d["date"].dt.month == month]
    if date_after:
        dt = pd.to_datetime(date_after)
        d = d[d["date"] > dt]
    if date_before:
        dt = pd.to_datetime(date_before)
        d = d[d["date"] < dt]
    return d


def _metric_series(df: pd.DataFrame, metric: str) -> pd.Series:
    if metric not in df.columns:
        raise KeyError(metric)
    return df[metric]


def analytics_tool_run(df: pd.DataFrame, arguments: dict[str, Any]) -> str:
    op = arguments.get("operation")
    metric = arguments.get("metric", "revenue")
    year = arguments.get("year")
    month = arguments.get("month")
    date_after = arguments.get("date_after")
    date_before = arguments.get("date_before")
    top_n = int(arguments.get("top_n", 5))
    month_a = arguments.get("month_a")
    month_b = arguments.get("month_b")

    try:
        subset = _slice_df(df, year=year, month=month, date_after=date_after, date_before=date_before)
        if subset.empty:
            return json.dumps(
                {
                    "ok": False,
                    "reason": "no_rows_for_filter",
                    "filters": {
                        "year": year,
                        "month": month,
                        "date_after": date_after,
                        "date_before": date_before,
                    },
                }
            )

        if op == "describe_window":
            return json.dumps(
                {
                    "ok": True,
                    "operation": op,
                    "filters": {"year": year, "month": month, "date_after": date_after, "date_before": date_before},
                    "row_count": int(len(subset)),
                    "date_range": {"min": str(subset["date"].min().date()), "max": str(subset["date"].max().date())},
                }
            )

        if op == "total":
            s = _metric_series(subset, metric)
            return json.dumps({"ok": True, "operation": op, "metric": metric, "value": float(s.sum())})

        if op == "average":
            s = _metric_series(subset, metric)
            return json.dumps({"ok": True, "operation": op, "metric": metric, "value": float(s.mean())})

        if op == "max":
            s = _metric_series(subset, metric)
            row = subset.loc[s.idxmax()]
            return json.dumps(
                {
                    "ok": True,
                    "operation": op,
                    "metric": metric,
                    "value": float(row[metric]),
                    "date": str(row["date"].date()),
                }
            )

        if op == "min":
            s = _metric_series(subset, metric)
            row = subset.loc[s.idxmin()]
            return json.dumps(
                {
                    "ok": True,
                    "operation": op,
                    "metric": metric,
                    "value": float(row[metric]),
                    "date": str(row["date"].date()),
                }
            )

        if op == "top_days":
            s = _metric_series(subset, metric)
            top = subset.assign(_m=s).nlargest(top_n, "_m")
            rows = []
            for _, r in top.iterrows():
                rows.append({"date": str(r["date"].date()), metric: float(r[metric])})
            return json.dumps({"ok": True, "operation": op, "metric": metric, "top": rows})

        if op == "compare_months":
            if month_a is None or month_b is None:
                return json.dumps({"ok": False, "reason": "month_a_and_month_b_required"})
            full = ensure_derived_columns(df).dropna(subset=["date"])
            if year is not None:
                full = full[full["date"].dt.year == int(year)]
            out: dict[str, Any] = {
                "ok": True,
                "operation": op,
                "metric": metric,
                "year_filter": year,
                "months": {},
            }
            for label, m in [("a", month_a), ("b", month_b)]:
                md = full[full["date"].dt.month == int(m)]
                if md.empty:
                    out["months"][label] = {"month": int(m), "empty": True}
                    continue
                s = _metric_series(md, metric)
                out["months"][label] = {
                    "month": int(m),
                    "empty": False,
                    "total": float(s.sum()),
                    "average": float(s.mean()),
                    "max": float(s.max()),
                    "min": float(s.min()),
                }
            return json.dumps(out)

        if op == "rolling_average_profit":
            window = int(arguments.get("window", 7))
            w = max(1, min(window, 90))
            sub = subset.sort_values("date")
            if "profit" not in sub.columns:
                return json.dumps({"ok": False, "reason": "profit_column_missing"})
            roll = sub["profit"].rolling(w).mean().dropna()
            if roll.empty:
                return json.dumps({"ok": False, "reason": "insufficient_data_for_window", "window": w})
            latest = float(roll.iloc[-1])
            return json.dumps(
                {
                    "ok": True,
                    "operation": op,
                    "window_days": w,
                    "latest_rolling_avg_profit": latest,
                    "simple_avg_profit_in_window": float(sub["profit"].mean()),
                }
            )

        return json.dumps({"ok": False, "reason": "unknown_operation", "operation": op})
    except KeyError as e:
        return json.dumps({"ok": False, "reason": "missing_column", "detail": str(e)})
    except Exception as e:
        return json.dumps({"ok": False, "reason": "error", "detail": str(e)})


ANALYTICS_TOOL_DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_business_analytics",
        "description": (
            "Compute exact numbers from the user's uploaded daily business dataset. "
            "Call this whenever the user asks for totals, averages, min/max, top days, "
            "month comparisons, rolling averages, or filtered periods. "
            "Do not guess or mentally calculate; always use this tool for numeric facts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "describe_window",
                        "total",
                        "average",
                        "max",
                        "min",
                        "top_days",
                        "compare_months",
                        "rolling_average_profit",
                    ],
                    "description": "Which aggregation to perform.",
                },
                "metric": {
                    "type": "string",
                    "enum": ["revenue", "cost", "profit", "margin_pct"],
                    "description": "Metric column. margin_pct is percentage points (not dollars).",
                },
                "year": {"type": "integer", "description": "Optional calendar year filter (e.g. 2026)."},
                "month": {"type": "integer", "description": "Optional month 1-12 filter."},
                "date_after": {"type": "string", "description": "Optional exclusive lower bound ISO date YYYY-MM-DD."},
                "date_before": {"type": "string", "description": "Optional exclusive upper bound ISO date YYYY-MM-DD."},
                "top_n": {"type": "integer", "description": "For top_days, how many rows (default 5)."},
                "month_a": {"type": "integer", "description": "For compare_months: first month 1-12."},
                "month_b": {"type": "integer", "description": "For compare_months: second month 1-12."},
                "window": {
                    "type": "integer",
                    "description": "For rolling_average_profit, window length in days (default 7, max 90).",
                },
            },
            "required": ["operation", "metric"],
        },
    },
}


# =============================================================================
# Groq: tool-grounded analyst
# =============================================================================
def _business_blurb(business: dict[str, Any]) -> str:
    return (
        f"Industry: {business.get('industry', 'unknown')}; "
        f"Business name: {business.get('name', 'unknown')}; "
        f"Size: {business.get('size', 'unknown')}"
    )


def _system_prompt(fact_sheet: dict[str, Any], business: dict[str, Any]) -> str:
    facts_json = json.dumps(fact_sheet, indent=2, default=str)
    return f"""You are an AI business analyst for a small business.

{_business_blurb(business)}

FACT_SHEET (precomputed; authoritative for high-level narrative and context):
{facts_json}

Rules:
1) For ANY specific number (totals, averages, min/max, top days, comparisons, filtered periods), you MUST call the tool `run_business_analytics` and then base your answer ONLY on the tool JSON result.
2) Never invent, extrapolate, or mentally recalculate figures. If the tool says a filter has no rows, explain that clearly.
3) margin_pct is a percentage (e.g. 12.3 means 12.3%), not a dollar amount.
4) Be concise and practical. End with one clear recommendation when appropriate.
5) If the user asks something outside the dataset (e.g. market benchmarks), say you only have their uploaded data."""


def run_grounded_analyst(
    client: Groq,
    df: pd.DataFrame,
    business: dict[str, Any],
    user_message: str,
    *,
    model: str,
    max_tool_rounds: int = 6,
) -> tuple[str, list[dict[str, Any]]]:
    fact_sheet = build_fact_sheet(df)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(fact_sheet, business)},
        {"role": "user", "content": user_message},
    ]
    tools = [ANALYTICS_TOOL_DEFINITION]

    for _ in range(max_tool_rounds):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=900,
        )
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in tool_calls
                    ],
                }
            )
            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                if name == "run_business_analytics":
                    result = analytics_tool_run(df, args)
                else:
                    result = json.dumps({"ok": False, "reason": "unknown_tool", "name": name})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        text = (msg.content or "").strip()
        if text:
            return text, messages

        messages.append({"role": "assistant", "content": "I need to call analytics tools to answer accurately."})
        messages.append(
            {
                "role": "user",
                "content": "Please call run_business_analytics as needed, then answer using only tool results.",
            }
        )

    return (
        "I could not finish the analysis in time. Please try a simpler question or narrow the date range.",
        messages,
    )


# =============================================================================
# Streamlit app
# =============================================================================
st.set_page_config(page_title="BizCopilot", layout="wide")

if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY to .streamlit/secrets.toml")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
GROQ_MODEL = str(st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile"))

st.markdown(STYLES, unsafe_allow_html=True)

for key, default in {
    "page": "auth",
    "user": None,
    "business": {},
    "messages": [],
    "df": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def has_word(text: str, word: str) -> bool:
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


def get_sample_data() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=60)
    revenue = [1000 + i * 50 for i in range(60)]
    cost = [600 + i * 30 for i in range(60)]
    df = pd.DataFrame({"date": dates, "revenue": revenue, "cost": cost})
    df["profit"] = df["revenue"] - df["cost"]
    df["margin_pct"] = (df["profit"] / df["revenue"] * 100).round(1)
    return df


def clean_dataframe(raw: pd.DataFrame) -> pd.DataFrame | None:
    df = raw.copy()
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


def get_months_from_text(text: str) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for name, num in MONTH_MAP.items():
        if name in text:
            found.append((name.capitalize(), num))
    return found


def filter_by_year(df: pd.DataFrame, text: str) -> tuple[pd.DataFrame | None, str | None]:
    years = re.findall(r"\b(20\d{2})\b", text)
    if not years:
        return df, None
    year = int(years[0])
    filtered = df[df["date"].dt.year == year]
    if filtered.empty:
        return None, str(year)
    return filtered, str(year)


def extract_specific_date(text: str) -> pd.Timestamp | None:
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if m:
        try:
            return pd.to_datetime(m.group(1))
        except Exception:
            pass
    m = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)"
        r"\s+(\d{1,2})[,\s]+(\d{4})\b",
        text,
    )
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})[,\s]+(\d{4})\b",
        text,
    )
    if m:
        try:
            return pd.to_datetime(m.group(0))
        except Exception:
            pass
    return None


def extract_date_filter(df: pd.DataFrame, text: str) -> tuple[pd.DataFrame, str]:
    after_match = re.search(r"\bafter\b\s+([\w\s,]+?\d{4})", text)
    before_match = re.search(r"\bbefore\b\s+([\w\s,]+?\d{4})", text)
    filtered = df.copy()
    note = ""
    try:
        if after_match:
            dt = pd.to_datetime(after_match.group(1).strip())
            filtered = filtered[filtered["date"] > dt]
            note = "after " + str(dt.date())
        if before_match:
            dt = pd.to_datetime(before_match.group(1).strip())
            filtered = filtered[filtered["date"] < dt]
            note = ("before " + str(dt.date())) if not note else (note + " before " + str(dt.date()))
    except Exception:
        pass
    return filtered, note


if st.session_state.page == "auth":
    st.markdown(
        """
    <div style="text-align:center;padding:3rem 0 1.5rem 0;">
      <div class="auth-logo">BizCopilot</div>
      <div class="auth-tagline">AI-powered business intelligence</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
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

if st.session_state.page == "onboarding":
    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.4, 1])
    with col_m:
        st.markdown(
            '<div class="onboard-title">Tell us about<br>your business.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="onboard-sub">We will personalize your dashboard and AI insights.</div>',
            unsafe_allow_html=True,
        )
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

user = st.session_state.user
business = st.session_state.business

with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">BizCopilot</div>'
        '<div class="sidebar-sub">'
        + business.get("industry", "Business").upper()
        + " / "
        + business.get("size", "").split(" ")[0].upper()
        + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed")
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
            '<div class="sidebar-stat">Records <span>'
            + str(len(_df))
            + "</span></div>"
            '<div class="sidebar-stat">From <span>'
            + str(_df["date"].min().date())
            + "</span></div>"
            '<div class="sidebar-stat">To <span>'
            + str(_df["date"].max().date())
            + "</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        for key in ["page", "user", "business", "messages", "df"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.markdown(
        '<div style="margin-top:1rem;font-size:0.7rem;color:#78716C;font-family:DM Mono,monospace;">'
        + user["name"]
        + "</div>",
        unsafe_allow_html=True,
    )

if st.session_state.df is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem;">'
        '<div style="font-size:3rem;margin-bottom:1.2rem;">&#128202;</div>'
        '<div style="font-family:Playfair Display,serif;font-size:1.4rem;font-weight:700;'
        'color:#44403C;margin-bottom:0.6rem;">No data loaded</div>'
        '<div style="color:#78716C;font-size:0.9rem;line-height:1.6;max-width:360px;margin:0 auto;">'
        "Upload a CSV or click <strong>Use Sample Data</strong> in the sidebar.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

df = st.session_state.df

row_h1, row_h2 = st.columns([3, 1])
with row_h1:
    st.markdown(
        "<h1>AI Business Copilot</h1>"
        '<div style="font-size:0.875rem;color:#78716C;margin-bottom:1.25rem;">Welcome back, <strong style="color:#0D9488;">'
        + html_module.escape(user["name"])
        + "</strong> — "
        + html_module.escape(business.get("name", ""))
        + "</div>",
        unsafe_allow_html=True,
    )

col1, col2, col3, col4 = st.columns(4)
if "revenue" in df.columns:
    col1.metric("Total Revenue", "$" + f"{df['revenue'].sum():,.2f}")
if "cost" in df.columns:
    col2.metric("Total Costs", "$" + f"{df['cost'].sum():,.2f}")
if "profit" in df.columns:
    col3.metric("Total Profit", "$" + f"{df['profit'].sum():,.2f}")
if "margin_pct" in df.columns:
    col4.metric("Avg Margin", str(round(df["margin_pct"].mean(), 1)) + "%")

st.markdown(
    '<div class="section-label" style="margin-top:1.5rem;">Performance Trend</div>',
    unsafe_allow_html=True,
)
c1, c2 = st.columns([1, 5])
with c1:
    metric_choice = st.selectbox("", ["revenue", "cost", "profit"], label_visibility="collapsed")
chart_cols = [c for c in [metric_choice] if c in df.columns]
if chart_cols:
    st.line_chart(df.set_index("date")[chart_cols], height=210)

with st.expander("View Raw Data"):
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<div class="ai-section-header">'
    '<div class="ai-orb"></div>'
    '<div class="ai-section-title">AI Business Analyst (tool-grounded)</div>'
    "</div>",
    unsafe_allow_html=True,
)
st.caption(f"Model: {GROQ_MODEL} — numbers come from your data via analytics tools, not from guesses.")

if not st.session_state.messages:
    st.info(
        "Ask questions in natural language. For totals, comparisons, and advice, the AI calls **run_business_analytics** "
        "so figures match your upload."
    )

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            '<div class="msg-user"><div class="bubble">'
            + html_module.escape(msg["content"]).replace("\n", "<br>")
            + "</div></div>",
            unsafe_allow_html=True,
        )
    else:
        raw = msg["content"]
        safe = html_module.escape(raw)
        if "  " in raw and "\n" in raw:
            formatted = (
                '<pre style="font-family:DM Mono,monospace;font-size:0.82rem;white-space:pre;overflow-x:auto;'
                'background:rgba(13,148,136,0.05);border-radius:10px;padding:0.75rem;margin:0;">'
                + safe
                + "</pre>"
            )
        else:
            formatted = safe.replace("\n", "<br>")
        st.markdown(
            '<div class="msg-bot"><div class="bot-avatar">AI</div>'
            '<div class="bubble">'
            + formatted
            + "</div></div>",
            unsafe_allow_html=True,
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

st.markdown('<div class="chat-input-sticky">', unsafe_allow_html=True)
user_input = st.chat_input("Ask anything about your business data...")
st.markdown("</div>", unsafe_allow_html=True)

if user_input:
    text = user_input.lower()
    full_df = df.copy()
    data = df.copy()
    response = ""
    chart_df_out = None
    chart_metric_out = "revenue"
    chart_type_out = "line"
    show_multi = False

    specific_date = extract_specific_date(text)
    is_asking_total_month = (has_word(text, "total") or has_word(text, "sum")) and any(
        m in text for m in MONTH_MAP
    )
    if specific_date is not None and not is_asking_total_month:
        row = full_df[full_df["date"].dt.date == specific_date.date()]
        if row.empty:
            response = (
                "No data for "
                + str(specific_date.date())
                + ". Data covers "
                + str(full_df["date"].min().date())
                + " to "
                + str(full_df["date"].max().date())
                + "."
            )
        else:
            r = row.iloc[0]
            response = (
                "On "
                + str(r["date"].date())
                + ":\n- Revenue: $"
                + f"{r['revenue']:,.2f}"
                + "\n- Cost:    $"
                + f"{r['cost']:,.2f}"
                + "\n- Profit:  $"
                + f"{r['profit']:,.2f}"
            )
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    data, matched_year = filter_by_year(data, text)
    if data is None:
        response = (
            "No data for "
            + str(matched_year)
            + ". Data covers "
            + str(full_df["date"].min().date())
            + " to "
            + str(full_df["date"].max().date())
            + "."
        )
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    data, date_filter_note = extract_date_filter(data, text)

    months_found = get_months_from_text(text)
    matched_month = None
    if not date_filter_note and months_found:
        ml, mn = months_found[0]
        month_data = data[data["date"].dt.month == mn]
        if month_data.empty:
            avail = sorted(full_df["date"].dt.strftime("%B %Y").unique())
            response = "No data for " + ml + " in the current filter. Available: " + ", ".join(avail) + "."
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        data = month_data
        matched_month = ml

    if has_word(text, "profit") or has_word(text, "loss") or has_word(text, "gain"):
        metric = "profit"
    elif has_word(text, "cost") or has_word(text, "expense") or has_word(text, "costs") or has_word(text, "expenses"):
        metric = "cost"
    elif has_word(text, "margin"):
        metric = "margin_pct"
    else:
        metric = "revenue"

    chart_metric_out = metric if metric in ["revenue", "cost", "profit"] else "revenue"
    if "bar" in text:
        chart_type_out = "bar"

    is_chart = any(
        k in text for k in ["chart", "graph", "trend", "plot", "visualize", "draw", "display"]
    )

    if is_chart:
        show_both = any(
            p in text
            for p in ["and expense", "and cost", "versus", "vs", "and revenue", "and sales", "and profit"]
        )
        if show_both:
            cols = []
            if has_word(text, "sales") or has_word(text, "revenue"):
                cols.append("revenue")
            if has_word(text, "expense") or has_word(text, "cost") or has_word(text, "expenses"):
                cols.append("cost")
            if has_word(text, "profit"):
                cols.append("profit")
            cols = cols if cols else ["revenue", "cost"]
            period_bits = []
            if matched_month:
                period_bits.append(matched_month)
            if matched_year:
                period_bits.append(matched_year)
            if date_filter_note:
                period_bits.append(date_filter_note)
            period = " ".join(period_bits) if period_bits else "selected period"
            response = "Chart: " + " & ".join(cols) + " (" + period + ")"
            chart_df_out = data[["date"] + [c for c in cols if c in data.columns]]
            chart_metric_out = cols[0]
            show_multi = True
        else:
            m = metric if metric in ["revenue", "cost", "profit"] else "revenue"
            response = m.capitalize() + " trend"
            chart_df_out = data[["date", m]] if m in data.columns else None
            chart_metric_out = m
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "chart": chart_df_out,
                "chart_metric": chart_metric_out,
                "chart_type": chart_type_out,
                "show_multi": show_multi,
            }
        )
        st.rerun()

    try:
        answer, _dbg = run_grounded_analyst(
            client,
            full_df,
            business,
            user_input,
            model=GROQ_MODEL,
        )
        response = answer
    except Exception as e:
        response = "Something went wrong: " + str(e)

    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "chart": chart_df_out,
            "chart_metric": chart_metric_out,
            "chart_type": chart_type_out,
            "show_multi": show_multi,
        }
    )
    st.rerun()
