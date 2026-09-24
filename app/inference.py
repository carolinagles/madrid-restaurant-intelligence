"""Load the saved sentiment pipeline and classify single reviews."""
from functools import lru_cache
from os import getenv
from pathlib import Path
from time import perf_counter

import joblib
import numpy as np

PROJECT_PATH = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_PATH / 'artifacts' / 'models' / 'sentiment_tfidf_linear_svc.joblib'
MODEL_PATH = Path(getenv('SENTIMENT_MODEL_PATH', str(DEFAULT_MODEL_PATH)))
MODEL_NAME = 'sentiment_tfidf_linear_svc'
MODEL_VERSION = getenv('MODEL_VERSION', '1.0.0')
VALID_SENTIMENTS = {'Negative', 'Neutral', 'Positive'}
MIN_CHARACTERS, MAX_CHARACTERS = 3, 5_000

# Backwards-compatible lowercase names used by older modules and notebooks.
project_path, default_model_path, model_path = PROJECT_PATH, DEFAULT_MODEL_PATH, MODEL_PATH
model_name, model_version, valid_sentiments = MODEL_NAME, MODEL_VERSION, VALID_SENTIMENTS


class ModelUnavailableError(RuntimeError):
    """The model file is missing or cannot be loaded."""


@lru_cache(maxsize=1)
def load_sentiment_model():
    """Load the pipeline once and check it has the expected classes."""
    if not MODEL_PATH.exists():
        raise ModelUnavailableError(f'Model file not found: {MODEL_PATH}')
    try:
        pipeline = joblib.load(MODEL_PATH)
    except Exception as error:  # corrupted file, incompatible scikit-learn version...
        raise ModelUnavailableError(f'Could not load the model: {error}') from error
    classes = {str(label) for label in pipeline[-1].classes_}
    if classes != VALID_SENTIMENTS:
        raise ModelUnavailableError(f'Unexpected model classes: {sorted(classes)}')
    return pipeline


def validate_review_text(review_text: str) -> str:
    """Validate and normalize the input review."""
    if not isinstance(review_text, str):
        raise TypeError('review_text must be a string')
    normalized_text = ' '.join(review_text.split())
    if len(normalized_text) < MIN_CHARACTERS:
        raise ValueError(f'review_text must contain at least {MIN_CHARACTERS} characters')
    if len(normalized_text) > MAX_CHARACTERS:
        raise ValueError(f'review_text must be {MAX_CHARACTERS:,} characters or less')
    return normalized_text


def get_model_information() -> dict:
    """Return information about the loaded model."""
    classifier = load_sentiment_model()[-1]
    return {'model_loaded': True, 'model_name': MODEL_NAME, 'model_version': MODEL_VERSION,
            'classes': [str(label) for label in classifier.classes_]}


def predict_sentiment(review_text: str) -> dict:
    """Predict the label for one review.

    The label is the class with the highest decision score, which is exactly what
    LinearSVC.predict does; computing the scores once avoids vectorizing the text twice.
    """
    normalized_text = validate_review_text(review_text)
    sentiment_model = load_sentiment_model()

    start_time = perf_counter()
    raw_scores = np.ravel(sentiment_model.decision_function([normalized_text]))
    prediction_milliseconds = (perf_counter() - start_time) * 1_000

    classes = [str(label) for label in sentiment_model[-1].classes_]
    predicted_sentiment = classes[int(np.argmax(raw_scores))]
    return {
        'sentiment': predicted_sentiment,
        'decision_scores': {label: round(float(score), 4) for label, score in zip(classes, raw_scores)},
        'model_name': MODEL_NAME,
        'model_version': MODEL_VERSION,
        'prediction_milliseconds': round(prediction_milliseconds, 4),
    }
