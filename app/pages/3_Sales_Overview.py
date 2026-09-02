import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_sales, load_skus, load_stores
from utils.styling import inject_css, render_topbar, render_kpi_tags, PLOTLY_THEME

st.set_page_config(page_title="Sales Overview | RetailPulse 360", page_icon="\U0001F4C8", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Sales Overview</div>', unsafe_allow_html=True)
st.caption(
    "~2.46M sales records, Feb 2024 \u2013 Aug 2026, across 190 stores. Includes real "
    "Pakistani seasonal patterns: pre-Eid shopping windows, wedding season, and winter."
)

sales = load_sales()
skus = load_skus()
stores = load_stores()

EID_DATES = [
    ("2024-04-10", "Eid-ul-Fitr"), ("2024-06-17", "Eid-ul-Adha"),
    ("2025-03-31", "Eid-ul-Fitr"), ("2025-06-07", "Eid-ul-Adha"),
    ("2026-03-20", "Eid-ul-Fitr"), ("2026-05-27", "Eid-ul-Adha"),
]

sales_j = sales.merge(skus[["sku_id", "category", "price_pkr"]], on="sku_id", how="left")
sales_j = sales_j.merge(stores[["store_id", "region", "store_size", "channel"]], on="store_id", how="left")
sales_j["revenue"] = sales_j["units_sold"] * sales_j["price_pkr"]

st.sidebar.header("Filters")
min_date, max_date = sales_j["date"].min().date(), sales_j["date"].max().date()
date_start, date_end = st.sidebar.date_input(
    "Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

regions = sorted(sales_j["region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

categories = sorted(sales_j["category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

sizes = sorted(sales_j["store_size"].dropna().unique())
selected_sizes = st.sidebar.multiselect("Store Size", sizes, default=sizes)

mask = (
    (sales_j["date"].dt.date >= date_start) & (sales_j["date"].dt.date <= date_end)
    & sales_j["region"].isin(selected_regions)
    & sales_j["category"].isin(selected_categories)
    & sales_j["store_size"].isin(selected_sizes)
)
filtered = sales_j[mask]

total_revenue = filtered["revenue"].sum()
total_units = filtered["units_sold"].sum()
days_covered = (date_end - date_start).days + 1
avg_daily_revenue = total_revenue / days_covered if days_covered > 0 else 0

render_kpi_tags([
    {"label": "Total Revenue", "value": f"PKR {total_revenue:,.0f}"},
    {"label": "Units Sold", "value": f"{total_units:,.0f}"},
    {"label": "Avg Daily Revenue", "value": f"PKR {avg_daily_revenue:,.0f}"},
    {"label": "Days Covered", "value": f"{days_covered:,}"},
])

# --- Daily trend with Eid markers ---
with st.container(border=True):
    st.markdown('<div class="rp-card-title">Daily Revenue Trend</div>', unsafe_allow_html=True)
    daily = filtered.groupby("date")["revenue"].sum().reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=daily["date"], y=daily["revenue"], mode="lines",
                               line=dict(color="#22D3EE", width=1.5), name="Revenue"))
    for eid_date, eid_name in EID_DATES:
        eid_ts = pd.Timestamp(eid_date)
        if pd.Timestamp(date_start) <= eid_ts <= pd.Timestamp(date_end):
            fig1.add_vline(x=eid_ts, line_dash="dash", line_color="#EC4899", opacity=0.6)
            fig1.add_annotation(x=eid_ts, y=1, yref="paper", text=eid_name, showarrow=False,
                                 font=dict(size=10, color="#EC4899"), yshift=10)
    fig1.update_layout(**PLOTLY_THEME, height=340, xaxis_title=None, yaxis_title="Revenue (PKR)", showlegend=False)
    fig1.update_xaxes(gridcolor="#263049")
    fig1.update_yaxes(gridcolor="#263049")
    st.plotly_chart(fig1, use_container_width=True)

# --- Two-column: Region | Category ---
col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Revenue by Region</div>', unsafe_allow_html=True)
        by_region = filtered.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=True)
        fig2 = px.bar(by_region, x="revenue", y="region", orientation="h")
        fig2.update_layout(**PLOTLY_THEME, height=320, showlegend=False, xaxis_title="Revenue (PKR)", yaxis_title=None)
        fig2.update_traces(marker_color="#22D3EE")
        fig2.update_xaxes(gridcolor="#263049")
        fig2.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig2, use_container_width=True)

with col_b:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Revenue by Category</div>', unsafe_allow_html=True)
        by_cat = filtered.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        fig3 = px.bar(by_cat, x="category", y="revenue")
        fig3.update_layout(**PLOTLY_THEME, height=320, showlegend=False, xaxis_title=None, yaxis_title="Revenue (PKR)")
        fig3.update_traces(marker_color="#EC4899")
        fig3.update_xaxes(gridcolor="#263049")
        fig3.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig3, use_container_width=True)

# --- Day-of-week rhythm ---
with st.container(border=True):
    st.markdown('<div class="rp-card-title">Weekly Rhythm (Avg Revenue by Day)</div>', unsafe_allow_html=True)
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    filtered_dow = filtered.copy()
    filtered_dow["day_name"] = filtered_dow["date"].dt.day_name()
    by_dow = filtered_dow.groupby("day_name")["revenue"].mean().reindex(dow_order).reset_index()
    fig4 = px.bar(by_dow, x="day_name", y="revenue")
    fig4.update_layout(**PLOTLY_THEME, height=280, showlegend=False, xaxis_title=None, yaxis_title="Avg Revenue (PKR)")
    fig4.update_traces(marker_color="#F59E0B")
    fig4.update_xaxes(gridcolor="#263049")
    fig4.update_yaxes(gridcolor="#263049")
    st.plotly_chart(fig4, use_container_width=True)

st.download_button(
    "Download filtered sales summary (CSV)",
    data=daily.to_csv(index=False),
    file_name="stylo_sales_summary.csv",
    mime="text/csv",
)
