"""Historical restaurant diagnosis, peer benchmarks and explainable text analysis."""
import json
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
from app.insights import prepare_aspects, render_restaurant_insights
from app.ui import (COLORS, FULL_WIDTH, apply_style, render_footer, render_header,
                    show_chart)

ROOT_PATH = Path(__file__).resolve().parent
DATA_PATH = ROOT_PATH / 'data'
FOREST = COLORS['forest']
SENTIMENT_COLORS = {'Negative': COLORS['clay'], 'Neutral': '#B8A16F', 'Positive': FOREST}

PAGE_DIAGNOSIS = 'Restaurant diagnosis'
PAGE_MARKET = 'Market & Top 10'
PAGE_CLASSIFIER = 'Review classifier'
PAGE_METHODOLOGY = 'Methodology'
PAGES = [PAGE_DIAGNOSIS, PAGE_MARKET, PAGE_CLASSIFIER, PAGE_METHODOLOGY]

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


def render_classifier():
    st.subheader('Classify and explain a review')
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
                                            f'Opposes {label}': COLORS['gold']})
        show_chart(figure, height=max(280, 34 * len(terms) + 110))
        st.caption(
            f"Showing the {len(terms)} most influential of {explanation.get('terms_in_review', len(terms))} "
            f"terms. Baseline: {fmt(explanation.get('intercept'), 3)}; remaining terms: "
            f"{fmt(explanation.get('other_terms_contribution'), 3)}.")
    st.caption('Contributions are exact for this linear model (TF-IDF weight × model coefficient), '
               'not an approximation. Scores are not calibrated probabilities.')


def render_methodology(snapshot, last_review):
    st.subheader('How the results are calculated')
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
    """Sidebar search + picker. Returns the selected row or None."""
    st.sidebar.markdown('### Restaurant')
    search = st.sidebar.text_input('Find a restaurant', placeholder='Type part of a name',
                                   key='restaurant_search').strip()
    options = diagnostics
    if search:
        options = diagnostics.loc[diagnostics['name'].str.contains(
            search, case=False, na=False, regex=False)]
    if options.empty:
        st.sidebar.warning('No matches. Try another name.')
        st.info(f'No restaurant name contains “{search}”. Clear the search box or try '
                'a shorter part of the name.')
        return None

    ordered = options.sort_values(['name', 'item_id'])
    labels = ordered['restaurant_label'].tolist()
    # Open the app on the default restaurant (accent- and case-insensitive match).
    default_matches = ordered['name'].map(_normalize).str.contains(
        _normalize(DEFAULT_RESTAURANT), regex=False).to_numpy().nonzero()[0]
    default_index = int(default_matches[0]) if len(default_matches) else 0

    st.sidebar.caption(f'{len(labels):,} matching restaurants')
    selected_label = st.sidebar.selectbox('Restaurant', labels, index=default_index,
                                          key='selected_restaurant',
                                          label_visibility='collapsed')
    return diagnostics.loc[diagnostics['restaurant_label'].eq(selected_label)].iloc[0]


def render_overview_tab(restaurant, restaurant_groups, config):
    indicators = st.columns(4)
    indicators[0].metric('Reviews', fmt_int(restaurant['reviews']))
    rating = restaurant['mean_review_rating']
    indicators[1].metric('Average review rating', fmt(rating, 2, ' / 5') if pd.notna(rating) else 'Unavailable')
    indicators[2].metric('Positive reviews', fmt(restaurant['positive_percentage'], 1, '%'))
    indicators[3].metric('Negative reviews', fmt(restaurant['negative_percentage'], 1, '%'))

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

    # The radio stores its value in session_state, so the header can adapt before it renders.
    current_page = st.session_state.get('active_page', PAGE_DIAGNOSIS)
    render_header(compact=current_page != PAGE_DIAGNOSIS)

    page = st.sidebar.radio('Choose a view', PAGES, label_visibility='collapsed', key='active_page')
    st.sidebar.caption('Use the arrow at the top left to hide or show this menu.')
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
    st.caption(f'Historical snapshot: alert window ends {snapshot}; latest review {last_review}. '
               'These results do not describe current restaurant performance.')

    if page == PAGE_MARKET:
        render_market_explorer(groups, membership, diagnostics)
    elif page == PAGE_CLASSIFIER:
        render_classifier()
    elif page == PAGE_METHODOLOGY:
        render_methodology(snapshot, last_review)
    else:
        render_diagnosis(diagnostics, membership, groups, config)

    render_footer('Madrid Restaurant Intelligence · Historical TripAdvisor review analysis. '
                  'Research project; not a live rating.')


main()
