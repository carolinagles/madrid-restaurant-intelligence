"""Historical restaurant diagnosis, peer benchmarks and explainable text analysis."""
import json
from html import escape
import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app.aspects import build_review_aspects
from app.benchmarking import (build_executive_summary, get_restaurant_groups,
                              render_benchmarking, render_market_explorer)
from app.explainability import explain_sentiment
from app.inference import predict_sentiment
from app.insights import ACTIONS, prepare_aspects, render_restaurant_insights
import numpy as np

from app.ui import (COLORS, FULL_WIDTH, PAGE_ICONS, apply_style, glass_container,
                    render_data_note, render_footer, render_header, render_sidebar_brand,
                    render_spectrum, show_chart, sidebar_label, sidebar_panel, spectrum_html)

ROOT_PATH = Path(__file__).resolve().parent
DATA_PATH = ROOT_PATH / 'data'
FOREST = COLORS['forest']
SENTIMENT_COLORS = {'Negative': COLORS['clay'], 'Neutral': COLORS['gold'],
                    'Positive': COLORS['positive']}

PAGE_START = 'Start here'
PAGE_DIAGNOSIS = 'Restaurant diagnosis'
PAGE_MARKET = 'Market & Top 10'
PAGE_CLASSIFIER = 'Review classifier'
PAGE_METHODOLOGY = 'Methodology'
PAGES = [PAGE_START, PAGE_DIAGNOSIS, PAGE_MARKET, PAGE_CLASSIFIER, PAGE_METHODOLOGY]
PAGE_SUBTITLES = {
    PAGE_DIAGNOSIS: 'Where one restaurant stands, and what to check first.',
    PAGE_CLASSIFIER: 'Paste any review in Spanish or English and see why the model decides.',
    PAGE_METHODOLOGY: 'Every number in this app, and how it was calculated.',
}

# Results from notebook 3: final test on restaurants never used in development.
MODEL_FACTS = {'accuracy': '90.5%', 'macro_f1': '0.81', 'baseline_accuracy': '75.7%',
               'baseline_macro_f1': '0.29', 'negative_recall': '0.88', 'test_restaurants': 996,
               'test_reviews': '110,912', 'raw_reviews': '1.34 million', 'features': '60,000',
               'c_value': '0.05'}
JOURNEY_REVIEW = 'Tardaron una hora en traer los platos y llegaron fríos.'
JOURNEY_THEME = 'Waiting time'

DEFAULT_RESTAURANT = 'Ramses'  # restaurant shown when the app opens
SIGNAL_LEVELS = ['Watch', 'High alert', 'Critical alert']
EMPTY_ASPECTS = pd.DataFrame(columns=['item_id', 'aspect', 'mentions'])


def fmt(value, decimals=1, suffix=''):
    """Format a number, returning 'Unavailable' for missing values."""
    if value is None or pd.isna(value):
        return 'Unavailable'
    return f'{float(value):,.{decimals}f}{suffix}'


def _normalize(text):
    """Lowercase and strip accents so 'Ramsés' matches 'ramses'."""
    decomposed = unicodedata.normalize('NFKD', str(text))
    return ''.join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def fmt_int(value):
    return 'Unavailable' if value is None or pd.isna(value) else f'{int(value):,}'


def text_or(value, fallback='Not specified'):
    return fallback if value is None or pd.isna(value) or str(value).strip() in {'', 'nan'} else str(value)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner='Loading historical restaurant data...')
def load_project_data():
    diagnostics = pd.read_parquet(DATA_PATH / 'restaurant_diagnostics.parquet')
    membership = pd.read_parquet(DATA_PATH / 'benchmark_membership.parquet')
    groups = pd.read_parquet(DATA_PATH / 'benchmark_groups.parquet').rename(
        columns={'restaurants': 'group_restaurants', 'reviews': 'group_reviews'})
    with (DATA_PATH / 'project_config.json').open(encoding='utf-8') as file:
        config = json.load(file)

    for frame in (diagnostics, membership):
        frame['item_id'] = frame['item_id'].astype(str)
    for frame in (membership, groups):
        for column in ('specialty', 'price_interval'):
            frame[column] = frame[column].astype(str)

    diagnostics['name'] = diagnostics['name'].fillna('Unnamed restaurant').astype(str).str.strip()
    diagnostics['restaurant_label'] = diagnostics['name'] + ' · ' + diagnostics['item_id']
    diagnostics['alert_evaluable'] = diagnostics['alert_evaluable'].fillna(False).astype(bool)

    group_metrics = (
        membership[['item_id', 'specialty', 'price_interval']].drop_duplicates()
        .merge(diagnostics[['item_id', 'mean_review_rating', 'negative_percentage']],
               on='item_id', how='inner', validate='many_to_one')
        .groupby(['specialty', 'price_interval'], as_index=False, observed=True)
        .agg(group_mean_rating=('mean_review_rating', 'mean'),
             group_negative_percentage=('negative_percentage', 'mean'))
    )
    groups = groups.merge(group_metrics, on=['specialty', 'price_interval'],
                          how='left', validate='one_to_one')
    return diagnostics, membership, groups, config


@st.cache_data(show_spinner='Preparing bilingual review themes. The first load may take a few minutes...')
def load_review_aspects(config):
    corrected = DATA_PATH / 'restaurant_review_aspects_EN.parquet'
    legacy = DATA_PATH / 'restaurant_review_aspects.parquet'
    simple = DATA_PATH / 'review_aspects.parquet'
    corpus_path = DATA_PATH / 'modeling_corpus.parquet'

    if corrected.is_file():
        return prepare_aspects(pd.read_parquet(corrected))
    if legacy.is_file():
        old = pd.read_parquet(legacy)
        # The old notebook used Spanish class names, while notebook 2 now exports English labels.
        if {'negative_reviews', 'positive_reviews'}.issubset(old.columns) and (
                old['negative_reviews'].sum() + old['positive_reviews'].sum() > 0):
            return prepare_aspects(old)
    if corpus_path.is_file():
        corpus = pd.read_parquet(corpus_path,
                                 columns=['item_id', 'review_id', 'review_text', 'sentiment', 'date'])
        aspects = build_review_aspects(corpus, config)
        try:
            aspects.to_parquet(corrected, index=False)
        except OSError:
            pass  # Read-only deployments (e.g. Streamlit Cloud) still get the in-memory result.
        return prepare_aspects(aspects)
    if simple.is_file():
        return prepare_aspects(pd.read_parquet(simple))
    return EMPTY_ASPECTS.copy()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def render_dataset_summary(diagnostics, groups):
    summary = st.columns(4)
    summary[0].metric('Restaurants', f"{diagnostics['item_id'].nunique():,}")
    summary[1].metric('Reviews', fmt_int(diagnostics['reviews'].sum()))
    summary[2].metric('Peer groups', f'{len(groups):,}')
    summary[3].metric('With an evaluable alert', f"{int(diagnostics['alert_evaluable'].sum()):,}",
                      help='Restaurants with at least five reviews in each six-month period.')


def go_to(page):
    """Button callback: switch the sidebar navigation before the next rerun."""
    st.session_state['active_page'] = page


def sentiment_position(decision_scores):
    """Place a review on the Negative (0) to Positive (1) spectrum.

    Softmax of the decision scores, then Neutral counts as 0.5. A relative display
    position, not a calibrated probability.
    """
    labels = ['Negative', 'Neutral', 'Positive']
    scores = np.array([float(decision_scores.get(label, 0.0)) for label in labels])
    weights = np.exp(scores - scores.max())
    weights /= weights.sum()
    return float(weights[1] * 0.5 + weights[2])


@st.cache_data(show_spinner=False)
def classify_example(text):
    """Run the real model on the hero example; fall back quietly if it is unavailable."""
    try:
        result = predict_sentiment(text)
    except Exception:  # model file missing on a demo laptop: the page must still render
        return {'label': 'Negative', 'position': 0.08, 'milliseconds': None}
    return {'label': str(result['sentiment']),
            'position': sentiment_position(result['decision_scores']),
            'milliseconds': result.get('prediction_milliseconds')}


def render_overview(diagnostics, groups, note):
    """One screen that explains the whole project to a mixed audience."""
    restaurants = diagnostics['item_id'].nunique()
    reviews = int(diagnostics['reviews'].sum())
    example = classify_example(JOURNEY_REVIEW)
    label = example['label']
    action = ACTIONS[JOURNEY_THEME][0]
    lens = spectrum_html(example['position'],
                         aria_label=f'The model places this review near {label}')

    st.markdown(f"""
<section class="hero glass">
  <div>
    <p class="hero__brand"><b>Madrid</b> Restaurant Intelligence</p>
    <h1>Customer reviews, turned into the next decision.</h1>
    <p class="hero__lede">We read {reviews:,} TripAdvisor reviews of {restaurants:,} Madrid
    restaurants, in Spanish and English. Owners see where they stand and what to fix first;
    engineers see a model they can audit, word by word.</p>
  </div>
  <figure class="journey" aria-label="How one review moves through the system">
    <figcaption>One real review, end to end</figcaption>
    <ol>
      <li><span class="journey__who">A guest writes</span>
          <q>{escape(JOURNEY_REVIEW)}</q></li>
      <li><span class="journey__who">The model reads the sentiment</span>
          <span class="chip chip--{label.lower()}">{escape(label)}</span>{lens}</li>
      <li><span class="journey__who">The theme is detected</span>
          <span class="journey__what">{escape(JOURNEY_THEME)}</span></li>
      <li><span class="journey__who">The owner gets a concrete check</span>
          <span class="journey__what">{escape(action)}</span></li>
    </ol>
  </figure>
</section>""", unsafe_allow_html=True)

    figures = st.columns(4)
    figures[0].metric('Reviews analysed', f'{reviews:,}')
    figures[1].metric('Restaurants', f'{restaurants:,}')
    figures[2].metric('Comparable peer groups', f'{len(groups):,}',
                      help='Same cuisine and price range, at least 30 restaurants and 1,000 reviews.')
    figures[3].metric('Accuracy on unseen restaurants', MODEL_FACTS['accuracy'],
                      help=f"Final test on {MODEL_FACTS['test_restaurants']} restaurants never used "
                           f"in training. Macro F1 {MODEL_FACTS['macro_f1']}; always guessing "
                           f"'Positive' would score {MODEL_FACTS['baseline_accuracy']}.")

    st.markdown(f"""
<div class="section-head"><h2>How it works</h2>
<p>Three steps, from raw text to a decision a manager can act on this week.</p></div>
<div class="steps">
  <article class="step glass"><span class="step__number">1</span>
    <h3>Clean the reviews</h3>
    <p>{MODEL_FACTS['raw_reviews']} raw reviews are de-duplicated, joined with restaurant
    details and kept in Spanish and English, the two languages of 86% of guests.</p></article>
  <article class="step glass"><span class="step__number">2</span>
    <h3>Learn from the text</h3>
    <p>A bilingual text model learns sentiment from star ratings and is tested on restaurants
    it never saw. Every prediction shows the exact words that drove it.</p></article>
  <article class="step glass"><span class="step__number">3</span>
    <h3>Turn it into decisions</h3>
    <p>Each restaurant gets a diagnosis, a fair comparison with peers of the same cuisine and
    price, historical warning signals and a short, ranked action plan.</p></article>
</div>
""", unsafe_allow_html=True)

    latency = (f"{example['milliseconds']:.1f} ms" if example['milliseconds']
               else 'Under 1 ms')
    st.markdown(f"""
<div class="section-head"><h2>Model card</h2>
<p>For the engineers in the room: what the model is, how it was tested and what it costs to run.</p></div>
<section class="model-card glass"><dl>
  <div><dt>Architecture</dt><dd>TF-IDF to LinearSVC
       <small>{MODEL_FACTS['features']} word and bigram features, Spanish and English, C = {MODEL_FACTS['c_value']}</small></dd></div>
  <div><dt>Evaluation</dt><dd>Split by restaurant
       <small>{MODEL_FACTS['test_restaurants']} held-out restaurants, {MODEL_FACTS['test_reviews']} reviews, zero overlap</small></dd></div>
  <div><dt>Test results</dt><dd>Macro F1 {MODEL_FACTS['macro_f1']}
       <small>Negative recall {MODEL_FACTS['negative_recall']}; majority baseline {MODEL_FACTS['baseline_macro_f1']}</small></dd></div>
  <div><dt>Serving</dt><dd>{latency} per review
       <small>Measured live; exact word attributions; FastAPI endpoint</small></dd></div>
</dl></section>
<div class="section-head"><h2>Choose your starting point</h2>
<p>The same data answers a different question for each person in the room.</p></div>
""", unsafe_allow_html=True)

    audiences = [
        ('owners', 'Restaurant owners',
         'Where your restaurant stands, what guests complain about and the three things '
         'to check first.', 'Diagnose a restaurant', PAGE_DIAGNOSIS),
        ('groups', 'Restaurant groups and investors',
         'Benchmark any cuisine and price range, find leaders and spot venues whose '
         'reputation is slipping.', 'Explore the market', PAGE_MARKET),
        ('ml', 'ML engineers',
         'Type a review and inspect the decision: class scores, margin and the exact '
         'contribution of every word.', 'Inspect the model', PAGE_CLASSIFIER),
    ]
    for column, (key, title, text, button, target) in zip(st.columns(3), audiences):
        with column:
            with glass_container(f'audience-{key}'):
                st.markdown(f'<div class="audience"><h3>{escape(title)}</h3>'
                            f'<p>{escape(text)}</p></div>', unsafe_allow_html=True)
                st.button(button, key=f'go_{key}', on_click=go_to, args=(target,),
                          type='primary', **FULL_WIDTH)

    st.markdown(f"""<div class="limits glass"><strong>What this is, and what it is not.</strong>
    {escape(note)} Sentiment labels come from star ratings. Themes show an association
    with complaints, not a proven cause.</div>""", unsafe_allow_html=True)


def render_classifier():
    st.caption('The model learned from English and Spanish reviews with labels derived from '
               'ratings. It is tested on restaurants not used in development.')

    examples = {
        'Mixed (EN)': 'The food was good, but the service was slow and the bill was expensive.',
        'Positive (ES)': 'Comida espectacular y un servicio muy atento. Volveremos seguro.',
        'Negative (ES)': 'Tardaron una hora en traer los platos y llegaron fríos.',
    }
    example_columns = st.columns(len(examples))
    for column, (label, text) in zip(example_columns, examples.items()):
        if column.button(f'Try: {label}', key=f'example_{label}', **FULL_WIDTH):
            st.session_state['review_text'] = text

    with st.form('classifier_form', border=False):
        review = st.text_area('Review text', key='review_text', height=135, max_chars=5000,
                              placeholder='The food was good, but the service was slow.')
        submitted = st.form_submit_button('Analyze this review', type='primary')

    if submitted:
        if len(review.strip()) < 3:
            st.warning('Enter at least three characters.')
            return
        with st.spinner('Analyzing the review...'):
            try:
                result = predict_sentiment(review)
                explanation = explain_sentiment(review)
            except (OSError, ValueError, RuntimeError) as error:
                st.error(f'Could not analyze the review: {error}')
                return
        # Keep the result so it survives reruns triggered by other widgets.
        st.session_state['classifier_result'] = {'review': review, 'result': result,
                                                 'explanation': explanation}

    stored = st.session_state.get('classifier_result')
    if not stored:
        st.info('Write or pick a review above, then select **Analyze this review**.')
        return
    if stored['review'] != st.session_state.get('review_text'):
        st.caption('Showing the result for the previously analyzed text.')

    result, explanation = stored['result'], stored['explanation']
    label = str(result['sentiment'])
    message = f'Predicted label: **{label}**'
    {'Positive': st.success, 'Negative': st.error}.get(label, st.info)(message)
    scores = explanation.get('class_scores') or result.get('decision_scores', {})
    if scores:
        render_spectrum(sentiment_position(scores),
                        value_label='Where this review sits <small>relative position from the '
                                    'three class scores, not a probability</small>',
                        aria_label=f'Predicted {label}')

    metrics = st.columns(3)
    metrics[0].metric('Decision score', fmt(explanation.get('decision_score'), 3),
                      help='The model score for the predicted label. Word contributions '
                           'plus the baseline add up exactly to this number.')
    runner_up = explanation.get('runner_up', 'next label')
    metrics[1].metric(f'Lead over {runner_up}', fmt(explanation.get('margin_over_runner_up'), 3),
                      help='How far ahead the predicted label is. Values near zero mean '
                           'the review is borderline between the two labels.')
    metrics[2].metric('Model response', fmt(result.get('prediction_milliseconds'), 1, ' ms'))

    terms = pd.DataFrame(explanation.get('terms', []))
    if terms.empty:
        st.warning('None of the words in this review were seen during training, so the '
                   'prediction comes only from the model baseline. Treat it as unreliable.')
    else:
        terms['Role'] = terms['contribution'].gt(0).map(
            {True: f'Supports {label}', False: f'Opposes {label}'})
        figure = px.bar(terms.sort_values('contribution'), x='contribution', y='term',
                        color='Role', orientation='h',
                        labels={'contribution': f'Contribution to the {label} score', 'term': ''},
                        color_discrete_map={f'Supports {label}': FOREST,
                                            f'Opposes {label}': COLORS['lime']})
        show_chart(figure, height=max(280, 34 * len(terms) + 110))
        st.caption(
            f"Showing the {len(terms)} most influential of {explanation.get('terms_in_review', len(terms))} "
            f"terms. Baseline: {fmt(explanation.get('intercept'), 3)}; remaining terms: "
            f"{fmt(explanation.get('other_terms_contribution'), 3)}.")
    st.caption('Contributions are exact for this linear model (TF-IDF weight × model coefficient), '
               'not an approximation. Scores are not calibrated probabilities.')

    with st.expander('Use the same model from code'):
        st.code('uvicorn app.api:app\n\n'
                'curl -X POST http://127.0.0.1:8000/api/v1/sentiment/explain \\\n'
                "  -H 'Content-Type: application/json' \\\n"
                '  -d \'{"review_text": "La comida estaba buena, pero el servicio fue lento."}\'',
                language='bash')
        st.caption('This page, the API and the notebooks load one saved pipeline. '
                   '/api/v1/sentiment returns the label; /explain adds the word contributions.')


def render_methodology(snapshot, last_review):
    sections = {
        'Data source and cleaning': 'Historical TripAdvisor reviews of Madrid restaurants, '
                                    'in Spanish and English. Duplicates and invalid values '
                                    'were handled in notebook 1.',
        'Restaurant diagnosis': 'A negative review has 1–2 stars, neutral has 3, and positive '
                                'has 4–5. Review volume describes the evidence behind an average.',
        'Peer benchmark': 'Eligible groups share a specialty and price range and include at '
                          'least 30 restaurants and 1,000 reviews. Group means give each '
                          'restaurant equal weight.',
        'Historical signals': 'Two complete six-month windows end in May 2023. Each restaurant '
                              'needs five reviews per period. Both rating decline and negative '
                              'share increase must meet the threshold.',
        'Themes and suggested checks': 'Bilingual keyword matches identify food, service, '
                                       'atmosphere, price, waiting and cleanliness. At least five '
                                       'historical mentions support a theme; three per period '
                                       'support a comparison. Association does not prove a cause.',
        'Text classifier and explanations': 'The final TF-IDF + LinearSVC model was selected on '
                                            'validation and tested on restaurants held out from '
                                            'development. Because the model is linear, each word\'s '
                                            'contribution is exact: its TF-IDF weight times the model '
                                            'coefficient. It explains one review, not a restaurant.',
    }
    for index, (title, description) in enumerate(sections.items()):
        with st.expander(title, expanded=index == 0):
            st.write(description)
    st.caption(f'Alert snapshot: {snapshot}. Most recent source review: {last_review}.')


def select_restaurant(diagnostics):
    """Sidebar search + picker in their own panel. Returns the selected row or None."""
    sidebar_label('Restaurant')
    panel = sidebar_panel('sidebar-filters')
    search = panel.text_input('Find a restaurant', placeholder='Type part of a name',
                              key='restaurant_search').strip()
    options = diagnostics
    if search:
        options = diagnostics.loc[diagnostics['name'].str.contains(
            search, case=False, na=False, regex=False)]
    if options.empty:
        panel.warning('No matches. Try another name.')
        st.info(f'No restaurant name contains “{search}”. Clear the search box or try '
                'a shorter part of the name.')
        return None

    ordered = options.sort_values(['name', 'item_id'])
    labels = ordered['restaurant_label'].tolist()
    # Open the app on the default restaurant (accent- and case-insensitive match).
    default_matches = ordered['name'].map(_normalize).str.contains(
        _normalize(DEFAULT_RESTAURANT), regex=False).to_numpy().nonzero()[0]
    default_index = int(default_matches[0]) if len(default_matches) else 0

    selected_label = panel.selectbox('Restaurant', labels, index=default_index,
                                     key='selected_restaurant', label_visibility='collapsed')
    panel.caption(f'{len(labels):,} matching restaurants')
    return diagnostics.loc[diagnostics['restaurant_label'].eq(selected_label)].iloc[0]


def render_overview_tab(restaurant, restaurant_groups, config):
    indicators = st.columns(4)
    indicators[0].metric('Reviews', fmt_int(restaurant['reviews']))
    rating = restaurant['mean_review_rating']
    indicators[1].metric('Average review rating', fmt(rating, 2, ' / 5') if pd.notna(rating) else 'Unavailable')
    indicators[2].metric('Positive reviews', fmt(restaurant['positive_percentage'], 1, '%'))
    indicators[3].metric('Negative reviews', fmt(restaurant['negative_percentage'], 1, '%'))

    if pd.notna(rating):
        peer_rating = None
        if not restaurant_groups.empty:
            group = restaurant_groups.sort_values('group_restaurants', ascending=False).iloc[0]
            if pd.notna(group['peer_mean_rating']):
                peer_rating = float(group['peer_mean_rating'])
        render_spectrum(
            (float(rating) - 1) / 4, low_label='1 star', high_label='5 stars',
            value_label=f'{rating:.2f} average rating <small>out of 5, from '
                        f'{fmt_int(restaurant["reviews"])} reviews</small>',
            marker=None if peer_rating is None else (peer_rating - 1) / 4,
            marker_label=None if peer_rating is None else f'Peers {peer_rating:.2f}',
            aria_label=f'Average rating {rating:.2f} out of 5')

    st.info(build_executive_summary(restaurant, restaurant_groups))

    try:
        aspects = load_review_aspects(config)
    except (OSError, ValueError, KeyError) as error:
        st.warning(f'Review themes could not be prepared: {error}')
        aspects = EMPTY_ASPECTS.copy()
    render_restaurant_insights(restaurant, restaurant_groups, aspects)

    with st.expander('Show the distribution of review ratings'):
        sentiment = pd.DataFrame({
            'Sentiment': list(SENTIMENT_COLORS),
            'Share (%)': [restaurant['negative_percentage'], restaurant['neutral_percentage'],
                          restaurant['positive_percentage']],
        })
        figure = px.bar(sentiment, x='Sentiment', y='Share (%)', color='Sentiment',
                        color_discrete_map=SENTIMENT_COLORS)
        figure.update_traces(texttemplate='%{y:.1f}%', textposition='outside', cliponaxis=False,
                             hovertemplate='%{x}: %{y:.1f}%<extra></extra>')
        figure.update_layout(showlegend=False, yaxis_range=[0, 105], xaxis_title=None)
        show_chart(figure, height=340)
        st.caption('Classes come from star ratings: Negative 1–2, Neutral 3, Positive 4–5.')

    platform_rating = restaurant.get('platform_rating')
    shown = fmt(platform_rating, 1, ' / 5') if pd.notna(platform_rating) else 'unavailable'
    st.caption(f'TripAdvisor item rating: {shown}. This differs from the review average.')


def render_alerts_tab(restaurant, diagnostics):
    st.subheader('Historical reputation signals')
    st.info('Earlier period: June–November 2022. Later period: December 2022–May 2023. '
            'At least five reviews in each period are required. No result forecasts the future.')

    # The selected restaurant comes first: it is what the person came to see.
    if bool(restaurant['alert_evaluable']):
        status = str(restaurant['alert_level'])
        show = {'Critical alert': st.error, 'High alert': st.error, 'Watch': st.warning}.get(status, st.success)
        show(f"**{restaurant['name']}**: {status}")
        indicators = st.columns(4)
        indicators[0].metric('Earlier reviews', fmt_int(restaurant['previous_reviews']))
        indicators[1].metric('Later reviews', fmt_int(restaurant['recent_reviews']))
        indicators[2].metric('Change in rating', fmt(restaurant['rating_change'], 2))
        indicators[3].metric('Change in negative share',
                             fmt(restaurant['negative_percentage_point_change'], 1, ' pp'))
    else:
        st.warning(f"**{restaurant['name']}** is not evaluable: it has fewer than five reviews in "
                   'one or both periods, so any change would not be stable.')

    with st.expander('Alert thresholds'):
        st.markdown('Both conditions must hold:\n\n'
                    '| Level | Rating change | Negative share change |\n'
                    '|---|---|---|\n'
                    '| Watch | −0.40 or worse | +10 pp or more |\n'
                    '| High alert | −0.80 or worse | +20 pp or more |\n'
                    '| Critical alert | −1.00 or worse | +30 pp or more |\n\n'
                    'These are observed changes, not model predictions.')

    st.markdown('#### All restaurants')
    evaluable = diagnostics.loc[diagnostics['alert_evaluable']]
    alerts = st.columns(4)
    alerts[0].metric('Evaluable', f'{len(evaluable):,}')
    alerts[1].metric('No alert', f"{int(evaluable['alert_level'].eq('No alert').sum()):,}")
    alerts[2].metric('With a signal', f"{int(evaluable['alert_level'].isin(SIGNAL_LEVELS).sum()):,}")
    alerts[3].metric('Critical alerts', f"{int(evaluable['alert_level'].eq('Critical alert').sum()):,}")

    levels = st.multiselect('Filter historical signals', SIGNAL_LEVELS,
                            default=['High alert', 'Critical alert'], key='alert_levels')
    signals = (evaluable.loc[evaluable['alert_level'].isin(levels),
                             ['name', 'price_interval', 'recent_reviews', 'rating_change',
                              'negative_percentage_point_change', 'alert_level',
                              'operational_priority']]
               .sort_values('rating_change')
               .rename(columns={'name': 'Restaurant', 'price_interval': 'Price',
                                'recent_reviews': 'Later reviews', 'rating_change': 'Rating change',
                                'negative_percentage_point_change': 'Negative share change (pp)',
                                'alert_level': 'Alert', 'operational_priority': 'Priority'}))
    if signals.empty:
        st.info('No restaurants match the selected levels. Add a level above to see results.')
        return

    st.dataframe(
        signals, hide_index=True, **FULL_WIDTH,
        column_config={
            'Later reviews': st.column_config.NumberColumn(format='%d'),
            'Rating change': st.column_config.NumberColumn(format='%+.2f'),
            'Negative share change (pp)': st.column_config.NumberColumn(format='%+.1f'),
        },
    )
    st.download_button('Download these signals (CSV)',
                       signals.to_csv(index=False).encode('utf-8'),
                       file_name='madrid_restaurant_signals.csv', mime='text/csv')


def render_diagnosis(diagnostics, membership, groups, config):
    restaurant = select_restaurant(diagnostics)
    if restaurant is None:
        return
    restaurant_groups = get_restaurant_groups(restaurant, membership, groups, diagnostics)

    render_dataset_summary(diagnostics, groups)
    with st.expander('How to read the dashboard'):
        st.markdown('**Diagnosis** summarizes historical ratings. **Peer groups** share specialty '
                    'and price. **Historical alerts** compare two six-month periods ending May 2023. '
                    '**Review themes** describe keyword mentions. **Word contributions** explain one '
                    'text prediction. Classifier scores are not calibrated probabilities.')

    st.header(str(restaurant['name']))
    st.caption(f"{text_or(restaurant['price_interval'], 'Price not specified')} · "
               f"{fmt_int(restaurant['reviews'])} historical reviews · "
               f"evidence support: {text_or(restaurant.get('diagnostic_support'), 'not rated')}")

    tabs = st.tabs(['Overview & actions', 'Peer comparison', 'Historical alerts'])
    with tabs[0]:
        render_overview_tab(restaurant, restaurant_groups, config)
    with tabs[1]:
        render_benchmarking(restaurant, restaurant_groups, membership, diagnostics)
    with tabs[2]:
        render_alerts_tab(restaurant, diagnostics)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title='Madrid Restaurant Intelligence', page_icon='🍽️',
                       layout='wide', initial_sidebar_state='expanded')
    apply_style()
    render_sidebar_brand()
    sidebar_label('Navigation')
    page = st.sidebar.radio('Choose a view', PAGES, label_visibility='collapsed', key='active_page',
                            format_func=lambda name: f'{PAGE_ICONS.get(name, "")} {name}'.strip())
    st.sidebar.divider()

    try:
        diagnostics, membership, groups, config = load_project_data()
    except (OSError, ValueError, KeyError) as error:
        st.error(f'Could not load project data: {error}. Check that the files in '
                 f'`{DATA_PATH.name}/` exist and were exported by the notebooks.')
        st.stop()

    alert_config = config.get('temporal_alert', {})
    snapshot = alert_config.get('as_of_date', '2023-05-31')
    last_review = alert_config.get('last_observed_review_date', '2023-06-10')
    note = (f'Historical data: latest review {last_review}, alert window ends {snapshot}. '
            'Results describe the past, not current performance.')

    if page == PAGE_START:
        render_overview(diagnostics, groups, note)
    else:
        if page != PAGE_MARKET:  # the market explorer has its own header
            render_header(title=page, subtitle=PAGE_SUBTITLES.get(page))
        render_data_note(note)
        if page == PAGE_MARKET:
            render_market_explorer(groups, membership, diagnostics)
        elif page == PAGE_CLASSIFIER:
            render_classifier()
        elif page == PAGE_METHODOLOGY:
            render_methodology(snapshot, last_review)
        else:
            render_diagnosis(diagnostics, membership, groups, config)

    render_footer('Madrid Restaurant Intelligence. Historical TripAdvisor review analysis; '
                  'a research project, not a live rating.')


main()
