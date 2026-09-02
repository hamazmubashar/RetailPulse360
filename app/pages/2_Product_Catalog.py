import streamlit as st
import pandas as pd
from utils.data_loader import load_products, load_skus, load_cross_sell_recommendations
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME
import plotly.express as px

st.set_page_config(page_title="Product Catalog | RetailPulse 360", page_icon="\U0001F45F", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Product Catalog</div>', unsafe_allow_html=True)
st.caption(
    "72 product styles, 3,296 SKUs (size \u00d7 color combinations), across Men's / "
    "Women's / Kids and Casual / Formal / Sports."
)

products = load_products()
cross_sell = load_cross_sell_recommendations()
skus = load_skus()

# --- Sidebar filters ---
st.sidebar.header("Filters")
genders = sorted(products["gender"].dropna().unique())
selected_genders = st.sidebar.multiselect("Gender", genders, default=genders)

categories = sorted(products["category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

data_source = st.sidebar.radio(
    "Color Data Source",
    ["All", "Real H&M Signal Only", "Industry Estimate Only"],
    help="Whether this style's color choices came from real H&M retail data "
         "or a documented industry-standard assumption (used where H&M had no "
         "real signal, e.g. Sports, Men's Formal).",
)

price_min, price_max = int(products["price_pkr"].min()), int(products["price_pkr"].max())
price_range = st.sidebar.slider("Price Range (PKR)", price_min, price_max, (price_min, price_max))

# --- Apply filters ---
filtered_products = products[
    products["gender"].isin(selected_genders)
    & products["category"].isin(selected_categories)
    & products["price_pkr"].between(price_range[0], price_range[1])
]
if data_source == "Real H&M Signal Only":
    filtered_products = filtered_products[filtered_products["has_real_color_signal"] == True]
elif data_source == "Industry Estimate Only":
    filtered_products = filtered_products[filtered_products["has_real_color_signal"] == False]

filtered_skus = skus[skus["product_id"].isin(filtered_products["product_id"])]

# --- KPI row ---
real_pct = (
    filtered_products["has_real_color_signal"].mean() * 100
    if len(filtered_products) > 0 else 0
)
render_kpi_tags([
    {"label": "Styles Matching Filters", "value": f"{len(filtered_products):,}"},
    {"label": "SKUs Matching Filters", "value": f"{len(filtered_skus):,}"},
    {"label": "Avg Price", "value": f"PKR {filtered_products['price_pkr'].mean():,.0f}" if len(filtered_products) else "\u2014"},
    {"label": "Real Color Data", "value": f"{real_pct:.0f}%",
     "note": "Share of styles whose colors came from real H&M signal"},
])

# --- Category x Gender breakdown chart ---
st.markdown('<div class="rp-card">', unsafe_allow_html=True)
st.markdown('<div class="rp-card-title">Styles by Gender & Category</div>', unsafe_allow_html=True)
breakdown = filtered_products.groupby(["gender", "category"]).size().reset_index(name="count")
if len(breakdown) > 0:
    fig = px.bar(breakdown, x="category", y="count", color="gender", barmode="group")
    fig.update_layout(**PLOTLY_THEME, height=320, xaxis_title=None, yaxis_title="Styles")
    fig.update_xaxes(gridcolor="#263049")
    fig.update_yaxes(gridcolor="#263049")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No styles match the selected filters.")
st.markdown('</div>', unsafe_allow_html=True)

# --- Product style table ---
st.markdown('<div class="rp-card-title">Product Styles</div>', unsafe_allow_html=True)
display = filtered_products.copy()
display["Data Source"] = display["has_real_color_signal"].map(
    {True: "Real H&M Signal", False: "Industry Estimate"}
)
display["Price"] = display["price_pkr"].apply(lambda x: f"PKR {x:,.0f}")
sku_counts = filtered_skus.groupby("product_id").size().rename("sku_count")
display = display.merge(sku_counts, on="product_id", how="left")

st.dataframe(
    display[["style_name", "gender", "category", "Price", "sku_count", "Data Source"]]
    .rename(columns={"style_name": "Style", "gender": "Gender", "category": "Category",
                      "sku_count": "SKU Count"})
    .sort_values(["Gender", "Category", "Style"]),
    use_container_width=True, hide_index=True,
)

# --- SKU drill-down ---
st.markdown('<div class="rp-card-title">SKU Explorer</div>', unsafe_allow_html=True)
if len(filtered_products) > 0:
    style_options = filtered_products.sort_values("style_name")["style_name"].tolist()
    selected_style = st.selectbox("Choose a style to see its size/color breakdown", style_options)
    selected_product_id = filtered_products[filtered_products["style_name"] == selected_style]["product_id"].iloc[0]
    style_skus = skus[skus["product_id"] == selected_product_id].copy()
    style_skus["Price"] = style_skus["price_pkr"].apply(lambda x: f"PKR {x:,.0f}")
    st.dataframe(
        style_skus[["sku_id", "size", "color", "Price"]]
        .rename(columns={"sku_id": "SKU", "size": "Size", "color": "Color"})
        .sort_values(["Color", "Size"]),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Download this style's SKUs (CSV)",
        data=style_skus.to_csv(index=False),
        file_name=f"{selected_style.replace(' ', '_')}_skus.csv",
        mime="text/csv",
    )

    # --- Customers Also Bought (real H&M-derived category affinity) ---
    st.markdown('<div class="rp-card-title">Customers Also Bought</div>', unsafe_allow_html=True)
    style_recs = cross_sell[cross_sell["source_product_id"] == selected_product_id].sort_values(
        "affinity_strength", ascending=False
    )
    if len(style_recs) > 0:
        st.dataframe(
            style_recs[["recommended_style_name", "affinity_strength"]]
            .rename(columns={"recommended_style_name": "Recommended Style",
                              "affinity_strength": "Affinity (real H&M signal)"}),
            use_container_width=True, hide_index=True,
        )
    else:
        render_pending_box(
            "No real cross-sell signal exists for this category (Sports and Men's/Formal "
            "have no matching H&M purchase data \u2014 see Notebook 03/11 for the documented "
            "gap). No recommendation is shown here rather than a fabricated one."
        )
else:
    st.info("No styles match the selected filters.")
