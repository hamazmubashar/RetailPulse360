import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from utils.data_loader import (load_business_impact_summary, load_store_segments,
                                 load_inventory_turnover, load_redistribution_recommendations,
                                 load_discount_recommendations, load_review_sentiment)
from utils.styling import inject_css, render_topbar, render_pending_box

st.set_page_config(page_title="Ask RetailPulse | RetailPulse 360", page_icon="\U0001F4AC", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Ask RetailPulse</div>', unsafe_allow_html=True)
st.caption(
    "Ask a plain-English business question. Answers are grounded strictly in RetailPulse "
    "360's real data \u2014 the AI is instructed never to invent numbers, only explain what "
    "the actual data shows."
)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    render_pending_box(
        "No GEMINI_API_KEY found in .env \u2014 this feature needs an API key configured "
        "before it can answer questions."
    )
    st.stop()


@st.cache_data
def build_business_context() -> str:
    """Compact, real-data summary handed to the AI as grounding context.
    Nothing here is invented -- every line comes from an already-validated
    notebook output."""
    impact = load_business_impact_summary()
    segments = load_store_segments()
    inventory = load_inventory_turnover()
    redistribution = load_redistribution_recommendations()
    discounts = load_discount_recommendations()
    sentiment = load_review_sentiment()

    lines = ["=== RETAILPULSE 360 — REAL BUSINESS DATA SUMMARY ===\n"]

    lines.append("BUSINESS IMPACT METRICS:")
    for _, row in impact.iterrows():
        lines.append(f"- [{row['category']}] {row['metric']}: {row['value']} (source: {row['source']})")

    lines.append("\nSTORE SEGMENTS (190 stores, K-means clustering):")
    lines.append(segments["segment_label"].value_counts().to_string())

    lines.append("\nINVENTORY STOCK STATUS (13,678 store-product situations):")
    lines.append(inventory["stock_status"].value_counts().to_string())

    lines.append(f"\nREDISTRIBUTION: {len(redistribution)} recommended transfers, "
                  f"{redistribution['transfer_qty'].sum()} total units, "
                  f"avg distance {redistribution['distance_km'].mean():.0f} km")

    lines.append(f"\nPRICING: {(discounts['discount_pct']==0.10).sum()} items recommended for "
                  f"margin-preserving 10% discount, {(discounts['discount_pct']==0.30).sum()} "
                  f"items for liquidation-oriented 30% discount")

    lines.append("\nCUSTOMER SENTIMENT (real Amazon shoe reviews, VADER analysis):")
    lines.append(sentiment.to_string(index=False))

    return "\n".join(lines)


SYSTEM_INSTRUCTION = (
    "You are a business analyst assistant for RetailPulse 360, a retail decision-intelligence "
    "platform for a footwear retailer. You will be given a REAL DATA SUMMARY below. "
    "Answer the user's question using ONLY the information in that summary. "
    "Never invent numbers, statistics, or facts not present in the summary. "
    "If the summary doesn't contain enough information to answer the question, say so "
    "plainly rather than guessing. Keep answers concise, business-focused, and actionable. "
    "When relevant, cite which part of the data (e.g. 'Redistribution' or 'Store Segments') "
    "your answer is based on."
)

context = build_business_context()

# --- Example questions (session-state bound, so text persists across reruns) ---
if "rp_question" not in st.session_state:
    st.session_state.rp_question = ""

st.markdown("**Try asking:**")
example_cols = st.columns(3)
examples = [
    "Which stores need the most attention right now?",
    "How much value has redistribution recovered?",
    "What should we do about slow-selling stock?",
]
for col, ex in zip(example_cols, examples):
    if col.button(ex, use_container_width=True):
        st.session_state.rp_question = ex

question = st.text_input("Your question:", key="rp_question")

if st.button("Ask", type="primary") and question:
    with st.spinner("Thinking..."):
        try:
            from google.genai import types
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=20000),  # 20 second timeout, in ms
            )
            full_prompt = f"{SYSTEM_INSTRUCTION}\n\n{context}\n\nQUESTION: {question}"
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=full_prompt,
            )
            st.markdown('<div class="rp-card">', unsafe_allow_html=True)
            st.markdown('<div class="rp-card-title">Answer</div>', unsafe_allow_html=True)
            st.write(response.text)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Something went wrong calling the AI: {type(e).__name__}: {e}")

with st.expander("What data does this AI actually see?"):
    st.text(context)
