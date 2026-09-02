import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_review_sentiment, load_sizing_feedback
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME

st.set_page_config(page_title="Reviews & Sentiment | RetailPulse 360", page_icon="\U0001F4AC", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Review & Sentiment Intelligence</div>', unsafe_allow_html=True)
st.caption(
    "Real customer sentiment and sizing feedback from Amazon footwear reviews (VADER "
    "sentiment, validated against real star ratings)."
)

sentiment = load_review_sentiment()
sizing = load_sizing_feedback()

# --- Honest scope disclosure ---
render_pending_box(
    "Data scope note: this dataset covers Men's and Women's reviews only \u2014 no Kids "
    "review data exists in the source (Men_Women_Shoes_Reviews, Kaggle). Sentiment is "
    "aggregated at the gender level, not by category, since the source data doesn't "
    "support finer granularity. Sizing feedback below is explicitly LOW CONFIDENCE / "
    "directional only \u2014 only 1.6% of all reviews mentioned sizing at all, not enough "
    "volume to drive precise size-curve corrections."
)

# --- KPI row ---
total_reviews = sentiment["review_count"].sum()
overall_avg_sentiment = (sentiment["avg_sentiment"] * sentiment["review_count"]).sum() / total_reviews
total_sizing_mentions = sizing["mention_count"].sum()

render_kpi_tags([
    {"label": "Reviews Analyzed", "value": f"{total_reviews:,}"},
    {"label": "Overall Avg Sentiment", "value": f"{overall_avg_sentiment:.3f}",
     "note": "VADER compound score, -1 to +1"},
    {"label": "Sizing Mentions", "value": f"{total_sizing_mentions:,}",
     "note": f"{total_sizing_mentions/total_reviews*100:.1f}% of reviews \u2014 low confidence"},
    {"label": "Coverage", "value": "Men's / Women's", "note": "No Kids data available"},
])

# --- Sentiment by gender ---
col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Sentiment by Gender</div>', unsafe_allow_html=True)
        fig1 = px.bar(sentiment, x="Shoe Type", y="avg_sentiment", error_y="std")
        fig1.update_layout(**PLOTLY_THEME, height=320, showlegend=False,
                            xaxis_title=None, yaxis_title="Avg Sentiment (VADER)")
        fig1.update_traces(marker_color="#22D3EE")
        fig1.update_xaxes(gridcolor="#263049")
        fig1.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig1, use_container_width=True)

with col_b:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Sizing Feedback Breakdown</div>', unsafe_allow_html=True)
        fig2 = px.bar(sizing, x="Shoe Type", y="mention_count", color="sizing_feedback", barmode="group")
        fig2.update_layout(**PLOTLY_THEME, height=320, xaxis_title=None, yaxis_title="Mentions")
        fig2.update_xaxes(gridcolor="#263049")
        fig2.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig2, use_container_width=True)

# --- Raw data tables ---
st.markdown('<div class="rp-card-title">Sentiment Summary</div>', unsafe_allow_html=True)
st.dataframe(
    sentiment.rename(columns={
        "Shoe Type": "Gender", "avg_sentiment": "Avg Sentiment", "median_sentiment": "Median Sentiment",
        "std": "Std Dev", "review_count": "Review Count",
    }),
    use_container_width=True, hide_index=True,
)

st.markdown('<div class="rp-card-title">Sizing Feedback Detail</div>', unsafe_allow_html=True)
st.dataframe(
    sizing.rename(columns={
        "Shoe Type": "Gender", "sizing_feedback": "Feedback Type", "mention_count": "Mentions",
        "confidence": "Confidence", "usage_note": "Usage Note",
    }),
    use_container_width=True, hide_index=True,
    column_config={"Usage Note": st.column_config.TextColumn(width="large")},
)

st.download_button(
    "Download sentiment summary (CSV)", data=sentiment.to_csv(index=False),
    file_name="review_sentiment_summary.csv", mime="text/csv",
)
