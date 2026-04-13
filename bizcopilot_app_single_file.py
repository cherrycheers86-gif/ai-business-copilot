# BizCopilot — single-file Streamlit app (tool-grounded Groq analyst).
# Run: streamlit run bizcopilot_app_single_file.py
# Secrets: .streamlit/secrets.toml → GROQ_API_KEY = "..."  (optional GROQ_MODEL)
# Deps: pip install streamlit pandas groq

from __future__ import annotations

import html as html_module
import json
import re
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
from groq import Groq


def _safe_int(val: Any, default: int) -> int:
    if val is None:
        return default
    if isinstance(val, bool):
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str) and val.strip():
        try:
            return int(float(val.strip()))
        except ValueError:
            return default
    return default


# =============================================================================
# UI (CSS) — dark analytics shell, distinct from prior cream/teal theme
# =============================================================================
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg0:      #07080d;
  --bg1:      #0e1118;
  --bg2:      #151a24;
  --stroke:   rgba(148, 163, 184, 0.18);
  --text:     #e8edf7;
  --muted:    #94a3b8;
  --accent:   #38bdf8;
  --accent2:  #a78bfa;
  --good:     #34d399;
  --warn:     #fbbf24;
  --danger:   #fb7185;
  --radius:   16px;
  --radius-lg: 22px;
  --font:     'Outfit', system-ui, sans-serif;
  --mono:     'IBM Plex Mono', ui-monospace, monospace;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg0) !important;
  color: var(--text) !important;
  font-family: var(--font) !important;
}

[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 90% 70% at 0% -10%, rgba(56, 189, 248, 0.14) 0%, transparent 55%),
    radial-gradient(ellipse 70% 60% at 100% 0%, rgba(167, 139, 250, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse 60% 50% at 80% 100%, rgba(52, 211, 153, 0.06) 0%, transparent 45%);
  pointer-events: none; z-index: 0;
}

[data-testid="stMain"] { background: transparent !important; position: relative; z-index: 1; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

.block-container {
  padding: 1.75rem 2rem 2rem 2rem !important;
  max-width: 1280px !important;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a0c12 0%, #0f1219 100%) !important;
  border-right: 1px solid var(--stroke) !important;
}
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { min-width: 270px !important; }

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label { color: var(--muted) !important; }

[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  background: rgba(56, 189, 248, 0.08) !important;
  border: 1px solid rgba(56, 189, 248, 0.28) !important;
  color: var(--accent) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 0.8125rem !important;
  padding: 0.5rem 0.9rem !important;
}

h1 {
  font-family: var(--font) !important;
  font-weight: 800 !important;
  font-size: 1.85rem !important;
  letter-spacing: -0.03em !important;
  color: var(--text) !important;
  background: linear-gradient(90deg, #f8fafc, #94a3b8);
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
}

[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(21, 26, 36, 0.95), rgba(14, 17, 24, 0.85)) !important;
  border: 1px solid var(--stroke) !important;
  border-radius: var(--radius) !important;
  padding: 1.1rem 1.25rem !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35) !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-family: var(--mono) !important; font-size: 0.65rem !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 700 !important; font-size: 1.45rem !important; }

[data-testid="stTabs"] { margin-top: 0.25rem; }
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: rgba(14, 17, 24, 0.6) !important;
  border: 1px solid var(--stroke) !important;
  border-radius: 14px !important;
  padding: 4px !important;
  gap: 4px !important;
}
[data-testid="stTabs"] button[data-baseweb="tab"] {
  border-radius: 10px !important;
  color: var(--muted) !important;
  font-weight: 600 !important;
  font-size: 0.875rem !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  background: linear-gradient(135deg, rgba(56,189,248,0.2), rgba(167,139,250,0.15)) !important;
  color: var(--text) !important;
}

[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
  background: rgba(14, 17, 24, 0.5) !important;
  border: 1px solid var(--stroke) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1rem !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] input,
[data-testid="stChatInput"] {
  background: var(--bg2) !important;
  border: 1px solid var(--stroke) !important;
  border-radius: 14px !important;
  color: var(--text) !important;
}

[data-testid="stExpander"] {
  background: rgba(14, 17, 24, 0.45) !important;
  border: 1px solid var(--stroke) !important;
  border-radius: var(--radius) !important;
}

hr { border-color: var(--stroke) !important; opacity: 1 !important; margin: 1.5rem 0 !important; }

[data-testid="stFileUploader"] {
  background: rgba(21, 26, 36, 0.5) !important;
  border: 1px dashed rgba(56, 189, 248, 0.35) !important;
  border-radius: 14px !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  box-shadow: 0 6px 24px rgba(14, 165, 233, 0.25) !important;
}

div[data-testid="stAlert"] {
  background: rgba(56, 189, 248, 0.08) !important;
  border: 1px solid rgba(56, 189, 248, 0.25) !important;
  border-radius: 12px !important;
}

.chat-input-sticky {
  position: sticky; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, var(--bg0) 70%, transparent);
  padding: 0.75rem 0 1rem 0; z-index: 50;
}

.msg-user { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
.msg-user .bubble {
  max-width: 78%;
  background: linear-gradient(135deg, #0ea5e9, #6366f1);
  color: #fff;
  border-radius: 20px 20px 6px 20px;
  padding: 0.8rem 1.1rem;
  font-size: 0.9rem;
  line-height: 1.6;
  box-shadow: 0 10px 40px rgba(99, 102, 241, 0.22);
}
.msg-bot {
  display: flex; justify-content: flex-start;
  margin-bottom: 1rem; gap: 0.65rem; align-items: flex-start;
}
.bot-avatar {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, rgba(56,189,248,0.25), rgba(167,139,250,0.25));
  border: 1px solid var(--stroke);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700; color: var(--accent);
  font-family: var(--mono);
  flex-shrink: 0;
}
.msg-bot .bubble {
  max-width: 82%;
  background: rgba(21, 26, 36, 0.85);
  border: 1px solid var(--stroke);
  color: var(--text);
  border-radius: 8px 20px 20px 20px;
  padding: 0.85rem 1.15rem;
  font-size: 0.9rem;
  line-height: 1.65;
}

.section-label {
  font-size: 0.62rem; font-family: var(--mono); color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.16em; margin: 0.5rem 0 0.85rem 0;
  display: flex; align-items: center; gap: 10px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--stroke); }

.hero-strip {
  display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
  gap: 1rem; margin-bottom: 1.25rem;
}
.hero-kicker { font-family: var(--mono); font-size: 0.65rem; letter-spacing: 0.2em; color: var(--muted); text-transform: uppercase; }
.hero-title { font-size: 1.35rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; margin-top: 0.25rem; }
.hero-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 999px;
  font-family: var(--mono); font-size: 0.7rem; color: var(--good);
  border: 1px solid rgba(52, 211, 153, 0.35);
  background: rgba(52, 211, 153, 0.08);
}

.sidebar-logo { font-family: var(--font); font-weight: 800; font-size: 1.35rem; color: var(--text); letter-spacing: -0.03em; }
.sidebar-logo span { color: var(--accent); }
.sidebar-sub { font-size: 0.68rem; color: var(--muted) !important; font-family: var(--mono); letter-spacing: 0.04em; }
.sidebar-stat {
  background: rgba(21, 26, 36, 0.65); border: 1px solid var(--stroke);
  border-radius: 12px; padding: 0.6rem 0.85rem; margin-bottom: 0.45rem;
  font-size: 0.72rem; color: var(--muted) !important; font-family: var(--mono);
}
.sidebar-stat span { color: var(--accent); font-weight: 600; }

.ai-panel-head {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;
  margin-bottom: 1rem;
}
.ai-panel-title { font-weight: 700; font-size: 1.05rem; color: var(--text); }
.ai-panel-meta { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); }

.onboard-title { font-family: var(--font); font-weight: 800; font-size: 1.65rem; color: var(--text); letter-spacing: -0.03em; }
.onboard-sub { color: var(--muted); font-size: 0.875rem; margin-bottom: 1.5rem; }

.auth-wrap { max-width: 420px; margin: 0 auto; padding: 2.5rem 0 2rem 0; }
.auth-logo { font-family: var(--font); font-weight: 800; font-size: 2.25rem; color: var(--text); letter-spacing: -0.04em; text-align: center; }
.auth-logo span { color: var(--accent); }
.auth-tagline { font-size: 0.78rem; color: var(--muted); font-family: var(--mono); text-align: center; margin-top: 0.35rem; letter-spacing: 0.06em; }

.card-surface {
  background: linear-gradient(160deg, rgba(21,26,36,0.9), rgba(14,17,24,0.75));
  border: 1px solid var(--stroke);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.35rem;
  margin-bottom: 1rem;
}

p, span, div, label { color: inherit; }
[data-testid="stMarkdownContainer"] p { color: var(--muted); }
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
    raw_year = arguments.get("year")
    raw_month = arguments.get("month")
    year = _safe_int(raw_year, 0) if raw_year not in (None, "", False) else None
    if year is not None and year < 1900:
        year = None
    month = _safe_int(raw_month, 0) if raw_month not in (None, "", False) else None
    if month is not None and not (1 <= month <= 12):
        month = None
    date_after = arguments.get("date_after")
    date_before = arguments.get("date_before")
    top_n = max(1, min(_safe_int(arguments.get("top_n"), 5), 60))
    month_a = arguments.get("month_a")
    month_b = arguments.get("month_b")

    def _month_num(val: Any) -> int | None:
        if val in (None, "", False):
            return None
        n = _safe_int(val, -1)
        if 1 <= n <= 12:
            return n
        return None

    month_a_i = _month_num(month_a)
    month_b_i = _month_num(month_b)

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

        if op == "bottom_days":
            s = _metric_series(subset, metric)
            bot = subset.assign(_m=s).nsmallest(top_n, "_m")
            rows = []
            for _, r in bot.iterrows():
                rows.append({"date": str(r["date"].date()), metric: float(r[metric])})
            return json.dumps({"ok": True, "operation": op, "metric": metric, "bottom": rows})

        if op == "compare_months":
            if month_a_i is None or month_b_i is None:
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
            for label, m in [("a", month_a_i), ("b", month_b_i)]:
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
            window = _safe_int(arguments.get("window"), 7)
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
            "Use top_days for 'highest/best/top N days' and bottom_days for 'lowest/worst/smallest N days'. "
            "Use min for a single minimum value; use bottom_days for a ranked list. "
            "For month filters use month 1-12 and optional year. "
            "Do not guess; always use this tool for numeric facts."
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
                        "bottom_days",
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
                "top_n": {
                    "anyOf": [{"type": "integer"}, {"type": "string"}],
                    "description": "For top_days/bottom_days: row count (e.g. 5). Integer preferred.",
                },
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
1) For ANY specific number (totals, averages, min/max, ranked days, comparisons, filtered periods), you MUST call `run_business_analytics` and answer ONLY from the latest tool JSON. Do not blend FACT_SHEET numbers with tool results if they could differ.
2) "Lowest/worst/smallest N days" -> operation bottom_days with metric revenue (or cost/profit as asked) and filters. "Highest/top N days" -> top_days. "Lowest single day" / "minimum" -> min with the same filters.
3) Never invent or mentally recalculate. If the tool returns multiple rows, list them exactly.
4) margin_pct is a percentage, not dollars.
5) Be concise; end with one recommendation when helpful.
6) If the question is outside the dataset, say you only have their upload."""


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
    <div class="auth-wrap">
      <div class="auth-logo">Biz<span>Copilot</span></div>
      <div class="auth-tagline">Analytics workspace · grounded AI</div>
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
        '<div class="sidebar-logo">Biz<span>Copilot</span></div>'
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
        '<div style="margin-top:1rem;font-size:0.7rem;color:#94a3b8;font-family:IBM Plex Mono,monospace;">'
        + html_module.escape(user["name"])
        + "</div>",
        unsafe_allow_html=True,
    )

if st.session_state.df is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="card-surface" style="text-align:center;padding:3rem 2rem;max-width:480px;margin:0 auto;">'
        '<div style="font-size:2.5rem;margin-bottom:1rem;">&#128200;</div>'
        '<div style="font-size:1.25rem;font-weight:700;color:#e8edf7;margin-bottom:0.5rem;">Connect your data</div>'
        '<div style="color:#94a3b8;font-size:0.9rem;line-height:1.65;">'
        "Upload a CSV in the sidebar or use <strong style=\"color:#38bdf8;\">Sample Data</strong> to open the workspace.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

df = st.session_state.df
_range = str(df["date"].min().date()) + " → " + str(df["date"].max().date())

st.markdown(
    '<div class="hero-strip">'
    "<div>"
    '<div class="hero-kicker">Workspace</div>'
    '<div class="hero-title">'
    + html_module.escape(business.get("name", "Your business"))
    + "</div>"
    '<div style="color:#94a3b8;font-size:0.88rem;margin-top:0.35rem;">Signed in as <strong style="color:#e8edf7;">'
    + html_module.escape(user["name"])
    + "</strong></div>"
    "</div>"
    '<div style="text-align:right;">'
    '<div class="hero-pill">● Live dataset</div>'
    '<div style="font-family:IBM Plex Mono,monospace;font-size:0.72rem;color:#64748b;margin-top:0.5rem;">'
    + html_module.escape(_range)
    + "<br>"
    + str(len(df))
    + " rows</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

tab_overview, tab_copilot = st.tabs(["Overview", "AI Copilot"])

with tab_overview:
    st.markdown("<h1>Performance</h1>", unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.9rem;margin:-0.25rem 0 1rem 0;">KPIs and trends from your current upload.</p>',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    if "revenue" in df.columns:
        col1.metric("Total revenue", "$" + f"{df['revenue'].sum():,.0f}")
    if "cost" in df.columns:
        col2.metric("Total costs", "$" + f"{df['cost'].sum():,.0f}")
    if "profit" in df.columns:
        col3.metric("Total profit", "$" + f"{df['profit'].sum():,.0f}")
    if "margin_pct" in df.columns:
        col4.metric("Avg margin", str(round(df["margin_pct"].mean(), 1)) + "%")

    st.markdown('<div class="section-label">Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-surface" style="padding-bottom:0.5rem;">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 5])
    with c1:
        metric_choice = st.selectbox("Metric", ["revenue", "cost", "profit"], label_visibility="collapsed")
    chart_cols = [c for c in [metric_choice] if c in df.columns]
    if chart_cols:
        st.line_chart(df.set_index("date")[chart_cols], height=240)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Raw data table"):
        st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

with tab_copilot:
    st.markdown(
        '<div class="ai-panel-head">'
        '<div class="ai-panel-title">Copilot</div>'
        '<div class="ai-panel-meta">'
        + html_module.escape(GROQ_MODEL)
        + " · tool-grounded analytics</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:#94a3b8;font-size:0.85rem;margin:-0.5rem 0 1rem 0;">'
        "Ask in plain language. Numbers are computed from your data; charts open here when you ask for visuals.</p>",
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        st.info("Try: **total revenue**, **5 lowest sales days in February**, **revenue vs expenses chart**, or **pie chart of totals**.")

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
                    '<pre style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;white-space:pre;overflow-x:auto;'
                    'background:rgba(56,189,248,0.06);border-radius:10px;padding:0.75rem;margin:0;border:1px solid rgba(148,163,184,0.2);">'
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
            ck = msg.get("chart_kind")
            try:
                if ck == "pie" and msg.get("pie_source"):
                    pddf = pd.DataFrame(msg["pie_source"])
                    pie_chart = (
                        alt.Chart(pddf)
                        .mark_arc(innerRadius=48, stroke="#1e293b", strokeWidth=1)
                        .encode(
                            theta=alt.Theta("value:Q"),
                            color=alt.Color(
                                "category:N",
                                scale=alt.Scale(range=["#38bdf8", "#a78bfa", "#34d399"]),
                                legend=alt.Legend(title=None),
                            ),
                            tooltip=["category:N", alt.Tooltip("value:Q", format=",.0f")],
                        )
                        .properties(height=280)
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
                elif ck == "scatter" and msg.get("chart") is not None:
                    cdf = msg["chart"].copy()
                    ym = msg.get("chart_metric", "revenue")
                    if ym in cdf.columns:
                        st.scatter_chart(cdf[["date", ym]], x="date", y=ym, height=280)
                elif msg.get("chart") is not None:
                    chart_data = msg["chart"].set_index("date")
                    allowed = [c for c in ["revenue", "cost", "profit"] if c in chart_data.columns]
                    if msg.get("show_multi"):
                        cols_to_show = allowed
                    elif msg.get("chart_metric") and msg["chart_metric"] in chart_data.columns:
                        cols_to_show = [msg["chart_metric"]]
                    else:
                        cols_to_show = allowed
                    if msg.get("chart_type") == "bar":
                        st.bar_chart(chart_data[cols_to_show], height=240)
                    else:
                        st.line_chart(chart_data[cols_to_show], height=240)
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
    chart_kind_out: str | None = None
    pie_source_out: list[dict[str, Any]] | None = None

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
        k in text
        for k in [
            "chart",
            "graph",
            "trend",
            "plot",
            "visualize",
            "draw",
            "display",
            "scatter",
            "pie",
            "histogram",
        ]
    ) or bool(re.search(r"\bmap\b", text))

    if is_chart:
        if re.search(r"\bmap\b", text) and "heatmap" not in text:
            response = (
                "Geographic maps need location data (region, store, latitude/longitude). "
                "Your spreadsheet is daily financial totals only, so a map is not available. "
                "Try a line or bar chart for trends, or a pie chart for revenue vs cost vs profit share."
            )
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "chart": None,
                    "chart_metric": chart_metric_out,
                    "chart_type": chart_type_out,
                    "show_multi": show_multi,
                    "chart_kind": None,
                    "pie_source": None,
                }
            )
            st.rerun()

        if "pie" in text:
            need = ["revenue", "cost", "profit"]
            if not all(c in data.columns for c in need):
                response = "Pie chart needs revenue, cost, and profit columns in the data."
            else:
                pie_source_out = [
                    {"category": "Revenue", "value": float(data["revenue"].sum())},
                    {"category": "Cost", "value": float(data["cost"].sum())},
                    {"category": "Profit", "value": float(data["profit"].sum())},
                ]
                chart_kind_out = "pie"
                period_bits = []
                if matched_month:
                    period_bits.append(matched_month)
                if matched_year:
                    period_bits.append(str(matched_year))
                period = " · ".join(period_bits) if period_bits else "full range"
                response = "Pie chart: share of revenue, cost, and profit (" + period + ")."
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "chart": chart_df_out,
                    "chart_metric": chart_metric_out,
                    "chart_type": chart_type_out,
                    "show_multi": show_multi,
                    "chart_kind": chart_kind_out,
                    "pie_source": pie_source_out,
                }
            )
            st.rerun()

        if "scatter" in text:
            m = metric if metric in ["revenue", "cost", "profit"] else "revenue"
            if m not in data.columns:
                response = "Cannot build a scatter plot: missing " + m + " column."
            else:
                chart_df_out = data[["date", m]].copy()
                chart_metric_out = m
                chart_kind_out = "scatter"
                response = "Scatter plot: " + m + " by day (each point is one day)."
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                    "chart": chart_df_out,
                    "chart_metric": chart_metric_out,
                    "chart_type": chart_type_out,
                    "show_multi": show_multi,
                    "chart_kind": chart_kind_out,
                    "pie_source": pie_source_out,
                }
            )
            st.rerun()

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
            chart_kind_out = "bar" if chart_type_out == "bar" else "line"
        else:
            m = metric if metric in ["revenue", "cost", "profit"] else "revenue"
            response = m.capitalize() + " trend"
            chart_df_out = data[["date", m]] if m in data.columns else None
            chart_metric_out = m
            chart_kind_out = "bar" if chart_type_out == "bar" else "line"
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response,
                "chart": chart_df_out,
                "chart_metric": chart_metric_out,
                "chart_type": chart_type_out,
                "show_multi": show_multi,
                "chart_kind": chart_kind_out,
                "pie_source": pie_source_out,
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
            "chart_kind": chart_kind_out,
            "pie_source": pie_source_out,
        }
    )
    st.rerun()
