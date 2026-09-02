"""
RetailPulse 360 — shared data loading utility.

All pages import from here rather than reading CSVs directly, so:
- loading logic (paths, caching, dtype handling) lives in exactly one place
- Streamlit's @st.cache_data means each file is only read from disk once
  per session, not once per page load
"""

from pathlib import Path
import pandas as pd
import streamlit as st

# app/utils/data_loader.py -> app/ -> project root -> datasets/processed/
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datasets" / "processed"


def _read_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        st.error(
            f"Missing data file: `{filename}`\n\n"
            f"Expected at: `{path}`\n\n"
            f"Make sure the notebook output has been downloaded into "
            f"`datasets/processed/`."
        )
        st.stop()
    return pd.read_csv(path)


@st.cache_data
def load_stores() -> pd.DataFrame:
    return _read_csv("stores.csv")


@st.cache_data
def load_cities() -> pd.DataFrame:
    # cities_with_coords.csv — has lat/lng, used for the map page.
    # Falls back to plain cities.csv if coords haven't been generated yet.
    path = DATA_DIR / "cities_with_coords.csv"
    if path.exists():
        return pd.read_csv(path)
    return _read_csv("cities.csv")


@st.cache_data
def load_store_personalities() -> pd.DataFrame:
    return _read_csv("store_personalities.csv")


@st.cache_data
def load_products() -> pd.DataFrame:
    return _read_csv("products.csv")


@st.cache_data
def load_skus() -> pd.DataFrame:
    return _read_csv("skus.csv")


@st.cache_data
def load_sales() -> pd.DataFrame:
    df = _read_csv("sales.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_color_popularity() -> pd.DataFrame:
    return _read_csv("color_popularity.csv")


@st.cache_data
def load_cross_sell_pairs() -> pd.DataFrame:
    return _read_csv("cross_sell_pairs.csv")


@st.cache_data
def load_review_sentiment() -> pd.DataFrame:
    return _read_csv("review_sentiment.csv")


@st.cache_data
def load_sizing_feedback() -> pd.DataFrame:
    return _read_csv("sizing_feedback.csv")


@st.cache_data
def load_inventory_turnover() -> pd.DataFrame:
    return _read_csv("inventory_turnover_summary.csv")


@st.cache_data
def load_redistribution_recommendations() -> pd.DataFrame:
    return _read_csv("redistribution_recommendations.csv")


@st.cache_data
def load_discount_recommendations() -> pd.DataFrame:
    return _read_csv("discount_recommendations.csv")


@st.cache_data
def load_cross_sell_recommendations() -> pd.DataFrame:
    return _read_csv("cross_sell_recommendations.csv")


@st.cache_data
def load_store_segments() -> pd.DataFrame:
    return _read_csv("store_segments.csv")


@st.cache_data
def load_business_impact_summary() -> pd.DataFrame:
    return _read_csv("business_impact_summary.csv")
