"""
RetailPulse 360 — Executive Dashboard (Home).
Run with: streamlit run Dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import (load_stores, load_cities, load_products, load_skus, load_sales,
                                 load_inventory_turnover, load_redistribution_recommendations)
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME

st.set_page_config(page_title="RetailPulse 360", page_icon="\U0001F45F", layout="wide",
                    initial_sidebar_state="expanded")
inject_css()

with st.sidebar:
    st.markdown("### RetailPulse 360")
    st.caption("Retail decision-intelligence platform")
    st.markdown("---")
    st.markdown("Use the pages above to explore the store network, product catalog, and sales data.")
    st.markdown("---")
    st.markdown(
        '<div style="position: fixed; bottom: 1.5rem; font-size: 0.8rem; color: #8B96AC;">'
        '\U0001F464 Developed by <b>Hamaz Mubashar</b><br>'
        '\U0001F517 <a href="https://www.linkedin.com/in/hamazmubashar" target="_blank" '
        'style="color: #22D3EE;">LinkedIn</a></div>',
        unsafe_allow_html=True,
    )

stores = load_stores()
cities = load_cities()
skus = load_skus()
sales = load_sales()
products = load_products()
inventory = load_inventory_turnover()
redistribution = load_redistribution_recommendations()

physical = stores[stores["channel"] == "Physical"]
sync_label = sales["date"].max().strftime("%b %d, %Y")
render_topbar(sync_label)

# --- Filters ---
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    date_range = st.selectbox("Date Range", ["Last 30 Days", "Last 90 Days", "All Time"], index=0)
with col_f2:
    region_options = ["All Regions"] + sorted(physical["region"].dropna().unique().tolist())
    region_filter = st.selectbox("Region", region_options)
with col_f3:
    channel_filter = st.selectbox("Channel", ["All", "Physical", "Online"])

# --- Apply filters to sales ---
max_date = sales["date"].max()
if date_range == "Last 30 Days":
    sales_f = sales[sales["date"] >= max_date - pd.Timedelta(days=30)]
elif date_range == "Last 90 Days":
    sales_f = sales[sales["date"] >= max_date - pd.Timedelta(days=90)]
else:
    sales_f = sales

sales_j = sales_f.merge(skus[["sku_id", "category", "price_pkr"]], on="sku_id", how="left")
sales_j = sales_j.merge(stores[["store_id", "region", "channel"]], on="store_id", how="left")

if region_filter != "All Regions":
    sales_j = sales_j[sales_j["region"] == region_filter]
if channel_filter != "All":
    sales_j = sales_j[sales_j["channel"] == channel_filter]

sales_j["revenue"] = sales_j["units_sold"] * sales_j["price_pkr"]

# --- KPI row ---
total_revenue = sales_j["revenue"].sum()
total_units = sales_j["units_sold"].sum()

active_inv = inventory[inventory["active_daily_velocity"] > 0]
avg_days_supply = active_inv["days_of_supply"].mean() if len(active_inv) > 0 else None
critical_count = (inventory["stock_status"] == "Critical (Reorder)").sum()
low_count = (inventory["stock_status"] == "Low").sum()

render_kpi_tags([
    {"label": "Total Revenue", "value": f"PKR {total_revenue:,.0f}"},
    {"label": "Pairs Sold", "value": f"{total_units:,.0f} Units"},
    {"label": "Avg Days of Supply", "value": f"{avg_days_supply:,.1f} days" if avg_days_supply else "\u2014"},
    {"label": "Stock Alerts", "value": f"{critical_count:,}", "delta": f"{low_count:,} more running low",
     "delta_dir": "down"},
])

# --- Two-column: Sales trend + Category | Critical Action Center ---
col_left, col_right = st.columns([1.6, 1])

with col_left:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Sales Performance (Daily)</div>', unsafe_allow_html=True)
        daily = sales_j.groupby("date")["revenue"].sum().reset_index()
        fig1 = px.line(daily, x="date", y="revenue")
        fig1.update_layout(**PLOTLY_THEME, height=300, xaxis_title=None, yaxis_title="Revenue (PKR)")
        fig1.update_traces(line_color="#22D3EE")
        fig1.update_xaxes(gridcolor="#263049")
        fig1.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig1, use_container_width=True)

    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Category Performance</div>', unsafe_allow_html=True)
        cat = sales_j.groupby("category")["units_sold"].sum().reset_index().sort_values("units_sold", ascending=False)
        fig2 = px.bar(cat, x="category", y="units_sold")
        fig2.update_layout(**PLOTLY_THEME, height=260, showlegend=False, xaxis_title=None, yaxis_title="Units")
        fig2.update_traces(marker_color="#EC4899")
        fig2.update_xaxes(gridcolor="#263049")
        fig2.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig2, use_container_width=True)

with col_right:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Stock Redistribution Engine</div>', unsafe_allow_html=True)
        total_units_to_move = redistribution["transfer_qty"].sum()
        st.markdown(
            f'<p style="color:#E7ECF4; font-size:0.9rem;">'
            f'<b>{len(redistribution):,} transfers recommended</b> \u2014 moving '
            f'<b>{total_units_to_move:,} units</b> of overstocked/dead stock to stores that '
            f'need them. See the full breakdown, routes, and reasoning on the '
            f'<b>Redistribution</b> page.</p>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown('<div class="rp-card-title">System Alerts Feed</div>', unsafe_allow_html=True)
        alerts = inventory[inventory["stock_status"].isin(["Critical (Reorder)", "Low"])].copy()
        alerts = alerts.merge(products[["product_id", "style_name"]], on="product_id", how="left")
        alerts = alerts.merge(stores[["store_id", "city"]], on="store_id", how="left")
        alerts = alerts.sort_values("days_of_supply").head(8)
        if len(alerts) > 0:
            st.dataframe(
                alerts[["city", "style_name", "days_of_supply", "stock_status"]]
                .rename(columns={"city": "Store City", "style_name": "Style",
                                  "days_of_supply": "Days Left", "stock_status": "Status"})
                .round({"Days Left": 1}),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No stores currently below the alert threshold.")

# --- Regional & Store Performance table ---
st.markdown('<div class="rp-card-title" style="margin-top:0.5rem;">Regional & Store Performance</div>',
            unsafe_allow_html=True)
store_perf = sales_j.groupby("store_id")["revenue"].sum().reset_index()
store_perf = store_perf.merge(stores[["store_id", "city", "region", "store_size"]], on="store_id", how="right")
store_perf["revenue"] = store_perf["revenue"].fillna(0)
store_perf = store_perf.sort_values("revenue", ascending=False)
store_perf["revenue_display"] = store_perf["revenue"].apply(lambda x: f"PKR {x:,.0f}")
st.dataframe(
    store_perf[["store_id", "city", "region", "store_size", "revenue_display"]]
    .rename(columns={"store_id": "Store", "city": "City", "region": "Region",
                      "store_size": "Size", "revenue_display": "Revenue"}),
    use_container_width=True, hide_index=True,
)

st.caption(
    "Built on real Rossmann Store Sales, H&M Personalized Fashion Recommendations, "
    "and Amazon footwear review data, structured around Stylo's actual business footprint. "
    "Pricing sourced from real Stylo Pakistan retail ranges."
)
