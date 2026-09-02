import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_stores, load_cities
from utils.styling import inject_css, render_topbar, PLOTLY_THEME

st.set_page_config(page_title="Store Network | RetailPulse 360", page_icon="\U0001F5FA", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Store Network</div>', unsafe_allow_html=True)
st.caption(
    "190 physical stores across 94 cities and towns, spanning every province and "
    "territory in Pakistan."
)

stores = load_stores()
cities = load_cities()
physical = stores[stores["channel"] == "Physical"].copy()

# --- Sidebar filters ---
st.sidebar.header("Filters")
regions = sorted(physical["region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

tiers = sorted(physical["city_tier"].dropna().unique())
selected_tiers = st.sidebar.multiselect("City Tier", tiers, default=tiers)

sizes = sorted(physical["store_size"].dropna().unique())
selected_sizes = st.sidebar.multiselect("Store Size", sizes, default=sizes)

filtered = physical[
    physical["region"].isin(selected_regions)
    & physical["city_tier"].isin(selected_tiers)
    & physical["store_size"].isin(selected_sizes)
]

st.sidebar.markdown("---")
st.sidebar.metric("Stores matching filters", len(filtered))

# --- Aggregate to city level for the map ---
city_counts = (
    filtered.groupby("city")
    .agg(store_count=("store_id", "count"))
    .reset_index()
    .merge(cities[["city", "lat", "lng", "province", "city_tier"]], on="city", how="left")
)
city_counts = city_counts.dropna(subset=["lat", "lng"])

# --- Map ---
with st.container(border=True):
    st.markdown('<div class="rp-card-title">Stores by City</div>', unsafe_allow_html=True)
    if len(city_counts) > 0:
        fig = px.scatter_map(
            city_counts,
            lat="lat",
            lon="lng",
            size="store_count",
            color="store_count",
            hover_name="city",
            hover_data={"store_count": True, "province": True, "lat": False, "lng": False},
            color_continuous_scale=[[0, "#22D3EE"], [0.5, "#EC4899"], [1, "#F59E0B"]],
            size_max=35,
            zoom=5.4,
            center={"lat": 30.3753, "lon": 69.3451},  # Pakistan's true geographic center
            map_style="open-street-map",
            height=550,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="#141B2E")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No stores match the selected filters.")

# --- Store table ---
st.markdown('<div class="rp-card-title">Store List</div>', unsafe_allow_html=True)
display_cols = ["store_id", "city", "region", "city_tier", "store_size"]
st.dataframe(
    filtered[display_cols]
    .rename(columns={"store_id": "Store", "city": "City", "region": "Region",
                      "city_tier": "City Tier", "store_size": "Size"})
    .sort_values(["Region", "City", "Store"]),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download filtered store list (CSV)",
    data=filtered[display_cols].to_csv(index=False),
    file_name="stylo_stores_filtered.csv",
    mime="text/csv",
)
