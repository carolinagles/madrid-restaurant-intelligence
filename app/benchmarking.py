"""Restaurant peer comparisons and the interactive market explorer."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.ui import COLORS, FULL_WIDTH, show_chart

FOREST = COLORS['forest']
MINIMUM_RANKING_REVIEWS = 30

# column, ascending, axis label, number format for bar labels
TOP_TEN_RULES = {
    'Highest rating (adjusted for review volume)': ('adjusted_rating', False, 'Adjusted rating', '.2f'),
    'Highest average rating': ('mean_review_rating', False, 'Rating', '.2f'),
    'Highest positive share': ('positive_percentage', False, 'Positive reviews (%)', '.1f'),
    'Most reviews': ('reviews', False, 'Reviews', ',.0f'),
    'Largest historical improvement': ('rating_change', False, 'Rating change', '+.2f'),
    'Largest historical decline': ('rating_change', True, 'Rating change', '+.2f'),
}
TOP_TEN_EXPLANATIONS = {
    'Highest rating (adjusted for review volume)':
        'Pulls each rating toward the group average in proportion to how few reviews it has, '
        'so 40 excellent reviews do not outrank 2,000 almost-as-excellent ones.',
    'Highest average rating': 'Ranks restaurants by their plain mean review rating.',
    'Highest positive share': 'Ranks by the share of reviews rated 4 or 5 stars.',
    'Most reviews': 'Ranks by volume. More reviews do not mean better service.',
    'Largest historical improvement': 'Ranks by the observed rating increase between two six-month windows.',
    'Largest historical decline': 'Ranks by the observed rating decrease. This is not a forecast.',
}


def get_group_restaurants(specialty, price_interval, membership, diagnostics,
                          minimum_reviews=MINIMUM_RANKING_REVIEWS):
    """Return peer restaurants with enough reviews to rank."""
    members = membership.loc[
        membership['specialty'].eq(specialty) & membership['price_interval'].eq(price_interval),
        ['item_id']
    ].drop_duplicates()
    peers = members.merge(diagnostics, on='item_id', how='inner', validate='one_to_one')
    return peers.loc[peers['reviews'].ge(minimum_reviews)].copy()


def get_restaurant_groups(restaurant, membership, groups, diagnostics=None):
    """Return the eligible specialty and price groups for one restaurant.

    With `diagnostics`, every gap is measured against the same reference used in the
    peer comparison tab: other restaurants in the group with at least 30 reviews,
    excluding the selected restaurant. Without it, the precomputed group means are used
    (they include every member, however few reviews it has).
    """
    item_id = str(restaurant['item_id'])
    selected = membership.loc[membership['item_id'].eq(item_id),
                              ['specialty', 'price_interval']].drop_duplicates()
    result = selected.merge(groups, on=['specialty', 'price_interval'],
                            how='inner', validate='one_to_one').copy()
    if result.empty:
        return result
    result['group_label'] = result['specialty'] + ' · ' + result['price_interval']

    if diagnostics is not None:
        references = []
        for row in result.itertuples():
            peers = get_group_restaurants(row.specialty, row.price_interval, membership, diagnostics)
            peers = peers.loc[peers['item_id'].ne(item_id)]
            references.append({'peer_restaurants': len(peers),
                               'peer_mean_rating': peers['mean_review_rating'].mean(),
                               'peer_negative_percentage': peers['negative_percentage'].mean()})
        result = pd.concat([result, pd.DataFrame(references, index=result.index)], axis=1)
    else:
        result['peer_restaurants'] = result['group_restaurants']
        result['peer_mean_rating'] = result['group_mean_rating']
        result['peer_negative_percentage'] = result['group_negative_percentage']

    result['rating_gap'] = restaurant['mean_review_rating'] - result['peer_mean_rating']
    result['negative_gap'] = restaurant['negative_percentage'] - result['peer_negative_percentage']
    return result


def build_executive_summary(restaurant, restaurant_groups):
    """Explain the diagnosis without claiming that the alert is current."""
    support = restaurant.get('diagnostic_support')
    support_text = 'unrated' if pd.isna(support) else str(support).lower()
    parts = [f"The diagnosis uses {int(restaurant['reviews']):,} historical reviews "
             f"and has {support_text} evidence support."]
    if restaurant_groups.empty:
        parts.append('No eligible specialty and price peer group is available.')
    else:
        group = restaurant_groups.sort_values('group_restaurants', ascending=False).iloc[0]
        rating_gap, negative_gap = group['rating_gap'], group['negative_gap']
        if pd.notna(rating_gap) and pd.notna(negative_gap):
            parts.append(f"Compared with other {group['group_label']} restaurants, the rating is "
                         f"{abs(rating_gap):.2f} points {'higher' if rating_gap >= 0 else 'lower'} "
                         f"and the negative review share is {abs(negative_gap):.1f} percentage points "
                         f"{'higher' if negative_gap >= 0 else 'lower'}.")
    if not bool(restaurant['alert_evaluable']):
        parts.append('There are too few reviews in the two periods for an alert.')
    elif str(restaurant['alert_level']) == 'No alert':
        parts.append('No historical deterioration threshold was reached.')
    else:
        parts.append(f"Historical signal: {restaurant['alert_level']}.")
    return ' '.join(parts)


def render_benchmarking(restaurant, restaurant_groups, membership, diagnostics):
    st.subheader('Compare with similar restaurants')
    st.caption('Peers share a specialty and price range. Eligible groups have at least '
               '30 restaurants and 1,000 reviews. A restaurant may belong to several groups.')
    if restaurant_groups.empty:
        st.info('This restaurant does not belong to an eligible competitive group.')
        return
    group_label = st.selectbox('Peer group', restaurant_groups['group_label'].tolist(),
                               key='benchmark_group')
    group = restaurant_groups.loc[restaurant_groups['group_label'].eq(group_label)].iloc[0]
    peers = get_group_restaurants(group['specialty'], group['price_interval'], membership, diagnostics)
    ranked = peers.dropna(subset=['mean_review_rating']).sort_values(
        ['mean_review_rating', 'reviews'], ascending=[False, False]).reset_index(drop=True)
    matches = ranked.index[ranked['item_id'].eq(str(restaurant['item_id']))].tolist()
    position = (f'{matches[0] + 1} of {len(ranked)}' if matches
                else f'Not ranked (under {MINIMUM_RANKING_REVIEWS} reviews)')

    rating_gap, negative_gap = group['rating_gap'], group['negative_gap']
    columns = st.columns(4)
    columns[0].metric('Rank among eligible peers', position)
    columns[1].metric(f'Other peers with {MINIMUM_RANKING_REVIEWS}+ reviews',
                      f"{int(group['peer_restaurants']):,}")
    columns[2].metric('Rating gap', f'{rating_gap:+.2f}' if pd.notna(rating_gap) else 'Unavailable',
                      help='Positive is better; the selected restaurant is excluded from the reference.')
    columns[3].metric('Negative review gap', f'{negative_gap:+.1f} pp' if pd.notna(negative_gap)
                      else 'Unavailable', help='Positive means more negative reviews than peers.')

    if int(group['peer_restaurants']) > 0:
        comparison = pd.DataFrame({
            'Measure': ['Average rating', 'Negative share (%)'],
            'Restaurant': [restaurant['mean_review_rating'], restaurant['negative_percentage']],
            'Other peers': [group['peer_mean_rating'], group['peer_negative_percentage']],
        }).melt('Measure', var_name='Reference', value_name='Value')
        figure = px.bar(comparison, x='Reference', y='Value', color='Reference', facet_col='Measure',
                        text_auto='.1f', labels={'Reference': '', 'Value': ''},
                        color_discrete_map={'Restaurant': FOREST, 'Other peers': COLORS['sage']})
        figure.update_yaxes(matches=None)
        show_chart(figure, height=360)
        st.caption('The peer reference gives each other restaurant equal weight. '
                   f'The ranking includes restaurants with at least {MINIMUM_RANKING_REVIEWS} reviews.')

    with st.expander('All eligible groups for this restaurant'):
        st.dataframe(
            restaurant_groups[['group_label', 'group_restaurants', 'group_reviews',
                               'rating_gap', 'negative_gap']].rename(columns={
                'group_label': 'Peer group', 'group_restaurants': 'Restaurants',
                'group_reviews': 'Reviews', 'rating_gap': 'Rating gap',
                'negative_gap': 'Negative share gap (pp)'}),
            hide_index=True, **FULL_WIDTH,
            column_config={'Reviews': st.column_config.NumberColumn(format='%d'),
                           'Rating gap': st.column_config.NumberColumn(format='%+.2f'),
                           'Negative share gap (pp)': st.column_config.NumberColumn(format='%+.1f')})


def add_adjusted_rating(ranking, prior_reviews=MINIMUM_RANKING_REVIEWS):
    """Bayesian average: (n * mean + m * group mean) / (n + m)."""
    group_mean = ranking['mean_review_rating'].mean()
    reviews = ranking['reviews'].astype(float)
    ranking['adjusted_rating'] = ((reviews * ranking['mean_review_rating'] + prior_reviews * group_mean)
                                  / (reviews + prior_reviews))
    return ranking


def get_top_ranking(specialty, price_interval, criterion, membership, diagnostics):
    column, ascending, label, _ = TOP_TEN_RULES[criterion]
    ranking = get_group_restaurants(specialty, price_interval, membership, diagnostics)
    ranking = add_adjusted_rating(ranking.dropna(subset=['mean_review_rating']))
    ranking = ranking.dropna(subset=[column])
    if column == 'rating_change':
        ranking = ranking.loc[ranking['alert_evaluable']]
    ranking = ranking.sort_values([column, 'reviews'], ascending=[ascending, False]).reset_index(drop=True)
    ranking['position'] = ranking.index + 1
    return ranking, column, label


def render_market_explorer(groups, membership, diagnostics):
    st.markdown('''<section class="market-hero"><span class="section-eyebrow">Market explorer</span>
    <h1>Explore Madrid's restaurant market</h1>
    <p>Compare businesses with the same specialty and price range. See leaders,
    review volume and historical changes in reputation.</p></section>''', unsafe_allow_html=True)
    guide = st.columns(3)
    guide[0].info('**Comparable businesses**\n\nSame specialty and price range.')
    guide[1].info(f'**Ranking eligibility**\n\nAt least {MINIMUM_RANKING_REVIEWS} reviews per restaurant.')
    guide[2].info('**Use**\n\nA historical benchmark, not a recommendation to customers.')
    specialties = sorted(groups['specialty'].dropna().unique())
    if not specialties:
        st.info('No eligible peer groups are available.')
        return
    selectors = st.columns(3)
    specialty = selectors[0].selectbox('Specialty', specialties, key='market_specialty')
    prices = sorted(groups.loc[groups['specialty'].eq(specialty), 'price_interval'].dropna().unique())
    price = selectors[1].selectbox('Price range', prices, key='market_price')
    criterion = selectors[2].selectbox('Top 10 measure', list(TOP_TEN_RULES), key='market_measure')
    st.caption(TOP_TEN_EXPLANATIONS[criterion])

    ranking, column, label = get_top_ranking(specialty, price, criterion, membership, diagnostics)
    if ranking.empty:
        st.info('No restaurant has enough evidence for this measure.')
        return

    # Group figures use the same restaurants as the ranking (30+ reviews), so they are comparable.
    eligible = get_group_restaurants(specialty, price, membership, diagnostics)
    overview = st.columns(4)
    overview[0].metric('Ranked restaurants', f'{len(ranking):,}')
    overview[1].metric('Their reviews', f"{int(eligible['reviews'].sum()):,}")
    overview[2].metric('Average rating', f"{eligible['mean_review_rating'].mean():.2f}")
    overview[3].metric('Average negative share', f"{eligible['negative_percentage'].mean():.1f}%")

    top_ten = ranking.head(10).copy()
    # Restaurant names are not unique; the rank prefix keeps each bar separate.
    top_ten['label'] = (top_ten['position'].astype(str) + '. '
                        + top_ten['name'].astype(str).str.slice(0, 42))
    text_format = TOP_TEN_RULES[criterion][3]
    figure = px.bar(top_ten.sort_values('position', ascending=False), x=column, y='label',
                    orientation='h', color_discrete_sequence=[FOREST],
                    labels={column: label, 'label': ''}, title=f'Top 10: {criterion.lower()}')
    figure.update_traces(texttemplate=f'%{{x:{text_format}}}', textposition='outside',
                         cliponaxis=False)
    show_chart(figure, height=max(360, 42 * len(top_ten) + 120))

    columns = ['position', 'name', 'reviews', 'mean_review_rating', 'positive_percentage',
               'negative_percentage']
    if column not in columns:
        columns.insert(2, column)
    st.dataframe(
        top_ten[columns].rename(columns={
            'position': 'Rank', 'name': 'Restaurant', 'reviews': 'Reviews',
            'adjusted_rating': 'Adjusted rating', 'mean_review_rating': 'Average rating',
            'positive_percentage': 'Positive (%)', 'negative_percentage': 'Negative (%)',
            'rating_change': 'Rating change'}),
        hide_index=True, **FULL_WIDTH,
        column_config={'Reviews': st.column_config.NumberColumn(format='%d'),
                       'Adjusted rating': st.column_config.NumberColumn(format='%.2f'),
                       'Average rating': st.column_config.NumberColumn(format='%.2f'),
                       'Positive (%)': st.column_config.NumberColumn(format='%.1f'),
                       'Negative (%)': st.column_config.NumberColumn(format='%.1f'),
                       'Rating change': st.column_config.NumberColumn(format='%+.2f')})
    with st.expander('How the Top 10 is calculated'):
        st.markdown(f'Restaurants share the chosen specialty and price range. Groups need '
                    f'at least 30 restaurants and 1,000 reviews. Rankings require '
                    f'{MINIMUM_RANKING_REVIEWS} reviews per restaurant. The adjusted rating adds '
                    f'{MINIMUM_RANKING_REVIEWS} "average" reviews to every restaurant, which barely '
                    'moves places with thousands of reviews but tempers small samples. Historical '
                    'change uses two complete six-month periods. A position does not guarantee '
                    'future quality or financial performance.')
