# BizCopilot — Streamlit app: Groq analyst runs AI-written pandas via restricted exec (see run_dataframe_code).
# Run: streamlit run bizcopilot_app_single_file.py
# Secrets: .streamlit/secrets.toml → GROQ_API_KEY = "..."  (optional GROQ_MODEL)
# Deps: pip install streamlit pandas groq altair numpy

from __future__ import annotations

import ast
import builtins
import contextlib
import html as html_module
import io
import json
import re
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st
from groq import Groq


# =============================================================================
# UI — premium light workspace (warm paper + teal, single-page flow)
# =============================================================================
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;7..144,700;9..144,800&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
  --paper:     #fbfaf7;
  --paper2:    #f3f0e8;
  --card:      rgba(255,255,255,0.88);
  --ink:       #1c1917;
  --ink-mid:   #44403c;
  --ink-soft:  #78716c;
  --line:      rgba(28,25,23,0.08);
  --line2:     rgba(28,25,23,0.12);
  --teal:      #0d9488;
  --teal-dim:  #0f766e;
  --amber:     #d97706;
  --rose:      #e11d48;
  --radius:    18px;
  --radius-sm: 12px;
  --shadow:    0 4px 24px rgba(28,25,23,0.06);
  --shadow-lg: 0 20px 50px rgba(28,25,23,0.08);
  --font-display: 'Fraunces', 'Georgia', serif;
  --font-body:    'DM Sans', system-ui, sans-serif;
  --font-mono:    'DM Mono', ui-monospace, monospace;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--paper) !important;
  color: var(--ink) !important;
  font-family: var(--font-body) !important;
}

[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 85% 55% at 0% -5%, rgba(13,148,136,0.09) 0%, transparent 55%),
    radial-gradient(ellipse 70% 50% at 100% 10%, rgba(217,119,6,0.06) 0%, transparent 50%),
    radial-gradient(ellipse 50% 40% at 50% 100%, rgba(225,29,72,0.03) 0%, transparent 60%);
  pointer-events: none; z-index: 0;
}

[data-testid="stMain"] { background: transparent !important; position: relative; z-index: 1; }
#MainMenu, footer { visibility: hidden; height: 0 !important; overflow: hidden !important; }
[data-testid="stDecoration"] { display: none; }

[data-testid="stHeader"] {
  background: rgba(251, 250, 247, 0.92) !important;
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--line2) !important;
}
[data-testid="stHeader"] button { color: var(--ink-mid) !important; }

.block-container {
  padding: 1.5rem 2rem 3rem 2rem !important;
  max-width: 1100px !important;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #faf8f4 0%, #f5f2eb 100%) !important;
  border-right: 1px solid var(--line2) !important;
}
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { min-width: 268px !important; }

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label { color: var(--ink-mid) !important; }

[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  background: rgba(13,148,136,0.07) !important;
  border: 1px solid rgba(13,148,136,0.22) !important;
  color: var(--teal-dim) !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  font-size: 0.8125rem !important;
}

h1 {
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-size: 1.65rem !important;
  letter-spacing: -0.02em !important;
  color: var(--ink) !important;
  margin: 0 0 0.25rem 0 !important;
}

h2, h3 {
  font-family: var(--font-body) !important;
  font-weight: 600 !important;
  font-size: 0.68rem !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
}

[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--line2) !important;
  border-radius: var(--radius) !important;
  padding: 1.15rem 1.3rem !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(10px);
  transition: box-shadow 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
  box-shadow: var(--shadow-lg) !important;
  transform: translateY(-2px);
}
[data-testid="stMetricLabel"] {
  color: var(--ink-soft) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.62rem !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  color: var(--ink) !important;
  font-family: var(--font-display) !important;
  font-weight: 700 !important;
  font-size: 1.5rem !important;
}

[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
  background: var(--card) !important;
  border: 1px solid var(--line2) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
  box-shadow: var(--shadow) !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] input,
[data-testid="stChatInput"] {
  background: #fff !important;
  border: 1px solid var(--line2) !important;
  border-radius: 14px !important;
  color: var(--ink) !important;
}

[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--line2) !important;
  border-radius: var(--radius) !important;
  box-shadow: var(--shadow) !important;
}

hr {
  border: none !important;
  border-top: 1px solid var(--line2) !important;
  margin: 2rem 0 !important;
}

[data-testid="stFileUploader"] {
  background: rgba(255,255,255,0.7) !important;
  border: 1.5px dashed rgba(13,148,136,0.35) !important;
  border-radius: 14px !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--teal), var(--teal-dim)) !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-weight: 600 !important;
  box-shadow: 0 6px 20px rgba(13,148,136,0.25) !important;
}

.stButton > button:not([kind="primary"]) {
  border-radius: var(--radius-sm) !important;
}

div[data-testid="stAlert"] {
  background: rgba(13,148,136,0.06) !important;
  border: 1px solid rgba(13,148,136,0.2) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--teal-dim) !important;
}

.chat-input-sticky {
  position: sticky; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, var(--paper) 75%, transparent);
  padding: 1rem 0 1.25rem 0;
  z-index: 50;
}

.msg-user { display: flex; justify-content: flex-end; margin-bottom: 1rem; }
.msg-user .bubble {
  max-width: 72%;
  background: linear-gradient(145deg, var(--teal), var(--teal-dim));
  color: #fff;
  border-radius: 22px 22px 6px 22px;
  padding: 0.8rem 1.15rem;
  font-size: 0.9rem;
  line-height: 1.6;
  box-shadow: 0 8px 28px rgba(13,148,136,0.22);
}
.msg-bot {
  display: flex; justify-content: flex-start;
  margin-bottom: 1rem; gap: 0.65rem; align-items: flex-start;
}
.bot-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(145deg, rgba(13,148,136,0.15), rgba(217,119,6,0.12));
  border: 1px solid var(--line2);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem; font-weight: 700; color: var(--teal-dim);
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.msg-bot .bubble {
  max-width: 78%;
  background: var(--card);
  border: 1px solid var(--line2);
  color: var(--ink);
  border-radius: 8px 22px 22px 22px;
  padding: 0.85rem 1.15rem;
  font-size: 0.9rem;
  line-height: 1.65;
  box-shadow: var(--shadow);
}

.section-label {
  font-size: 0.62rem; font-family: var(--font-mono); color: var(--ink-soft);
  text-transform: uppercase; letter-spacing: 0.16em; margin: 1.5rem 0 0.75rem 0;
  display: flex; align-items: center; gap: 10px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--line2); }

.hero-strip {
  display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
  gap: 1rem; margin-bottom: 1.5rem;
  padding: 1.25rem 1.5rem;
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.hero-kicker {
  font-family: var(--font-mono); font-size: 0.62rem; letter-spacing: 0.18em;
  color: var(--ink-soft); text-transform: uppercase;
}
.hero-title {
  font-family: var(--font-display); font-size: 1.5rem; font-weight: 700;
  color: var(--ink); letter-spacing: -0.02em; margin-top: 0.2rem;
}
.hero-sub { color: var(--ink-soft); font-size: 0.88rem; margin-top: 0.35rem; }
.hero-sub strong { color: var(--ink); }
.hero-range {
  font-family: var(--font-mono); font-size: 0.72rem; color: var(--ink-soft); margin-top: 0.5rem; line-height: 1.45;
}
.hero-pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 999px;
  font-family: var(--font-mono); font-size: 0.68rem; font-weight: 500;
  color: var(--teal-dim);
  border: 1px solid rgba(13,148,136,0.25);
  background: rgba(13,148,136,0.06);
}

.sidebar-logo { font-family: var(--font-display); font-weight: 800; font-size: 1.4rem; color: var(--ink); letter-spacing: -0.03em; }
.sidebar-logo span { color: var(--teal); }
.sidebar-sub { font-size: 0.68rem; color: var(--ink-soft) !important; font-family: var(--font-mono); letter-spacing: 0.04em; }
.sidebar-stat {
  background: rgba(255,255,255,0.75); border: 1px solid var(--line2);
  border-radius: var(--radius-sm); padding: 0.55rem 0.85rem; margin-bottom: 0.4rem;
  font-size: 0.72rem; color: var(--ink-soft) !important; font-family: var(--font-mono);
}
.sidebar-stat span { color: var(--teal); font-weight: 600; }

.ai-section-wrap {
  margin-top: 0.5rem;
  padding: 1.5rem 1.5rem 0.5rem 1.5rem;
  background: linear-gradient(180deg, rgba(255,255,255,0.65) 0%, rgba(251,250,247,0.4) 100%);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.ai-section-head {
  display: flex; align-items: center; gap: 12px; margin-bottom: 0.35rem;
}
.ai-orb {
  width: 40px; height: 40px; border-radius: 14px;
  background: linear-gradient(145deg, var(--teal), var(--amber));
  opacity: 0.92;
  box-shadow: 0 8px 24px rgba(13,148,136,0.2);
}
.ai-section-title { font-family: var(--font-display); font-weight: 700; font-size: 1.2rem; color: var(--ink); }
.ai-section-meta { font-family: var(--font-mono); font-size: 0.68rem; color: var(--ink-soft); margin-left: 52px; }

.onboard-title { font-family: var(--font-display); font-weight: 800; font-size: 1.65rem; color: var(--ink); letter-spacing: -0.03em; }
.onboard-sub { color: var(--ink-soft); font-size: 0.875rem; margin-bottom: 1.5rem; }

.auth-wrap { max-width: 420px; margin: 0 auto; padding: 2.5rem 0 2rem 0; }
.auth-logo { font-family: var(--font-display); font-weight: 800; font-size: 2.35rem; color: var(--ink); letter-spacing: -0.04em; text-align: center; }
.auth-logo span { color: var(--teal); }
.auth-tagline { font-size: 0.78rem; color: var(--ink-soft); font-family: var(--font-mono); text-align: center; margin-top: 0.35rem; letter-spacing: 0.05em; }

.card-surface {
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
}

.empty-copilot {
  text-align: center; padding: 2rem 1rem 1.5rem 1rem;
}
.empty-copilot-icon {
  width: 64px; height: 64px; margin: 0 auto 1rem auto; border-radius: 50%;
  background: linear-gradient(145deg, rgba(13,148,136,0.12), rgba(217,119,6,0.1));
  border: 1px solid rgba(13,148,136,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
}
.empty-copilot h3 { font-family: var(--font-display); font-size: 1.05rem; color: var(--ink-mid); margin: 0 0 0.35rem 0; font-weight: 700; }
.empty-copilot p { color: var(--ink-soft); font-size: 0.875rem; line-height: 1.6; max-width: 400px; margin: 0 auto 1rem auto; }
.pill-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; max-width: 520px; margin: 0 auto; }
.pill-hint {
  background: #fff; border: 1px solid var(--line2); color: var(--teal-dim);
  border-radius: 999px; padding: 6px 14px; font-size: 0.78rem; font-family: var(--font-body);
}

p, span, div, label { color: inherit; }
[data-testid="stMarkdownContainer"] p { color: var(--ink-mid); }

.sidebar-upload-shell {
  background: linear-gradient(160deg, rgba(255,255,255,0.97) 0%, rgba(255,255,255,0.88) 100%);
  border: 1px solid rgba(13,148,136,0.2);
  border-radius: var(--radius);
  padding: 1.05rem 1.15rem 1.2rem 1.15rem;
  box-shadow: 0 8px 32px rgba(13,148,136,0.08);
  margin-bottom: 0.35rem;
}
.sidebar-upload-shell .sut-title {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--ink);
  margin: 0 0 0.35rem 0;
  letter-spacing: -0.02em;
}
.sidebar-upload-shell .sut-hint {
  font-size: 0.78rem;
  color: var(--ink-soft);
  line-height: 1.55;
  margin: 0 0 0.85rem 0;
}
.empty-connect-hero {
  max-width: 560px;
  margin: 0 auto;
  text-align: center;
  padding: 2.5rem 1.5rem 2rem 1.5rem;
  background: linear-gradient(180deg, rgba(255,255,255,0.75) 0%, rgba(251,250,247,0.5) 100%);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
}
.empty-connect-hero .ech-icon {
  width: 72px; height: 72px; margin: 0 auto 1.25rem auto;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(13,148,136,0.18), rgba(217,119,6,0.12));
  border: 1px solid rgba(13,148,136,0.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem;
}
.empty-connect-hero .ech-title {
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
  margin: 0 0 0.5rem 0;
}
.empty-connect-hero .ech-body {
  color: var(--ink-soft);
  font-size: 0.92rem;
  line-height: 1.65;
  margin: 0 0 1.25rem 0;
}
.empty-connect-hero .ech-kbd {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 8px;
  background: rgba(13,148,136,0.1);
  border: 1px solid rgba(13,148,136,0.22);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--teal-dim);
  font-weight: 600;
}

.page-head {
  margin-bottom: 1.75rem;
}
.page-head-kicker {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-bottom: 0.35rem;
}
.page-head-title {
  font-family: var(--font-display);
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
  margin: 0 0 0.35rem 0;
}
.page-head-desc {
  color: var(--ink-soft);
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
  max-width: 640px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  padding: 1.2rem 1.35rem;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
.kpi-card .lbl {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-bottom: 0.5rem;
}
.kpi-card .val {
  font-family: var(--font-display);
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.2;
}
.kpi-card .sub {
  font-size: 0.75rem;
  color: var(--ink-soft);
  margin-top: 0.35rem;
}

.chart-card {
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  padding: 1.25rem 1.35rem;
  box-shadow: var(--shadow);
  margin-bottom: 1.5rem;
}
.chart-card h3 {
  font-family: var(--font-body);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin: 0 0 1rem 0;
}

.analytics-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1.25rem;
}

.rank-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-top: 0.5rem;
}
.rank-card {
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  padding: 1.15rem 1.25rem;
  box-shadow: var(--shadow);
}
.rank-card h4 {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 0.75rem 0;
}

.ai-page-wrap {
  background: linear-gradient(180deg, rgba(255,255,255,0.72) 0%, rgba(251,250,247,0.5) 100%);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  padding: 1.5rem 1.5rem 1.25rem 1.5rem;
  box-shadow: var(--shadow);
  margin-bottom: 1rem;
}
.suggest-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.report-block {
  background: var(--card);
  border: 1px solid var(--line2);
  border-radius: var(--radius);
  padding: 1.25rem 1.4rem;
  box-shadow: var(--shadow);
  margin-bottom: 1.25rem;
}
.report-block h3 {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 0.75rem 0;
}
.report-block ul { margin: 0.25rem 0 0 1.1rem; color: var(--ink-mid); line-height: 1.65; }

[data-testid="stSidebar"] [data-testid="stRadio"] > div { flex-direction: column !important; gap: 0.35rem !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border: 1px solid var(--line2) !important;
  border-radius: 12px !important;
  padding: 0.55rem 0.75rem !important;
  background: rgba(255,255,255,0.65) !important;
  margin: 0 !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] {
  width: 100%;
}
</style>
"""


# =============================================================================
# Fact sheet (precomputed context)
# =============================================================================
def ensure_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Keep this helper as a safe copy hook; no hardcoded business derivations.
    return df.copy()


def detect_dataset_schema(df: pd.DataFrame) -> dict[str, Any]:
    d = df.copy()
    numeric_cols = [c for c in d.columns if pd.api.types.is_numeric_dtype(d[c])]
    datetime_cols = [c for c in d.columns if pd.api.types.is_datetime64_any_dtype(d[c])]
    categorical_cols = [c for c in d.columns if c not in numeric_cols and c not in datetime_cols]
    columns: list[dict[str, Any]] = []
    for c in d.columns:
        if c in numeric_cols:
            role = "numeric"
        elif c in datetime_cols:
            role = "datetime"
        else:
            role = "categorical"
        sample_values = d[c].dropna().astype(str).head(3).tolist()
        columns.append(
            {
                "name": str(c),
                "dtype": str(d[c].dtype),
                "role": role,
                "non_null_count": int(d[c].notna().sum()),
                "sample_values": sample_values,
            }
        )
    return {
        "columns": columns,
        "numeric_columns": [str(c) for c in numeric_cols],
        "datetime_columns": [str(c) for c in datetime_cols],
        "categorical_columns": [str(c) for c in categorical_cols],
    }


def build_fact_sheet(df: pd.DataFrame) -> dict[str, Any]:
    d = df.copy()
    schema = detect_dataset_schema(d)
    numeric_cols = schema["numeric_columns"]
    datetime_cols = schema["datetime_columns"]
    categorical_cols = schema["categorical_columns"]

    numeric_summary: dict[str, Any] = {}
    for c in numeric_cols[:10]:
        s = d[c].dropna()
        if s.empty:
            continue
        numeric_summary[c] = {
            "sum": float(s.sum()),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "min": float(s.min()),
            "max": float(s.max()),
        }

    datetime_ranges: dict[str, Any] = {}
    for c in datetime_cols[:6]:
        s = d[c].dropna()
        if s.empty:
            continue
        datetime_ranges[c] = {"min": str(s.min()), "max": str(s.max())}

    category_samples: dict[str, Any] = {}
    for c in categorical_cols[:8]:
        vals = d[c].dropna().astype(str).head(5).tolist()
        category_samples[c] = vals

    return {
        "row_count": int(len(d)),
        "column_count": int(len(d.columns)),
        "columns_present": [str(c) for c in d.columns.tolist()],
        "schema": schema,
        "numeric_summary": numeric_summary,
        "datetime_ranges": datetime_ranges,
        "categorical_samples": category_samples,
    }


# =============================================================================
# AI-authored pandas (restricted exec) — flexible answers without fixed op enums
# =============================================================================
_MAX_CODE_CHARS = 12_000

_FORBIDDEN_CALL_NAMES = frozenset({"eval", "exec", "compile", "__import__", "open", "globals", "locals", "input"})


def _dataframe_schema_line(df: pd.DataFrame) -> str:
    schema = detect_dataset_schema(df)
    out: list[str] = []
    for c in df.columns:
        role = "categorical"
        if c in schema["numeric_columns"]:
            role = "numeric"
        elif c in schema["datetime_columns"]:
            role = "datetime"
        out.append(f"{c} ({role}, dtype={df[c].dtype})")
    return "; ".join(out)


def _validate_copilot_code(src: str) -> tuple[bool, str]:
    if "__" in src:
        return False, "code_must_not_contain__"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, f"syntax_error: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "import_not_allowed"
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in _FORBIDDEN_CALL_NAMES:
                return False, f"forbidden_call:{fn.id}"
            if isinstance(fn, ast.Attribute) and fn.attr in ("open", "system", "popen", "unlink", "remove", "rmtree"):
                return False, f"forbidden_call:{fn.attr}"
    return True, ""


def _sanitize_tool_result(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return obj
    if isinstance(obj, pd.DataFrame):
        return {
            "_type": "dataframe",
            "records": obj.replace({pd.NA: None}).to_dict(orient="records"),
        }
    if isinstance(obj, pd.Series):
        return {"_type": "series", "pairs": list(zip(obj.index.astype(str).tolist(), obj.tolist()))}
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    try:
        import numpy as np

        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
    except ImportError:
        pass
    if isinstance(obj, dict):
        return {str(k): _sanitize_tool_result(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_tool_result(x) for x in obj]
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    return str(obj)


def run_dataframe_code(df: pd.DataFrame, code: str) -> str:
    """Execute model-written pandas in a tight namespace; answer must be assigned to RESULT."""
    stripped = (code or "").strip()
    if not stripped:
        return json.dumps({"ok": False, "error": "empty_code"})
    if len(stripped) > _MAX_CODE_CHARS:
        return json.dumps({"ok": False, "error": "code_too_long", "max": _MAX_CODE_CHARS})
    ok, reason = _validate_copilot_code(stripped)
    if not ok:
        return json.dumps({"ok": False, "error": reason})

    out_buf = io.StringIO()
    err_buf = io.StringIO()

    def _safe_print(*args: Any, **kwargs: Any) -> None:
        kwargs = {**kwargs, "file": out_buf}
        builtins.print(*args, **kwargs)

    safe_builtins: dict[str, Any] = {
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "round": round,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "sorted": sorted,
        "enumerate": enumerate,
        "zip": zip,
        "range": range,
        "print": _safe_print,
    }

    ns: dict[str, Any] = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "df": df.copy(),
        "RESULT": None,
    }
    try:
        import numpy as np

        ns["np"] = np
    except ImportError:
        pass

    try:
        compiled = compile(stripped, "<bizcopilot>", "exec")
        with contextlib.redirect_stderr(err_buf):
            exec(compiled, ns, ns)
    except Exception as e:
        return json.dumps(
            {
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "stdout": out_buf.getvalue(),
                "stderr": err_buf.getvalue(),
            }
        )

    raw_result = ns.get("RESULT")
    try:
        payload = _sanitize_tool_result(raw_result)
        return json.dumps(
            {
                "ok": True,
                "result": payload,
                "stdout": (out_buf.getvalue().strip() or None),
                "stderr": (err_buf.getvalue().strip() or None),
            },
            default=str,
        )
    except Exception as e:
        return json.dumps(
            {
                "ok": False,
                "error": "result_not_serializable",
                "detail": str(e),
                "hint": "Set RESULT to dict, list, number, str, or a DataFrame/Series.",
            }
        )


CODE_TOOL_DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_dataframe_code",
        "description": (
            "MANDATORY for analysis: run real pandas computations on this dataset only. Variables: df (copy), pd, optional np. "
            "You MUST group, aggregate, sort, compare, and derive metrics (ratios, differences, percentages) when needed—do not skip computation. "
            "Set RESULT to serializable output (numbers, dict/list summary, small DataFrame). Respect user filters (dates/ranges); exclude out-of-range rows. "
            "For vague terms (high/low/unusual), compute a threshold (e.g. quantile, z-score vs mean, top/bottom share) and return only rows that meet it—never dump all rows as 'unusual'. "
            "No import/open/exec/eval or __ names. If a filter yields no rows, set RESULT to a string starting with: No data available for this request."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Pandas script that computes the answer (groupby/agg/sort/ratios as needed); must set RESULT.",
                },
            },
            "required": ["code"],
        },
    },
}


# =============================================================================
# Groq: tool-grounded analyst
# =============================================================================
def _groq_auth_error_message(exc: Exception) -> str | None:
    """Human-readable hint when Groq returns 401 / invalid key."""
    raw = str(exc)
    low = raw.lower()
    if (
        "401" in raw
        or "invalid api key" in low
        or "invalid_api_key" in low
        or "authenticationerror" in low.replace(" ", "")
    ):
        return (
            "Groq rejected this API key (401 invalid_api_key). Fix `.streamlit/secrets.toml`: "
            "copy a new key from https://console.groq.com/keys and set `GROQ_API_KEY = \"gsk_...\"` "
            "(no spaces before/after the value, no extra quotes inside the string). "
            "Restart the app after saving."
        )
    return None


def _business_blurb(business: dict[str, Any]) -> str:
    return (
        f"Industry: {business.get('industry', 'unknown')}; "
        f"Business name: {business.get('name', 'unknown')}; "
        f"Size: {business.get('size', 'unknown')}"
    )


def _blocked_user_request(message: str) -> str | None:
    """Refuse obvious OS/file/shell-jailbreak phrasing without calling the model."""
    t = message.lower()
    needles = (
        "/etc/passwd",
        "\\etc\\passwd",
        "c:\\windows\\system32",
        "subprocess",
        "os.system",
        "__import__",
        "rm -rf",
        "format c:",
        "powershell -e",
        "powershell -enc",
        "cmd.exe /c",
        "delete system files",
        "read all files on disk",
        "cat /etc",
    )
    if any(n in t for n in needles):
        return "I can't help with that request."
    return None


def _system_prompt(fact_sheet: dict[str, Any], business: dict[str, Any], df: pd.DataFrame) -> str:
    facts_json = json.dumps(fact_sheet, indent=2, default=str)
    schema = _dataframe_schema_line(df)
    return f"""You are a professional data analyst. Your ONLY source of truth is the uploaded dataset accessed via run_dataframe_code. Behave like an analyst, not a generic chatbot.

{_business_blurb(business)}

DATAFRAME_SCHEMA (use exact column names on df):
{schema}

FACT_SHEET (dataset summary and schema context):
{facts_json}

CORE PRINCIPLE
- Every number, category, rank, trend, and comparison MUST come from tool output (computed on df). No assumptions, no external facts, no guessing.
- Do NOT cite marketing campaigns, seasonality, macroeconomics, competitor actions, or any cause not explicitly present as a column or label in the data.
- You may describe time patterns (e.g. month-over-month from dates) ONLY as computed from the dataset—not as "seasonality" in a general business sense unless the data itself supports that wording.

MANDATORY: ALWAYS COMPUTE
- For ANY analytical question you MUST call run_dataframe_code and perform real calculations (aggregations, filters, groupby, merges of columns, sorts).
- Do NOT refuse with vague phrases like "not clear" or "insufficient data" unless it is truly impossible (e.g. required columns missing AND cannot be derived from available numerics). If ambiguous, pick a reasonable interpretation from the schema, compute it, and state that interpretation in Explanation.
- Prefer: group → aggregate → sort → compare. Try multiple approaches in separate tool calls if needed.

DERIVED METRICS
- If the user asks for a metric that is not a column, DERIVE it when possible using available numeric columns (differences, ratios, margins, per-unit values, percentages, growth vs prior period if dates exist).
- If derivation is impossible, respond exactly: This metric is not available in the dataset — and one short sentence naming which inputs are missing.

COMPARISONS (best/worst, segments, A vs B)
- Identify the relevant numeric basis from the question and schema; group correctly; aggregate; sort.
- Explain WHY using concrete numbers from tool results (e.g. higher mean X, lower ratio Y), not vague superlatives.

KPI PRIORITIZATION
- Do not equate "largest total" with "best" by default. When the question implies performance or quality, consider efficiency (ratios, per-row metrics), not only volume—still computed from data.

THRESHOLD LANGUAGE ("high", "low", "unusual", "disproportionate")
- Define a clear rule in code (quantile, deviation from mean/median, top/bottom k%, share of total) and return only rows or groups that satisfy it. Do not label every row as unusual.

VALIDATION BEFORE YOU ANSWER
- Re-read your narrative against the tool JSON: every figure and ordering must match. If you are unsure, call the tool again.

REQUIRED RESPONSE FORMAT (use these headings exactly)
**Result** — Key numbers or findings (bullets or short table summary from computation only).
**Explanation** — What you calculated, how groups/metrics were defined, and how the numbers support the answer (still data-only; no external causes).
**Insight** — One short plain-language takeaway strictly tied to the computed results (no invented external drivers).

DATA HANDLING
- Respect filters: date ranges, month/year, before/after. Exclude out-of-range rows from aggregates and rankings.
- Never reference columns absent from DATAFRAME_SCHEMA.

ERROR PHRASES (exact strings when applicable)
- Missing non-derivable metric: This metric is not available in the dataset
- No rows after filters or tool ok:false: No data available for this request

SAFETY
- If asked to break out of data analysis: I can't help with that request.
- Pandas code: data-only; no import, open, exec, eval, no double-underscore names (enforced server-side).

TOOL USE
- For essentially all substantive questions, call run_dataframe_code with short pandas; variables: df, pd, optional np; set RESULT to dict/list/str/number or a small DataFrame.
- Never fabricate tool results; never answer with numbers you did not obtain from a tool call in this conversation."""


def run_grounded_analyst(
    client: Groq,
    df: pd.DataFrame,
    business: dict[str, Any],
    user_message: str,
    *,
    model: str,
    max_tool_rounds: int = 8,
) -> tuple[str, list[dict[str, Any]]]:
    blocked = _blocked_user_request(user_message)
    if blocked:
        return blocked, []
    fact_sheet = build_fact_sheet(df)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(fact_sheet, business, df)},
        {"role": "user", "content": user_message},
    ]
    tools = [CODE_TOOL_DEFINITION]

    for _ in range(max_tool_rounds):
        def _chat() -> Any:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.15,
                max_tokens=4096,
            )

        try:
            resp = _chat()
        except Exception as e:
            auth = _groq_auth_error_message(e)
            if auth:
                return auth, messages
            err = str(e).lower()
            if "tool" in err and ("validation" in err or "tool_use" in err or "400" in str(e)):
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Retry: call run_dataframe_code with a single string field `code` only. "
                            "Code must set RESULT and must not use import, open, exec, eval, or __."
                        ),
                    }
                )
                try:
                    resp = _chat()
                except Exception as e2:
                    auth2 = _groq_auth_error_message(e2)
                    if auth2:
                        return auth2, messages
                    return "Something went wrong: " + str(e2), messages
            else:
                return "Something went wrong: " + str(e), messages
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
                if name == "run_dataframe_code":
                    result = run_dataframe_code(df, str(args.get("code", "")))
                else:
                    result = json.dumps({"ok": False, "reason": "unknown_tool", "name": name})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        text = (msg.content or "").strip()
        if text:
            return text, messages

        messages.append({"role": "assistant", "content": "I need to run dataframe code to answer accurately."})
        messages.append(
            {
                "role": "user",
                "content": (
                    "You must call run_dataframe_code with pandas that sets RESULT, then reply using the required "
                    "format (**Result**, **Explanation**, **Insight**) with numbers taken only from tool JSON."
                ),
            }
        )

    return (
        "I could not finish the analysis in time. Please try a simpler question or narrow the date range.",
        messages,
    )


# =============================================================================
# Streamlit app
# =============================================================================
st.set_page_config(page_title="BizCopilot", layout="wide", initial_sidebar_state="expanded")

if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY to .streamlit/secrets.toml")
    st.stop()

_groq_key = str(st.secrets["GROQ_API_KEY"]).strip()
if not _groq_key:
    st.error("GROQ_API_KEY is empty in .streamlit/secrets.toml after trimming spaces.")
    st.stop()

client = Groq(api_key=_groq_key)
GROQ_MODEL = str(st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile"))

st.markdown(STYLES, unsafe_allow_html=True)

for key, default in {
    "page": "auth",
    "user": None,
    "business": {},
    "messages": [],
    "df": None,
    "pending_question": None,
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
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        st.error("The uploaded file has no rows.")
        return None
    if len(df.columns) == 0:
        st.error("The uploaded file has no columns.")
        return None

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_numeric_dtype(df[col]):
            continue
        s = df[col]
        parsed_dt = pd.to_datetime(s, errors="coerce")
        dt_ratio = float(parsed_dt.notna().mean()) if len(s) else 0.0
        if dt_ratio >= 0.8 and parsed_dt.notna().sum() >= 3:
            df[col] = parsed_dt
            continue
        parsed_num = pd.to_numeric(s, errors="coerce")
        num_ratio = float(parsed_num.notna().mean()) if len(s) else 0.0
        if num_ratio >= 0.85:
            df[col] = parsed_num
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


def ingest_uploaded_csv(uploaded_obj: Any) -> None:
    """Load CSV from a Streamlit UploadedFile into session_state.df."""
    if uploaded_obj is None:
        return
    try:
        raw_df = pd.read_csv(uploaded_obj)
        cleaned = clean_dataframe(raw_df)
        if cleaned is not None:
            st.session_state.df = cleaned
            st.success("Loaded " + str(len(cleaned)) + " rows")
    except Exception as e:
        st.error("Could not read file: " + str(e))


def monthly_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    """Month-level aggregates for Reports using first datetime + numeric columns."""
    d = df.copy()
    schema = detect_dataset_schema(d)
    if not schema["datetime_columns"] or not schema["numeric_columns"]:
        return pd.DataFrame()
    dt_col = schema["datetime_columns"][0]
    d = d.dropna(subset=[dt_col])
    if d.empty:
        return pd.DataFrame()
    d["_p"] = d[dt_col].dt.to_period("M")
    g = d.groupby("_p", sort=True)
    parts: dict[str, Any] = {"rows": g[dt_col].count()}
    for col in schema["numeric_columns"][:4]:
        if col in d.columns:
            parts[f"{col}_sum"] = g[col].sum()
    out = pd.DataFrame(parts).reset_index()
    out["_p"] = out["_p"].astype(str)
    return out.rename(columns={"_p": "month"})


def build_report_text(df: pd.DataFrame, business: dict[str, Any]) -> str:
    fs = build_fact_sheet(df)
    schema = fs.get("schema") or {}
    lines = [
        "BizCopilot — summary report",
        "Business: " + str(business.get("name", "—")),
        "",
        "Dataset: " + str(fs.get("row_count", 0)) + " rows",
        "Columns: " + str(fs.get("column_count", 0)),
    ]
    lines.append("Numeric columns: " + ", ".join(schema.get("numeric_columns", [])[:8]))
    lines.append("Datetime columns: " + ", ".join(schema.get("datetime_columns", [])[:6]))
    lines.append("Categorical columns: " + ", ".join(schema.get("categorical_columns", [])[:8]))
    lines.append("")
    lines.append("Numeric summary (automated)")
    num_sum = fs.get("numeric_summary") or {}
    if num_sum:
        for col, vals in num_sum.items():
            lines.append(
                f"- {col}: sum={vals.get('sum')}, mean={vals.get('mean')}, median={vals.get('median')}, min={vals.get('min')}, max={vals.get('max')}"
            )
    lines.append("")
    lines.append("Monthly summary (automated if datetime exists)")
    mdf = monthly_summary_df(df)
    if not mdf.empty:
        lines.append(mdf.to_string(index=False))
    else:
        lines.append("No monthly rows.")
    return "\n".join(lines)


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
    st.markdown('<div class="section-label">Data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-upload-shell">'
        '<p class="sut-title">Upload CSV</p>'
        '<p class="sut-hint">Daily rows with a <strong>date</strong> column. This is the only upload zone—keeps the main view clean.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    ingest_uploaded_csv(
        st.file_uploader("Choose file", type=["csv"], label_visibility="visible", key="upload_sidebar")
    )
    if st.button("Try sample data", use_container_width=True, key="sample_sidebar"):
        st.session_state.df = get_sample_data()
        st.success("Sample data loaded")
    if st.session_state.df is not None:
        _df = st.session_state.df
        _sc = detect_dataset_schema(_df)
        _dt = _sc["datetime_columns"][0] if _sc["datetime_columns"] else None
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
        date_bits = ""
        if _dt:
            _dmin = _df[_dt].dropna().min()
            _dmax = _df[_dt].dropna().max()
            _from = str(_dmin.date()) if pd.notna(_dmin) else "—"
            _to = str(_dmax.date()) if pd.notna(_dmax) else "—"
            date_bits = (
                '<div class="sidebar-stat">From <span>'
                + _from
                + "</span></div>"
                '<div class="sidebar-stat">To <span>'
                + _to
                + "</span></div>"
            )
        st.markdown(
            '<div class="sidebar-stat">Records <span>'
            + str(len(_df))
            + "</span></div>"
            + date_bits
            + '<div class="sidebar-stat">Columns <span>'
            + str(len(_df.columns))
            + "</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-label">Workspace</div>', unsafe_allow_html=True)
        st.radio(
            "Go to",
            ["Dashboard", "Analytics", "AI Assistant", "Reports"],
            key="main_nav",
            label_visibility="collapsed",
        )
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True, key="signout_sidebar"):
        for key in ["page", "user", "business", "messages", "df", "main_nav", "pending_question"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.markdown(
        '<div style="margin-top:1rem;font-size:0.7rem;color:#78716c;font-family:DM Mono,monospace;">'
        + html_module.escape(user["name"])
        + "</div>",
        unsafe_allow_html=True,
    )

if st.session_state.df is None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="empty-connect-hero">'
        '<div class="ech-icon">&#128200;</div>'
        '<div class="ech-title">Connect your spreadsheet</div>'
        '<div class="ech-body">'
        "Upload your CSV from the <strong>sidebar</strong> on the left. "
        "Tap <span class=\"ech-kbd\">&nbsp;&#9776;&nbsp;</span> if the sidebar is hidden. "
        "Or load demo data below to explore the workspace."
        "</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("Load sample data", key="sample_main_empty", use_container_width=True, type="primary"):
        st.session_state.df = get_sample_data()
        st.rerun()
    st.stop()

df = st.session_state.df
_main_sc = detect_dataset_schema(df)
if _main_sc["datetime_columns"]:
    _dt_main = _main_sc["datetime_columns"][0]
    _range = str(df[_dt_main].min().date()) + " → " + str(df[_dt_main].max().date())
else:
    _range = "No datetime column"
nav = str(st.session_state.get("main_nav", "Dashboard"))

st.markdown(
    '<div class="hero-strip">'
    "<div>"
    '<div class="hero-kicker">Your workspace</div>'
    '<div class="hero-title">'
    + html_module.escape(business.get("name", "Your business"))
    + "</div>"
    '<div class="hero-sub">Signed in as <strong>'
    + html_module.escape(user["name"])
    + "</strong></div>"
    "</div>"
    '<div style="text-align:right;">'
    '<div class="hero-pill">● Data connected</div>'
    '<div class="hero-range">'
    + html_module.escape(_range)
    + "<br>"
    + str(len(df))
    + " rows</div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

_dash = df.copy()
_schema = detect_dataset_schema(_dash)
_num_cols = _schema["numeric_columns"]
_dt_cols = _schema["datetime_columns"]
_cat_cols = _schema["categorical_columns"]

if nav == "Dashboard":
    st.markdown(
        '<div class="page-head">'
        '<div class="page-head-kicker">Overview</div>'
        '<div class="page-head-title">Dashboard</div>'
        '<p class="page-head-desc">Key performance indicators and daily trend for your connected file.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    if _num_cols:
        cards = []
        for c in _num_cols[:4]:
            s = _dash[c].dropna()
            if s.empty:
                val = "—"
                sub = "No numeric rows"
            else:
                val = f"{float(s.sum()):,.2f}"
                sub = "Avg " + f"{float(s.mean()):,.2f}"
            cards.append(
                '<div class="kpi-card"><div class="lbl">'
                + html_module.escape(str(c))
                + '</div><div class="val">'
                + html_module.escape(val)
                + '</div><div class="sub">'
                + html_module.escape(sub)
                + "</div></div>"
            )
        st.markdown('<div class="kpi-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
    else:
        st.info("No numeric columns detected for KPI cards.")

    st.markdown('<div class="chart-card"><h3>Trend</h3></div>', unsafe_allow_html=True)
    if _dt_cols and _num_cols:
        dt_col = _dt_cols[0]
        dm = st.selectbox("Trend metric", _num_cols, index=0, key="dash_metric_sel")
        td = _dash.dropna(subset=[dt_col]).sort_values(dt_col)
        if not td.empty and dm in td.columns:
            st.line_chart(td.set_index(dt_col)[[dm]], height=280)
        else:
            st.info("Not enough rows for trend chart.")
    elif _num_cols:
        dm = st.selectbox("Trend metric", _num_cols, index=0, key="dash_metric_sel")
        st.line_chart(_dash[[dm]], height=280)
    else:
        st.info("No chartable columns detected.")

    st.markdown('<div class="report-block">', unsafe_allow_html=True)
    st.markdown("#### Detected schema")
    schema_rows = [
        {"column": c["name"], "role": c["role"], "dtype": c["dtype"], "sample": ", ".join(c["sample_values"])}
        for c in _schema["columns"]
    ]
    st.dataframe(pd.DataFrame(schema_rows), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="report-block">', unsafe_allow_html=True)
    st.markdown("#### Data preview")
    st.dataframe(_dash.head(5), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    with st.expander("View raw data"):
        if _dt_cols:
            st.dataframe(_dash.sort_values(_dt_cols[0], ascending=False), use_container_width=True)
        else:
            st.dataframe(_dash, use_container_width=True)

elif nav == "Analytics":
    st.markdown(
        '<div class="page-head">'
        '<div class="page-head-kicker">Explore</div>'
        '<div class="page-head-title">Analytics</div>'
        '<p class="page-head-desc">Filter by date range, pick a metric, and inspect extremes.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    if not _num_cols:
        st.info("Analytics view needs at least one numeric column.")
        filt = _dash.copy()
        an_metric = ""
    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            if _dt_cols:
                dt_col = _dt_cols[0]
                dmin = _dash[dt_col].dropna().min().date()
                dmax = _dash[dt_col].dropna().max().date()
                dr_input = st.date_input(
                    "Date range",
                    value=(dmin, dmax),
                    min_value=dmin,
                    max_value=dmax,
                    key="analytics_dr",
                )
            else:
                dt_col = None
                dr_input = None
                st.caption("No datetime column detected. Showing full dataset.")
        with c2:
            an_metric = st.selectbox("Metric", _num_cols, key="analytics_metric_sel")

        filt = _dash.copy()
        if dt_col and dr_input is not None:
            if isinstance(dr_input, (tuple, list)) and len(dr_input) == 2:
                ra, rb = dr_input[0], dr_input[1]
            else:
                ra = rb = dr_input
            filt = filt[(filt[dt_col].dt.date >= ra) & (filt[dt_col].dt.date <= rb)].copy()
    st.markdown('<div class="chart-card"><h3>' + html_module.escape(an_metric.title()) + " over time</h3></div>", unsafe_allow_html=True)
    if an_metric in filt.columns and not filt.empty and _dt_cols:
        dt_col2 = _dt_cols[0]
        st.line_chart(filt.sort_values(dt_col2).set_index(dt_col2)[[an_metric]], height=280)
    elif an_metric in filt.columns and not filt.empty:
        st.line_chart(filt[[an_metric]], height=280)
    elif filt.empty:
        st.info("No rows in this date range.")
    st.markdown('<div class="rank-grid">', unsafe_allow_html=True)
    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown('<div class="rank-card">', unsafe_allow_html=True)
        st.markdown("#### Top 5 days")
        if an_metric in filt.columns and not filt.empty:
            top5 = filt.assign(_v=filt[an_metric]).nlargest(5, "_v")[
                ([_dt_cols[0]] if _dt_cols else []) + [an_metric]
            ].rename(columns={an_metric: "value"})
            st.dataframe(top5, use_container_width=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)
    with rc2:
        st.markdown('<div class="rank-card">', unsafe_allow_html=True)
        st.markdown("#### Lowest 5 days")
        if an_metric in filt.columns and not filt.empty:
            bot5 = filt.assign(_v=filt[an_metric]).nsmallest(5, "_v")[
                ([_dt_cols[0]] if _dt_cols else []) + [an_metric]
            ].rename(columns={an_metric: "value"})
            st.dataframe(bot5, use_container_width=True)
        else:
            st.caption("No data.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif nav == "Reports":
    st.markdown(
        '<div class="page-head">'
        '<div class="page-head-kicker">Export</div>'
        '<div class="page-head-title">Reports</div>'
        '<p class="page-head-desc">Monthly rollups, quick insights, and downloadable summary.</p>'
        "</div>",
        unsafe_allow_html=True,
    )
    fs = build_fact_sheet(df)
    st.markdown('<div class="report-block">', unsafe_allow_html=True)
    st.markdown("#### Monthly summary")
    mdf = monthly_summary_df(df)
    if not mdf.empty:
        st.dataframe(mdf, use_container_width=True)
    else:
        st.caption("No monthly rows to display.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="report-block">', unsafe_allow_html=True)
    st.markdown("#### Key insights")
    insights: list[str] = []
    sc = fs.get("schema") or {}
    insights.append("Rows: " + str(fs.get("row_count", 0)) + " · Columns: " + str(fs.get("column_count", 0)))
    if sc.get("datetime_columns"):
        insights.append("Datetime fields detected: " + ", ".join(sc.get("datetime_columns", [])[:4]) + ".")
    if sc.get("numeric_columns"):
        insights.append("Numeric fields detected: " + ", ".join(sc.get("numeric_columns", [])[:6]) + ".")
    ns = fs.get("numeric_summary") or {}
    if ns:
        first_col = next(iter(ns.keys()))
        first_vals = ns[first_col]
        insights.append(
            f"{first_col}: mean={first_vals.get('mean'):.2f}, min={first_vals.get('min'):.2f}, max={first_vals.get('max'):.2f}."
        )
    if not insights:
        insights.append("Upload more rows for richer insights.")
    st.markdown("<ul>" + "".join("<li>" + html_module.escape(s) + "</li>" for s in insights) + "</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    report_txt = build_report_text(df, business)
    st.download_button(
        label="Download summary (.txt)",
        data=report_txt,
        file_name="bizcopilot_report.txt",
        mime="text/plain",
        key="dl_report_txt",
        use_container_width=True,
    )

elif nav == "AI Assistant":
    injected = st.session_state.pop("pending_question", None)
    st.markdown(
        '<div class="ai-page-wrap">'
        '<div class="ai-section-head"><div class="ai-orb"></div>'
        '<div><div class="ai-section-title">AI Assistant</div></div></div>'
        '<div class="ai-section-meta">'
        + html_module.escape(GROQ_MODEL)
        + " · Answers grounded in your CSV via code execution</div>"
        '<p style="color:#78716c;font-size:0.88rem;margin:0.75rem 0 0 52px;line-height:1.55;">'
        "Charts for chart-style questions render below assistant replies.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    sug_cols = st.columns(4)
    if _num_cols:
        m0 = _num_cols[0]
        m1 = _num_cols[1] if len(_num_cols) > 1 else _num_cols[0]
        suggestions = [
            f"Top 5 {m0} rows",
            f"Lowest {m0} rows",
            f"Average {m0} by month",
            f"{m0} vs {m1} trend",
        ]
    else:
        suggestions = [
            "Show row count by category",
            "List unique values per column",
            "Summarize this dataset",
            "Show missing values by column",
        ]
    for i, s in enumerate(suggestions):
        with sug_cols[i]:
            if st.button(s, key="sug_" + str(i), use_container_width=True):
                st.session_state.pending_question = s
                st.rerun()

    if not st.session_state.messages:
        st.markdown(
            """
<div class="empty-copilot">
  <div class="empty-copilot-icon">&#10022;</div>
  <h3>Ask a question</h3>
  <p>Use a suggestion above or type below. Switch sections anytime from the sidebar.</p>
  <div class="pill-grid">
    <span class="pill-hint">Top 5 values for a numeric column</span>
    <span class="pill-hint">Average by month for a date column</span>
    <span class="pill-hint">Compare two numeric columns</span>
    <span class="pill-hint">Summarize this dataset</span>
  </div>
</div>
""",
            unsafe_allow_html=True,
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
                    '<pre style="font-family:DM Mono,monospace;font-size:0.8rem;white-space:pre;overflow-x:auto;'
                    'background:rgba(13,148,136,0.06);border-radius:10px;padding:0.75rem;margin:0;border:1px solid rgba(28,25,23,0.1);">'
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
                        .mark_arc(innerRadius=48, stroke="#e7e5e4", strokeWidth=1)
                        .encode(
                            theta=alt.Theta("value:Q"),
                            color=alt.Color(
                                "category:N",
                                scale=alt.Scale(range=["#0d9488", "#d97706", "#e11d48"]),
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

    effective_input = injected or user_input
    if effective_input:
        text = effective_input.lower()
        full_df = df.copy()
        data = df.copy()
        response = ""
        chart_df_out = None
        chart_metric_out = "revenue"
        chart_type_out = "line"
        show_multi = False
        chart_kind_out: str | None = None
        pie_source_out: list[dict[str, Any]] | None = None

        # Universal path: let the AI generate pandas for the actual schema.
        try:
            with st.spinner("Analyzing your data…"):
                answer, _dbg = run_grounded_analyst(
                    client,
                    full_df,
                    business,
                    effective_input,
                    model=GROQ_MODEL,
                )
            response = answer
        except Exception as e:
            response = _groq_auth_error_message(e) or ("Something went wrong: " + str(e))

        st.session_state.messages.append({"role": "user", "content": effective_input})
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
            st.session_state.messages.append({"role": "user", "content": effective_input})
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
            st.session_state.messages.append({"role": "user", "content": effective_input})
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
                st.session_state.messages.append({"role": "user", "content": effective_input})
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
                st.session_state.messages.append({"role": "user", "content": effective_input})
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
                st.session_state.messages.append({"role": "user", "content": effective_input})
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
                st.session_state.messages.append({"role": "user", "content": effective_input})
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
            st.session_state.messages.append({"role": "user", "content": effective_input})
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
            with st.spinner("Analyzing your data…"):
                answer, _dbg = run_grounded_analyst(
                    client,
                    full_df,
                    business,
                    effective_input,
                    model=GROQ_MODEL,
                )
            response = answer
        except Exception as e:
            response = _groq_auth_error_message(e) or ("Something went wrong: " + str(e))

        st.session_state.messages.append({"role": "user", "content": effective_input})
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
