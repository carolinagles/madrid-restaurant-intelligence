"""Prepare bilingual review themes when the earlier export has mismatched labels."""
import re

import numpy as np
import pandas as pd

PATTERNS = {
    'Food': r'\b(?:food|meal|dishes?|taste|flavou?r|comida|platos?|sabor|cocina)\b',
    'Service': r'\b(?:service|staff|waiter|waitress|servicio|atenci[oó]n|camarer[oa]s?|personal)\b',
    'Atmosphere': r'\b(?:atmosphere|ambience|music|terrace|ambiente|m[uú]sica|terraza)\b',
    'Price and value': r'\b(?:price|expensive|cheap|value|precio|car[oa]s?|barat[oa]s?)\b',
    'Waiting time': r'\b(?:wait(?:ing|ed)?|delay|slow|espera|tard[oa]|lent[oa])\b',
    'Cleanliness': r'\b(?:clean|dirty|hygiene|limpi[oa]|suci[oa]|higiene)\b',
}


def build_review_aspects(corpus, config):
    """Summarize historical and temporal mentions using English rating labels."""
    required = {'item_id', 'review_id', 'review_text', 'sentiment', 'date'}
    if not required.issubset(corpus.columns):
        raise ValueError(f'Modeling corpus needs: {sorted(required - set(corpus.columns))}')
    dates = pd.to_datetime(corpus['date'])
    last_complete = pd.Timestamp(config['temporal_alert']['as_of_date'])
    later_start = last_complete.replace(day=1) - pd.DateOffset(months=5)
    earlier_start = later_start - pd.DateOffset(months=6)
    period = np.select([dates.ge(earlier_start) & dates.lt(later_start),
                        dates.ge(later_start) & dates.le(last_complete)],
                       ['previous', 'recent'], default='outside')
    texts = corpus['review_text'].fillna('').astype(str)
    labels = corpus['sentiment'].astype(str)
    frames = []
    for aspect, pattern in PATTERNS.items():
        matches = texts.str.contains(pattern, flags=re.IGNORECASE, regex=True, na=False)
        if not matches.any():
            continue
        found = pd.DataFrame({'item_id': corpus.loc[matches, 'item_id'].to_numpy(),
                              'sentiment': labels.loc[matches].to_numpy(),
                              'period': period[matches.to_numpy()]})
        found['negative'] = found['sentiment'].eq('Negative').astype(int)
        found['neutral'] = found['sentiment'].eq('Neutral').astype(int)
        found['positive'] = found['sentiment'].eq('Positive').astype(int)
        total = found.groupby('item_id', observed=True).agg(
            mentions=('negative', 'size'), negative_reviews=('negative', 'sum'),
            neutral_reviews=('neutral', 'sum'), positive_reviews=('positive', 'sum'))
        windows = found.loc[found['period'].ne('outside')].groupby(
            ['item_id', 'period'], observed=True).agg(
                mentions=('negative', 'size'), negative_reviews=('negative', 'sum'))
        wide = windows.unstack('period', fill_value=0)
        wide.columns = [f'{period_name}_{measure}' for measure, period_name in wide.columns]
        total = total.join(wide, how='left').fillna(0)
        for name in ['previous', 'recent']:
            for measure in ['mentions', 'negative_reviews']:
                field = f'{name}_{measure}'
                if field not in total:
                    total[field] = 0
            total[f'{name}_negative_percentage'] = (
                total[f'{name}_negative_reviews'] / total[f'{name}_mentions'].replace(0, np.nan) * 100)
        for name in ['negative', 'neutral', 'positive']:
            total[f'{name}_percentage'] = total[f'{name}_reviews'] / total['mentions'] * 100
        total['temporal_aspect_evaluable'] = total[
            ['previous_mentions', 'recent_mentions']].min(axis=1).ge(3)
        total['temporal_negative_change'] = (
            total['recent_negative_percentage'] - total['previous_negative_percentage'])
        total['support_level'] = pd.cut(total['mentions'], bins=[0, 4, 9, 29, np.inf],
                                        labels=['Insufficient', 'Low', 'Medium', 'High']).astype(str)
        total['aspect'] = aspect
        frames.append(total.reset_index())
    if not frames:
        return pd.DataFrame(columns=['item_id', 'aspect', 'mentions'])
    return pd.concat(frames, ignore_index=True).sort_values(
        ['item_id', 'mentions'], ascending=[True, False]).reset_index(drop=True)
