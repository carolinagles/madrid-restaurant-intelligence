"""Visual layer for Madrid Restaurant Intelligence: "Liquid glass".

Near-white backdrop with faint construction lines, clear glass objects with
refractive rims, and vivid colour only where it carries meaning: blue for actions,
green / amber / red for sentiment. The signature element is the sentiment spectrum:
a colour track with a glass lens that shows where a review or restaurant sits.

Public API:
    apply_style(), render_sidebar_brand(), render_header(compact, title, subtitle),
    render_data_note(text), render_footer(text), glass_container(key),
    spectrum_html(...), render_spectrum(...),
    style_figure(fig), styled_chart(fig), show_chart(fig),
    FULL_WIDTH, PLOTLY_CONFIG, COLORS
"""

from html import escape
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import quote

import streamlit as st

# ---------------------------------------------------------------------------
# Palette. Old key names are kept so the other modules keep working.
# Colours that carry text meet WCAG AA against white.
# ---------------------------------------------------------------------------
COLORS = {
    'blue': '#0A66E0',         # actions, the selected restaurant
    'forest': '#248A3D',       # positive (legacy key name)
    'forest_soft': '#34C759',
    'sage': '#AEB6C0',         # peer reference, quiet series
    'ivory': '#F2F3F5',
    'paper': '#FFFFFF',
    'ink': '#1D1D1F',
    'muted': '#5E636B',
    'gold': '#F2A51A',         # neutral
    'gold_text': '#8A5A00',
    'wine': '#B3261E',
    'clay': '#E5352B',         # negative
}

FONT = "'Instrument Sans', -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
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

# Backdrop: two large glass slabs plus faint construction circles and guides,
# as in a design spec sheet.
_BACKDROP_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1600 1000' preserveAspectRatio='xMidYMid slice'>
<defs>
<linearGradient id='f' x1='0' y1='0' x2='1' y2='1'>
<stop offset='0' stop-color='#fff' stop-opacity='.55'/><stop offset='1' stop-color='#fff' stop-opacity='.10'/></linearGradient>
<linearGradient id='s' x1='0' y1='0' x2='1' y2='1'>
<stop offset='0' stop-color='#fff' stop-opacity='1'/><stop offset='.55' stop-color='#c9ced6' stop-opacity='.55'/>
<stop offset='1' stop-color='#8e96a1' stop-opacity='.55'/></linearGradient>
<filter id='d' x='-30%' y='-30%' width='160%' height='160%'>
<feDropShadow dx='0' dy='30' stdDeviation='28' flood-color='#2a3140' flood-opacity='.10'/></filter>
</defs>
<g fill='url(#f)' stroke='url(#s)' stroke-width='2' filter='url(#d)'>
<rect x='-120' y='-140' width='540' height='560' rx='110'/>
<rect x='960' y='560' width='600' height='620' rx='120'/>
</g>
<g fill='none' stroke='#1d1d1f' stroke-opacity='.07' stroke-width='1'>
<circle cx='230' cy='300' r='118'/><circle cx='230' cy='300' r='56'/>
<line x1='0' y1='300' x2='560' y2='300'/><line x1='230' y1='120' x2='230' y2='470'/>
<circle cx='1260' cy='790' r='112'/><circle cx='1260' cy='790' r='52'/>
<line x1='1040' y1='790' x2='1600' y2='790'/><line x1='1260' y1='600' x2='1260' y2='1000'/>
<circle cx='820' cy='470' r='70'/>
<line x1='700' y1='470' x2='940' y2='470'/><line x1='820' y1='360' x2='820' y2='580'/>
<line x1='0' y1='560' x2='520' y2='560' stroke-dasharray='2 6'/>
<line x1='1080' y1='330' x2='1600' y2='330' stroke-dasharray='2 6'/>
</g></svg>"""
_BACKDROP_URI = 'data:image/svg+xml,' + quote(' '.join(_BACKDROP_SVG.split()), safe="=:/,'#.-")

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap');

:root {
    --blue: #0A66E0;
    --blue-bright: #2F86FF;
    --green: #248A3D;
    --green-bright: #34C759;
    --amber: #F2A51A;
    --red: #E5352B;
    --red-text: #B3261E;
    --ink: #1D1D1F;
    --body: #33363B;
    --muted: #5E636B;
    --hairline: rgba(29,29,31,0.08);

    --spectrum: linear-gradient(90deg, #E5352B 0%, #FF6A2B 22%, #F2A51A 45%,
                                #E9D21E 58%, #8FD14F 76%, #34C759 90%, #248A3D 100%);

    --font: 'Instrument Sans', -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif;

    /* Liquid glass: clear body, thick bright rim, soft lift. */
    --glass: linear-gradient(160deg, rgba(255,255,255,0.62) 0%, rgba(255,255,255,0.30) 100%);
    --glass-strong: linear-gradient(160deg, rgba(255,255,255,0.86) 0%, rgba(255,255,255,0.56) 100%);
    --glass-blur: blur(20px) saturate(180%);
    --glass-rim:
        inset 1.5px 1.5px 0 rgba(255,255,255,1),
        inset -1px -1px 0 rgba(40,48,60,0.06),
        inset 0 0 0 1px rgba(255,255,255,0.55),
        0 0 0 0.5px rgba(40,48,60,0.10);
    --glass-lift:
        0 1px 2px rgba(40,48,60,0.05),
        0 22px 44px -24px rgba(40,48,60,0.30);
    --glass-shadow: var(--glass-rim), var(--glass-lift);

    --r-xl: 40px;
    --r-lg: 28px;
    --r-md: 18px;
    --r-sm: 14px;
}

/* ---------- Base and backdrop -------------------------------------- */
html, body, [class*='css'], .stApp, .stMarkdown, button, input, textarea { font-family: var(--font); }
html { font-size: 17px; }
body, .stApp { color: var(--ink); }

.stApp {
    background:
        radial-gradient(60rem 40rem at 0% 100%, #FFFFFF 0%, transparent 60%),
        linear-gradient(165deg, #EEF0F3 0%, #E6E8EC 50%, #DFE2E7 100%);
    background-attachment: fixed;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background: url("__BACKDROP__") center / cover no-repeat;
}
[data-testid='stAppViewContainer'], [data-testid='stMain'], .main {
    position: relative; z-index: 1; background: transparent;
}
[data-testid='stHeader'] {
    background: rgba(238,240,243,0.45);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    box-shadow: 0 0.5px 0 rgba(40,48,60,0.10);
}
.block-container { max-width: 1280px; padding-top: 3rem; padding-bottom: 4rem; }

h1, h2, h3, h4 { color: var(--ink); font-family: var(--font); font-weight: 600; letter-spacing: -0.025em; }
h2 { font-size: 1.9rem; line-height: 1.15; }
h3 { font-size: 1.28rem; line-height: 1.25; }
p, li { color: var(--body); line-height: 1.6; }
[data-testid='stMetricValue'], [data-testid='stDataFrame'], .tabular { font-variant-numeric: tabular-nums; }

button:focus-visible, a:focus-visible, [role='tab']:focus-visible,
[data-baseweb='select'] > div:focus-within, [data-baseweb='input'] > div:focus-within,
textarea:focus-visible { outline: 2px solid var(--blue) !important; outline-offset: 2px; }
::selection { background: rgba(10,102,224,0.18); color: var(--ink); }
[data-testid='stHeaderActionElements'], .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a { display: none !important; }

/* ---------- Glass surfaces ------------------------------------------ */
[data-testid='stMetric'],
[data-testid='stExpander'] details,
[data-testid='stPlotlyChart'],
[data-testid='stDataFrame'],
[data-testid='stVerticalBlockBorderWrapper'],
[class*='st-key-glass-'],
.glass, .priority-card, .driver-card, .strength-card, .market-hero {
    background: var(--glass);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 0 !important;
    box-shadow: var(--glass-shadow);
}
[data-testid='stVerticalBlockBorderWrapper'], [class*='st-key-glass-'] {
    border-radius: var(--r-lg) !important;
    padding: 1.4rem 1.5rem !important;
}
[class*='st-key-glass-'] [data-testid='stVerticalBlockBorderWrapper'] {
    background: transparent; box-shadow: none; backdrop-filter: none; padding: 0 !important;
}

[data-testid='stMetric'] { min-height: 124px; padding: 1.2rem 1.35rem; border-radius: var(--r-lg); }
[data-testid='stMetricLabel'], [data-testid='stMetricLabel'] p { color: var(--muted); font-size: 0.86rem; font-weight: 500; }
[data-testid='stMetricValue'] { color: var(--ink); font-size: 2.05rem; font-weight: 600; letter-spacing: -0.035em; }

[data-testid='stPlotlyChart'] { padding: 0.8rem 0.6rem 0.2rem; border-radius: var(--r-lg); overflow: hidden; }
[data-testid='stDataFrame'] { padding: 0.35rem; border-radius: var(--r-lg); overflow: hidden; }

[data-testid='stExpander'] details { border-radius: var(--r-lg); overflow: hidden; }
[data-testid='stExpander'] summary { padding: 0.95rem 1.2rem; }
[data-testid='stExpander'] summary p { color: var(--ink); font-weight: 600; }
[data-testid='stExpander'] summary:hover { background: rgba(255,255,255,0.4); }

[data-testid='stAlert'] > div {
    background: var(--glass-strong) !important;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border: 0;
    border-radius: var(--r-md);
    box-shadow: var(--glass-rim), inset 4px 0 0 #8E96A1, var(--glass-lift);
    color: var(--ink);
}
[data-testid='stAlert'] p { color: var(--ink); }
[data-testid='stAlert']:has([data-testid='stAlertContentInfo'])    > div { box-shadow: var(--glass-rim), inset 4px 0 0 var(--blue),  var(--glass-lift); }
[data-testid='stAlert']:has([data-testid='stAlertContentSuccess']) > div { box-shadow: var(--glass-rim), inset 4px 0 0 var(--green), var(--glass-lift); }
[data-testid='stAlert']:has([data-testid='stAlertContentWarning']) > div { box-shadow: var(--glass-rim), inset 4px 0 0 var(--amber), var(--glass-lift); }
[data-testid='stAlert']:has([data-testid='stAlertContentError'])   > div { box-shadow: var(--glass-rim), inset 4px 0 0 var(--red),   var(--glass-lift); }

[data-testid='stCaptionContainer'], [data-testid='stCaptionContainer'] p { color: var(--muted); font-size: 0.86rem; }

[data-testid='stCode'] pre, .stCode pre {
    background: rgba(29,29,31,0.90) !important;
    border-radius: var(--r-md) !important;
}

/* ---------- Sidebar -------------------------------------------------- */
[data-testid='stSidebar'] {
    background: rgba(255,255,255,0.40);
    backdrop-filter: blur(30px) saturate(180%);
    -webkit-backdrop-filter: blur(30px) saturate(180%);
    border-right: 0;
    box-shadow: inset -1px 0 0 rgba(255,255,255,0.9), 0.5px 0 0 rgba(40,48,60,0.10);
}
[data-testid='stSidebar'] > div:first-child { background: transparent; }
[data-testid='stSidebar'] h3 { font-size: 1rem; color: var(--muted); font-weight: 600; }
[data-testid='stSidebar'] hr { border-color: var(--hairline); }

.sidebar-brand {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.6rem 0 1.4rem; margin-bottom: 1.1rem;
    border-bottom: 1px solid var(--hairline);
}
/* A tiny spectrum with a glass lens: the brand mark echoes the main component. */
.sidebar-brand__mark {
    position: relative;
    flex: 0 0 2.8rem; height: 0.7rem;
    border-radius: 999px;
    background: var(--spectrum);
}
.sidebar-brand__mark::after {
    content: '';
    position: absolute; top: 50%; left: 72%;
    width: 1.25rem; height: 1.25rem;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: rgba(255,255,255,0.25);
    backdrop-filter: saturate(200%) brightness(1.08);
    -webkit-backdrop-filter: saturate(200%) brightness(1.08);
    box-shadow: inset 1px 1px 0 #FFFFFF, inset 0 0 0 1px rgba(255,255,255,0.7),
                0 0 0 0.5px rgba(40,48,60,0.18), 0 4px 8px -3px rgba(40,48,60,0.35);
}
.sidebar-brand strong { display: block; color: var(--ink); font-size: 1.05rem; font-weight: 400; line-height: 1.2; }
.sidebar-brand strong b { font-weight: 700; }
.sidebar-brand span { display: block; color: var(--muted); font-size: 0.82rem; }

[data-testid='stSidebar'] [role='radiogroup'] { gap: 0.3rem; }
[data-testid='stSidebar'] [role='radiogroup'] label {
    position: relative;
    display: flex; align-items: center;
    min-height: 46px; padding: 0.5rem 0.95rem;
    border-radius: 999px; cursor: pointer;
    transition: background-color 160ms ease, box-shadow 160ms ease;
}
[data-testid='stSidebar'] [role='radiogroup'] label > div:first-child { display: none; }
[data-testid='stSidebar'] [role='radiogroup'] label:hover { background: rgba(255,255,255,0.55); }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) {
    background: var(--glass-strong);
    box-shadow: var(--glass-rim), 0 10px 22px -14px rgba(40,48,60,0.45);
}
/* A small blue "on" capsule, like a toggle. */
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked)::after {
    content: '';
    position: absolute; right: 0.9rem; top: 50%;
    width: 1.1rem; height: 0.55rem;
    transform: translateY(-50%);
    border-radius: 999px;
    background: linear-gradient(180deg, var(--blue-bright), var(--blue));
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
}
[data-testid='stSidebar'] [role='radiogroup'] label p { color: var(--body); font-weight: 500; }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) p { color: var(--ink) !important; font-weight: 600; }
[data-testid='stSidebar'] [role='radiogroup'] label:has(input:focus-visible) { outline: 2px solid var(--blue); outline-offset: 2px; }

/* ---------- Tabs ------------------------------------------------------ */
.stTabs [data-baseweb='tab-list'] {
    gap: 0.25rem; padding: 0.3rem;
    border-radius: 999px;
    background: rgba(29,29,31,0.05);
    box-shadow: inset 0 1px 2px rgba(40,48,60,0.08);
    overflow-x: auto; width: fit-content; max-width: 100%;
}
.stTabs [data-baseweb='tab'] {
    height: 42px; padding: 0 1.15rem;
    border-radius: 999px; color: var(--muted);
    font-weight: 500; white-space: nowrap; background: transparent;
}
.stTabs [aria-selected='true'] { background: var(--glass-strong); box-shadow: var(--glass-rim), 0 6px 14px -8px rgba(40,48,60,0.35); }
.stTabs [aria-selected='true'] p { color: var(--ink) !important; font-weight: 600; }
.stTabs [data-baseweb='tab-highlight'], .stTabs [data-baseweb='tab-border'] { display: none; }

/* ---------- Buttons ---------------------------------------------------- */
.stButton > button, .stDownloadButton > button, [data-testid='stFormSubmitButton'] > button {
    min-height: 46px; padding: 0 1.35rem;
    border: 0; border-radius: 999px;
    color: var(--ink);
    background: var(--glass-strong);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    box-shadow: var(--glass-rim), 0 8px 18px -12px rgba(40,48,60,0.40);
    font-weight: 600;
    transition: box-shadow 160ms ease, background-color 160ms ease;
}
.stButton > button p, .stDownloadButton > button p, [data-testid='stFormSubmitButton'] > button p { color: inherit; font-weight: 600; }
.stButton > button:hover, .stDownloadButton > button:hover { color: var(--blue); background: #FFFFFF; }

/* Primary: colour seen through glass, like the green toggle in the reference. */
button[kind='primary'], button[kind='primaryFormSubmit'], [data-testid^='stBaseButton-primary'] {
    color: #FFFFFF !important;
    background: linear-gradient(180deg, var(--blue-bright) 0%, var(--blue) 100%) !important;
    box-shadow:
        inset 0 1.5px 0 rgba(255,255,255,0.55),
        inset 0 -3px 6px rgba(0,40,120,0.25),
        0 0 0 0.5px rgba(0,60,160,0.35),
        0 12px 24px -12px rgba(10,102,224,0.65) !important;
}
button[kind='primary'] p, button[kind='primaryFormSubmit'] p, [data-testid^='stBaseButton-primary'] p { color: #FFFFFF !important; }
button[kind='primary']:hover, button[kind='primaryFormSubmit']:hover, [data-testid^='stBaseButton-primary']:hover {
    color: #FFFFFF !important; filter: brightness(1.06);
}

/* ---------- Inputs ------------------------------------------------------ */
[data-baseweb='select'] > div, [data-baseweb='input'] > div, [data-baseweb='textarea'], textarea {
    border: 0 !important;
    border-radius: var(--r-sm) !important;
    background: rgba(255,255,255,0.72) !important;
    box-shadow: inset 0 1px 2px rgba(40,48,60,0.10), 0 0 0 0.5px rgba(40,48,60,0.14);
}
textarea { font-size: 1rem !important; line-height: 1.55 !important; }
[data-baseweb='tag'] { border-radius: 999px !important; background: var(--blue) !important; }
[data-baseweb='popover'] > div, [data-baseweb='menu'] {
    background: rgba(255,255,255,0.88) !important;
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    border-radius: var(--r-md) !important;
}

/* ---------- Sentiment spectrum (signature component) ------------------ */
.spectrum { position: relative; padding: 1.1rem 0 0.2rem; }
.spectrum__track {
    position: relative;
    height: 1.25rem;
    border-radius: 999px;
    background: var(--spectrum);
    box-shadow: inset 0 1px 1px rgba(255,255,255,0.45), inset 0 -2px 3px rgba(0,0,0,0.10),
                0 6px 14px -8px rgba(40,48,60,0.35);
}
.spectrum__lens {
    position: absolute;
    top: 50%;
    width: 3rem; height: 3rem;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: radial-gradient(circle at 32% 28%, rgba(255,255,255,0.65), rgba(255,255,255,0.08) 55%);
    backdrop-filter: saturate(210%) brightness(1.08) blur(1px);
    -webkit-backdrop-filter: saturate(210%) brightness(1.08) blur(1px);
    box-shadow:
        inset 2px 2px 0 rgba(255,255,255,0.95),
        inset -2px -2px 3px rgba(40,48,60,0.15),
        inset 0 0 0 1.5px rgba(255,255,255,0.75),
        0 0 0 0.5px rgba(40,48,60,0.20),
        0 10px 20px -8px rgba(40,48,60,0.45);
    animation: lens-in 1100ms cubic-bezier(.2,.8,.2,1) both;
}
@keyframes lens-in { from { left: 50%; opacity: 0; } }
.spectrum__marker {
    position: absolute; top: -0.55rem; bottom: -0.55rem;
    width: 0; border-left: 1.5px dashed rgba(29,29,31,0.55);
}
.spectrum__marker span {
    position: absolute; top: -1.45rem; left: 0;
    transform: translateX(-50%);
    color: var(--muted); font-size: 0.78rem; white-space: nowrap;
}
.spectrum__scale {
    display: flex; justify-content: space-between;
    margin-top: 0.7rem; color: var(--muted); font-size: 0.82rem;
}
.spectrum__value { margin: 0 0 0.3rem; color: var(--ink); font-weight: 600; }
.spectrum__value small { color: var(--muted); font-weight: 400; font-size: 0.86rem; }
.spectrum-panel { padding: 1.3rem 1.6rem 1.2rem; border-radius: var(--r-lg); margin: 0.8rem 0 1rem; }

/* ---------- Page header & data note ------------------------------------ */
.page-head { display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.3rem 1rem; margin-bottom: 1.4rem; }
.page-head h1 { margin: 0; padding: 0; font-size: clamp(1.9rem, 3vw, 2.5rem); letter-spacing: -0.035em; }
.page-head p { margin: 0; color: var(--muted); }
.data-note {
    display: inline-flex; align-items: center; gap: 0.55rem;
    margin: 0 0 1.4rem; padding: 0.45rem 1rem;
    border-radius: 999px; font-size: 0.84rem; color: var(--muted);
}
.data-note::before {
    content: ''; width: 0.5rem; height: 0.5rem; border-radius: 50%;
    background: var(--blue); box-shadow: 0 0 0 3px rgba(10,102,224,0.18);
}

/* ---------- Start here --------------------------------------------------- */
.hero {
    position: relative;
    display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
    gap: 3rem; align-items: center;
    padding: 3.6rem 3.8rem; margin-bottom: 1.6rem;
    border-radius: var(--r-xl); overflow: hidden;
}
.hero > * { position: relative; }
.hero__brand { margin: 0 0 1.4rem; color: var(--muted); font-size: 1rem; }
.hero__brand b { color: var(--ink); font-weight: 700; }
.hero h1 {
    margin: 0; padding: 0;
    font-size: clamp(2.5rem, 4.8vw, 4.2rem);
    font-weight: 600; line-height: 1.02; letter-spacing: -0.045em; text-wrap: balance;
}
.hero__lede { max-width: 52ch; margin: 1.4rem 0 0; font-size: 1.1rem; line-height: 1.65; color: var(--body); }

.journey {
    margin: 0; padding: 1.5rem 1.6rem;
    border-radius: var(--r-lg);
    background: var(--glass-strong);
    box-shadow: var(--glass-shadow);
}
.journey figcaption { margin-bottom: 1rem; color: var(--muted); font-size: 0.86rem; }
.journey ol { list-style: none; margin: 0; padding: 0; }
.journey li {
    position: relative; padding: 0 0 1.2rem 1.9rem;
    opacity: 0; animation: journey-in 520ms cubic-bezier(.2,.7,.2,1) forwards;
}
.journey li:nth-child(1) { animation-delay: 150ms; }
.journey li:nth-child(2) { animation-delay: 600ms; }
.journey li:nth-child(3) { animation-delay: 1050ms; }
.journey li:nth-child(4) { animation-delay: 1500ms; padding-bottom: 0; }
.journey li::before {
    content: ''; position: absolute; left: 0.42rem; top: 0.45rem;
    width: 0.62rem; height: 0.62rem; border-radius: 50%;
    background: #FFFFFF; border: 2px solid var(--blue);
}
.journey li:not(:last-child)::after {
    content: ''; position: absolute; left: 0.69rem; top: 1.2rem; bottom: 0.1rem;
    width: 2px; background: linear-gradient(var(--blue), rgba(10,102,224,0.12));
}
.journey li:last-child::before { background: var(--blue); }
.journey__who { display: block; color: var(--muted); font-size: 0.84rem; margin-bottom: 0.2rem; }
.journey__what { display: block; color: var(--ink); font-weight: 600; font-size: 1.02rem; line-height: 1.45; }
.journey q { display: block; color: var(--ink); font-size: 1.05rem; font-style: italic; line-height: 1.5; quotes: '“' '”'; }
.journey .spectrum { padding-top: 0.75rem; }
.journey .spectrum__lens { width: 2.3rem; height: 2.3rem; }
.journey .spectrum__track { height: 0.95rem; }
.journey .spectrum__scale { margin-top: 0.55rem; }
@keyframes journey-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.chip { display: inline-block; padding: 0.18rem 0.7rem; border-radius: 999px; font-size: 0.9rem; font-weight: 600;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.45); }
.chip--negative { color: #FFFFFF; background: var(--red-text); }
.chip--neutral  { color: var(--ink); background: var(--amber); }
.chip--positive { color: #FFFFFF; background: var(--green); }

.section-head { margin: 2.6rem 0 1rem; }
.section-head h2 { margin: 0; padding: 0; }
.section-head p { max-width: 64ch; margin: 0.4rem 0 0; color: var(--muted); }

.steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; }
.step { padding: 1.5rem 1.5rem 1.6rem; border-radius: var(--r-lg); }
.step__number {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2.2rem; height: 2.2rem; margin-bottom: 1rem;
    border-radius: 50%; color: var(--blue); font-weight: 700;
    background: var(--glass-strong); box-shadow: var(--glass-rim);
    font-variant-numeric: tabular-nums;
}
.step h3 { margin: 0 0 0.45rem; padding: 0; }
.step p { margin: 0; }

/* Model card for ML engineers: a spec sheet in glass. */
.model-card { border-radius: var(--r-lg); padding: 0.4rem; }
.model-card dl {
    display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.4rem; margin: 0;
}
.model-card dl > div { padding: 1rem 1.15rem; border-radius: var(--r-md); background: rgba(255,255,255,0.45); }
.model-card dt { color: var(--muted); font-size: 0.82rem; margin-bottom: 0.3rem; }
.model-card dd { margin: 0; color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; line-height: 1.35; }
.model-card dd small { display: block; color: var(--muted); font-weight: 400; font-size: 0.82rem; margin-top: 0.15rem; }

.audience h3 { margin: 0 0 0.4rem; padding: 0; }
.audience p { margin: 0 0 0.9rem; min-height: 4.8em; }

.limits { margin-top: 1.6rem; padding: 1.1rem 1.4rem; border-radius: var(--r-md); color: var(--body); font-size: 0.92rem; }
.limits strong { color: var(--ink); }

/* ---------- Insights & benchmarking ------------------------------------- */
.action-section, .strength-section, .driver-section { margin: 2.4rem 0 1rem; }
.action-section h2, .strength-section h2, .driver-section h2 { margin: 0.15rem 0 0.35rem; padding: 0; }
.action-section p, .driver-section p { max-width: 66ch; margin: 0; color: var(--muted); }
.section-eyebrow, .card-label { color: var(--muted); font-size: 0.84rem; font-weight: 600; letter-spacing: 0; text-transform: none; }

/* Decision summary: strong glass with a spectrum hairline on top. */
.decision-summary {
    position: relative; overflow: hidden;
    margin: 1.2rem 0; padding: 1.5rem 1.7rem;
    border-radius: var(--r-lg);
    background: var(--glass-strong);
    backdrop-filter: var(--glass-blur);
    -webkit-backdrop-filter: var(--glass-blur);
    box-shadow: var(--glass-shadow);
}
.decision-summary::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: 4px; background: var(--spectrum); }
.decision-summary .card-label { color: var(--blue); }
.decision-summary p { max-width: 72ch; margin: 0.4rem 0 0; color: var(--ink); font-size: 1.15rem; line-height: 1.6; }

.priority-card { position: relative; margin: 1rem 0; padding: 1.5rem 1.6rem; border-radius: var(--r-lg); overflow: hidden; }
.priority-card::before, .strength-card::before {
    content: ''; position: absolute; left: 0; top: 1.2rem; bottom: 1.2rem;
    width: 4px; border-radius: 0 4px 4px 0; background: var(--red);
}
.strength-card::before { background: var(--green-bright); top: 1rem; bottom: 1rem; }
.priority-card__head { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
.priority-card h3, .strength-card h3 { margin: 0.1rem 0 0; padding: 0; }
.priority-number {
    display: inline-flex; flex: 0 0 2.6rem; align-items: center; justify-content: center; height: 2.6rem;
    border-radius: 50%; color: var(--red-text); font-size: 0.9rem; font-weight: 700;
    background: var(--glass-strong); box-shadow: var(--glass-rim);
    font-variant-numeric: tabular-nums;
}
.priority-evidence { margin-bottom: 0.8rem; padding: 0.95rem 1.1rem; border-radius: var(--r-md);
                     background: rgba(229,53,43,0.06); box-shadow: inset 0 0 0 1px rgba(229,53,43,0.12); }
.priority-evidence p, .priority-grid p, .strength-card p { margin: 0.3rem 0 0; color: var(--body); line-height: 1.55; }
.priority-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.8rem; }
.priority-grid > div { padding: 0.95rem 1.1rem; border-radius: var(--r-md); background: rgba(255,255,255,0.5); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.8); }
.strength-card { position: relative; margin: 0.75rem 0; padding: 1.15rem 1.4rem; border-radius: var(--r-lg); overflow: hidden; }

.driver-card { display: grid; grid-template-columns: 1fr 1.3fr; align-items: center; gap: 1.2rem;
               margin: 0.8rem 0; padding: 1.2rem 1.4rem; border-radius: var(--r-lg); }
.driver-card h3 { margin: 0.15rem 0 0; padding: 0; }
.driver-card p { margin: 0.4rem 0 0; color: var(--muted); }
.driver-comparison { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 0.7rem;
                     padding: 0.9rem; border-radius: var(--r-md); background: rgba(255,255,255,0.5);
                     text-align: center; font-variant-numeric: tabular-nums; }
.driver-comparison div:not(.driver-arrow) { display: flex; flex-direction: column; }
.driver-comparison span, .driver-comparison small { color: var(--muted); font-size: 0.8rem; }
.driver-comparison strong { margin: 0.2rem 0; color: var(--red-text); font-size: 1.35rem; }
.driver-arrow { color: var(--muted); font-size: 1.3rem; }

.market-hero { margin: 0.5rem 0 1.3rem; padding: 2rem 2.2rem; border-radius: var(--r-xl); }
.market-hero h1 { margin: 0.3rem 0 0.6rem; padding: 0; font-size: clamp(1.9rem, 3vw, 2.5rem); letter-spacing: -0.035em; line-height: 1.1; }
.market-hero p { max-width: 66ch; margin: 0; color: var(--body); }

.app-footer { margin-top: 3.2rem; padding-top: 1.2rem; border-top: 1px solid var(--hairline); color: var(--muted); font-size: 0.82rem; }

/* ---------- Responsive, fallbacks, motion, print ------------------------ */
@media (max-width: 900px) {
    .hero { grid-template-columns: 1fr; gap: 2rem; padding: 2.2rem 1.5rem; border-radius: 28px; }
    .steps { grid-template-columns: 1fr; }
    .model-card dl { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .priority-grid, .driver-card { grid-template-columns: 1fr; }
    .market-hero { padding: 1.4rem; }
    .audience p { min-height: 0; }
}
@media (max-width: 760px) { html { font-size: 16px; } .block-container { padding-top: 1.6rem; } }
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
    [data-testid='stMetric'], [data-testid='stExpander'] details, [data-testid='stPlotlyChart'],
    [data-testid='stDataFrame'], [data-testid='stVerticalBlockBorderWrapper'], [class*='st-key-glass-'],
    .glass, .priority-card, .driver-card, .strength-card, .market-hero, .decision-summary,
    [data-testid='stSidebar'] { background: rgba(255,255,255,0.94); }
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
""".replace('__BACKDROP__', _BACKDROP_URI)

app_css = APP_CSS  # legacy name


def apply_style():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_sidebar_brand():
    st.sidebar.markdown(
        '<div class="sidebar-brand"><div class="sidebar-brand__mark" aria-hidden="true"></div>'
        '<div><strong><b>Madrid</b>Intelligence</strong>'
        '<span>Restaurant reviews into decisions</span></div></div>',
        unsafe_allow_html=True)


def render_header(compact=False, title=None, subtitle=None):
    """Slim page header for secondary pages (`compact` kept for older callers)."""
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
    except TypeError:  # Streamlit < 1.39
        return st.container(border=True)


def _clamp(value):
    return max(0.0, min(1.0, float(value)))


def spectrum_html(position, low_label='Negative', high_label='Positive', value_label=None,
                  marker=None, marker_label=None, aria_label=None):
    """Colour track (red to green) with a glass lens at `position` (0 to 1).

    `marker` adds a dashed reference line, e.g. the peer average.
    """
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
    """Spectrum on its own glass panel."""
    st.markdown('<div class="spectrum-panel glass">'
                + spectrum_html(position, low_label, high_label, value_label, marker,
                                marker_label, aria_label) + '</div>', unsafe_allow_html=True)


def _legend_repeats_x_axis(figure):
    traces = [trace for trace in figure.data if getattr(trace, 'x', None) is not None]
    if not traces:
        return False
    return all({str(value) for value in trace.x} == {str(trace.name)} for trace in traces)


def style_figure(figure, height=None):
    """Apply the house style to a Plotly figure and return it."""
    has_title = bool(getattr(figure.layout.title, 'text', None))
    facet_titles = [a for a in figure.layout.annotations if a.text and '=' in a.text]
    for annotation in facet_titles:
        annotation.text = annotation.text.split('=', 1)[1]
        annotation.font = {'family': FONT, 'size': 14, 'color': COLORS['ink']}
    has_facets = bool(facet_titles)
    if _legend_repeats_x_axis(figure):
        figure.update_layout(showlegend=False)

    top_margin = 20 + (45 if has_title else 0) + (35 if figure.layout.showlegend is not False else 0) \
        + (25 if has_facets else 0)
    figure.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'family': FONT, 'color': COLORS['ink'], 'size': 14},
        colorway=[COLORS['blue'], COLORS['forest'], COLORS['clay'], COLORS['gold'],
                  COLORS['sage'], '#5E636B'],
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.10 if has_facets else 1.02,
                'xanchor': 'left', 'x': 0, 'font': {'size': 13, 'color': COLORS['muted']},
                'title': {'font': {'size': 13, 'color': COLORS['muted']}, 'side': 'left'},
                'bgcolor': 'rgba(0,0,0,0)'},
        hoverlabel={'bgcolor': 'rgba(255,255,255,0.96)', 'bordercolor': 'rgba(40,48,60,0.18)',
                    'font': {'family': FONT, 'color': COLORS['ink'], 'size': 14}},
        margin={'l': 20, 'r': 24, 't': top_margin, 'b': 20},
        bargap=0.32,
    )
    if has_title:
        figure.update_layout(title={'font': {'family': FONT, 'size': 19, 'color': COLORS['ink']},
                                    'x': 0, 'xanchor': 'left'})
    if height:
        figure.update_layout(height=height)
    # Rounded bar ends where Plotly supports it (5.19+).
    try:
        figure.update_traces(marker_cornerradius=8, selector={'type': 'bar'})
    except (ValueError, TypeError):
        pass
    axis_style = {'gridcolor': 'rgba(29,29,31,0.07)', 'zerolinecolor': 'rgba(29,29,31,0.25)',
                  'linecolor': 'rgba(29,29,31,0.14)', 'tickfont': {'color': COLORS['muted']},
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
