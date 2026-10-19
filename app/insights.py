"""Explain review themes and turn supported signals into concrete checks."""
from html import escape

import pandas as pd
import streamlit as st

ACTIONS = {
    'Food': ('Review the dishes named in complaints. Check taste, temperature and consistency.',
             'Track whether the share of negative food mentions decreases.'),
    'Service': ('Review service at busy times and check staffing and follow-up.',
                'Track whether negative service mentions decrease in later reviews.'),
    'Atmosphere': ('Check noise, lighting, comfort and seating.',
                   'Track positive and negative atmosphere mentions in new reviews.'),
    'Price and value': ('Review portion sizes, menu clarity and perceived value.',
                        'Track whether negative price and value mentions decrease.'),
    'Waiting time': ('Measure waiting and serving times during busy periods.',
                      'Track complaints about waiting and slow service.'),
    'Cleanliness': ('Review cleaning routines and use a simple inspection log.',
                    'Track whether cleanliness complaints decrease.'),
}
ASPECT_NAMES = {
    'Comida y sabor': 'Food', 'Servicio y atención': 'Service',
    'Ambiente': 'Atmosphere', 'Precio y valor': 'Price and value',
    'Espera y rapidez': 'Waiting time', 'Limpieza': 'Cleanliness',
}


def prepare_aspects(frame):
    """Accept the detailed original export and the simpler English export."""
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    result['item_id'] = result['item_id'].astype(str)
    result['aspect'] = result['aspect'].replace(ASPECT_NAMES)
    if 'negative_percentage' not in result and 'share_of_negative_reviews' in result:
        # The simpler file counts negative mentions only; it cannot establish topic polarity.
        result['negative_percentage'] = pd.NA
    if 'support_level' not in result:
        result['support_level'] = pd.cut(
            result['mentions'], bins=[0, 4, 9, 29, float('inf')],
            labels=['Insufficient', 'Low', 'Medium', 'High'])
    return result


def supported_aspects(aspects, restaurant, minimum_mentions=5):
    if aspects.empty:
        return aspects.copy()
    return aspects.loc[
        aspects['item_id'].eq(str(restaurant['item_id'])) &
        aspects['mentions'].ge(minimum_mentions)
    ].copy()


def temporal_drivers(aspects):
    required = {'temporal_aspect_evaluable', 'temporal_negative_change',
                'previous_mentions', 'recent_mentions', 'previous_negative_percentage',
                'recent_negative_percentage'}
    if not required.issubset(aspects.columns):
        return aspects.iloc[0:0].copy()
    return aspects.loc[
        aspects['temporal_aspect_evaluable'].fillna(False) &
        aspects['temporal_negative_change'].gt(0)
    ].sort_values(['temporal_negative_change', 'recent_mentions'], ascending=False).copy()


def build_action_plan(restaurant, groups, aspects):
    """Rank practical checks by alert, thematic support and peer gaps."""
    selected = supported_aspects(aspects, restaurant)
    drivers = temporal_drivers(selected)
    priorities = []
    strengths = []
    if bool(restaurant['alert_evaluable']) and str(restaurant['alert_level']) != 'No alert':
        window_support = restaurant.get('minimum_window_reviews', 0)
        if pd.isna(window_support):
            window_support = 0
        priorities.append({
            'score': 100 if str(restaurant['alert_level']) == 'Critical alert' else 85,
            'title': 'Check the historical deterioration',
            'evidence': f"The mean rating changed {restaurant['rating_change']:+.2f} points "
                        f"and the negative share changed "
                        f"{restaurant['negative_percentage_point_change']:+.1f} points. "
                        f"The smaller period contains {int(window_support)} reviews.",
            'action': 'Read the negative reviews from the later period and compare them '
                      'with staff, menu or operating changes at that time.',
            'measurement': 'After collecting new reviews, repeat the same comparison '
                           'and check whether the thresholds are still met.',
        })
        for row in drivers.head(2).itertuples():
            action, measurement = ACTIONS.get(row.aspect, ('Read the relevant reviews.',
                                                            'Review new mentions.'))
            priorities.append({
                'score': 88 + float(row.temporal_negative_change),
                'title': f'Check {row.aspect.lower()}',
                'evidence': f"Negative mentions moved from "
                            f"{row.previous_negative_percentage:.1f}% to "
                            f"{row.recent_negative_percentage:.1f}% "
                            f"({int(row.previous_mentions)} and {int(row.recent_mentions)} "
                            'mentions in the two periods).',
                'action': action, 'measurement': measurement,
            })
    detailed = {'negative_reviews', 'positive_reviews', 'positive_percentage',
                'negative_percentage'}.issubset(selected.columns)
    if detailed:
        candidates = selected.loc[
            selected['negative_reviews'].ge(3) &
            selected['negative_percentage'].ge(max(20., float(restaurant['negative_percentage'])))
        ].sort_values(['negative_percentage', 'negative_reviews'], ascending=False).head(2)
        for row in candidates.itertuples():
            if row.aspect in set(drivers['aspect']):
                continue
            action, measurement = ACTIONS.get(row.aspect, ('Read the relevant reviews.',
                                                            'Track the same theme in new reviews.'))
            priorities.append({
                'score': 75 + float(row.negative_percentage) / 10,
                'title': f'Improve {row.aspect.lower()}',
                'evidence': f'{int(row.negative_reviews)} of {int(row.mentions)} reviews '
                            f'mentioning this theme are negative ({row.negative_percentage:.1f}%).',
                'action': action, 'measurement': measurement,
            })
        strong = selected.loc[
            selected['positive_reviews'].ge(3) &
            selected['positive_percentage'].ge(max(50., float(restaurant['positive_percentage'])))
        ].sort_values(['positive_percentage', 'positive_reviews'], ascending=False).head(2)
        for row in strong.itertuples():
            strengths.append({'title': row.aspect,
                              'evidence': f'{int(row.positive_reviews)} of '
                                          f'{int(row.mentions)} mentions are in positive reviews.'})
    elif not selected.empty:
        for row in selected.sort_values('mentions', ascending=False).head(2).itertuples():
            action, measurement = ACTIONS.get(row.aspect, ('Read recent reviews.',
                                                            'Track later reviews.'))
            priorities.append({'score': 60 + min(int(row.mentions), 30) / 10,
                               'title': f'Review {row.aspect.lower()}',
                               'evidence': f'{int(row.mentions)} negative reviews mention this theme. '
                                           'The simple export does not measure its share of all mentions.',
                               'action': action, 'measurement': measurement})
    if not groups.empty:
        group = groups.sort_values('group_restaurants', ascending=False).iloc[0]
        if pd.isna(group['rating_gap']):
            pass
        elif group['rating_gap'] < -0.10:
            priorities.append({'score': 60 + abs(group['rating_gap']) * 10,
                               'title': 'Close the rating gap',
                               'evidence': f"The restaurant is {abs(group['rating_gap']):.2f} "
                                           f"points below other {group['group_label']} restaurants.",
                               'action': 'Review recurring complaints alongside peer results.',
                               'measurement': 'Compare the gap again after collecting new reviews.'})
        elif group['rating_gap'] > 0.10:
            strengths.append({'title': 'Strong rating relative to peers',
                              'evidence': f"Rating is {group['rating_gap']:.2f} points above "
                                          f"other {group['group_label']} restaurants."})
        if pd.isna(group['negative_gap']):
            pass
        elif group['negative_gap'] > 2:
            priorities.append({'score': 60 + group['negative_gap'],
                               'title': 'Reduce negative reviews',
                               'evidence': f"Negative share exceeds similar restaurants by "
                                           f"{group['negative_gap']:.1f} percentage points.",
                               'action': 'Start with the best supported complaint theme.',
                               'measurement': 'Recheck the negative review gap later.'})
        elif group['negative_gap'] < -2:
            strengths.append({'title': 'Lower negative share than peers',
                              'evidence': f"Negative share is "
                                          f"{abs(group['negative_gap']):.1f} points below similar restaurants."})
    if not priorities:
        priorities = [{'score': 0, 'title': 'Keep monitoring the reviews',
                       'evidence': 'No material gap is supported by the available data.',
                       'action': 'Maintain working practices and read new reviews.',
                       'measurement': 'Update the diagnosis when new reviews are available.'}]
    return sorted(priorities, key=lambda item: item['score'], reverse=True)[:3], strengths[:3], drivers


def render_restaurant_insights(restaurant, groups, aspects):
    """Show a decision summary, temporal drivers, actions and strengths."""
    priorities, strengths, drivers = build_action_plan(restaurant, groups, aspects)
    group_note = ''
    if not groups.empty and groups[['rating_gap', 'negative_gap']].notna().all(axis=None):
        group = groups.sort_values('group_restaurants', ascending=False).iloc[0]
        group_note = (f" Against other {group['group_label']} restaurants, the rating gap is "
                      f"{group['rating_gap']:+.2f} and the negative share gap "
                      f"is {group['negative_gap']:+.1f} points.")
    summary = f"{restaurant['negative_percentage']:.1f}% of the restaurant's historical "
    summary += f"reviews are negative.{group_note} First check: {priorities[0]['title'].lower()}."
    st.markdown('<article class="decision-summary"><span class="card-label">Decision summary</span>'
                f'<p>{escape(summary)}</p></article>', unsafe_allow_html=True)

    st.markdown('<section class="driver-section"><span class="section-eyebrow">Historical signals</span>'
                '<h2>What changed in the reviews?</h2><p>Compare themes in the earlier and later '
                'six-month periods. A change does not establish its cause.</p></section>',
                unsafe_allow_html=True)
    if not bool(restaurant['alert_evaluable']):
        st.info('Too few reviews were available in the two periods to evaluate a change.')
    elif str(restaurant['alert_level']) == 'No alert':
        st.success('No historical deterioration threshold was reached.')
    elif drivers.empty:
        st.info('No theme has at least three mentions in both periods with a rising '
                'negative share. Read the later reviews directly.')
    else:
        for row in drivers.head(3).itertuples():
            st.markdown('<article class="driver-card"><div><span class="card-label">Theme to check</span>'
                        f'<h3>{escape(str(row.aspect))}</h3><p>Negative share rose by '
                        f'<strong>{row.temporal_negative_change:+.1f} pp</strong>.</p></div>'
                        '<div class="driver-comparison"><div><span>Earlier period</span>'
                        f'<strong>{row.previous_negative_percentage:.1f}%</strong>'
                        f'<small>{int(row.previous_mentions)} mentions</small></div>'
                        '<div class="driver-arrow">→</div><div><span>Later period</span>'
                        f'<strong>{row.recent_negative_percentage:.1f}%</strong>'
                        f'<small>{int(row.recent_mentions)} mentions</small></div></div></article>',
                        unsafe_allow_html=True)
    st.caption('Keyword themes summarize review text. Review rating gives each full review '
               'its sentiment. Theme change is an association, not a verified cause.')

    st.markdown('<section class="action-section"><span class="section-eyebrow">Action plan</span>'
                '<h2>What should you check first?</h2><p>Evidence, a practical action and a '
                'way to check improvement for each priority.</p></section>', unsafe_allow_html=True)
    for position, item in enumerate(priorities, 1):
        st.markdown(f'<article class="priority-card"><div class="priority-card__head">'
                    f'<span class="priority-number">{position:02d}</span><div>'
                    f'<span class="card-label">Priority</span><h3>{escape(item["title"])}</h3></div></div>'
                    '<div class="priority-evidence"><span class="card-label">Evidence</span>'
                    f'<p>{escape(item["evidence"])}</p></div><div class="priority-grid">'
                    '<div><span class="card-label">Suggested check</span>'
                    f'<p>{escape(item["action"])}</p></div><div>'
                    '<span class="card-label">How to measure</span>'
                    f'<p>{escape(item["measurement"])}</p></div></div></article>',
                    unsafe_allow_html=True)
    st.markdown('<section class="strength-section"><span class="section-eyebrow">Strengths</span>'
                '<h2>What should you keep doing?</h2></section>', unsafe_allow_html=True)
    if strengths:
        for item in strengths:
            st.markdown(f'<article class="strength-card"><h3>{escape(item["title"])}</h3>'
                        f'<p>{escape(item["evidence"])}</p></article>', unsafe_allow_html=True)
    else:
        st.info('The available themes do not support a clear strength for this restaurant.')
    st.caption('Suggested checks support decisions; they are not proof that an action will change ratings.')
