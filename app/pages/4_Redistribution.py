import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import (load_redistribution_recommendations, load_discount_recommendations,
                                 load_inventory_turnover, load_cities)
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME

st.set_page_config(page_title="Redistribution & Pricing | RetailPulse 360", page_icon="\U0001F69A", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Overstock & Dead Stock Resolution</div>', unsafe_allow_html=True)
st.caption(
    "Two strategies for the same underlying problem: move surplus stock to where it's "
    "needed, or discount what can't be moved."
)

inventory = load_inventory_turnover()
cities = load_cities()

tab_redistribution, tab_pricing = st.tabs(["\U0001F69A Redistribution", "\U0001F3F7\uFE0F Pricing & Promotion"])

# =====================================================================
# TAB 1: REDISTRIBUTION
# =====================================================================
with tab_redistribution:
    recs = load_redistribution_recommendations()

    total_need = (inventory["stock_status"].isin(["Critical (Reorder)", "Low"])).sum()
    addressed = recs.groupby(["to_store", "product_id"]).ngroups
    coverage_pct = addressed / total_need * 100 if total_need > 0 else 0

    render_pending_box(
        f"Honest scope note: this engine addresses {addressed:,} of {total_need:,} understocked "
        f"situations ({coverage_pct:.1f}%) using existing surplus/dead stock elsewhere in the "
        f"network. The remaining shortages have no matching surplus anywhere \u2014 redistribution "
        f"recovers real value from stock that would otherwise sit dead, but it is not a substitute "
        f"for reordering from the supplier."
    )

    render_kpi_tags([
        {"label": "Recommended Transfers", "value": f"{len(recs):,}"},
        {"label": "Total Units to Move", "value": f"{recs['transfer_qty'].sum():,}"},
        {"label": "Situations Addressed", "value": f"{coverage_pct:.1f}%",
         "note": f"{addressed:,} of {total_need:,} shortages"},
        {"label": "Avg Distance", "value": f"{recs['distance_km'].mean():.0f} km"},
    ])

    st.sidebar.header("Redistribution Filters")
    products_list = ["All"] + sorted(recs["style_name"].dropna().unique().tolist())
    selected_product = st.sidebar.selectbox("Product Style", products_list)
    max_distance = int(recs["distance_km"].max()) if len(recs) > 0 else 0
    distance_filter = st.sidebar.slider("Max Distance (km)", 0, max_distance, max_distance)

    filtered = recs[recs["distance_km"] <= distance_filter]
    if selected_product != "All":
        filtered = filtered[filtered["style_name"] == selected_product]
    filtered = filtered.sort_values("priority_score", ascending=False)

    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Transfer Routes</div>', unsafe_allow_html=True)
        map_data = filtered.merge(
            cities[["city", "lat", "lng"]].rename(columns={"city": "from_city", "lat": "from_lat", "lng": "from_lng"}),
            on="from_city", how="left"
        )
        map_data = map_data.merge(
            cities[["city", "lat", "lng"]].rename(columns={"city": "to_city", "lat": "to_lat", "lng": "to_lng"}),
            on="to_city", how="left"
        )
        map_data = map_data.dropna(subset=["from_lat", "to_lat"])
        if len(map_data) > 0:
            fig = go.Figure()
            for _, row in map_data.head(100).iterrows():
                fig.add_trace(go.Scattermap(
                    lat=[row["from_lat"], row["to_lat"]], lon=[row["from_lng"], row["to_lng"]],
                    mode="lines+markers", line=dict(width=1.5, color="#22D3EE"),
                    marker=dict(size=6, color=["#EC4899", "#F59E0B"]),
                    hoverinfo="text", text=[f"From: {row['from_city']}", f"To: {row['to_city']}"],
                    showlegend=False,
                ))
            fig.update_layout(
                map=dict(style="open-street-map", zoom=5.4, center={"lat": 30.3753, "lon": 69.3451}),
                height=500, margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="#141B2E",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transfers match the selected filters.")

    st.markdown('<div class="rp-card-title">Recommended Transfers</div>', unsafe_allow_html=True)
    display_cols = ["style_name", "from_city", "from_store_status", "to_city", "to_store_status",
                     "transfer_qty", "distance_km", "days_gained", "priority_score"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "style_name": "Product", "from_city": "From", "from_store_status": "Source Status",
            "to_city": "To", "to_store_status": "Destination Status", "transfer_qty": "Units",
            "distance_km": "Distance (km)", "days_gained": "Days Gained", "priority_score": "Priority",
        }),
        use_container_width=True, hide_index=True,
    )

    st.markdown('<div class="rp-card-title">Why This Transfer? (Reasoning)</div>', unsafe_allow_html=True)
    if len(filtered) > 0:
        options = filtered.apply(lambda r: f"{r['style_name']}: {r['from_city']} \u2192 {r['to_city']}", axis=1).tolist()
        selected_idx = st.selectbox("Choose a transfer to see its full reasoning", range(len(options)),
                                      format_func=lambda i: options[i], key="redist_select")
        st.info(filtered.iloc[selected_idx]["reasoning"])

    st.download_button(
        "Download all recommendations (CSV)", data=filtered.to_csv(index=False),
        file_name="redistribution_recommendations_filtered.csv", mime="text/csv",
    )

# =====================================================================
# TAB 2: PRICING & PROMOTION
# =====================================================================
with tab_pricing:
    discounts = load_discount_recommendations()

    render_pending_box(
        "Key finding: since real footwear price elasticity of demand (0.7, sourced from "
        "published economics research) is INELASTIC, discounting can never increase revenue "
        "or margin for items that still sell at a normal pace \u2014 deeper discounts only make "
        "economic sense as a liquidation strategy for genuinely dead stock. Recommendations "
        "below reflect this: slow-but-selling stock gets the smallest margin-preserving "
        "discount; fully dead stock gets a deeper liquidation discount."
    )

    margin_preserving = (discounts["discount_pct"] == 0.10).sum()
    liquidation = (discounts["discount_pct"] == 0.30).sum()

    render_kpi_tags([
        {"label": "Items Analyzed", "value": f"{len(discounts):,}"},
        {"label": "Margin-Preserving (10%)", "value": f"{margin_preserving:,}",
         "note": "Still selling \u2014 smallest discount recommended"},
        {"label": "Liquidation (30%)", "value": f"{liquidation:,}",
         "note": "Fully dead stock \u2014 deeper discount to recover capital"},
        {"label": "Avg Projected Daily Margin", "value": f"PKR {discounts['projected_daily_margin_pkr'].mean():,.0f}"},
    ])

    st.sidebar.header("Pricing Filters")
    status_options = ["All"] + sorted(discounts["stock_status"].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Stock Status", status_options, key="pricing_status")

    filtered_disc = discounts if selected_status == "All" else discounts[discounts["stock_status"] == selected_status]

    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Recommended Discount Distribution</div>', unsafe_allow_html=True)
        dist_data = filtered_disc["discount_pct"].value_counts().reset_index()
        dist_data.columns = ["discount_pct", "count"]
        dist_data["discount_label"] = (dist_data["discount_pct"] * 100).astype(int).astype(str) + "%"
        fig2 = px.bar(dist_data, x="discount_label", y="count")
        fig2.update_layout(**PLOTLY_THEME, height=280, showlegend=False, xaxis_title="Discount", yaxis_title="Items")
        fig2.update_traces(marker_color="#F59E0B")
        fig2.update_xaxes(gridcolor="#263049")
        fig2.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="rp-card-title">Discount Recommendations</div>', unsafe_allow_html=True)
    display_cols2 = ["style_name", "stock_status", "discount_pct", "discounted_price_pkr",
                      "projected_daily_units", "projected_daily_margin_pkr", "rationale"]
    display_df = filtered_disc[display_cols2].copy()
    display_df["discount_pct"] = (display_df["discount_pct"] * 100).astype(int).astype(str) + "%"
    st.dataframe(
        display_df.rename(columns={
            "style_name": "Product", "stock_status": "Status", "discount_pct": "Discount",
            "discounted_price_pkr": "New Price (PKR)", "projected_daily_units": "Projected Daily Units",
            "projected_daily_margin_pkr": "Projected Daily Margin (PKR)", "rationale": "Rationale",
        }),
        use_container_width=True, hide_index=True,
    )

    st.download_button(
        "Download discount recommendations (CSV)", data=filtered_disc.to_csv(index=False),
        file_name="discount_recommendations_filtered.csv", mime="text/csv",
    )
