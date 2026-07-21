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
        "footages": find_col(cols, "footages"),
        "lus": find_col(cols, "lus"),
        "qualityScore": find_col(cols, "qualityscore"),
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
    out["footages"] = pd.to_numeric(df[col["footages"]], errors="coerce").fillna(0) if col["footages"] else 0
    out["lus"] = pd.to_numeric(df[col["lus"]], errors="coerce").fillna(0) if col["lus"] else 0
    out["qualityScore"] = pd.to_numeric(df[col["qualityScore"]], errors="coerce") if col["qualityScore"] else None
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


def style_header_zebra(styler):
    """Navy header + white bold text, zebra-striped rows — used on every table."""
    styler = styler.set_table_styles(
        [
            {"selector": "th", "props": [
                ("background-color", NAVY), ("color", "white"),
                ("font-weight", "600"), ("text-align", "center"), ("padding", "8px 10px"),
            ]},
            {"selector": "td", "props": [("padding", "6px 10px"), ("font-size", "13px")]},
        ],
        overwrite=False,
    )
    styler = styler.apply(
        lambda row: ["background-color: #F4F6FA" if row.name % 2 else "background-color: white" for _ in row],
        axis=1,
    )
    return styler


def gradient_style(s, rgb=(46, 95, 163)):
    """Light-to-dark blue background gradient for a numeric column (no matplotlib needed)."""
    vals = pd.to_numeric(s, errors="coerce")
    mn, mx = vals.min(), vals.max()
    rng = (mx - mn) or 1
    out = []
    for v in vals:
        if pd.isna(v):
            out.append("")
            continue
        pct = (v - mn) / rng
        r = int(255 - pct * (255 - rgb[0]))
        g = int(255 - pct * (255 - rgb[1]))
        b = int(255 - pct * (255 - rgb[2]))
        txt = "white" if pct > 0.55 else "#1a1a1a"
        out.append(f"background-color: rgb({r},{g},{b}); color:{txt}; font-weight:600;")
    return out


# Final-status pipeline columns for the Month-wise / Year-wise / Market-wise / Job Type-wise summaries.
# (label, matcher) — matcher checks the normalized Final Status text.
STATUS_COLUMNS = [
    ("YTS", lambda n: n == "yts"),
    ("IP", lambda n: n == "ip"),
    ("QC Feedback", lambda n: "qc" in n),
    ("Ready for Billing", lambda n: "readyforbilling" in n),
    ("Hold", lambda n: n == "hold"),
    ("Invoicing Done", lambda n: "invoicingdone" in n),
]


def build_status_summary(df, group_col, group_label, include_quality=False):
    records = []
    for key, g in df.groupby(group_col):
        rec = {
            group_label: key,
            "Total Job Count": len(g),
            "Total Distance (Feet)": g["footages"].sum(),
            "Total LU's": g["lus"].sum(),
            "Total FC Revenue (₹)": g["fcRevenue"].sum(),
        }
        norm_status = g["finalStatus"].apply(normalize)
        for label, matcher in STATUS_COLUMNS:
            mask = norm_status.apply(matcher)
            if label == "Hold":
                rec["Hold"] = int(mask.sum())
            else:
                rec[f"{label} Job Count"] = int(mask.sum())
                rec[f"{label} Revenue (₹)"] = g.loc[mask, "actualRevenue"].sum()
        if include_quality:
            q = g["qualityScore"].dropna() if "qualityScore" in g else pd.Series(dtype=float)
            rec["Avg Quality Score (%)"] = (q.mean() * 100) if len(q) else None
        records.append(rec)
    return pd.DataFrame(records)


def style_summary_table(df, group_label, gradient_col="Total Job Count"):
    money_cols = [c for c in df.columns if "Revenue" in c]
    qual_col = "Avg Quality Score (%)" if "Avg Quality Score (%)" in df.columns else None
    count_cols = [c for c in df.columns if c not in money_cols and c != group_label and c != qual_col]

    fmt = {c: fmt_inr for c in money_cols}
    fmt.update({c: (lambda v: f"{int(round(v)):,}") for c in count_cols})
    if qual_col:
        fmt[qual_col] = lambda v: "—" if pd.isna(v) else f"{v:.1f}%"

    styler = df.style.format(fmt)
    styler = style_header_zebra(styler)
    if gradient_col in df.columns:
        styler = styler.apply(gradient_style, subset=[gradient_col], axis=0)
    styler = styler.set_properties(**{"text-align": "right"})
    styler = styler.set_properties(subset=[group_label], **{"text-align": "left", "font-weight": "700"})
    return styler


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
# FILTERS  (professional checklist-style dropdown, multi-select)
# ----------------------------------------------------------------------------
years_available = sorted([int(y) for y in rows["year"].dropna().unique()])
months_available = [m for m in MONTH_ORDER if m in rows["monthName"].unique()]

for y in years_available:
    st.session_state.setdefault(f"flt_year_{y}", True)
for m in months_available:
    st.session_state.setdefault(f"flt_month_{m}", True)

fc1, fc2 = st.columns(2)
with fc1:
    n_sel = sum(st.session_state.get(f"flt_year_{y}", True) for y in years_available)
    with st.popover(f"📅 Year  ({n_sel} selected)", use_container_width=True):
        b1, b2 = st.columns(2)
        if b1.button("Select all", key="year_all", use_container_width=True):
            for y in years_available:
                st.session_state[f"flt_year_{y}"] = True
            st.rerun()
        if b2.button("Clear all", key="year_none", use_container_width=True):
            for y in years_available:
                st.session_state[f"flt_year_{y}"] = False
            st.rerun()
        st.markdown("---")
        for y in years_available:
            st.checkbox(str(y), key=f"flt_year_{y}")

with fc2:
    n_sel = sum(st.session_state.get(f"flt_month_{m}", True) for m in months_available)
    with st.popover(f"🗓️ Month  ({n_sel} selected)", use_container_width=True):
        b1, b2 = st.columns(2)
        if b1.button("Select all", key="month_all", use_container_width=True):
            for m in months_available:
                st.session_state[f"flt_month_{m}"] = True
            st.rerun()
        if b2.button("Clear all", key="month_none", use_container_width=True):
            for m in months_available:
                st.session_state[f"flt_month_{m}"] = False
            st.rerun()
        st.markdown("---")
        grid = st.columns(3)
        for i, m in enumerate(months_available):
            with grid[i % 3]:
                st.checkbox(m, key=f"flt_month_{m}")

sel_years = [y for y in years_available if st.session_state.get(f"flt_year_{y}", True)]
sel_months = [m for m in months_available if st.session_state.get(f"flt_month_{m}", True)]

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
# MONTH-ON-MONTH (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Month-on-Month Comparison  (reflects the filters above)")
mom = filtered.groupby(["year", "monthName", "month"]).agg(
    count=("jobNo", "count"), revenue=("actualRevenue", "sum")
).reset_index()
mom["month_idx"] = mom["monthName"].apply(lambda m: MONTH_ORDER.index(m) if m in MONTH_ORDER else 99)
mom = mom.sort_values(["year", "month_idx"]).reset_index(drop=True)
mom["Jobs vs Prev."] = [pct_change(mom["count"][i], mom["count"][i - 1]) if i > 0 else None for i in range(len(mom))]
mom["Revenue vs Prev."] = [pct_change(mom["revenue"][i], mom["revenue"][i - 1]) if i > 0 else None for i in range(len(mom))]

if mom.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
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
    styler = mom_display.style.format({"Revenue": fmt_inr, "Jobs vs Prev.": fmt_pct, "Revenue vs Prev.": fmt_pct})
    styler = style_header_zebra(styler)
    styler = styler.map(style_change, subset=["Jobs vs Prev.", "Revenue vs Prev."])
    styler = styler.set_properties(**{"text-align": "right"})
    styler = styler.set_properties(subset=["Month"], **{"text-align": "left", "font-weight": "700"})
    st.dataframe(styler, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# YEAR-ON-YEAR (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Year-on-Year Comparison  (reflects the filters above)")
yoy = filtered.groupby("year").agg(count=("jobNo", "count"), revenue=("actualRevenue", "sum")).reset_index()
yoy = yoy.sort_values("year").reset_index(drop=True)
yoy["Jobs vs Prev. Yr"] = [pct_change(yoy["count"][i], yoy["count"][i - 1]) if i > 0 else None for i in range(len(yoy))]
yoy["Revenue vs Prev. Yr"] = [pct_change(yoy["revenue"][i], yoy["revenue"][i - 1]) if i > 0 else None for i in range(len(yoy))]

if yoy.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
    yoy_display = yoy.rename(columns={"year": "Year", "count": "Jobs", "revenue": "Revenue"})
    yoy_display["Year"] = yoy_display["Year"].astype(int)
    styler_yoy = yoy_display.style.format({"Revenue": fmt_inr, "Jobs vs Prev. Yr": fmt_pct, "Revenue vs Prev. Yr": fmt_pct})
    styler_yoy = style_header_zebra(styler_yoy)
    styler_yoy = styler_yoy.map(style_change, subset=["Jobs vs Prev. Yr", "Revenue vs Prev. Yr"])
    styler_yoy = styler_yoy.set_properties(**{"text-align": "right"})
    styler_yoy = styler_yoy.set_properties(subset=["Year"], **{"text-align": "left", "font-weight": "700"})
    st.dataframe(styler_yoy, use_container_width=True, hide_index=True)

st.markdown("---")

# ----------------------------------------------------------------------------
# MONTH-WISE DETAILED SUMMARY  (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Month-wise Summary  (reflects the filters above)")
month_summary = build_status_summary(filtered, "month", "Month")
if month_summary.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
    order_map = filtered.drop_duplicates("month").set_index("month")
    month_summary["_year"] = month_summary["Month"].map(order_map["year"])
    month_summary["_midx"] = month_summary["Month"].map(order_map["monthName"]).apply(
        lambda m: MONTH_ORDER.index(m) if m in MONTH_ORDER else 99
    )
    month_summary = month_summary.sort_values(["_year", "_midx"]).drop(columns=["_year", "_midx"]).reset_index(drop=True)
    st.dataframe(style_summary_table(month_summary, "Month"), use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# YEAR-WISE DETAILED SUMMARY  (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Year-wise Summary  (reflects the filters above)")
year_summary = build_status_summary(filtered, "year", "Year")
if year_summary.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
    year_summary = year_summary.sort_values("Year").reset_index(drop=True)
    year_summary["Year"] = year_summary["Year"].astype(int)
    st.dataframe(style_summary_table(year_summary, "Year"), use_container_width=True, hide_index=True)

st.markdown("---")

# ----------------------------------------------------------------------------
# MARKET-WISE DETAILED SUMMARY  (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Market-wise Summary  (reflects the filters above)")
market_summary = build_status_summary(filtered, "market", "Market", include_quality=True)
if market_summary.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
    market_summary = market_summary.sort_values("Total Job Count", ascending=False).reset_index(drop=True)
    st.dataframe(style_summary_table(market_summary, "Market"), use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# JOB TYPE-WISE DETAILED SUMMARY  (reflects the filters above)
# ----------------------------------------------------------------------------
st.subheader("Job Type-wise Summary  (reflects the filters above)")
jobtype_summary = build_status_summary(filtered, "jobType", "Job Type", include_quality=True)
if jobtype_summary.empty:
    st.info("Is filter ke liye koi data nahi hai.")
else:
    jobtype_summary = jobtype_summary.sort_values("Total Job Count", ascending=False).reset_index(drop=True)
    st.dataframe(style_summary_table(jobtype_summary, "Job Type"), use_container_width=True, hide_index=True)
