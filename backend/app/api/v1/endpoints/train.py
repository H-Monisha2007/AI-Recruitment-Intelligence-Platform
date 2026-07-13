"""
ML Training endpoint — train supervised classifiers on a CSV dataset.
"""
from __future__ import annotations
import io
import os
import time

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

from app.auth.dependencies import require_recruiter
from app.core.config import settings
from app.core.exceptions import BadRequestException
from app.core.logging_config import get_logger
from app.database.models import User
from app.schemas import TrainMetrics, TrainResponse
from app.services.ml_service import clean_resume

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=TrainResponse, summary="Train ML classifiers on a labelled resume dataset", tags=["train"])
async def train_models(
    file: UploadFile = File(..., description="CSV with 'Resume' and 'Category' columns"),
    current_user: User = Depends(require_recruiter),
):
    t0 = time.perf_counter()
    content = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise BadRequestException(f"Failed to parse CSV: {exc}")

    if "Resume" not in df.columns or "Category" not in df.columns:
        raise BadRequestException("Dataset must contain 'Resume' and 'Category' columns")

    df = df.dropna(subset=["Resume", "Category"])
    if len(df) < 20:
        raise BadRequestException("Dataset too small — need at least 20 labelled samples")

    df["cleaned"] = df["Resume"].apply(clean_resume)

    le = LabelEncoder()
    y = le.fit_transform(df["Category"])
    tfidf = TfidfVectorizer(sublinear_tf=True, stop_words="english", max_features=1500)
    X = tfidf.fit_transform(df["cleaned"]).toarray()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model_zoo = {
        "Logistic Regression": LogisticRegression(max_iter=1000, multi_class="ovr"),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Support Vector Machine": SVC(kernel="linear", probability=True),
    }

    metrics_list: list[TrainMetrics] = []
    best_acc, best_model, best_name = 0.0, None, ""

    for name, model in model_zoo.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc   = accuracy_score(y_test, y_pred)
        prec  = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec   = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1    = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        metrics_list.append(TrainMetrics(Model=name, Accuracy=f"{acc*100:.2f}%", Precision=f"{prec*100:.2f}%", Recall=f"{rec*100:.2f}%", F1_Score=f"{f1*100:.2f}%"))
        if acc > best_acc:
            best_acc, best_model, best_name = acc, model, name

    os.makedirs(settings.ML_MODELS_DIR, exist_ok=True)
    joblib.dump(best_model, os.path.join(settings.ML_MODELS_DIR, "best_model.pkl"))
    joblib.dump(tfidf,      os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl"))
    joblib.dump(le,         os.path.join(settings.ML_MODELS_DIR, "label_encoder.pkl"))

    elapsed = time.perf_counter() - t0
    logger.info("ML training completed: best=%s acc=%.2f%% time=%.1fs", best_name, best_acc * 100, elapsed)

    return TrainResponse(
        success=True,
        message=f"Training complete. Best: {best_name} ({best_acc*100:.1f}%)",
        metrics=metrics_list,
        best_model=best_name,
        training_time_seconds=round(elapsed, 2),
    )