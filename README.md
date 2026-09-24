# Madrid Restaurant Intelligence · full dashboard

This version restores the detailed content of the earlier application and arranges it into two pages: **Restaurant diagnosis** and **Market & Top 10**. The restaurant view has tabs for overview and action plan, peer comparison, historical alerts, a review classifier, and methodology.

## Replace the current app

1. From this archive, copy `streamlit_app.py` and the complete `app/` folder into the root of your existing project. Replace the old files when your computer asks. Keep your existing `data/` and `artifacts/` folders.
2. In a new terminal, from the project root, start the app with `python -m streamlit run streamlit_app.py --server.port 10001`.
3. Open `http://localhost:10001`.

The first load can take a few minutes if the earlier theme file was made with Spanish labels while the cleaned corpus uses English labels. The app rebuilds the topic table from `data/modeling_corpus.parquet` and saves `data/restaurant_review_aspects_EN.parquet` for later launches. It does not retrain the model or rerun any notebook.

The app needs the existing model in `artifacts/models/sentiment_tfidf_linear_svc.joblib`, `data/project_config.json`, `data/modeling_corpus.parquet`, and the three prepared restaurant and benchmark Parquet files. Dependencies are in `requirements.txt`.

Historical alerts refer to two six month windows ending May 2023; the score of a text classifier is not a calibrated probability. Keywords are descriptive and do not establish a cause of dissatisfaction.
