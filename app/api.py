"""REST API for the restaurant review sentiment model.

Run from the project root:  uvicorn app.api:app --reload
Interactive docs:           http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.explainability import explain_sentiment
from app.inference import (MAX_CHARACTERS, MIN_CHARACTERS, ModelUnavailableError,
                           get_model_information, predict_sentiment)


class PredictionRequest(BaseModel):
    review_text: str = Field(min_length=MIN_CHARACTERS, max_length=MAX_CHARACTERS,
                             examples=['The food was good, but the service was slow.'])


class ExplanationRequest(PredictionRequest):
    num_features: int = Field(default=10, ge=1, le=50)


class PredictionResponse(BaseModel):
    sentiment: str
    decision_scores: dict[str, float]
    model_name: str
    model_version: str
    prediction_milliseconds: float


class TermContribution(BaseModel):
    term: str
    contribution: float
    effect: str


class ExplanationResponse(BaseModel):
    sentiment: str
    runner_up: str
    decision_score: float
    margin_over_runner_up: float
    intercept: float
    other_terms_contribution: float
    terms_in_review: int
    class_scores: dict[str, float]
    method: str
    explanation_seconds: float
    terms: list[TermContribution]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    model_version: str
    classes: list[str]


app = FastAPI(
    title='Restaurant Sentiment API',
    description=('Classifies Spanish and English restaurant reviews as Negative, Neutral or '
                 'Positive. Labels were learned from star ratings; decision scores are not '
                 'calibrated probabilities.'),
    version='1.1.0',
)


def _run(function, *args, **kwargs):
    """Map model and input errors to the right HTTP status codes."""
    try:
        return function(*args, **kwargs)
    except ModelUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get('/health', response_model=HealthResponse)
def health_check():
    return {'status': 'ok', **_run(get_model_information)}


@app.post('/api/v1/sentiment', response_model=PredictionResponse)
def predict_review_sentiment(request: PredictionRequest):
    return _run(predict_sentiment, request.review_text)


@app.post('/api/v1/sentiment/explain', response_model=ExplanationResponse)
def explain_review_sentiment(request: ExplanationRequest):
    """Exact per-term contributions to the predicted label's score."""
    return _run(explain_sentiment, request.review_text, num_features=request.num_features)
