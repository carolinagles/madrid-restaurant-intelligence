"""Visual layer for Madrid Restaurant Intelligence: "Silver glass".

A quiet silver backdrop with floating glass pills, and clear bevelled glass panels on top.
Designed to be read on a projector in a business room: large type, high contrast,
left-aligned Swiss grid, one typeface.

Public API (used by streamlit_app.py and the other app modules):
    apply_style()               inject the global stylesheet
    render_sidebar_brand()      brand block at the top of the sidebar
    render_header(compact, title)  page header (compact bar on secondary pages)
    render_data_note(text)      small glass note about the data snapshot
    render_footer(text)         quiet footer line
    glass_container(key)        bordered st.container styled as a glass panel
    style_figure(fig)           apply the house style to a Plotly figure
    styled_chart(fig)           legacy alias of style_figure
    show_chart(fig)             style + render a Plotly figure at full width
    FULL_WIDTH, PLOTLY_CONFIG, COLORS
"""

from html import escape
from importlib.metadata import PackageNotFoundError, version

import streamlit as st

# ---------------------------------------------------------------------------
# Palette. Keep in sync with the CSS custom properties below.
# Old key names (forest, sage, clay, gold...) are kept so other modules still work.
# All text colours reach WCAG AA (>= 4.5:1) on the frosted panels.
# ---------------------------------------------------------------------------
COLORS = {
    'forest': '#2F3A44',       # slate: primary series, positive
    'forest_soft': '#4A5561',
    'sage': '#B4BAC2',         # silver: peer reference
    'ivory': '#E4E7EB',        # base
    'paper': '#FFFFFF',
    'ink': '#1A1D21',
    'muted': '#4A5058',
    'gold': '#9AA1AA',         # pewter: neutral, secondary fills
    'gold_text': '#4A5058',
    'wine': '#8E3B2F',
    'clay': '#A4483A',         # muted brick: negative
}

FONT = "'Instrument Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif"
SANS = SERIF = FONT  # legacy names

PLOTLY_CONFIG = {
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
    'toImageButtonOptions': {'format': 'png', 'scale': 2},
}


def _streamlit_supports_width_stretch():
    """`use_container_width` is deprecated in recent Streamlit; use `width` when possible."""
    try:
        major, minor = (int(part) for part in version('streamlit').split('.')[:2])
    except (PackageNotFoundError, ValueError):
        return False
    return (major, minor) >= (1, 50)


# Pass as **FULL_WIDTH to st.plotly_chart, st.dataframe, st.button...
FULL_WIDTH = ({'width': 'stretch'} if _streamlit_supports_width_stretch()
              else {'use_container_width': True})

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');

:root {
    --graphite: #1A1D21;
    --graphite-soft: #3A4048;
    --slate: #2F3A44;
    --steel: #8C949E;
    --amber: #B48A3E;
    --brick: #A4483A;
    --brick-text: #8E3B2F;
    --base: #DCDFE3;
    --ink: #1A1D21;
    --body: #30353B;
    --muted: #4A5058;

    --font: 'Instrument Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;

    /* Clear glass: mostly transparent, with a bevelled edge that catches the light. */
    --glass: linear-gradient(145deg, rgba(255,255,255,0.46) 0%, rgba(255,255,255,0.14) 100%);
    --glass-strong: linear-gradient(145deg, rgba(255,255,255,0.70) 0%, rgba(255,255,255,0.38) 100%);
    --glass-edge: rgba(255,255,255,0.78);
    --glass-blur: blur(18px) saturate(140%);
    --glass-shadow:
        inset 1px 1px 0 rgba(255,255,255,0.95),
        inset -1px -1px 0 rgba(26,29,33,0.07),
        inset 0 0 24px rgba(255,255,255,0.18),
        0 30px 60px -32px rgba(26,29,33,0.40),
        0 8px 18px -12px rgba(26,29,33,0.16);
    --line: rgba(26,29,33,0.10);

    --r-xl: 44px;   /* hero: a wide pill */
    --r-lg: 26px;   /* panels */
    --r-md: 18px;   /* inner blocks */
    --r-sm: 14px;   /* inputs */
}

/* ---------- Base & liquid backdrop --------------------------------- */
html, body, [class*='css'], .stApp, .stMarkdown, button, input, textarea {
    font-family: var(--font);
}
html { font-size: 17px; }
body, .stApp { color: var(--ink); }

.stApp {
    background:
        radial-gradient(70rem 40rem at 85% -10%, rgba(255,255,255,0.85), transparent 60%),
        linear-gradient(110deg, #AEB4BC 0%, #CDD1D6 28%, #E6E8EB 60%, #EEF0F2 100%);
    background-attachment: fixed;
}

/* Large glass pills drift behind the content, like objects under a frosted pane. */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background: url("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%201600%201000'%20preserveAspectRatio='xMidYMid%20slice'%3E%20%3Cdefs%3E%20%3ClinearGradient%20id='f'%20x1='0'%20y1='0'%20x2='1'%20y2='1'%3E%3Cstop%20offset='0'%20stop-color='#fff'%20stop-opacity='.30'/%3E%3Cstop%20offset='1'%20stop-color='#fff'%20stop-opacity='.04'/%3E%3C/linearGradient%3E%20%3ClinearGradient%20id='s'%20x1='0'%20y1='0'%20x2='1'%20y2='1'%3E%3Cstop%20offset='0'%20stop-color='#fff'%20stop-opacity='.95'/%3E%3Cstop%20offset='.5'%20stop-color='#fff'%20stop-opacity='.25'/%3E%3Cstop%20offset='1'%20stop-color='#59616b'%20stop-opacity='.28'/%3E%3C/linearGradient%3E%20%3Cfilter%20id='d'%20x='-20%25'%20y='-40%25'%20width='140%25'%20height='180%25'%3E%3CfeDropShadow%20dx='0'%20dy='26'%20stdDeviation='22'%20flood-color='#1a1d21'%20flood-opacity='.16'/%3E%3C/filter%3E%20%3C/defs%3E%20%3Cg%20fill='url%28#f%29'%20stroke='url%28#s%29'%20stroke-width='1.6'%20filter='url%28#d%29'%3E%20%3Crect%20x='-240'%20y='-110'%20width='560'%20height='230'%20rx='115'/%3E%20%3Crect%20x='470'%20y='-90'%20width='1340'%20height='250'%20rx='125'/%3E%20%3Crect%20x='1230'%20y='390'%20width='560'%20height='220'%20rx='110'/%3E%20%3Crect%20x='-180'%20y='780'%20width='1120'%20height='290'%20rx='145'/%3E%20%3Crect%20x='1120'%20y='820'%20width='640'%20height='260'%20rx='130'/%3E%20%3C/g%3E%3C/svg%3E") center / cover no-repeat;
}

[data-testid='stAppViewContainer'],
[data-testid='stMain'],
.main {
    position: relative;
    z-index: 1;
    background: transparent;
}

[data-testid='stHeader'] {
    background: rgba(230,232,235,0.30);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid rgba(255,255,255,0.55);
}

.block-container {
    max-width: 1280px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4 {
    color: var(--ink);
    font-family: var(--font);
    font-weight: 600;
    letter-spacing: -0.025em;
}
h2 { font-size: 1.9rem; line-height: 1.15; }
h3 { font-size: 1.3rem; line-height: 1.25; }
p, li { color: var(--body); line-height: 1.6; }

[data-testid='stMetricValue'],
[data-testid='stDataFrame'],
.tabular { font-variant-numeric: tabular-nums; }

button:focus-visible,
a:focus-visible,
[role='tab']:focus-visible,
[data-baseweb='select'] > div:focus-within,
[data-baseweb='input'] > div:focus-within,
textarea:focus-visible {
    outline: 2px solid var(--graphite) !important;
    outline-offset: 2px;
}
::selection { background: rgba(140,148,158,0.45); color: var(--ink); }

/* ---------- Glass surfaces (Streamlit widgets) ---------------------- */
[data-testid='stMetric'],
[data-testid='stExpander'] details,
[data-testid='stPlotlyChart'],
[data-testid='stDataFrame'],
[data-testid='stVerticalBlockBorderWrapper'],
[class*='st-key-glass-'],
.glass {
    background: var(--glass);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-edge) !important;
    box-shadow: var(--glass-shadow);
}

[data-testid='stVerticalBlockBorderWrapper'],
[class*='st-key-glass-'] {
    border-radius: var(--r-lg) !important;
    padding: 1.4rem 1.5rem !important;
}
/* Avoid a double panel when Streamlit nests its own wrapper inside the keyed one. */
[class*='st-key-glass-'] [data-testid='stVerticalBlockBorderWrapper'] {
    background: transparent; box-shadow: none; border: 0 !important;
    backdrop-filter: none; padding: 0 !important;
}

/* Metrics */
[data-testid='stMetric'] {
    min-height: 124px;
    padding: 1.2rem 1.35rem;
    border-radius: var(--r-lg);
}
[data-testid='stMetricLabel'],
[data-testid='stMetricLabel'] p {
    color: var(--muted);
    font-size: 0.86rem;
    font-weight: 500;
}
[data-testid='stMetricValue'] {
    color: var(--ink);
    font-size: 2.05rem;
    font-weight: 600;
    letter-spacing: -0.03em;
}

/* Charts and tables sit on their own panel. */
[data-testid='stPlotlyChart'] {
    padding: 0.8rem 0.6rem 0.2rem;
    border-radius: var(--r-lg);
    overflow: hidden;
}
[data-testid='stDataFrame'] {
    padding: 0.35rem;
    border-radius: var(--r-lg);
    overflow: hidden;
}

/* Expanders */
[data-testid='stExpander'] details {
    border-radius: var(--r-lg);
    overflow: hidden;
}
[data-testid='stExpander'] summary { padding: 0.95rem 1.2rem; }
[data-testid='stExpander'] summary p { color: var(--ink); font-weight: 600; }
[data-testid='stExpander'] summary:hover { background: rgba(255,255,255,0.35); }

/* Alerts become tinted glass with a slim status edge. */
[data-testid='stAlert'] > div {
    background: var(--glass-strong) !important;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-edge);
    border-left: 4px solid var(--steel);
    border-radius: var(--r-md);
    box-shadow: var(--glass-shadow);
    color: var(--ink);
}
[data-testid='stAlert'] p { color: var(--ink); }
[data-testid='stAlert']:has([data-testid='stAlertContentSuccess']) > div { border-left-color: var(--slate); }
[data-testid='stAlert']:has([data-testid='stAlertContentWarning']) > div { border-left-color: var(--amber); }
[data-testid='stAlert']:has([data-testid='stAlertContentError'])   > div { border-left-color: var(--brick); }

[data-testid='stCaptionContainer'],
[data-testid='stCaptionContainer'] p { color: var(--muted); font-size: 0.86rem; }

/* ---------- Sidebar: a tall pane of glass --------------------------- */
[data-testid='stSidebar'] {
    background: rgba(255,255,255,0.22);
    backdrop-filter: blur(30px) saturate(140%);
    -webkit-backdrop-filter: blur(30px) saturate(160%);
    border-right: 1px solid rgba(255,255,255,0.7);
    box-shadow: inset -1px 0 0 rgba(26,29,33,0.05);
}
[data-testid='stSidebar'] > div:first-child { background: transparent; }
[data-testid='stSidebar'] h3 { font-size: 1rem; color: var(--muted); font-weight: 600; }
[data-testid='stSidebar'] hr { border-color: rgba(26,29,33,0.10); }

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0 1.4rem;
    margin-bottom: 1.1rem;
    border-bottom: 1px solid rgba(26,29,33,0.10);
}
.sidebar-brand__mark {
    flex: 0 0 2.6rem;
    height: 1.5rem;
    border-radius: 999px;
    background: linear-gradient(145deg, rgba(255,255,255,0.8), rgba(255,255,255,0.15));
    border: 1px solid rgba(255,255,255,0.95);
    box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 rgba(26,29,33,0.12),
                0 8px 16px -8px rgba(26,29,33,0.35);
}
.sidebar-brand strong {
    display: block;
    color: var(--ink);
    font-size: 1.05rem;
    font-weight: 400;
    letter-spacing: -0.01em;
    line-height: 1.2;
}
.sidebar-brand span {
    display: block;
    color: var(--muted);
    font-size: 0.82rem;
}

/* Navigation as glass pills; the active page is a raised white pill. */
[data-testid='stSidebar'] [role='radiogroup'] { gap: 0.3rem; }
[data-testid='stSidebar'] [role='radiogroup'] label {
    display: flex;
    align-items: center;
    min-height: 46px;
    padding: 0.5rem 0.85rem;
    border: 1px solid transparent;
    border-radius: 999px;
    cursor: pointer;
    transition: background-color 160ms ease, border-color 160ms ease;
}
[data-testid='stSidebar'] [role='radiogroup'] label > div:first-child { display: none; }
[data-testid='stSidebar'] [role='radiogroup'] label:hover {
    background: rgba(255,255,255,0.5);
    border-color: rgba(255,255,255,0.8);
}
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) {
    background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(255,255,255,0.62));
    border-color: rgba(255,255,255,0.95);
    box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 rgba(26,29,33,0.06),
                0 10px 22px -14px rgba(26,29,33,0.45);
}
[data-testid='stSidebar'] [role='radiogroup'] label p { color: var(--ink); font-weight: 500; }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) p { color: var(--ink) !important; font-weight: 600; }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:focus-visible) {
    outline: 2px solid var(--graphite);
    outline-offset: 2px;
}

/* ---------- Tabs: segmented glass control ---------------------------- */
.stTabs [data-baseweb='tab-list'] {
    gap: 0.25rem;
    padding: 0.3rem;
    border: 1px solid var(--glass-edge);
    border-radius: 999px;
    background: var(--glass);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    box-shadow: var(--glass-shadow);
    overflow-x: auto;
    width: fit-content;
    max-width: 100%;
}
.stTabs [data-baseweb='tab'] {
    height: 42px;
    padding: 0 1.15rem;
    border-radius: 999px;
    color: var(--muted);
    font-weight: 500;
    white-space: nowrap;
    background: transparent;
}
.stTabs [aria-selected='true'] {
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(26,29,33,0.08), 0 6px 14px -8px rgba(26,29,33,0.3);
}
.stTabs [aria-selected='true'] p { color: var(--ink) !important; font-weight: 600; }
.stTabs [data-baseweb='tab-highlight'],
.stTabs [data-baseweb='tab-border'] { display: none; }

/* ---------- Buttons -------------------------------------------------- */
.stButton > button,
.stDownloadButton > button,
[data-testid='stFormSubmitButton'] > button {
    min-height: 46px;
    padding: 0 1.3rem;
    border: 1px solid var(--glass-edge);
    border-radius: 999px;
    color: var(--ink);
    background: var(--glass-strong);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 6px 16px -10px rgba(26,29,33,0.35);
    font-weight: 600;
    transition: background-color 160ms ease, box-shadow 160ms ease, color 160ms ease;
}
.stButton > button p,
.stDownloadButton > button p,
[data-testid='stFormSubmitButton'] > button p { color: inherit; font-weight: 600; }
.stButton > button:hover,
.stDownloadButton > button:hover {
    color: var(--graphite);
    border-color: rgba(26,29,33,0.35);
    background: rgba(255,255,255,0.9);
}

/* Primary actions: a brighter, raised glass pill with dark text. */
button[kind='primary'],
button[kind='primaryFormSubmit'],
[data-testid^='stBaseButton-primary'] {
    color: var(--ink) !important;
    border: 1px solid rgba(255,255,255,0.95) !important;
    background: linear-gradient(145deg, rgba(255,255,255,0.92), rgba(255,255,255,0.55)) !important;
    box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 rgba(26,29,33,0.08),
                0 14px 28px -16px rgba(26,29,33,0.55) !important;
}
button[kind='primary'] p, button[kind='primaryFormSubmit'] p,
[data-testid^='stBaseButton-primary'] p { color: var(--ink) !important; }
button[kind='primary']:hover,
button[kind='primaryFormSubmit']:hover,
[data-testid^='stBaseButton-primary']:hover {
    background: #FFFFFF !important;
    box-shadow: inset 1px 1px 0 #FFFFFF, 0 18px 32px -16px rgba(26,29,33,0.6) !important;
}

/* ---------- Inputs and menus ---------------------------------------- */
[data-baseweb='select'] > div,
[data-baseweb='input'] > div,
[data-baseweb='textarea'],
textarea {
    border: 1px solid rgba(255,255,255,0.85) !important;
    border-radius: var(--r-sm) !important;
    background: rgba(255,255,255,0.62) !important;
    box-shadow: inset 0 1px 2px rgba(26,29,33,0.06);
}
textarea { font-size: 1rem !important; line-height: 1.55 !important; }
[data-baseweb='tag'] { border-radius: 999px !important; background: var(--slate) !important; }
[data-baseweb='popover'] > div,
[data-baseweb='menu'] {
    background: rgba(255,255,255,0.86) !important;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--r-md) !important;
}

/* Code blocks (developer snippet) and heading anchors. */
[data-testid='stCode'] pre, .stCode pre {
    background: rgba(36,40,46,0.88) !important;
    border-radius: var(--r-md) !important;
    border: 1px solid rgba(255,255,255,0.15);
}
[data-testid='stHeaderActionElements'], .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a {
    display: none !important;
}

/* ---------- Page header --------------------------------------------- */
.page-head {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 0.3rem 1rem;
    margin-bottom: 1.4rem;
}
.page-head h1 {
    margin: 0;
    padding: 0;
    font-size: clamp(1.9rem, 3vw, 2.5rem);
    letter-spacing: -0.035em;
}
.page-head p { margin: 0; color: var(--muted); }

.data-note {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    margin: 0 0 1.4rem;
    padding: 0.45rem 0.95rem;
    border-radius: 999px;
    font-size: 0.84rem;
    color: var(--muted);
}
.data-note::before {
    content: '';
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: var(--amber);
    box-shadow: 0 0 0 3px rgba(140,148,158,0.25);
}

/* ---------- Start here: hero with a review journey ------------------- */
.hero {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
    gap: 3rem;
    align-items: center;
    padding: 3.6rem 4rem;
    margin-bottom: 1.6rem;
    border-radius: var(--r-xl);
    overflow: hidden;
}
/* Liquid specular highlight across the top of the pane. */
.hero::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    background:
        radial-gradient(55% 45% at 15% 0%, rgba(255,255,255,0.55), transparent 70%),
        linear-gradient(180deg, rgba(255,255,255,0.20), transparent 35%);
}
.hero > * { position: relative; }
.hero__brand {
    margin: 0 0 1.4rem;
    color: var(--muted);
    font-size: 1rem;
    font-weight: 400;
}
.hero__brand b { color: var(--ink); font-weight: 700; }
.hero h1 {
    margin: 0;
    padding: 0;
    font-size: clamp(2.5rem, 4.8vw, 4.2rem);
    font-weight: 600;
    line-height: 1.02;
    letter-spacing: -0.045em;
    text-wrap: balance;
}
.hero__lede {
    max-width: 52ch;
    margin: 1.4rem 0 0;
    font-size: 1.1rem;
    line-height: 1.65;
    color: var(--body);
}

.journey {
    margin: 0;
    padding: 1.4rem 1.5rem;
    border-radius: var(--r-lg);
    background: linear-gradient(145deg, rgba(255,255,255,0.55), rgba(255,255,255,0.20));
    border: 1px solid rgba(255,255,255,0.9);
    box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 rgba(26,29,33,0.06),
                0 18px 40px -24px rgba(26,29,33,0.4);
}
.journey figcaption {
    margin-bottom: 1rem;
    color: var(--muted);
    font-size: 0.86rem;
}
.journey ol { list-style: none; margin: 0; padding: 0; }
.journey li {
    position: relative;
    padding: 0 0 1.15rem 1.9rem;
    opacity: 0;
    animation: journey-in 520ms cubic-bezier(.2,.7,.2,1) forwards;
}
.journey li:nth-child(1) { animation-delay: 150ms; }
.journey li:nth-child(2) { animation-delay: 650ms; }
.journey li:nth-child(3) { animation-delay: 1150ms; }
.journey li:nth-child(4) { animation-delay: 1650ms; padding-bottom: 0; }
/* The thread that connects the steps. */
.journey li::before {
    content: '';
    position: absolute;
    left: 0.42rem;
    top: 0.45rem;
    width: 0.62rem;
    height: 0.62rem;
    border-radius: 50%;
    background: #FFFFFF;
    border: 2px solid var(--graphite);
}
.journey li:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 0.69rem;
    top: 1.2rem;
    bottom: 0.1rem;
    width: 2px;
    background: linear-gradient(var(--graphite), rgba(26,29,33,0.15));
}
.journey li:last-child::before { background: var(--graphite); }
.journey__who { display: block; color: var(--muted); font-size: 0.84rem; margin-bottom: 0.2rem; }
.journey__what { display: block; color: var(--ink); font-weight: 600; font-size: 1.02rem; line-height: 1.45; }
.journey q {
    display: block;
    color: var(--ink);
    font-size: 1.05rem;
    font-style: italic;
    line-height: 1.5;
    quotes: '“' '”';
}
.chip {
    display: inline-block;
    padding: 0.18rem 0.7rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 600;
}
.chip--negative { color: #FFFFFF; background: var(--brick); }
.chip--neutral  { color: var(--ink); background: #C9CDD3; }
.chip--positive { color: #FFFFFF; background: var(--slate); }
@keyframes journey-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: none; }
}

/* Sections on the start page */
.section-head { margin: 2.6rem 0 1rem; }
.section-head h2 { margin: 0; padding: 0; }
.section-head p { max-width: 64ch; margin: 0.4rem 0 0; color: var(--muted); }

.steps {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}
.step {
    padding: 1.5rem 1.5rem 1.6rem;
    border-radius: var(--r-lg);
}
.step__number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.1rem;
    height: 2.1rem;
    margin-bottom: 1rem;
    border-radius: 50%;
    color: var(--graphite);
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(26,29,33,0.18);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.step h3 { margin: 0 0 0.45rem; padding: 0; }
.step p { margin: 0; }

.audience h3 { margin: 0 0 0.4rem; padding: 0; }
.audience p { margin: 0 0 0.9rem; min-height: 4.8em; }

.limits {
    margin-top: 1.6rem;
    padding: 1.1rem 1.4rem;
    border-radius: var(--r-md);
    color: var(--body);
    font-size: 0.92rem;
}
.limits strong { color: var(--ink); }

/* ---------- Section headings (insights / benchmarking) ---------------- */
.action-section,
.strength-section,
.driver-section { margin: 2.4rem 0 1rem; }
.action-section h2,
.strength-section h2,
.driver-section h2 { margin: 0.15rem 0 0.35rem; padding: 0; }
.action-section p,
.driver-section p { max-width: 66ch; margin: 0; color: var(--muted); }

.section-eyebrow,
.card-label {
    color: var(--muted);
    font-size: 0.84rem;
    font-weight: 600;
    letter-spacing: 0;
    text-transform: none;
}

/* ---------- Decision summary: smoked glass --------------------------- */
.decision-summary {
    margin: 1.2rem 0;
    padding: 1.4rem 1.6rem;
    border-radius: var(--r-lg);
    background: linear-gradient(145deg, rgba(36,40,46,0.82) 0%, rgba(58,64,72,0.70) 100%);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid rgba(255,255,255,0.25);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.25), 0 24px 48px -26px rgba(26,29,33,0.7);
}
.decision-summary .card-label { color: #D5D9DE; }
.decision-summary p {
    max-width: 72ch;
    margin: 0.4rem 0 0;
    color: #FFFFFF;
    font-size: 1.15rem;
    line-height: 1.6;
}

/* ---------- Priority, driver and strength cards ---------------------- */
.priority-card,
.driver-card,
.strength-card,
.market-hero {
    background: var(--glass);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-edge);
    box-shadow: var(--glass-shadow);
}

.priority-card {
    position: relative;
    margin: 1rem 0;
    padding: 1.5rem 1.6rem;
    border-radius: var(--r-lg);
    overflow: hidden;
}
.priority-card::before {
    content: '';
    position: absolute;
    left: 0; top: 1.2rem; bottom: 1.2rem;
    width: 4px;
    border-radius: 0 4px 4px 0;
    background: var(--brick);
}
.priority-card__head {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}
.priority-card h3,
.strength-card h3 { margin: 0.1rem 0 0; padding: 0; }
.priority-number {
    display: inline-flex;
    flex: 0 0 2.6rem;
    align-items: center;
    justify-content: center;
    height: 2.6rem;
    border-radius: 50%;
    color: #FFFFFF;
    background: var(--brick);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);
    font-size: 0.9rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.priority-evidence {
    margin-bottom: 0.8rem;
    padding: 0.95rem 1.1rem;
    border-radius: var(--r-md);
    background: rgba(164,72,58,0.07);
    border: 1px solid rgba(164,72,58,0.12);
}
.priority-evidence p,
.priority-grid p,
.strength-card p { margin: 0.3rem 0 0; color: var(--body); line-height: 1.55; }
.priority-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.8rem;
}
.priority-grid > div {
    padding: 0.95rem 1.1rem;
    border-radius: var(--r-md);
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(255,255,255,0.85);
}

.strength-card {
    position: relative;
    margin: 0.75rem 0;
    padding: 1.15rem 1.4rem;
    border-radius: var(--r-lg);
    overflow: hidden;
}
.strength-card::before {
    content: '';
    position: absolute;
    left: 0; top: 1rem; bottom: 1rem;
    width: 4px;
    border-radius: 0 4px 4px 0;
    background: var(--slate);
}

.driver-card {
    display: grid;
    grid-template-columns: 1fr 1.3fr;
    align-items: center;
    gap: 1.2rem;
    margin: 0.8rem 0;
    padding: 1.2rem 1.4rem;
    border-radius: var(--r-lg);
}
.driver-card h3 { margin: 0.15rem 0 0; padding: 0; }
.driver-card p { margin: 0.4rem 0 0; color: var(--muted); }
.driver-comparison {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 0.7rem;
    padding: 0.9rem;
    border-radius: var(--r-md);
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(255,255,255,0.85);
    text-align: center;
    font-variant-numeric: tabular-nums;
}
.driver-comparison div:not(.driver-arrow) { display: flex; flex-direction: column; }
.driver-comparison span,
.driver-comparison small { color: var(--muted); font-size: 0.8rem; }
.driver-comparison strong { margin: 0.2rem 0; color: var(--brick-text); font-size: 1.35rem; }
.driver-arrow { color: var(--muted); font-size: 1.3rem; }

/* ---------- Market explorer ----------------------------------------- */
.market-hero {
    margin: 0.5rem 0 1.3rem;
    padding: 2rem 2.2rem;
    border-radius: var(--r-xl);
}
.market-hero h1 {
    margin: 0.3rem 0 0.6rem;
    padding: 0;
    font-size: clamp(1.9rem, 3vw, 2.5rem);
    letter-spacing: -0.035em;
    line-height: 1.1;
}
.market-hero p { max-width: 66ch; margin: 0; color: var(--body); }

/* ---------- Footer -------------------------------------------------- */
.app-footer {
    margin-top: 3.2rem;
    padding-top: 1.2rem;
    border-top: 1px solid rgba(26,29,33,0.12);
    color: var(--muted);
    font-size: 0.82rem;
}

/* ---------- Responsive, motion, print ------------------------------- */
@media (max-width: 900px) {
    .hero { grid-template-columns: 1fr; gap: 2rem; padding: 2.2rem 1.5rem; border-radius: 24px; }
    .steps { grid-template-columns: 1fr; }
    .priority-grid, .driver-card { grid-template-columns: 1fr; }
    .market-hero { padding: 1.4rem; }
    .audience p { min-height: 0; }
}
@media (max-width: 760px) {
    html { font-size: 16px; }
    .block-container { padding-top: 1.6rem; }
}
/* Browsers without backdrop-filter get solid, readable panels. */
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    [data-testid='stMetric'], [data-testid='stExpander'] details, [data-testid='stPlotlyChart'],
    [data-testid='stDataFrame'], [data-testid='stVerticalBlockBorderWrapper'], [class*='st-key-glass-'],
    .glass, .priority-card, .driver-card, .strength-card, .market-hero, [data-testid='stSidebar'] {
        background: rgba(255,255,255,0.92);
    }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
    .journey li { opacity: 1; }
}
@media print {
    [data-testid='stSidebar'], [data-testid='stHeader'] { display: none; }
    .stApp::before { display: none; }
    .stApp { background: #FFFFFF; }
}
</style>
"""

# Kept for backwards compatibility with modules that import the old name.
app_css = APP_CSS


def apply_style():
    """Inject the global stylesheet once per rerun."""
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_sidebar_brand():
    st.sidebar.markdown(
        '<div class="sidebar-brand"><div class="sidebar-brand__mark" aria-hidden="true"></div>'
        '<div><strong><b>Madrid</b>Intelligence</strong>'
        '<span>Restaurant reviews into decisions</span></div></div>',
        unsafe_allow_html=True)


def render_header(compact=False, title=None, subtitle=None):
    """Page header for secondary pages.

    `compact` is kept for older callers; every secondary page now uses the same
    slim header so the content starts high on a projector screen.
    """
    title = title or 'Turn reviews into clear decisions'
    sub = f'<p>{escape(subtitle)}</p>' if subtitle else ''
    st.markdown(f'<header class="page-head"><h1>{escape(title)}</h1>{sub}</header>',
                unsafe_allow_html=True)


def render_data_note(text):
    st.markdown(f'<div class="data-note glass">{escape(text)}</div>', unsafe_allow_html=True)


def render_footer(text):
    """Quiet footer line at the end of every page."""
    st.markdown(f'<div class="app-footer">{escape(text)}</div>', unsafe_allow_html=True)


def glass_container(key):
    """A bordered container styled as a glass panel (keyed when Streamlit allows it)."""
    try:
        return st.container(border=True, key=f'glass-{key}')
    except TypeError:  # Streamlit < 1.39 has no `key` on containers
        return st.container(border=True)


def _legend_repeats_x_axis(figure):
    """True when each trace is a single x category (e.g. px.bar(x=col, color=col))."""
    traces = [trace for trace in figure.data if getattr(trace, 'x', None) is not None]
    if not traces:
        return False
    return all({str(value) for value in trace.x} == {str(trace.name)} for trace in traces)


def style_figure(figure, height=None):
    """Apply the house style to a Plotly figure and return it."""
    has_title = bool(getattr(figure.layout.title, 'text', None))

    facet_titles = [annotation for annotation in figure.layout.annotations
                    if annotation.text and '=' in annotation.text]
    for annotation in facet_titles:
        annotation.text = annotation.text.split('=', 1)[1]
        annotation.font = {'family': FONT, 'size': 14, 'color': COLORS['ink']}
    has_facets = bool(facet_titles)

    if _legend_repeats_x_axis(figure):
        figure.update_layout(showlegend=False)

    top_margin = 20
    if has_title:
        top_margin += 45
    if figure.layout.showlegend is not False:
        top_margin += 35
    if has_facets:
        top_margin += 25

    figure.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',          # the glass panel shows through
        font={'family': FONT, 'color': COLORS['ink'], 'size': 14},
        colorway=[COLORS['forest'], COLORS['gold'], COLORS['clay'],
                  '#5E8C86', COLORS['sage'], COLORS['wine']],
        legend={'orientation': 'h', 'yanchor': 'bottom',
                'y': 1.10 if has_facets else 1.02, 'xanchor': 'left', 'x': 0,
                'font': {'size': 13, 'color': COLORS['muted']},
                'title': {'font': {'size': 13, 'color': COLORS['muted']}, 'side': 'left'},
                'bgcolor': 'rgba(0,0,0,0)'},
        hoverlabel={'bgcolor': 'rgba(255,255,255,0.95)', 'bordercolor': 'rgba(26,29,33,0.25)',
                    'font': {'family': FONT, 'color': COLORS['ink'], 'size': 14}},
        margin={'l': 20, 'r': 24, 't': top_margin, 'b': 20},
        bargap=0.32,
    )
    if has_title:
        figure.update_layout(title={'font': {'family': FONT, 'size': 19, 'color': COLORS['ink']},
                                    'x': 0, 'xanchor': 'left'})
    if height:
        figure.update_layout(height=height)

    axis_style = {
        'gridcolor': 'rgba(26,29,33,0.09)',
        'zerolinecolor': 'rgba(26,29,33,0.28)',
        'linecolor': 'rgba(26,29,33,0.18)',
        'tickfont': {'color': COLORS['muted']},
        'title': {'font': {'color': COLORS['muted'], 'size': 13}},
    }
    figure.update_xaxes(**axis_style)
    figure.update_yaxes(**axis_style)
    if has_facets:
        figure.update_yaxes(showticklabels=True)
    return figure


def show_chart(figure, height=None):
    """Style a Plotly figure and render it at full width."""
    st.plotly_chart(style_figure(figure, height=height), config=PLOTLY_CONFIG, **FULL_WIDTH)


def styled_chart(figure):
    """Support older application modules that used this function name."""
    return style_figure(figure)
