import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_store_segments, load_cities
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME

st.set_page_config(page_title="Store Segments | RetailPulse 360", page_icon="\U0001F3EA", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Store Performance Segmentation</div>', unsafe_allow_html=True)
st.caption(
    "190 stores grouped into 4 real behavioral segments using K-means clustering \u2014 "
    "performance measured RELATIVE to each store's own size-tier peers, not raw revenue, "
    "so the segments reflect genuine behavioral differences rather than just re-confirming "
    "that big stores make more money."
)

segments = load_store_segments()
cities = load_cities()

SEGMENT_COLORS = {
    "Rising Stars": "#10B981",
    "Steady Performers": "#22D3EE",
    "Lean & Consistent": "#F59E0B",
    "At-Risk / Declining": "#EF4444",
}

# --- Sidebar filters ---
st.sidebar.header("Filters")
segment_options = sorted(segments["segment_label"].dropna().unique())
selected_segments = st.sidebar.multiselect("Segment", segment_options, default=segment_options)

region_options = sorted(segments["region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", region_options, default=region_options)

size_options = sorted(segments["store_size"].dropna().unique())
selected_sizes = st.sidebar.multiselect("Store Size", size_options, default=size_options)

filtered = segments[
    segments["segment_label"].isin(selected_segments)
    & segments["region"].isin(selected_regions)
    & segments["store_size"].isin(selected_sizes)
]

# --- KPI row ---
render_kpi_tags([
    {"label": lbl, "value": f"{(filtered['segment_label']==lbl).sum():,}"}
    for lbl in ["Rising Stars", "Steady Performers", "Lean & Consistent", "At-Risk / Declining"]
])

# --- Map colored by segment ---
with st.container(border=True):
    st.markdown('<div class="rp-card-title">Store Segments Map</div>', unsafe_allow_html=True)
    map_data = filtered.merge(cities[["city", "lat", "lng"]], on="city", how="left").dropna(subset=["lat", "lng"])
    if len(map_data) > 0:
        fig = px.scatter_map(
            map_data, lat="lat", lon="lng", color="segment_label",
            color_discrete_map=SEGMENT_COLORS,
            hover_name="city",
            hover_data={"store_id": True, "revenue_vs_size_peer_avg": ":.2f", "lat": False, "lng": False},
            zoom=5.4, center={"lat": 30.3753, "lon": 69.3451}, map_style="open-street-map", height=500,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="#141B2E")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No stores match the selected filters.")

# --- Segment comparison chart ---
with st.container(border=True):
    st.markdown('<div class="rp-card-title">Relative Performance vs. Trend, by Segment</div>', unsafe_allow_html=True)
    if len(filtered) > 0:
        fig2 = px.scatter(
            filtered, x="trend_pct_per_year", y="revenue_vs_size_peer_avg", color="segment_label",
            color_discrete_map=SEGMENT_COLORS, hover_name="store_id",
            labels={"trend_pct_per_year": "Growth Trend", "revenue_vs_size_peer_avg": "Performance vs. Size Peers"},
        )
        fig2.update_layout(**PLOTLY_THEME, height=380)
        fig2.update_xaxes(gridcolor="#263049")
        fig2.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig2, use_container_width=True)

# --- Store table ---
st.markdown('<div class="rp-card-title">Store List</div>', unsafe_allow_html=True)
display_cols = ["store_id", "city", "region", "store_size", "segment_label",
                 "revenue_vs_size_peer_avg", "trend_pct_per_year", "volatility_cv"]
st.dataframe(
    filtered[display_cols].rename(columns={
        "store_id": "Store", "city": "City", "region": "Region", "store_size": "Size",
        "segment_label": "Segment", "revenue_vs_size_peer_avg": "Perf. vs Peers",
        "trend_pct_per_year": "Trend", "volatility_cv": "Volatility",
    }).sort_values("Segment"),
    use_container_width=True, hide_index=True,
)

st.download_button(
    "Download filtered store segments (CSV)",
    data=filtered.to_csv(index=False),
    file_name="stylo_store_segments_filtered.csv",
    mime="text/csv",
)
