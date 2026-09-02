"""
RetailPulse 360 — shared visual identity (navy/slate executive dashboard).

IMPORTANT: every HTML fragment built here is a SINGLE-LINE string with no
embedded blank lines. Streamlit's markdown parser treats a blank line
inside an HTML block as the end of "raw HTML" mode -- everything after
it reverts to literal/code rendering. Single-line strings avoid this
entirely, rather than relying on careful whitespace management.
"""

import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --bg-primary: #0B1220;
            --bg-card: #141B2E;
            --border: #263049;
            --text-primary: #E7ECF4;
            --text-muted: #8B96AC;
            --accent-cyan: #22D3EE;
            --accent-magenta: #EC4899;
            --status-green: #10B981;
            --status-amber: #F59E0B;
            --status-red: #EF4444;
        }

        .stApp { background-color: var(--bg-primary); }
        html, body, [class*="css"] {
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700; color: var(--text-primary); }
        [data-testid="stSidebar"] { background-color: #080D18; border-right: 1px solid var(--border); }
        [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

        .rp-topbar {
            display: flex; align-items: center; justify-content: space-between;
            padding: 0.9rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.25rem;
        }
        .rp-brand { font-size: 1.35rem; font-weight: 700; color: var(--text-primary); }
        .rp-brand span { color: var(--accent-magenta); }
        .rp-brand-sub { font-size: 0.8rem; color: var(--text-muted); margin-left: 0.6rem; }
        .rp-sync { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-muted); }

        .rp-kpi-row { display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0 1.75rem 0; }
        .rp-kpi {
            background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
            padding: 1.1rem 1.3rem; flex: 1; min-width: 190px;
        }
        .rp-kpi-label {
            font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
            color: var(--text-muted); display: block; margin-bottom: 0.5rem;
        }
        .rp-kpi-value { font-size: 1.9rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
        .rp-kpi-value.pending { font-size: 1.1rem; font-weight: 500; color: var(--text-muted); font-style: italic; }
        .rp-kpi-delta { font-size: 0.78rem; margin-top: 0.4rem; }
        .rp-kpi-delta.up { color: var(--status-green); }
        .rp-kpi-delta.down { color: var(--status-red); }
        .rp-kpi-note { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.4rem; }

        .rp-card {
            background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
            padding: 1.25rem 1.4rem; margin-bottom: 1.25rem;
        }
        .rp-card-title { font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.9rem; }

        .rp-pending-box {
            border: 1px dashed var(--border); border-radius: 8px; padding: 1.5rem;
            text-align: center; color: var(--text-muted); font-size: 0.85rem;
        }

        .rp-badge {
            display: inline-block; padding: 0.15rem 0.55rem; border-radius: 5px;
            font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 600;
        }
        .rp-badge.p1 { background: rgba(239,68,68,0.15); color: var(--status-red); }
        .rp-badge.p2 { background: rgba(245,158,11,0.15); color: var(--status-amber); }
        .rp-badge.p3 { background: rgba(16,185,129,0.15); color: var(--status-green); }

        [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }

        /* Restyle Streamlit's NATIVE bordered container (st.container(border=True))
           to match our theme -- this replaces the broken manual div-open/close
           pattern used before, which couldn't actually nest native widgets. */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
            padding: 0.5rem 0.25rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(sync_label: str):
    html = (
        '<div class="rp-topbar">'
        '<div><span class="rp-brand">RetailPulse 360 <span>| Stylo</span></span>'
        f'<span class="rp-brand-sub">Executive Dashboard</span></div>'
        f'<div class="rp-sync">Last data: {sync_label}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_tags(items: list[dict]):
    """Each item: {"label","value","delta","delta_dir","pending","note"} -- all optional except label/value."""
    cards = []
    for it in items:
        value_class = "rp-kpi-value pending" if it.get("pending") else "rp-kpi-value"
        delta_html = ""
        if it.get("delta") and not it.get("pending"):
            d = it.get("delta_dir", "up")
            arrow = "\u25b2" if d == "up" else "\u25bc"
            delta_html = f'<div class="rp-kpi-delta {d}">{arrow} {it["delta"]}</div>'
        note_html = f'<div class="rp-kpi-note">{it["note"]}</div>' if it.get("note") else ""
        card = (
            '<div class="rp-kpi">'
            f'<span class="rp-kpi-label">{it["label"]}</span>'
            f'<div class="{value_class}">{it["value"]}</div>'
            f'{delta_html}{note_html}'
            '</div>'
        )
        cards.append(card)
    st.markdown(f'<div class="rp-kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_pending_box(message: str):
    st.markdown(f'<div class="rp-pending-box">{message}</div>', unsafe_allow_html=True)


def priority_badge(level: str) -> str:
    cls = {"P1": "p1", "P2": "p2", "P3": "p3"}.get(level, "p3")
    return f'<span class="rp-badge {cls}">{level}</span>'


PLOTLY_THEME = dict(
    paper_bgcolor="#141B2E",
    plot_bgcolor="#141B2E",
    font=dict(family="Inter, sans-serif", color="#E7ECF4"),
    colorway=["#22D3EE", "#EC4899", "#10B981", "#F59E0B"],
)
