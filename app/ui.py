"""Visual layer for Madrid Restaurant Intelligence.

Public API (used by streamlit_app.py and the other app modules):
    apply_style()           inject the global stylesheet
    render_header(compact)  hero + sidebar brand
    style_figure(fig)       apply the house style to a Plotly figure
    styled_chart(fig)       legacy alias of style_figure
    show_chart(fig)         style + render a Plotly figure at full width
    FULL_WIDTH              width kwargs that work on old and new Streamlit
    PLOTLY_CONFIG           config dict for st.plotly_chart(config=...)
    COLORS                  palette as Python constants
"""

from importlib.metadata import PackageNotFoundError, version

import streamlit as st

# ---------------------------------------------------------------------------
# Palette. Keep these in sync with the CSS custom properties below.
# Text colours were adjusted to reach WCAG AA contrast (≥ 4.5:1) on ivory.
# ---------------------------------------------------------------------------
COLORS = {
    'forest': '#05402B',
    'forest_soft': '#1D5A43',
    'sage': '#B8C8BB',
    'ivory': '#F7F5EF',
    'paper': '#FFFEFA',
    'ink': '#183027',
    'muted': '#5E6A63',       # was #6F7B74 (4.05:1) -> now 5.2:1
    'gold': '#A8874F',        # decorative only (rules, arrows, fills)
    'gold_text': '#8A6A35',   # gold for small text (5.0:1)
    'wine': '#8B1E1E',
    'clay': '#A84B45',
}

SERIF = "'Newsreader', Georgia, 'Times New Roman', serif"
SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', "
        "'Helvetica Neue', Arial, sans-serif")

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
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');

:root {
    --forest: #05402B;
    --forest-soft: #1D5A43;
    --sage: #B8C8BB;
    --ivory: #F7F5EF;
    --paper: #FFFEFA;
    --ink: #183027;
    --body: #3E4B46;
    --muted: #5E6A63;
    --gold: #A8874F;
    --gold-text: #8A6A35;
    --gold-light: #D4BA88;
    --wine: #8B1E1E;
    --wine-wash: rgba(139, 30, 30, 0.055);
    --line: rgba(5, 64, 43, 0.10);
    --line-strong: rgba(5, 64, 43, 0.16);

    --serif: 'Newsreader', Georgia, 'Times New Roman', serif;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI',
            'Helvetica Neue', Arial, sans-serif;

    --radius-lg: 24px;
    --radius-md: 16px;
    --radius-sm: 12px;
    --shadow-soft: 0 12px 30px rgba(5, 64, 43, 0.05);
    --shadow-lift: 0 18px 48px rgba(5, 64, 43, 0.08);
}

/* ---------- Base ---------------------------------------------------- */
html,
body,
[class*='css'] {
    font-family: var(--sans);
    color: var(--ink);
}

.stApp {
    background:
        radial-gradient(circle at 92% 0%,
                        rgba(184, 200, 187, 0.34), transparent 28rem),
        var(--ivory);
}

[data-testid='stHeader'] {
    background: rgba(247, 245, 239, 0.88);
    border-bottom: 1px solid rgba(5, 64, 43, 0.08);
    backdrop-filter: blur(18px);
}

.block-container {
    max-width: 1240px;
    padding-top: 2.8rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    color: var(--forest);
    font-family: var(--serif);
    font-weight: 500;
    letter-spacing: -0.02em;
}

/* Numbers line up in tables and metrics. */
[data-testid='stMetricValue'],
[data-testid='stDataFrame'],
.driver-comparison strong {
    font-variant-numeric: tabular-nums;
}

/* Keyboard focus is always visible. */
button:focus-visible,
a:focus-visible,
[role='tab']:focus-visible,
[data-baseweb='select'] > div:focus-within,
[data-baseweb='input'] > div:focus-within,
textarea:focus-visible {
    outline: 2px solid var(--gold) !important;
    outline-offset: 2px;
}

::selection {
    background: rgba(184, 200, 187, 0.65);
    color: var(--ink);
}

/* ---------- Hero ---------------------------------------------------- */
.hero {
    padding: 3.4rem 3.6rem;
    margin-bottom: 1.25rem;
    border: 1px solid var(--line);
    border-radius: 28px;
    background: linear-gradient(125deg,
                                rgba(255, 254, 250, 0.98),
                                rgba(229, 235, 227, 0.88));
    box-shadow: var(--shadow-lift);
}

.hero-label {
    margin-bottom: 1rem;
    color: var(--gold-text);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

.hero h1 {
    max-width: 780px;
    margin: 0;
    padding: 0;
    font-size: clamp(2.6rem, 5vw, 4.6rem);
    font-weight: 500;
    line-height: 1.0;
    text-wrap: balance;
}

.hero p {
    max-width: 62ch;
    margin: 1.3rem 0 0;
    color: var(--muted);
    font-size: 1.06rem;
    line-height: 1.7;
}

/* Compact variant: used on secondary pages so content starts higher. */
.hero--compact {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 0.4rem 1.2rem;
    padding: 1.4rem 1.8rem;
    border-radius: 20px;
    box-shadow: var(--shadow-soft);
}

.hero--compact .hero-label {
    margin: 0;
}

.hero--compact h1 {
    font-size: clamp(1.5rem, 2.4vw, 1.9rem);
    line-height: 1.2;
}

/* ---------- Metrics ------------------------------------------------- */
[data-testid='stMetric'] {
    min-height: 126px;
    padding: 1.25rem 1.35rem;
    border: 1px solid var(--line);
    border-radius: 20px;
    background: rgba(255, 254, 250, 0.88);
    box-shadow: var(--shadow-soft);
}

[data-testid='stMetricLabel'],
[data-testid='stMetricLabel'] p {
    color: var(--muted);
    font-size: 0.76rem;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

[data-testid='stMetricValue'] {
    color: var(--forest);
    font-family: var(--serif);
    font-size: 2rem;
}

/* ---------- Sidebar ------------------------------------------------- */
[data-testid='stSidebar'] {
    background: var(--forest);
    border-right: 0;
}

[data-testid='stSidebar'] h1,
[data-testid='stSidebar'] h2,
[data-testid='stSidebar'] h3,
[data-testid='stSidebar'] p,
[data-testid='stSidebar'] label,
[data-testid='stSidebar'] [data-testid='stCaptionContainer'] {
    color: var(--ivory) !important;
}

/* Inputs keep dark text on their light background. */
[data-testid='stSidebar'] [data-baseweb='select'] *,
[data-testid='stSidebar'] [data-baseweb='input'] input {
    color: var(--ink) !important;
}

[data-testid='stSidebar'] input::placeholder {
    color: var(--muted) !important;
}

/* Fix: warnings/infos in the sidebar inherited ivory text on a pale box. */
[data-testid='stSidebar'] [data-testid='stAlert'] p {
    color: var(--ink) !important;
}

/* Fix: the collapse arrow was dark-on-dark. */
[data-testid='stSidebar'] [data-testid='stSidebarCollapseButton'] button,
[data-testid='stSidebar'] [data-testid='stSidebarCollapseButton'] svg {
    color: var(--ivory) !important;
    fill: var(--ivory) !important;
}

[data-testid='stSidebar'] hr {
    border-color: rgba(255, 255, 255, 0.18);
}

.sidebar-brand {
    padding: 1.2rem 0 1.6rem;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.18);
}

.sidebar-brand strong {
    display: block;
    color: var(--ivory);
    font-family: var(--serif);
    font-size: 1.7rem;
    font-weight: 500;
    line-height: 1.15;
}

.sidebar-brand span {
    display: block;
    margin-top: 0.45rem;
    color: rgba(247, 245, 239, 0.72);
    font-size: 0.72rem;
    letter-spacing: 0.13em;
    text-transform: uppercase;
}

/* Navigation: the active page is obvious. */
[data-testid='stSidebar'] [role='radiogroup'] {
    gap: 0.35rem;
}

[data-testid='stSidebar'] [role='radiogroup'] label {
    display: flex;
    align-items: center;
    min-height: 46px;
    padding: 0.55rem 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.11);
    border-radius: var(--radius-sm);
    background: rgba(255, 255, 255, 0.035);
    cursor: pointer;
}

[data-testid='stSidebar'] [role='radiogroup'] label:hover {
    background: rgba(255, 255, 255, 0.12);
}

[data-testid='stSidebar'] [role='radiogroup'] label:has(input:checked) {
    border-color: rgba(255, 255, 255, 0.55);
    background: rgba(255, 255, 255, 0.18);
}

[data-testid='stSidebar'] [role='radiogroup'] label:has(input:focus-visible) {
    outline: 2px solid var(--gold-light);
    outline-offset: 2px;
}

[data-testid='stSidebar'] [role='radiogroup'] label p {
    color: var(--ivory) !important;
    font-weight: 650;
}

/* Fix: sidebar buttons were forest-on-forest (invisible). */
[data-testid='stSidebar'] .stButton > button {
    min-height: 2.8rem;
    border-color: var(--ivory);
    border-radius: var(--radius-sm);
    color: var(--forest);
    background: var(--ivory);
}

[data-testid='stSidebar'] .stButton > button:hover {
    color: var(--forest);
    background: #FFFFFF;
}

[data-testid='stSidebar'] .stButton > button p {
    color: var(--forest) !important;
}

/* ---------- Tabs ---------------------------------------------------- */
.stTabs [data-baseweb='tab-list'] {
    gap: 0.4rem;
    padding: 0.35rem;
    border: 1px solid rgba(5, 64, 43, 0.09);
    border-radius: var(--radius-md);
    background: rgba(255, 254, 250, 0.72);
    overflow-x: auto;
}

.stTabs [data-baseweb='tab'] {
    height: 44px;
    padding: 0 1rem;
    border-radius: var(--radius-sm);
    color: var(--muted);
    font-weight: 600;
    white-space: nowrap;
}

.stTabs [aria-selected='true'],
.stTabs [aria-selected='true'] p {
    color: var(--ivory) !important;
    background: var(--forest);
}

.stTabs [data-baseweb='tab-highlight'],
.stTabs [data-baseweb='tab-border'] {
    display: none;
}

/* ---------- Buttons ------------------------------------------------- */
.stButton > button,
.stDownloadButton > button,
[data-testid='stFormSubmitButton'] > button {
    min-height: 46px;
    padding: 0 1.4rem;
    border: 1px solid var(--forest);
    border-radius: 999px;
    color: var(--ivory);
    background: var(--forest);
    font-weight: 650;
    transition: background-color 160ms ease, box-shadow 160ms ease,
                transform 160ms ease;
}

.stButton > button p,
.stDownloadButton > button p,
[data-testid='stFormSubmitButton'] > button p {
    color: inherit;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid='stFormSubmitButton'] > button:hover {
    border-color: var(--forest-soft);
    color: var(--ivory);
    background: var(--forest-soft);
    box-shadow: 0 10px 24px rgba(5, 64, 43, 0.16);
    transform: translateY(-1px);
}

.stButton > button:active,
.stDownloadButton > button:active {
    transform: translateY(0);
}

/* Secondary download button reads as a quieter action. */
.stDownloadButton > button {
    color: var(--forest);
    background: transparent;
}

.stDownloadButton > button:hover {
    color: var(--ivory);
}

/* ---------- Inputs, tables, alerts, expanders ----------------------- */
[data-baseweb='select'] > div,
[data-baseweb='input'] > div,
textarea {
    border-color: var(--line-strong) !important;
    border-radius: 14px !important;
    background: var(--paper) !important;
}

[data-baseweb='tag'] {
    border-radius: 999px !important;
}

[data-testid='stDataFrame'] {
    overflow: hidden;
    border: 1px solid var(--line);
    border-radius: 18px;
    background: var(--paper);
}

[data-testid='stAlert'] {
    border-radius: var(--radius-md);
}

[data-testid='stExpander'] details {
    border: 1px solid var(--line);
    border-radius: var(--radius-md);
    background: rgba(255, 254, 250, 0.6);
}

[data-testid='stExpander'] summary p {
    color: var(--ink);
    font-weight: 600;
}

[data-testid='stCaptionContainer'] {
    color: var(--muted);
}

/* ---------- Section headings (used by insights / benchmarking) ------ */
.action-section,
.strength-section,
.driver-section {
    margin: 2.4rem 0 1rem;
}

.action-section h2,
.strength-section h2,
.driver-section h2 {
    margin: 0.2rem 0 0.35rem;
    padding: 0;
    color: var(--ink);
    font-family: var(--serif);
    font-size: 2rem;
}

.action-section p,
.driver-section p {
    max-width: 68ch;
    margin: 0;
    color: var(--muted);
}

.section-eyebrow,
.card-label {
    color: var(--gold-text);
    font-size: 0.70rem;
    font-weight: 750;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

/* ---------- Priority cards (action plan) ---------------------------- */
.priority-card {
    margin: 1rem 0;
    padding: 1.45rem;
    border: 1px solid rgba(139, 30, 30, 0.14);
    border-left: 5px solid var(--wine);
    border-radius: 20px;
    background: linear-gradient(135deg, #FFFEFB 0%, #FBF4EF 100%);
    box-shadow: 0 14px 32px rgba(24, 48, 39, 0.07);
}

.priority-card__head {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
}

.priority-card h3,
.strength-card h3 {
    margin: 0.15rem 0 0;
    padding: 0;
    color: var(--ink);
    font-family: var(--serif);
    font-size: 1.35rem;
    line-height: 1.25;
}

.priority-number {
    display: inline-flex;
    flex: 0 0 2.65rem;
    align-items: center;
    justify-content: center;
    height: 2.65rem;
    border-radius: 999px;
    color: #FFFFFF;
    background: var(--wine);
    font-size: 0.82rem;
    font-weight: 750;
    letter-spacing: 0.06em;
}

.priority-evidence {
    margin-bottom: 0.85rem;
    padding: 0.9rem 1rem;
    border-radius: 14px;
    background: var(--wine-wash);
}

.priority-evidence p,
.priority-grid p,
.strength-card p {
    margin: 0.3rem 0 0;
    color: var(--body);
    line-height: 1.55;
}

.priority-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.85rem;
}

.priority-grid > div {
    padding: 0.9rem 1rem;
    border: 1px solid var(--line);
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.82);
}

.strength-card {
    margin: 0.75rem 0;
    padding: 1.1rem 1.25rem;
    border: 1px solid rgba(5, 64, 43, 0.13);
    border-left: 5px solid var(--forest);
    border-radius: 18px;
    background: linear-gradient(135deg, #F9FCF8 0%, #EEF5EF 100%);
}

/* ---------- Deterioration signals ----------------------------------- */
.driver-card {
    display: grid;
    grid-template-columns: 1fr 1.3fr;
    align-items: center;
    gap: 1.2rem;
    margin: 0.8rem 0;
    padding: 1.15rem 1.25rem;
    border: 1px solid rgba(139, 30, 30, 0.14);
    border-radius: 18px;
    background: #FFFFFF;
}

.driver-card h3 {
    margin: 0.2rem 0 0;
    padding: 0;
    color: var(--ink);
    font-family: var(--serif);
}

.driver-card p {
    margin: 0.45rem 0 0;
    color: var(--muted);
}

.driver-comparison {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 0.7rem;
    padding: 0.85rem;
    border-radius: 14px;
    background: #FBF7F3;
    text-align: center;
}

.driver-comparison div:not(.driver-arrow) {
    display: flex;
    flex-direction: column;
}

.driver-comparison span,
.driver-comparison small {
    color: var(--muted);
    font-size: 0.72rem;   /* was 0.66rem: too small to read */
}

.driver-comparison strong {
    margin: 0.2rem 0;
    color: var(--wine);
    font-size: 1.25rem;
}

.driver-arrow {
    color: var(--gold);
    font-size: 1.4rem;
}

.decision-summary {
    margin: 1.2rem 0;
    padding: 1.35rem 1.5rem;
    border-radius: 20px;
    background: linear-gradient(135deg, var(--forest) 0%, var(--forest-soft) 100%);
    box-shadow: 0 16px 34px rgba(5, 64, 43, 0.16);
}

.decision-summary .card-label {
    color: var(--gold-light);
}

.decision-summary p {
    max-width: 70ch;
    margin: 0.45rem 0 0;
    color: #FFFFFF;
    font-family: var(--serif);
    font-size: 1.15rem;
    line-height: 1.6;
}

/* ---------- Market explorer ----------------------------------------- */
.market-hero {
    margin: 1rem 0 1.3rem;
    padding: 2rem;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: linear-gradient(135deg, #FFFEFB 0%, #EAF2EC 100%);
}

.market-hero h1 {
    margin: 0.35rem 0 0.75rem;
    padding: 0;
    color: var(--ink);
    font-family: var(--serif);
    font-size: 2.4rem;
    line-height: 1.1;
}

.market-hero p {
    max-width: 68ch;
    margin: 0;
    color: var(--muted);
    line-height: 1.6;
}

/* ---------- Footer -------------------------------------------------- */
.app-footer {
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: 0.8rem;
}

/* ---------- Responsive & motion ------------------------------------- */
@media (max-width: 760px) {
    .block-container {
        padding-top: 1.4rem;
    }

    .hero {
        padding: 2.2rem 1.5rem;
        border-radius: 22px;
    }

    .hero--compact {
        padding: 1.1rem 1.2rem;
    }

    .priority-grid,
    .driver-card {
        grid-template-columns: 1fr;
    }

    .market-hero {
        padding: 1.4rem;
    }

    .market-hero h1 {
        font-size: 1.9rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        transition: none !important;
        animation: none !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: none;
    }
}

@media print {
    [data-testid='stSidebar'],
    [data-testid='stHeader'] {
        display: none;
    }

    .stApp {
        background: #FFFFFF;
    }
}
</style>
"""

# Kept for backwards compatibility with modules that import the old name.
app_css = APP_CSS


def apply_style():
    """Inject the global stylesheet once per rerun."""
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_header(compact=False):
    """Display the page header and the sidebar brand.

    compact=True renders a slim title bar for secondary pages so the
    actual content is visible without scrolling.
    """
    if compact:
        hero_html = (
            '<section class="hero hero--compact">'
            '<div class="hero-label">Madrid restaurant intelligence</div>'
            '<h1>Turn reviews into clear decisions.</h1>'
            '</section>'
        )
    else:
        hero_html = (
            '<section class="hero">'
            '<div class="hero-label">Madrid restaurant intelligence</div>'
            '<h1>Turn reviews into clear decisions.</h1>'
            '<p>Diagnose a restaurant, compare it with similar places and '
            'spot historical warning signs, all from customer reviews '
            'written in Madrid.</p>'
            '</section>'
        )

    sidebar_html = (
        '<div class="sidebar-brand">'
        '<strong>Madrid Intelligence</strong>'
        '<span>Restaurant reputation system</span>'
        '</div>'
    )

    st.markdown(hero_html, unsafe_allow_html=True)
    st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)


def render_footer(text):
    """Quiet footer line at the end of every page."""
    st.markdown(f'<div class="app-footer">{text}</div>',
                unsafe_allow_html=True)


def _legend_repeats_x_axis(figure):
    """True when each trace is a single x category (e.g. px.bar(x=col, color=col))."""
    traces = [trace for trace in figure.data if getattr(trace, 'x', None) is not None]
    if not traces:
        return False
    return all({str(value) for value in trace.x} == {str(trace.name)}
               for trace in traces)


def style_figure(figure, height=None):
    """Apply the house style to a Plotly figure and return it."""
    has_title = bool(getattr(figure.layout.title, 'text', None))

    # Facet panels from plotly express are labelled "column=value"; keep the value.
    facet_titles = [annotation for annotation in figure.layout.annotations
                    if annotation.text and '=' in annotation.text]
    for annotation in facet_titles:
        annotation.text = annotation.text.split('=', 1)[1]
        annotation.font = {'family': SANS, 'size': 13, 'color': COLORS['ink']}
    has_facets = bool(facet_titles)

    hide_legend = _legend_repeats_x_axis(figure)
    if hide_legend:
        figure.update_layout(showlegend=False)

    # Leave room above the plot for whatever sits there: title, legend, panel titles.
    top_margin = 20
    if has_title:
        top_margin += 45
    if figure.layout.showlegend is not False:
        top_margin += 35
    if has_facets:
        top_margin += 25

    figure.update_layout(
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(255, 254, 250, 0.72)',
        font={'family': SANS, 'color': COLORS['ink'], 'size': 13},
        colorway=[COLORS['forest'], COLORS['gold'], COLORS['clay'],
                  '#6C8B76', COLORS['sage'], COLORS['wine']],
        legend={'orientation': 'h', 'yanchor': 'bottom',
                'y': 1.10 if has_facets else 1.02,
                'xanchor': 'left', 'x': 0,
                'font': {'size': 12, 'color': COLORS['muted']},
                'title': {'font': {'size': 12, 'color': COLORS['muted']},
                          'side': 'left'},
                'bgcolor': 'rgba(0, 0, 0, 0)'},
        hoverlabel={'bgcolor': COLORS['paper'],
                    'bordercolor': 'rgba(5, 64, 43, 0.25)',
                    'font': {'family': SANS, 'color': COLORS['ink'],
                             'size': 13}},
        margin={'l': 20, 'r': 20, 't': top_margin, 'b': 20},
        bargap=0.3,
    )
    # Only style the title when there is one: an empty title object makes
    # Plotly draw the word "undefined".
    if has_title:
        figure.update_layout(title={'font': {'family': SERIF, 'size': 20,
                                             'color': COLORS['forest']},
                                    'x': 0, 'xanchor': 'left'})
    if height:
        figure.update_layout(height=height)

    axis_style = {
        'gridcolor': 'rgba(5, 64, 43, 0.08)',
        'zerolinecolor': 'rgba(5, 64, 43, 0.25)',
        'linecolor': 'rgba(5, 64, 43, 0.18)',
        'tickfont': {'color': COLORS['muted']},
        'title': {'font': {'color': COLORS['muted'], 'size': 12}},
    }
    figure.update_xaxes(**axis_style)
    figure.update_yaxes(**axis_style)
    if has_facets:
        # Panels often measure different things (a rating vs. a percentage),
        # so every panel shows its own scale.
        figure.update_yaxes(showticklabels=True)
    return figure


def show_chart(figure, height=None):
    """Style a Plotly figure and render it at full width."""
    st.plotly_chart(style_figure(figure, height=height), config=PLOTLY_CONFIG, **FULL_WIDTH)


def styled_chart(figure):
    """Support older application modules that used this function name."""
    return style_figure(figure)
