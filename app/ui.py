"""Visual layer for MadridIntelligence: Swiss Forest x Liquid Glass.

Design system
    Colour      Swiss Forest palette (tokens in COLORS and in :root below).
                Semantic colours (red, amber, green) keep their meaning in charts,
                alerts and the sentiment spectrum.
    Type        The operating system's sans serif (SF Pro on macOS, Segoe UI on
                Windows): no web font, so it also works offline at a conference.
                Scale: 12 / 14 / 16 / 18 / 20 / 28 / 40 / 56 px.
    Space       4 px base unit; spacing tokens are multiples of 4 or 8.
    Radius      10 (inputs) / 14 (inner blocks) / 20 (panels) / 28 (hero) / pill.
    Glass       White, lightly translucent surfaces with a bright top rim and a wide,
                soft shadow. Opaque fallback where backdrop-filter is unsupported.

Public API (used by streamlit_app.py and the other app modules):
    apply_style(), render_sidebar_brand(), render_header(compact, title, subtitle),
    render_data_note(text), render_footer(text), glass_container(key),
    sidebar_panel(key), spectrum_html(...), render_spectrum(...),
    style_figure(fig), styled_chart(fig), show_chart(fig),
    FULL_WIDTH, PLOTLY_CONFIG, COLORS, PAGE_ICONS
"""

from html import escape
from importlib.metadata import PackageNotFoundError, version

import streamlit as st

# ---------------------------------------------------------------------------
# Tokens (Python side). Legacy key names are kept for the other modules.
# ---------------------------------------------------------------------------
COLORS = {
    # Brand
    'forest': '#123C32',
    'forest_deep': '#092B24',
    'forest_soft': '#2C5A4D',
    'ivory': '#F7F7F2',
    'paper': '#FFFFFF',
    'sage': '#A9BFB0',          # peer reference in charts (DCE7DE is too pale on white)
    'sage_light': '#DCE7DE',
    'lime': '#B7E05C',
    'ink': '#202725',
    'muted': '#68716E',
    'border': '#E1E7E2',
    # Semantic (never used for decoration)
    'clay': '#D2452F',          # negative
    'wine': '#A8321F',          # negative text
    'gold': '#E8A33D',          # neutral / watch
    'gold_text': '#8A5A00',
    'positive': '#2F8F5B',
}

# Material Symbols (outlined, linear) rendered by Streamlit in widget labels.
PAGE_ICONS = {
    'Start here': ':material/space_dashboard:',
    'Restaurant diagnosis': ':material/storefront:',
    'Market & Top 10': ':material/leaderboard:',
    'Review classifier': ':material/text_snippet:',
    'Methodology': ':material/menu_book:',
}

FONT = ("-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI Variable Text', "
        "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif")
SANS = SERIF = FONT  # legacy names

PLOTLY_CONFIG = {
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
    'toImageButtonOptions': {'format': 'png', 'scale': 2},
}


def _streamlit_supports_width_stretch():
    try:
        major, minor = (int(part) for part in version('streamlit').split('.')[:2])
    except (PackageNotFoundError, ValueError):
        return False
    return (major, minor) >= (1, 50)


FULL_WIDTH = ({'width': 'stretch'} if _streamlit_supports_width_stretch()
              else {'use_container_width': True})

APP_CSS = """
<style>
:root {
    /* Colour */
    --forest: #123C32;
    --forest-deep: #092B24;
    --forest-soft: #2C5A4D;
    --ivory: #F7F7F2;
    --white: #FFFFFF;
    --sage: #DCE7DE;
    --lime: #B7E05C;
    --ink: #202725;
    --muted: #68716E;
    --border: #E1E7E2;
    --red: #D2452F;
    --red-text: #A8321F;
    --amber: #E8A33D;
    --green: #2F8F5B;
    --spectrum: linear-gradient(90deg, #D2452F 0%, #EE7A36 24%, #E8A33D 44%,
                                #E3CB3F 58%, #9CCB55 76%, #2F8F5B 100%);

    /* Type */
    --font: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI Variable Text',
            'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --font-display: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI Variable Display',
            'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --t-12: 0.75rem; --t-14: 0.875rem; --t-16: 1rem; --t-18: 1.125rem;
    --t-20: 1.25rem; --t-28: 1.75rem; --t-40: 2.5rem; --t-56: 3.5rem;

    /* Space (4 px grid) */
    --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px; --s-5: 20px; --s-6: 24px;
    --s-8: 32px; --s-10: 40px; --s-12: 48px; --s-16: 64px;

    /* Radius */
    --r-sm: 10px; --r-md: 14px; --r-lg: 20px; --r-xl: 28px; --r-pill: 999px;

    /* Surfaces */
    --surface: rgba(255,255,255,0.78);
    --surface-strong: rgba(255,255,255,0.92);
    --blur: blur(16px) saturate(150%);
    --rim: inset 0 1px 0 rgba(255,255,255,0.95);
    --shadow: 0 1px 2px rgba(18,60,50,0.04), 0 12px 32px -16px rgba(18,60,50,0.16);
    --shadow-lift: 0 2px 4px rgba(18,60,50,0.05), 0 20px 44px -20px rgba(18,60,50,0.24);
    --focus: 0 0 0 3px rgba(18,60,50,0.22);
}

/* ===================== Base ===================== */
html { font-size: 16px; }
html, body, [class*='css'], .stApp, .stMarkdown, button, input, textarea, select {
    font-family: var(--font);
    -webkit-font-smoothing: antialiased;
}
body, .stApp { color: var(--ink); }

/* Ivory canvas with two very faint washes: enough for the glass to read, no decoration. */
.stApp {
    background:
        radial-gradient(56rem 32rem at 100% 0%, rgba(220,231,222,0.70), transparent 65%),
        radial-gradient(40rem 28rem at 0% 100%, rgba(183,224,92,0.10), transparent 65%),
        var(--ivory);
    background-attachment: fixed;
}
[data-testid='stHeader'] {
    background: rgba(247,247,242,0.72);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    box-shadow: 0 1px 0 var(--border);
}
.block-container { max-width: 1240px; padding: var(--s-12) var(--s-10) var(--s-16); }

h1, h2, h3, h4 { color: var(--ink); font-family: var(--font-display); font-weight: 650; letter-spacing: -0.02em; }
h2 { font-size: var(--t-28); line-height: 1.2; }
h3 { font-size: var(--t-20); line-height: 1.3; }
p, li { color: var(--ink); line-height: 1.6; }
[data-testid='stMetricValue'], [data-testid='stDataFrame'], .tabular { font-variant-numeric: tabular-nums; }
[data-testid='stHeaderActionElements'], .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a { display: none !important; }
::selection { background: rgba(183,224,92,0.45); color: var(--ink); }

/* Focus is always visible. */
button:focus-visible, a:focus-visible, [role='tab']:focus-visible,
[data-baseweb='select'] > div:focus-within, [data-baseweb='input'] > div:focus-within,
textarea:focus-visible {
    outline: none !important;
    box-shadow: var(--focus) !important;
}

/* ===================== Surfaces ===================== */
[data-testid='stMetric'],
[data-testid='stExpander'] details,
[data-testid='stPlotlyChart'],
[data-testid='stDataFrame'],
[data-testid='stMain'] [data-testid='stVerticalBlockBorderWrapper'],
[class*='st-key-glass-'],
.glass, .priority-card, .driver-card, .strength-card, .market-hero {
    background: var(--surface);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    border: 1px solid var(--border) !important;
    box-shadow: var(--rim), var(--shadow);
}
[data-testid='stMain'] [data-testid='stVerticalBlockBorderWrapper'], [class*='st-key-glass-'] {
    border-radius: var(--r-lg) !important;
    padding: var(--s-6) !important;
}
[class*='st-key-glass-'] [data-testid='stVerticalBlockBorderWrapper'] {
    background: transparent; border: 0 !important; box-shadow: none; backdrop-filter: none; padding: 0 !important;
}

/* KPI cards */
[data-testid='stMetric'] {
    min-height: 112px;
    padding: var(--s-5) var(--s-6);
    border-radius: var(--r-lg);
    transition: box-shadow 180ms ease, transform 180ms ease;
}
[data-testid='stMetric']:hover { box-shadow: var(--rim), var(--shadow-lift); }
[data-testid='stMetricLabel'], [data-testid='stMetricLabel'] p {
    color: var(--muted); font-size: var(--t-14); font-weight: 500;
}
[data-testid='stMetricValue'] {
    color: var(--forest); font-family: var(--font-display);
    font-size: var(--t-28); font-weight: 650; letter-spacing: -0.02em;
}

[data-testid='stPlotlyChart'] { padding: var(--s-3) var(--s-2) var(--s-1); border-radius: var(--r-lg); overflow: hidden; }
[data-testid='stDataFrame'] { padding: var(--s-1); border-radius: var(--r-lg); overflow: hidden; }

[data-testid='stExpander'] details { border-radius: var(--r-lg); overflow: hidden; }
[data-testid='stExpander'] summary { padding: var(--s-4) var(--s-5); }
[data-testid='stExpander'] summary p { color: var(--ink); font-weight: 600; }
[data-testid='stExpander'] summary:hover { background: rgba(220,231,222,0.35); }
[data-testid='stExpander'] summary svg { color: var(--forest); }

/* Alerts: white glass with a semantic edge (meaning preserved). */
[data-testid='stAlert'] > div {
    background: var(--surface-strong) !important;
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    box-shadow: var(--rim), inset 3px 0 0 var(--muted), var(--shadow);
    color: var(--ink);
}
[data-testid='stAlert'] p { color: var(--ink); }
[data-testid='stAlert']:has([data-testid='stAlertContentInfo'])    > div { box-shadow: var(--rim), inset 3px 0 0 var(--forest), var(--shadow); }
[data-testid='stAlert']:has([data-testid='stAlertContentSuccess']) > div { box-shadow: var(--rim), inset 3px 0 0 var(--green),  var(--shadow); }
[data-testid='stAlert']:has([data-testid='stAlertContentWarning']) > div { box-shadow: var(--rim), inset 3px 0 0 var(--amber),  var(--shadow); }
[data-testid='stAlert']:has([data-testid='stAlertContentError'])   > div { box-shadow: var(--rim), inset 3px 0 0 var(--red),    var(--shadow); }

[data-testid='stCaptionContainer'], [data-testid='stCaptionContainer'] p { color: var(--muted); font-size: var(--t-14); }
[data-testid='stCode'] pre, .stCode pre { background: var(--forest-deep) !important; border-radius: var(--r-md) !important; }
[data-testid='stCode'] code { color: #E9F2EA !important; }

/* ===================== Sidebar: deep forest ===================== */
[data-testid='stSidebar'] {
    background: linear-gradient(180deg, var(--forest) 0%, var(--forest-deep) 100%);
    border-right: 0;
    box-shadow: inset -1px 0 0 rgba(255,255,255,0.06);
}
[data-testid='stSidebar'][aria-expanded='true'] { width: 296px !important; min-width: 296px !important; }
[data-testid='stSidebar'] > div:first-child { background: transparent; }
[data-testid='stSidebar'] h1, [data-testid='stSidebar'] h2, [data-testid='stSidebar'] h3,
[data-testid='stSidebar'] p, [data-testid='stSidebar'] label,
[data-testid='stSidebar'] [data-testid='stCaptionContainer'] { color: rgba(247,247,242,0.92) !important; }
[data-testid='stSidebar'] [data-testid='stCaptionContainer'] p { color: rgba(247,247,242,0.62) !important; }
[data-testid='stSidebar'] hr { border-color: rgba(255,255,255,0.10); margin: var(--s-4) 0; }
[data-testid='stSidebar'] [data-testid='stSidebarCollapseButton'] button,
[data-testid='stSidebar'] [data-testid='stSidebarCollapseButton'] svg { color: var(--ivory) !important; fill: var(--ivory) !important; }
[data-testid='stSidebar'] button:focus-visible,
[data-testid='stSidebar'] [data-baseweb='select'] > div:focus-within,
[data-testid='stSidebar'] [data-baseweb='input'] > div:focus-within { box-shadow: 0 0 0 3px rgba(183,224,92,0.55) !important; }

.sidebar-brand {
    display: flex; align-items: center; gap: var(--s-3);
    padding: var(--s-2) 0 var(--s-6);
}
.sidebar-brand__mark {
    display: inline-flex; align-items: center; justify-content: center;
    flex: 0 0 36px; height: 36px; border-radius: var(--r-sm);
    background: linear-gradient(160deg, rgba(255,255,255,0.16), rgba(255,255,255,0.04));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.22), inset 0 0 0 1px rgba(255,255,255,0.10);
}
.sidebar-brand__mark svg { width: 20px; height: 20px; }
.sidebar-brand strong { display: block; color: var(--ivory); font-size: var(--t-16); font-weight: 400; letter-spacing: -0.01em; line-height: 1.25; }
.sidebar-brand strong b { font-weight: 700; }
.sidebar-brand span { display: block; color: rgba(247,247,242,0.60); font-size: var(--t-12); }

.sidebar-label { margin: 0 0 var(--s-2) var(--s-1); color: rgba(247,247,242,0.55); font-size: var(--t-12); font-weight: 600; }

/* Navigation: icon + label. Active item is a translucent green lens with a lime accent. */
[data-testid='stSidebar'] [role='radiogroup'] { gap: var(--s-1); }
[data-testid='stSidebar'] [role='radiogroup'] label {
    position: relative;
    display: flex; align-items: center;
    min-height: 44px; margin: 0; padding: var(--s-2) var(--s-3);
    border-radius: var(--r-md); cursor: pointer;
    transition: background-color 160ms ease, box-shadow 160ms ease;
}
[data-testid='stSidebar'] [role='radiogroup'] label > div:first-child { display: none; }
[data-testid='stSidebar'] [role='radiogroup'] label p {
    display: flex; align-items: center; gap: var(--s-3);
    color: rgba(247,247,242,0.78) !important; font-size: var(--t-14); font-weight: 500;
}
[data-testid='stSidebar'] [role='radiogroup'] label [data-testid='stIconMaterial'],
[data-testid='stSidebar'] [role='radiogroup'] label span[class*='material'] {
    font-size: 20px; color: rgba(247,247,242,0.62);
}
[data-testid='stSidebar'] [role='radiogroup'] label:hover { background: rgba(255,255,255,0.06); }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) {
    background: linear-gradient(160deg, rgba(220,231,222,0.20), rgba(220,231,222,0.08));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.20), inset 0 0 0 1px rgba(255,255,255,0.10),
                0 8px 20px -12px rgba(0,0,0,0.45);
}
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked)::before {
    content: ''; position: absolute; left: 0; top: 12px; bottom: 12px;
    width: 3px; border-radius: 0 3px 3px 0; background: var(--lime);
}
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) p { color: var(--ivory) !important; font-weight: 600; }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) [data-testid='stIconMaterial'],
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) span[class*='material'] { color: var(--lime); }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:focus-visible) { box-shadow: 0 0 0 3px rgba(183,224,92,0.55); }

/* Restaurant search and picker: a discreet panel, separate from navigation. */
.st-key-sidebar-filters {
    margin-top: var(--s-2);
    padding: var(--s-4);
    border-radius: var(--r-lg);
    background: rgba(255,255,255,0.05);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), inset 0 0 0 1px rgba(255,255,255,0.07);
}
[data-testid='stSidebar'] [data-baseweb='select'] > div,
[data-testid='stSidebar'] [data-baseweb='input'] > div {
    background: rgba(255,255,255,0.94) !important;
    border: 0 !important;
}
[data-testid='stSidebar'] [data-baseweb='select'] *,
[data-testid='stSidebar'] [data-baseweb='input'] input { color: var(--ink) !important; }
[data-testid='stSidebar'] input::placeholder { color: var(--muted) !important; }
[data-testid='stSidebar'] [data-testid='stAlert'] p { color: var(--ink) !important; }

/* ===================== Tabs: glass track with a lens ===================== */
.stTabs [data-baseweb='tab-list'] {
    gap: var(--s-1); padding: var(--s-1);
    border-radius: var(--r-pill);
    background: rgba(220,231,222,0.55);
    box-shadow: inset 0 1px 2px rgba(18,60,50,0.10), inset 0 0 0 1px rgba(255,255,255,0.6);
    overflow-x: auto; width: fit-content; max-width: 100%;
    margin-bottom: var(--s-4);
}
.stTabs [data-baseweb='tab'] {
    height: 40px; padding: 0 var(--s-5);
    border-radius: var(--r-pill); background: transparent;
    color: var(--muted); font-weight: 500; white-space: nowrap;
    transition: background-color 160ms ease, box-shadow 160ms ease;
}
.stTabs [data-baseweb='tab']:hover p { color: var(--forest); }
.stTabs [aria-selected='true'] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.80));
    box-shadow: inset 0 1px 0 #FFFFFF, inset 0 -1px 0 rgba(18,60,50,0.06),
                0 0 0 1px rgba(18,60,50,0.06), 0 6px 14px -8px rgba(18,60,50,0.35);
}
.stTabs [aria-selected='true'] p { color: var(--forest) !important; font-weight: 600; }
.stTabs [data-baseweb='tab-highlight'], .stTabs [data-baseweb='tab-border'] { display: none; }

/* ===================== Buttons ===================== */
.stButton > button, .stDownloadButton > button, [data-testid='stFormSubmitButton'] > button {
    min-height: 44px; padding: 0 var(--s-5);
    border: 1px solid var(--border); border-radius: var(--r-pill);
    color: var(--forest); background: var(--surface-strong);
    box-shadow: var(--rim), 0 2px 6px -2px rgba(18,60,50,0.12);
    font-weight: 600;
    transition: background-color 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}
.stButton > button p, .stDownloadButton > button p, [data-testid='stFormSubmitButton'] > button p { color: inherit; font-weight: 600; }
.stButton > button:hover, .stDownloadButton > button:hover {
    color: var(--forest); border-color: rgba(18,60,50,0.28); background: var(--white);
}
button[kind='primary'], button[kind='primaryFormSubmit'], [data-testid^='stBaseButton-primary'] {
    color: var(--ivory) !important;
    border: 1px solid var(--forest-deep) !important;
    background: linear-gradient(180deg, var(--forest-soft) -40%, var(--forest) 60%) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 8px 18px -10px rgba(9,43,36,0.6) !important;
}
button[kind='primary'] p, button[kind='primaryFormSubmit'] p, [data-testid^='stBaseButton-primary'] p { color: var(--ivory) !important; }
button[kind='primary']:hover, button[kind='primaryFormSubmit']:hover, [data-testid^='stBaseButton-primary']:hover {
    background: var(--forest-deep) !important; color: var(--ivory) !important;
}

/* ===================== Inputs ===================== */
[data-baseweb='select'] > div, [data-baseweb='input'] > div, [data-baseweb='textarea'], textarea {
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
    background: var(--white) !important;
}
textarea { font-size: var(--t-16) !important; line-height: 1.55 !important; }
[data-baseweb='tag'] { border-radius: var(--r-pill) !important; background: var(--forest) !important; }
[data-baseweb='tag'] span { color: var(--ivory) !important; }
[data-baseweb='popover'] > div, [data-baseweb='menu'] {
    border-radius: var(--r-md) !important;
    box-shadow: var(--shadow-lift) !important;
}

/* ===================== Page header and context note ===================== */
.page-head { margin-bottom: var(--s-6); }
.page-head h1 {
    margin: 0; padding: 0;
    font-size: var(--t-40); line-height: 1.1; letter-spacing: -0.03em; font-weight: 700;
}
.page-head p { max-width: 64ch; margin: var(--s-2) 0 0; color: var(--muted); font-size: var(--t-18); }
.data-note {
    display: inline-flex; align-items: center; gap: var(--s-2);
    margin: 0 0 var(--s-6); padding: var(--s-2) var(--s-4);
    border-radius: var(--r-pill); color: var(--muted); font-size: var(--t-14);
}
.data-note::before {
    content: ''; width: 8px; height: 8px; border-radius: 50%;
    background: var(--lime); box-shadow: 0 0 0 3px rgba(18,60,50,0.10);
}

/* ===================== Sentiment spectrum ===================== */
.spectrum { position: relative; padding: var(--s-4) 0 var(--s-1); }
.spectrum__track {
    position: relative; height: 16px; border-radius: var(--r-pill);
    background: var(--spectrum);
    box-shadow: inset 0 1px 1px rgba(255,255,255,0.45), inset 0 -1px 2px rgba(0,0,0,0.10);
}
.spectrum__lens {
    position: absolute; top: 50%;
    width: 40px; height: 40px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: radial-gradient(circle at 32% 28%, rgba(255,255,255,0.70), rgba(255,255,255,0.10) 58%);
    backdrop-filter: saturate(200%) brightness(1.06);
    -webkit-backdrop-filter: saturate(200%) brightness(1.06);
    box-shadow: inset 2px 2px 0 rgba(255,255,255,0.95), inset -1px -2px 3px rgba(18,60,50,0.16),
                inset 0 0 0 1.5px rgba(255,255,255,0.75), 0 0 0 1px rgba(18,60,50,0.14),
                0 8px 16px -6px rgba(18,60,50,0.40);
    animation: lens-in 900ms cubic-bezier(.2,.8,.2,1) both;
}
@keyframes lens-in { from { left: 50%; opacity: 0; } }
.spectrum__marker { position: absolute; top: -8px; bottom: -8px; width: 0; border-left: 2px dashed rgba(32,39,37,0.6); }
.spectrum__marker span {
    position: absolute; top: -24px; left: 0; transform: translateX(-50%);
    color: var(--muted); font-size: var(--t-12); white-space: nowrap;
}
.spectrum__scale { display: flex; justify-content: space-between; margin-top: var(--s-3); color: var(--muted); font-size: var(--t-12); }
.spectrum__value { margin: 0 0 var(--s-1); color: var(--ink); font-weight: 600; }
.spectrum__value small { color: var(--muted); font-weight: 400; font-size: var(--t-14); }
.spectrum-panel { margin: var(--s-4) 0; padding: var(--s-5) var(--s-6); border-radius: var(--r-lg); }

/* ===================== Start here ===================== */
.hero {
    display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
    gap: var(--s-12); align-items: center;
    padding: var(--s-12) var(--s-12); margin-bottom: var(--s-6);
    border-radius: var(--r-xl);
}
.hero__brand { margin: 0 0 var(--s-5); color: var(--muted); font-size: var(--t-16); }
.hero__brand b { color: var(--forest); font-weight: 700; }
.hero h1 {
    margin: 0; padding: 0;
    font-size: clamp(2.5rem, 4.4vw, var(--t-56));
    font-weight: 700; line-height: 1.05; letter-spacing: -0.035em; text-wrap: balance;
}
.hero__lede { max-width: 50ch; margin: var(--s-5) 0 0; color: var(--muted); font-size: var(--t-18); line-height: 1.6; }

.journey { margin: 0; padding: var(--s-6); border-radius: var(--r-lg); background: var(--surface-strong);
           border: 1px solid var(--border); box-shadow: var(--rim), var(--shadow); }
.journey figcaption { margin-bottom: var(--s-4); color: var(--muted); font-size: var(--t-14); }
.journey ol { list-style: none; margin: 0; padding: 0; }
.journey li { position: relative; padding: 0 0 var(--s-5) var(--s-8); opacity: 0; animation: journey-in 480ms cubic-bezier(.2,.7,.2,1) forwards; }
.journey li:nth-child(1) { animation-delay: 120ms; }
.journey li:nth-child(2) { animation-delay: 520ms; }
.journey li:nth-child(3) { animation-delay: 920ms; }
.journey li:nth-child(4) { animation-delay: 1320ms; padding-bottom: 0; }
.journey li::before {
    content: ''; position: absolute; left: 6px; top: 7px; width: 10px; height: 10px;
    border-radius: 50%; background: var(--white); border: 2px solid var(--forest);
}
.journey li:not(:last-child)::after {
    content: ''; position: absolute; left: 11px; top: 21px; bottom: 2px; width: 2px;
    background: linear-gradient(var(--forest), rgba(18,60,50,0.12));
}
.journey li:last-child::before { background: var(--lime); border-color: var(--forest); }
.journey__who { display: block; margin-bottom: var(--s-1); color: var(--muted); font-size: var(--t-14); }
.journey__what { display: block; color: var(--ink); font-weight: 600; line-height: 1.45; }
.journey q { display: block; color: var(--ink); font-size: var(--t-18); font-style: italic; line-height: 1.5; quotes: '“' '”'; }
.journey .spectrum { padding-top: var(--s-3); }
.journey .spectrum__lens { width: 32px; height: 32px; }
.journey .spectrum__track { height: 12px; }
@keyframes journey-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }

.chip { display: inline-block; padding: 2px var(--s-3); border-radius: var(--r-pill); font-size: var(--t-14); font-weight: 600; }
.chip--negative { color: #FFFFFF; background: var(--red-text); }
.chip--neutral  { color: var(--ink); background: var(--amber); }
.chip--positive { color: #FFFFFF; background: var(--green); }

.section-head { margin: var(--s-12) 0 var(--s-5); }
.section-head h2 { margin: 0; padding: 0; }
.section-head p { max-width: 64ch; margin: var(--s-2) 0 0; color: var(--muted); }

.steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--s-4); }
.step { padding: var(--s-6); border-radius: var(--r-lg); }
.step__number {
    display: inline-flex; align-items: center; justify-content: center;
    width: 32px; height: 32px; margin-bottom: var(--s-4); border-radius: 50%;
    color: var(--forest); background: var(--sage); font-size: var(--t-14); font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.step h3 { margin: 0 0 var(--s-2); padding: 0; }
.step p { margin: 0; color: var(--muted); }

.model-card { padding: var(--s-1); border-radius: var(--r-lg); }
.model-card dl { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--s-1); margin: 0; }
.model-card dl > div { padding: var(--s-4) var(--s-5); border-radius: var(--r-md); }
.model-card dl > div + div { box-shadow: inset 1px 0 0 var(--border); border-radius: 0; }
.model-card dt { margin-bottom: var(--s-1); color: var(--muted); font-size: var(--t-12); font-weight: 500; }
.model-card dd { margin: 0; color: var(--forest); font-weight: 650; line-height: 1.35; font-variant-numeric: tabular-nums; }
.model-card dd small { display: block; margin-top: var(--s-1); color: var(--muted); font-weight: 400; font-size: var(--t-12); line-height: 1.45; }

.audience h3 { margin: 0 0 var(--s-2); padding: 0; }
.audience p { min-height: 4.8em; margin: 0 0 var(--s-4); color: var(--muted); }

.limits { margin-top: var(--s-6); padding: var(--s-4) var(--s-5); border-radius: var(--r-md); color: var(--muted); font-size: var(--t-14); }
.limits strong { color: var(--ink); }

/* ===================== Insights and benchmarking ===================== */
.action-section, .strength-section, .driver-section { margin: var(--s-10) 0 var(--s-4); }
.action-section h2, .strength-section h2, .driver-section h2 { margin: var(--s-1) 0 var(--s-2); padding: 0; }
.action-section p, .driver-section p { max-width: 66ch; margin: 0; color: var(--muted); }
.section-eyebrow, .card-label { color: var(--muted); font-size: var(--t-12); font-weight: 600; letter-spacing: 0; text-transform: none; }

.decision-summary {
    position: relative; overflow: hidden;
    margin: var(--s-5) 0; padding: var(--s-6);
    border-radius: var(--r-lg);
    background: linear-gradient(160deg, var(--forest) 0%, var(--forest-deep) 100%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), var(--shadow-lift);
}
.decision-summary .card-label { color: var(--lime); }
.decision-summary p { max-width: 72ch; margin: var(--s-2) 0 0; color: var(--ivory); font-size: var(--t-18); line-height: 1.6; }

.priority-card { position: relative; margin: var(--s-4) 0; padding: var(--s-6); border-radius: var(--r-lg); overflow: hidden; }
.priority-card::before, .strength-card::before {
    content: ''; position: absolute; left: 0; top: var(--s-5); bottom: var(--s-5);
    width: 3px; border-radius: 0 3px 3px 0; background: var(--red);
}
.strength-card::before { background: var(--lime); top: var(--s-4); bottom: var(--s-4); }
.priority-card__head { display: flex; align-items: flex-start; gap: var(--s-4); margin-bottom: var(--s-4); }
.priority-card h3, .strength-card h3 { margin: var(--s-1) 0 0; padding: 0; }
.priority-number {
    display: inline-flex; flex: 0 0 40px; align-items: center; justify-content: center; height: 40px;
    border-radius: 50%; color: var(--red-text); background: rgba(210,69,47,0.08);
    box-shadow: inset 0 0 0 1px rgba(210,69,47,0.18);
    font-size: var(--t-14); font-weight: 700; font-variant-numeric: tabular-nums;
}
.priority-evidence { margin-bottom: var(--s-3); padding: var(--s-4); border-radius: var(--r-md); background: rgba(210,69,47,0.05); }
.priority-evidence p, .priority-grid p, .strength-card p { margin: var(--s-1) 0 0; color: var(--ink); line-height: 1.55; }
.priority-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--s-3); }
.priority-grid > div { padding: var(--s-4); border-radius: var(--r-md); background: var(--ivory); }
.strength-card { position: relative; margin: var(--s-3) 0; padding: var(--s-5) var(--s-6); border-radius: var(--r-lg); overflow: hidden; }

.driver-card { display: grid; grid-template-columns: 1fr 1.3fr; align-items: center; gap: var(--s-5);
               margin: var(--s-3) 0; padding: var(--s-5) var(--s-6); border-radius: var(--r-lg); }
.driver-card h3 { margin: var(--s-1) 0 0; padding: 0; }
.driver-card p { margin: var(--s-2) 0 0; color: var(--muted); }
.driver-comparison { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: var(--s-3);
                     padding: var(--s-4); border-radius: var(--r-md); background: var(--ivory);
                     text-align: center; font-variant-numeric: tabular-nums; }
.driver-comparison div:not(.driver-arrow) { display: flex; flex-direction: column; }
.driver-comparison span, .driver-comparison small { color: var(--muted); font-size: var(--t-12); }
.driver-comparison strong { margin: var(--s-1) 0; color: var(--red-text); font-size: var(--t-20); }
.driver-arrow { color: var(--muted); font-size: var(--t-20); }

.market-hero { margin: 0 0 var(--s-6); padding: var(--s-8); border-radius: var(--r-xl); }
.market-hero h1 { margin: var(--s-1) 0 var(--s-3); padding: 0; font-size: var(--t-40); font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; }
.market-hero p { max-width: 66ch; margin: 0; color: var(--muted); font-size: var(--t-18); }

.app-footer { margin-top: var(--s-12); padding-top: var(--s-5); border-top: 1px solid var(--border); color: var(--muted); font-size: var(--t-12); }

/* ===================== Responsive, fallbacks, motion, print ===================== */
@media (max-width: 1080px) {
    .model-card dl { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .model-card dl > div + div { box-shadow: none; }
}
@media (max-width: 900px) {
    .block-container { padding: var(--s-8) var(--s-5) var(--s-12); }
    .hero { grid-template-columns: 1fr; gap: var(--s-8); padding: var(--s-8) var(--s-6); }
    .steps { grid-template-columns: 1fr; }
    .priority-grid, .driver-card { grid-template-columns: 1fr; }
    .audience p { min-height: 0; }
    .market-hero { padding: var(--s-6); }
}
@media (max-width: 600px) {
    .page-head h1, .market-hero h1 { font-size: var(--t-28); }
    .model-card dl { grid-template-columns: 1fr; }
    .stTabs [data-baseweb='tab'] { padding: 0 var(--s-3); }
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    :root { --surface: #FFFFFF; --surface-strong: #FFFFFF; }
}
@media (prefers-reduced-transparency: reduce) {
    :root { --surface: #FFFFFF; --surface-strong: #FFFFFF; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
    .journey li { opacity: 1; }
}
@media print {
    [data-testid='stSidebar'], [data-testid='stHeader'] { display: none; }
    .stApp { background: #FFFFFF; }
}
</style>
"""

app_css = APP_CSS  # legacy name

_LOGO_SVG = ("<svg viewBox='0 0 20 20' fill='none' aria-hidden='true'>"
             "<rect x='2' y='11' width='3.2' height='7' rx='1.6' fill='#DCE7DE'/>"
             "<rect x='8.4' y='6.5' width='3.2' height='11.5' rx='1.6' fill='#DCE7DE'/>"
             "<rect x='14.8' y='2' width='3.2' height='16' rx='1.6' fill='#B7E05C'/></svg>")


def apply_style():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_sidebar_brand():
    st.sidebar.markdown(
        f'<div class="sidebar-brand"><span class="sidebar-brand__mark">{_LOGO_SVG}</span>'
        '<div><strong><b>Madrid</b>Intelligence</strong>'
        '<span>Restaurant reputation intelligence</span></div></div>',
        unsafe_allow_html=True)


def sidebar_label(text):
    st.sidebar.markdown(f'<p class="sidebar-label">{escape(text)}</p>', unsafe_allow_html=True)


def sidebar_panel(key='sidebar-filters'):
    """A discreet panel in the sidebar for search and filters."""
    try:
        return st.sidebar.container(key=key)
    except TypeError:  # Streamlit < 1.39 has no `key` on containers
        return st.sidebar.container()


def render_header(compact=False, title=None, subtitle=None):
    """Page title with its subtitle aligned underneath (`compact` kept for old callers)."""
    title = title or 'Turn reviews into clear decisions'
    sub = f'<p>{escape(subtitle)}</p>' if subtitle else ''
    st.markdown(f'<header class="page-head"><h1>{escape(title)}</h1>{sub}</header>',
                unsafe_allow_html=True)


def render_data_note(text):
    st.markdown(f'<div class="data-note glass">{escape(text)}</div>', unsafe_allow_html=True)


def render_footer(text):
    st.markdown(f'<div class="app-footer">{escape(text)}</div>', unsafe_allow_html=True)


def glass_container(key):
    try:
        return st.container(border=True, key=f'glass-{key}')
    except TypeError:
        return st.container(border=True)


def _clamp(value):
    return max(0.0, min(1.0, float(value)))


def spectrum_html(position, low_label='Negative', high_label='Positive', value_label=None,
                  marker=None, marker_label=None, aria_label=None):
    """Semantic colour track (red to green) with a glass lens at `position` (0 to 1)."""
    pos = _clamp(position) * 100
    value = f'<p class="spectrum__value">{value_label}</p>' if value_label else ''
    mark = ''
    if marker is not None:
        mark = (f'<div class="spectrum__marker" style="left:{_clamp(marker) * 100:.1f}%">'
                f'<span>{escape(marker_label or "")}</span></div>')
    aria = escape(aria_label or f'Position {pos:.0f} of 100 between {low_label} and {high_label}')
    return (f'{value}<div class="spectrum" role="img" aria-label="{aria}">'
            f'<div class="spectrum__track">{mark}'
            f'<div class="spectrum__lens" style="left:{pos:.1f}%"></div></div>'
            f'<div class="spectrum__scale"><span>{escape(low_label)}</span>'
            f'<span>{escape(high_label)}</span></div></div>')


def render_spectrum(position, low_label='Negative', high_label='Positive', value_label=None,
                    marker=None, marker_label=None, aria_label=None):
    st.markdown('<div class="spectrum-panel glass">'
                + spectrum_html(position, low_label, high_label, value_label, marker,
                                marker_label, aria_label) + '</div>', unsafe_allow_html=True)


def _legend_repeats_x_axis(figure):
    traces = [trace for trace in figure.data if getattr(trace, 'x', None) is not None]
    if not traces:
        return False
    return all({str(value) for value in trace.x} == {str(trace.name)} for trace in traces)


def style_figure(figure, height=None):
    """Minimal, legible chart style. Trace colours set by callers are left untouched."""
    has_title = bool(getattr(figure.layout.title, 'text', None))
    facet_titles = [a for a in figure.layout.annotations if a.text and '=' in a.text]
    for annotation in facet_titles:
        annotation.text = annotation.text.split('=', 1)[1]
        annotation.font = {'family': FONT, 'size': 14, 'color': COLORS['ink']}
    has_facets = bool(facet_titles)
    if _legend_repeats_x_axis(figure):
        figure.update_layout(showlegend=False)

    top_margin = (16 + (44 if has_title else 0)
                  + (36 if figure.layout.showlegend is not False else 0)
                  + (24 if has_facets else 0))
    figure.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'family': FONT, 'color': COLORS['ink'], 'size': 14},
        colorway=[COLORS['forest'], COLORS['lime'], COLORS['sage'], COLORS['forest_soft'],
                  COLORS['gold'], COLORS['clay']],
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.10 if has_facets else 1.02,
                'xanchor': 'left', 'x': 0, 'font': {'size': 13, 'color': COLORS['muted']},
                'title': {'font': {'size': 13, 'color': COLORS['muted']}, 'side': 'left'},
                'bgcolor': 'rgba(0,0,0,0)'},
        hoverlabel={'bgcolor': '#FFFFFF', 'bordercolor': COLORS['border'],
                    'font': {'family': FONT, 'color': COLORS['ink'], 'size': 14}},
        margin={'l': 16, 'r': 24, 't': top_margin, 'b': 16},
        bargap=0.32,
    )
    if has_title:
        figure.update_layout(title={'font': {'family': FONT, 'size': 18, 'color': COLORS['ink']},
                                    'x': 0, 'xanchor': 'left'})
    if height:
        figure.update_layout(height=height)
    try:  # rounded bar ends (Plotly 5.19+)
        figure.update_traces(marker_cornerradius=6, selector={'type': 'bar'})
    except (ValueError, TypeError):
        pass
    axis_style = {'gridcolor': 'rgba(32,39,37,0.07)', 'zerolinecolor': 'rgba(32,39,37,0.25)',
                  'linecolor': COLORS['border'], 'tickfont': {'color': COLORS['muted']},
                  'title': {'font': {'color': COLORS['muted'], 'size': 13}}}
    figure.update_xaxes(**axis_style)
    figure.update_yaxes(**axis_style)
    if has_facets:
        figure.update_yaxes(showticklabels=True)
    return figure


def show_chart(figure, height=None):
    st.plotly_chart(style_figure(figure, height=height), config=PLOTLY_CONFIG, **FULL_WIDTH)


def styled_chart(figure):
    return style_figure(figure)
