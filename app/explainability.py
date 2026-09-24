"""Exact explanations for the TF-IDF + LinearSVC sentiment pipeline.

The final model is linear, so its decision score for class k is

    score_k(text) = intercept_k + sum_j  weight_kj * tfidf_j(text)

Each term's contribution is therefore weight_kj * tfidf_j(text), and the
contributions plus the intercept add up exactly to the model's score.
This replaces LIME, which only approximated this linear model with random
perturbations: it was slower, changed between runs and needed a fidelity
metric (R²) to say how far it could be trusted.
"""

from functools import lru_cache
from time import perf_counter

import numpy as np

from app.inference import load_sentiment_model, validate_review_text


def _split_pipeline(sentiment_model):
    """Return (vectorizer, classifier) from the saved sklearn Pipeline."""
    return sentiment_model[:-1], sentiment_model[-1]


@lru_cache(maxsize=1)
def _feature_names():
    vectorizer, _ = _split_pipeline(load_sentiment_model())
    return np.asarray(vectorizer.get_feature_names_out())


def predict_normalized_scores(review_texts):
    """Softmax of the decision margins.

    These are relative scores for display, not calibrated probabilities.
    """
    decision_scores = np.atleast_2d(load_sentiment_model().decision_function(review_texts))
    shifted_scores = decision_scores - decision_scores.max(axis=1, keepdims=True)
    exponential_scores = np.exp(shifted_scores)
    return exponential_scores / exponential_scores.sum(axis=1, keepdims=True)


def explain_sentiment(review_text: str, num_features: int = 10, num_samples=None) -> dict:
    """Explain one prediction with exact per-term contributions.

    num_features: how many terms to return, ranked by absolute contribution.
    num_samples:  ignored; kept so existing callers (e.g. app/api.py) that
                  passed LIME's argument keep working.
    """
    start_time = perf_counter()

    normalized_text = validate_review_text(review_text)
    sentiment_model = load_sentiment_model()
    vectorizer, classifier = _split_pipeline(sentiment_model)

    classes = [str(label) for label in classifier.classes_]
    features = vectorizer.transform([normalized_text])            # 1 x n_features, sparse
    decision_scores = np.ravel(classifier.decision_function(features))

    predicted_index = int(np.argmax(decision_scores))
    predicted_sentiment = classes[predicted_index]
    runner_up_index = int(np.argsort(decision_scores)[-2])

    # Contributions of the terms present in this review to the predicted class score.
    present = features.indices
    tfidf_values = features.data
    weights = classifier.coef_[predicted_index]
    weights = weights.toarray().ravel() if hasattr(weights, 'toarray') else np.ravel(weights)
    contributions = tfidf_values * weights[present]
    intercept = float(np.ravel(classifier.intercept_)[predicted_index])

    # Exactness check: contributions + intercept must equal the model score.
    reconstructed = float(contributions.sum() + intercept)
    if not np.isclose(reconstructed, decision_scores[predicted_index], atol=1e-4):
        raise RuntimeError('The explanation does not reproduce the model score.')

    order = np.argsort(-np.abs(contributions))
    shown = order[:num_features]
    names = _feature_names()

    terms = [
        {
            'term': str(names[present[i]]),
            'contribution': round(float(contributions[i]), 4),
            'effect': (f'Supports {predicted_sentiment}' if contributions[i] > 0
                       else f'Opposes {predicted_sentiment}'),
        }
        for i in shown
        if contributions[i] != 0
    ]

    normalized_scores = predict_normalized_scores([normalized_text])[0]
    explanation_seconds = perf_counter() - start_time

    return {
        'sentiment': predicted_sentiment,
        'runner_up': classes[runner_up_index],
        'decision_score': round(float(decision_scores[predicted_index]), 4),
        'margin_over_runner_up': round(
            float(decision_scores[predicted_index] - decision_scores[runner_up_index]), 4),
        'intercept': round(intercept, 4),
        'other_terms_contribution': round(float(contributions[order[num_features:]].sum()), 4),
        'terms_in_review': int(len(present)),
        'normalized_class_score': round(float(normalized_scores[predicted_index]), 4),
        'class_scores': {label: round(float(score), 4)
                         for label, score in zip(classes, decision_scores)},
        'method': 'exact_linear',
        # Exact by construction; kept for callers that still read LIME's fidelity field.
        'local_fidelity_r2': 1.0,
        'explanation_seconds': round(explanation_seconds, 4),
        'terms': terms,
    }
