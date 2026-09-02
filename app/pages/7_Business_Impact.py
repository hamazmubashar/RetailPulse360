import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from utils.data_loader import load_business_impact_summary, load_redistribution_recommendations, load_discount_recommendations
from utils.styling import inject_css, render_topbar, render_kpi_tags, render_pending_box, PLOTLY_THEME

st.set_page_config(page_title="Business Impact | RetailPulse 360", page_icon="\U0001F4CA", layout="wide")
inject_css()
render_topbar("Live")

st.markdown('<div class="rp-card-title">Business Impact Summary</div>', unsafe_allow_html=True)
st.caption(
    "Every phase of RetailPulse 360, translated into real business metrics. Deliberately "
    "shown as individually-sourced numbers, not one blended \u2018total impact\u2019 figure \u2014 "
    "every number here is traceable to the notebook that produced it."
)

impact = load_business_impact_summary()
redistribution = load_redistribution_recommendations()
discounts = load_discount_recommendations()

def get_metric(name_contains):
    row = impact[impact["metric"].str.contains(name_contains, case=False, na=False)]
    return row["value"].iloc[0] if len(row) > 0 else "\u2014"

# --- Headline KPIs ---
render_kpi_tags([
    {"label": "Revenue Recovered (Redistribution)", "value": get_metric("Revenue recovered")},
    {"label": "Forecast Accuracy", "value": get_metric("within 1 unit"), "note": "of predictions, within 1 unit of actual"},
    {"label": "Daily Margin Preserved (Pricing)", "value": get_metric("Daily margin preserved")},
    {"label": "Shortages Addressed", "value": get_metric("Shortage situations addressed")},
])

STATUS_COLORS = {"Healthy": "#10B981", "Low": "#F59E0B", "Critical": "#EF4444",
                  "Overstock": "#8B96AC", "Dead": "#EC4899"}

health_row = impact[impact["metric"].str.contains("stock status breakdown", case=False, na=False)]
raw = health_row["value"].iloc[0]
pairs = re.findall(r'([A-Za-z ]+?)\s+(\d+)', raw)
health_df = pd.DataFrame([(label.strip(), int(count)) for label, count in pairs], columns=["Status", "Count"])

# --- Row 1: Stock health, two views (bar + donut) ---
col1, col2 = st.columns([1.4, 1])
with col1:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Current Network Stock Health</div>', unsafe_allow_html=True)
        fig = px.bar(health_df, x="Status", y="Count", color="Status",
                     color_discrete_map=STATUS_COLORS, text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(**PLOTLY_THEME, height=340, showlegend=False, xaxis_title=None, yaxis_title="Store-Products")
        fig.update_xaxes(gridcolor="#263049")
        fig.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Stock Health Share</div>', unsafe_allow_html=True)
        fig_donut = go.Figure(data=[go.Pie(
            labels=health_df["Status"], values=health_df["Count"], hole=0.55,
            marker=dict(colors=[STATUS_COLORS[s] for s in health_df["Status"]]),
            textinfo="percent", textfont=dict(color="#E7ECF4"),
        )])
        fig_donut.update_layout(
            paper_bgcolor="#141B2E", plot_bgcolor="#141B2E", height=340,
            font=dict(color="#E7ECF4"), showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# --- Row 2: Redistribution coverage + Pricing strategy split ---
col3, col4 = st.columns(2)
with col3:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Redistribution Coverage (Honest View)</div>', unsafe_allow_html=True)
        addressed = redistribution.groupby(["to_store", "product_id"]).ngroups
        total_need = 8359  # from Notebook 09 -- total Critical+Low situations
        still_needed = total_need - addressed
        coverage_df = pd.DataFrame({
            "Category": ["Addressed by Redistribution", "Still Needs Supplier Reorder"],
            "Count": [addressed, still_needed],
        })
        fig_cov = px.bar(coverage_df, x="Count", y="Category", orientation="h", text="Count",
                          color="Category", color_discrete_map={
                              "Addressed by Redistribution": "#22D3EE",
                              "Still Needs Supplier Reorder": "#8B96AC",
                          })
        fig_cov.update_traces(textposition="outside")
        fig_cov.update_layout(**PLOTLY_THEME, height=260, showlegend=False, xaxis_title="Situations", yaxis_title=None)
        fig_cov.update_xaxes(gridcolor="#263049")
        fig_cov.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig_cov, use_container_width=True)
        st.caption(
            f"Redistribution addresses {addressed:,} of {total_need:,} situations "
            f"({addressed/total_need*100:.1f}%) using existing network stock \u2014 the "
            f"remainder genuinely needs new inventory from the supplier."
        )

with col4:
    with st.container(border=True):
        st.markdown('<div class="rp-card-title">Pricing Strategy Split</div>', unsafe_allow_html=True)
        margin_preserving = (discounts["discount_pct"] == 0.10).sum()
        liquidation = (discounts["discount_pct"] == 0.30).sum()
        strategy_df = pd.DataFrame({
            "Strategy": ["Margin-Preserving (10%)", "Liquidation (30%)"],
            "Items": [margin_preserving, liquidation],
        })
        fig_strat = px.bar(strategy_df, x="Strategy", y="Items", text="Items", color="Strategy",
                            color_discrete_map={"Margin-Preserving (10%)": "#F59E0B", "Liquidation (30%)": "#EC4899"})
        fig_strat.update_traces(textposition="outside")
        fig_strat.update_layout(**PLOTLY_THEME, height=260, showlegend=False, xaxis_title=None, yaxis_title="Items")
        fig_strat.update_xaxes(gridcolor="#263049")
        fig_strat.update_yaxes(gridcolor="#263049")
        st.plotly_chart(fig_strat, use_container_width=True)
        st.caption(
            f"{margin_preserving} slow-selling items get the smallest discount to preserve "
            f"margin; {liquidation} fully-dead items get a deeper discount to recover capital."
        )

# --- Full data table ---
st.markdown('<div class="rp-card-title">Complete Metrics Table</div>', unsafe_allow_html=True)
st.dataframe(
    impact.rename(columns={"category": "Phase", "metric": "Metric", "value": "Value", "source": "Source"}),
    use_container_width=True, hide_index=True,
    column_config={"Value": st.column_config.TextColumn(width="large")},
)

# --- Honest limitations, called out distinctly ---
st.markdown('<div class="rp-card-title">Honest Limitations</div>', unsafe_allow_html=True)
caveats = impact[impact["source"].str.contains("honest", case=False, na=False)]
for _, row in caveats.iterrows():
    render_pending_box(f"<b>{row['metric']}:</b> {row['value']}")

st.download_button(
    "Download full business impact summary (CSV)",
    data=impact.to_csv(index=False),
    file_name="retailpulse360_business_impact_summary.csv",
    mime="text/csv",
)
