import os
import datetime as dt

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Job Delivery Dashboard", layout="wide")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "Raw_Data.xlsx")

NAVY = "#1F3864"
BLUE = "#2E5FA3"
ORANGE = "#ED7D31"
GREEN = "#2E7D32"
RED = "#C62828"
BAR_COLORS = [BLUE, ORANGE, "#8E9AAF", GREEN, "#B08968", "#5C6B73", "#A64B2A"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 1.5rem; }}
    div[data-testid="stMetric"] {{
        background: white; border-radius: 10px; padding: 14px 16px;
        border-top: 3px solid {BLUE};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def normalize(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def find_col(columns, target):
    for c in columns:
        if normalize(c) == target:
            return c
    for c in columns:
        if target in normalize(c):
            return c
    return None


def standardize_market(m):
    v = str(m).strip()
    n = v.lower()
    if n in ("fl", "florida"):
        return "Florida"
    if n in ("nc", "north carolina"):
        return "North Carolina"
    if v.isupper() and len(v) > 3:
        return v.title()
    return v


@st.cache_data(show_spinner=False)
def load_data(path, mtime):
    """mtime is passed so the cache auto-invalidates whenever the file changes."""
    xls = pd.ExcelFile(path)
    sheet = next((s for s in xls.sheet_names if "raw" in s.lower()), xls.sheet_names[0])
    df = pd.read_excel(path, sheet_name=sheet)
    cols = list(df.columns)

    col = {
        "jobNo": find_col(cols, "jobno"),
        "market": find_col(cols, "market"),
        "jobType": find_col(cols, "jobtype"),
        "currentStatus": find_col(cols, "currentstatus"),
        "finalStatus": find_col(cols, "finalstatus"),
        "month": find_col(cols, "month"),
        "year": find_col(cols, "year"),
        "fcRevenue": find_col(cols, "fcrevenue"),
        "actualRevenue": find_col(cols, "actualrevenue"),
    }
    missing = [k for k in ("jobNo", "market", "jobType") if not col[k]]
    if missing:
        raise ValueError(f"Zaroori columns nahi mile: {missing}")

    out = pd.DataFrame()
    out["jobNo"] = df[col["jobNo"]]
    out["market"] = df[col["market"]].apply(standardize_market)
    out["jobType"] = df[col["jobType"]].astype(str).str.strip()
    out["currentStatus"] = df[col["currentStatus"]].astype(str).str.strip() if col["currentStatus"] else ""
    out["finalStatus"] = df[col["finalStatus"]].astype(str).str.strip() if col["finalStatus"] else ""
    out["month"] = df[col["month"]].astype(str).str.strip() if col["month"] else ""
    out["monthName"] = out["month"].apply(lambda x: x.split("'")[0] if "'" in x else x[:3])
    out["year"] = pd.to_numeric(df[col["year"]], errors="coerce") if col["year"] else None
    out["fcRevenue"] = pd.to_numeric(df[col["fcRevenue"]], errors="coerce").fillna(0) if col["fcRevenue"] else 0
    out["actualRevenue"] = pd.to_numeric(df[col["actualRevenue"]], errors="coerce").fillna(0) if col["actualRevenue"] else 0
    out = out.dropna(subset=["jobNo"])
    return out


def fmt_inr(n):
    try:
        return "₹" + f"{round(n):,}"
    except Exception:
        return "₹0"


def pct_change(curr, prev):
    if prev in (0, None) or pd.isna(prev):
        return None
    return (curr - prev) / prev


def fmt_pct(v):
    if v is None or pd.isna(v):
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v*100:.1f}%"


def style_change(val):
    if val is None or pd.isna(val):
        return ""
    color = GREEN if val >= 0 else RED
    return f"color: {color}; font-weight: 600;"


# ----------------------------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------------------------
st.markdown(
    f"""<div style="background:{NAVY};border-radius:12px;padding:18px 26px;margin-bottom:18px;">
    <span style="color:white;font-size:24px;font-weight:700;">Job Delivery Dashboard</span></div>""",
    unsafe_allow_html=True,
)

if not os.path.exists(DATA_PATH):
    st.warning(
        "Abhi tak koi data file nahi mili. `data/Raw_Data.xlsx` ko is folder mein rakhein "
        "(ya update_dashboard.bat chalayein) aur page refresh karein."
    )
    st.stop()

mtime = os.path.getmtime(DATA_PATH)
try:
    rows = load_data(DATA_PATH, mtime)
except Exception as e:
    st.error(f"File padhne mein dikkat aayi: {e}")
    st.stop()

last_updated = dt.datetime.fromtimestamp(mtime).strftime("%d %b %Y, %I:%M %p")
st.caption(f"🕒 Last updated: {last_updated}  ·  {len(rows)} rows loaded")

# ----------------------------------------------------------------------------
# FILTERS
# ----------------------------------------------------------------------------
years_available = sorted([int(y) for y in rows["year"].dropna().unique()])
months_available = [m for m in MONTH_ORDER if m in rows["monthName"].unique()]

with st.container():
    fc1, fc2 = st.columns(2)
    sel_years = fc1.multiselect("Year", years_available, default=years_available)
    sel_months = fc2.multiselect("Month", months_available, default=months_available)

filtered = rows[rows["year"].isin(sel_years) & rows["monthName"].isin(sel_months)]

# ----------------------------------------------------------------------------
# KPI CARDS
# ----------------------------------------------------------------------------
total_jobs = len(filtered)
total_fc = filtered["fcRevenue"].sum()
total_actual = filtered["actualRevenue"].sum()
invoiced = (filtered["finalStatus"] == "Invoicing Done").sum()
pct_invoiced = (invoiced / total_jobs) if total_jobs else 0
in_progress = (filtered["currentStatus"] == "IP").sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Jobs (filtered)", f"{total_jobs:,}")
k2.metric("Total FC Revenue", fmt_inr(total_fc))
k3.metric("Total Actual Revenue", fmt_inr(total_actual))
k4.metric("% Invoiced", f"{pct_invoiced*100:.1f}%")
k5.metric("Jobs In Progress", f"{in_progress:,}")

st.markdown("---")

# ----------------------------------------------------------------------------
# PIPELINE + FINAL STATUS
# ----------------------------------------------------------------------------
c1, c2 = st.columns([1, 1.3])
with c1:
    st.subheader("Job Status Pipeline")
    pipe = filtered["currentStatus"].value_counts().reset_index()
    pipe.columns = ["Status", "Count"]
    fig = px.pie(pipe, names="Status", values="Count", hole=0.35,
                 color_discrete_sequence=[BLUE, ORANGE, "#8E9AAF", GREEN])
    fig.update_traces(textinfo="label+value")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Final Status — Actual Revenue")
    fs = filtered.groupby("finalStatus").agg(count=("jobNo", "count"), revenue=("actualRevenue", "sum")).reset_index()
    fs = fs.sort_values("revenue", ascending=False)
    fig = px.bar(fs, x="finalStatus", y="revenue", color_discrete_sequence=[BLUE])
    fig.update_layout(xaxis_title="", yaxis_title="Revenue (₹)")
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# MARKET + JOB TYPE
# ----------------------------------------------------------------------------
c3, c4 = st.columns(2)
with c3:
    st.subheader("Market-wise Job Count")
    mk = filtered.groupby("market").agg(count=("jobNo", "count"), revenue=("actualRevenue", "sum")).reset_index()
    mk = mk.sort_values("count", ascending=False)
    fig = px.bar(mk, x="market", y="count", color="market", color_discrete_sequence=BAR_COLORS)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Jobs")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Job Type-wise Job Count")
    jt = filtered.groupby("jobType").agg(count=("jobNo", "count"), revenue=("actualRevenue", "sum")).reset_index()
    jt = jt.sort_values("count", ascending=False)
    fig = px.bar(jt, x="jobType", y="count", color="jobType", color_discrete_sequence=BAR_COLORS)
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Jobs")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------------------------------
# MONTH-ON-MONTH (always full data, ignores filters)
# ----------------------------------------------------------------------------
st.subheader("Month-on-Month Comparison  (full data, ignores filters above)")
mom = rows.groupby(["year", "monthName", "month"]).agg(
    count=("jobNo", "count"), revenue=("actualRevenue", "sum")
).reset_index()
mom["month_idx"] = mom["monthName"].apply(lambda m: MONTH_ORDER.index(m) if m in MONTH_ORDER else 99)
mom = mom.sort_values(["year", "month_idx"]).reset_index(drop=True)
mom["Jobs vs Prev."] = [pct_change(mom["count"][i], mom["count"][i - 1]) if i > 0 else None for i in range(len(mom))]
mom["Revenue vs Prev."] = [pct_change(mom["revenue"][i], mom["revenue"][i - 1]) if i > 0 else None for i in range(len(mom))]

fig = go.Figure()
fig.add_trace(go.Scatter(x=mom["month"], y=mom["count"], name="Job Count", yaxis="y1",
                          line=dict(color=BLUE, width=3), mode="lines+markers"))
fig.add_trace(go.Scatter(x=mom["month"], y=mom["revenue"], name="Actual Revenue", yaxis="y2",
                          line=dict(color=ORANGE, width=3), mode="lines+markers"))
fig.update_layout(
    yaxis=dict(title="Job Count"),
    yaxis2=dict(title="Revenue (₹)", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.15),
)
st.plotly_chart(fig, use_container_width=True)

mom_display = mom[["month", "count", "revenue", "Jobs vs Prev.", "Revenue vs Prev."]].rename(
    columns={"month": "Month", "count": "Jobs", "revenue": "Revenue"}
)
mom_display["Revenue"] = mom_display["Revenue"].apply(fmt_inr)
styled = mom_display.style.format({"Jobs vs Prev.": fmt_pct, "Revenue vs Prev.": fmt_pct}) \
    .applymap(style_change, subset=["Jobs vs Prev.", "Revenue vs Prev."])
st.dataframe(styled, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# YEAR-ON-YEAR (always full data, ignores filters)
# ----------------------------------------------------------------------------
st.subheader("Year-on-Year Comparison  (full data, ignores filters above)")
yoy = rows.groupby("year").agg(count=("jobNo", "count"), revenue=("actualRevenue", "sum")).reset_index()
yoy = yoy.sort_values("year").reset_index(drop=True)
yoy["Jobs vs Prev. Yr"] = [pct_change(yoy["count"][i], yoy["count"][i - 1]) if i > 0 else None for i in range(len(yoy))]
yoy["Revenue vs Prev. Yr"] = [pct_change(yoy["revenue"][i], yoy["revenue"][i - 1]) if i > 0 else None for i in range(len(yoy))]
yoy_display = yoy.rename(columns={"year": "Year", "count": "Jobs", "revenue": "Revenue"})
yoy_display["Year"] = yoy_display["Year"].astype(int)
yoy_display["Revenue"] = yoy_display["Revenue"].apply(fmt_inr)
styled_yoy = yoy_display.style.format({"Jobs vs Prev. Yr": fmt_pct, "Revenue vs Prev. Yr": fmt_pct}) \
    .applymap(style_change, subset=["Jobs vs Prev. Yr", "Revenue vs Prev. Yr"])
st.dataframe(styled_yoy, use_container_width=True, hide_index=True)
