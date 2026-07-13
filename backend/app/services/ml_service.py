"""
ML Service — semantic + keyword resume matching using sentence-transformers with
graceful TF-IDF fallback when GPU/model is unavailable.
"""
from __future__ import annotations

import functools
import os
import re
import time
from typing import Optional

import joblib
import numpy as np

from app.core.config import settings
from app.core.exceptions import MLServiceException
from app.core.logging_config import get_logger
from app.core.utils import clean_resume, remove_emojis

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Sentence-transformer (lazy-loaded at first use)                              #
# --------------------------------------------------------------------------- #

_sentence_model = None
_sentence_model_loaded = False


def _get_sentence_model():
    global _sentence_model, _sentence_model_loaded
    if _sentence_model_loaded:
        return _sentence_model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformer model: %s", settings.SENTENCE_MODEL_NAME)
        _sentence_model = SentenceTransformer(settings.SENTENCE_MODEL_NAME)
        logger.info("Sentence-transformer loaded successfully")
    except Exception as exc:
        logger.warning("Could not load sentence-transformer (%s). Falling back to TF-IDF.", exc)
        _sentence_model = None
    finally:
        _sentence_model_loaded = True
    return _sentence_model




# --------------------------------------------------------------------------- #
# Experience extraction                                                         #
# --------------------------------------------------------------------------- #

def extract_experience_years(resume_text: str) -> int:
    if not resume_text:
        return 0
    text_lower = resume_text.lower()
    patterns = [
        r"(\d+)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:exp(?:erience)?)?",
        r"experience[:\-]?\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = int(match.group(1))
            if 0 < value < 50:
                return value
    return 0


# --------------------------------------------------------------------------- #
# ATS score                                                                     #
# --------------------------------------------------------------------------- #

def advanced_ats_score(text: str) -> float:
    if not text:
        return 0.0
    score = 0.0
    text_lower = text.lower()
    for sec in ["experience", "education", "skills", "projects", "summary", "objective"]:
        if sec in text_lower:
            score += 12
    if re.search(r"[\w\.-]+@[\w\.-]+", text_lower):
        score += 15
    if re.search(r"\d{10,}", text_lower):
        score += 10
    for verb in ["developed", "designed", "implemented", "created", "led", "managed", "built"]:
        if verb in text_lower:
            score += 5
    for term in ["github", "aws", "docker", "api", "database", "kubernetes", "ci/cd"]:
        if term in text_lower:
            score += 3
    return min(score, 100.0)


# --------------------------------------------------------------------------- #
# ML keyword score                                                              #
# --------------------------------------------------------------------------- #

_ML_KEYWORDS = [
    "machine learning", "deep learning", "neural network", "tensorflow", "pytorch",
    "scikit-learn", "nlp", "computer vision", "transformers", "gradient boosting",
    "feature engineering", "model deployment", "hyperparameter", "cross validation",
    "random forest", "xgboost", "llm", "bert", "yolo", "opencv",
]


def ml_resume_classifier(resume_text: str) -> float:
    if not resume_text:
        return 0.0
    text_lower = resume_text.lower()
    hits = sum(1 for kw in _ML_KEYWORDS if kw in text_lower)
    return min(hits * 8.0, 100.0)


# --------------------------------------------------------------------------- #
# Skill matching                                                                #
# --------------------------------------------------------------------------- #

def skill_match_score(resume_text: str, job_skills: list[str]) -> tuple[list[str], list[str], float]:
    resume_lower = re.sub(r"[^\w\s]", "", resume_text.lower())
    found, missing = [], []
    for skill in job_skills:
        if skill.lower() in resume_lower:
            found.append(skill)
        else:
            missing.append(skill)
    total = len(job_skills)
    coverage = (len(found) / total * 100.0) if total > 0 else 0.0
    return found, missing, coverage


# --------------------------------------------------------------------------- #
# Semantic similarity                                                           #
# --------------------------------------------------------------------------- #

def _tfidf_similarity(resume_text: str, reference: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as cos_sim
        vect = TfidfVectorizer(stop_words="english", max_features=1000)
        matrix = vect.fit_transform([resume_text.lower(), reference.lower()])
        return float(cos_sim(matrix[0:1], matrix[1:2])[0][0]) * 100.0
    except Exception as exc:
        logger.error("TF-IDF similarity failed: %s", exc)
        return 0.0


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Return 0-100 cosine similarity. Uses sentence-transformers, falls back to TF-IDF."""
    model = _get_sentence_model()
    if model is not None:
        try:
            import numpy as np
            embs = model.encode([text_a, text_b], normalize_embeddings=True)
            score = float(np.dot(embs[0], embs[1])) * 100.0
            return max(0.0, min(score, 100.0))
        except Exception as exc:
            logger.warning("Sentence-transformer inference failed: %s", exc)
    return _tfidf_similarity(text_a, text_b)


def get_embedding(text: str) -> list[float] | None:
    model = _get_sentence_model()
    if model is None:
        return None
    try:
        emb = model.encode([text], normalize_embeddings=True)[0]
        return emb.tolist()
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        return None


# --------------------------------------------------------------------------- #
# Role data (config-driven, extensible)                                        #
# --------------------------------------------------------------------------- #

from app.core.roles import JOB_ROLES

_JOB_ROLES = JOB_ROLES


def get_all_job_roles() -> dict[str, dict]:
    """Return the canonical role catalog."""
    return _JOB_ROLES.copy()


def get_role_data(role_name: str) -> dict | None:
    """Look up role by exact name (strips leading emoji if present)."""
    clean = role_name.strip()
    if clean in _JOB_ROLES:
        return _JOB_ROLES[clean]
    # Try stripping emoji prefix
    for name, data in _JOB_ROLES.items():
        if name in clean or clean in name:
            return data
    return None


# --------------------------------------------------------------------------- #
# Role finding                                                                  #
# --------------------------------------------------------------------------- #

def find_best_roles(resume_text: str) -> list[list]:
    scores: dict[str, float] = {}
    for role, data in _JOB_ROLES.items():
        _, _, coverage = skill_match_score(resume_text, data["skills"])
        ml_boost = 15.0 if any(
            kw in resume_text.lower()
            for kw in ["machine learning", "deep learning", "nlp", "computer vision"]
        ) else 0.0
        role_type_bonus = 0.0
        if "ML" in role or "AI" in role:
            role_type_bonus = ml_resume_classifier(resume_text) * 0.2
        scores[role] = coverage * 0.6 + ml_boost * 0.2 + role_type_bonus * 0.2

    return [[r, s] for r, s in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]]


# --------------------------------------------------------------------------- #
# Resume review                                                                 #
# --------------------------------------------------------------------------- #

def comprehensive_resume_review(resume_text: str) -> dict:
    text_lower = resume_text.lower()
    sections = [s for s in ["experience", "education", "skills", "projects", "summary", "objective"] if s in text_lower]
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+", text_lower))
    has_phone = bool(re.search(r"\d{10,}", text_lower))
    action_verbs = ["developed", "designed", "implemented", "created", "led", "managed", "built", "deployed"]
    action_count = sum(1 for v in action_verbs if v in text_lower)
    has_quant = bool(re.search(r"\d+%|\d+x|\d+\s*(?:years?|months?)|saved\s+\$?\d+|increased\s+\d+", text_lower))
    wc = len(resume_text.split())
    length_status = "Ideal (150-400 words)" if 150 <= wc <= 400 else ("Too Short" if wc < 150 else "Too Long")
    tech_map = {
        "Python": ["python"], "ML/AI": ["machine learning", "tensorflow", "pytorch", "scikit-learn"],
        "Web": ["react", "javascript", "html", "css", "nodejs"], "Cloud": ["aws", "azure", "gcp"],
        "DevOps": ["docker", "kubernetes", "jenkins"], "Database": ["sql", "mongodb", "postgres", "mysql"],
    }
    tech_stack = [cat for cat, terms in tech_map.items() if any(t in text_lower for t in terms)]
    return {
        "sections_found": [s.title() for s in sections],
        "has_contact": has_email and has_phone,
        "action_verbs": action_count,
        "has_quant": has_quant,
        "word_count": wc,
        "length_status": length_status,
        "tech_stack": tech_stack,
        "has_github": "github" in text_lower,
        "has_portfolio": any(x in text_lower for x in ["portfolio", "personal website", "linkedin"]),
    }


# --------------------------------------------------------------------------- #
# Saved ML model prediction                                                     #
# --------------------------------------------------------------------------- #

def predict_role_from_model(resume_text: str) -> tuple[str | None, float, list]:
    model_path = os.path.join(settings.ML_MODELS_DIR, "best_model.pkl")
    vect_path  = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")
    enc_path   = os.path.join(settings.ML_MODELS_DIR, "label_encoder.pkl")
    if not all(os.path.exists(p) for p in [model_path, vect_path, enc_path]):
        return None, 0.0, []
    try:
        model  = joblib.load(model_path)
        vect   = joblib.load(vect_path)
        le     = joblib.load(enc_path)
        feats  = vect.transform([clean_resume(resume_text)]).toarray()
        probs  = model.predict_proba(feats)[0]
        top3_i = probs.argsort()[-3:][::-1]
        top3r  = le.inverse_transform(top3_i)
        top3p  = probs[top3_i]
        return str(top3r[0]), float(top3p[0]) * 100.0, [[str(r), float(p) * 100.0] for r, p in zip(top3r, top3p)]
    except Exception as exc:
        logger.error("Model prediction failed: %s", exc)
        return None, 0.0, []


# --------------------------------------------------------------------------- #
# Composite analysis                                                            #
# --------------------------------------------------------------------------- #

def analyze_resume(resume_text: str, role_name: str) -> dict:
    """Run all analysis steps and return a composite result dict."""
    t0 = time.perf_counter()

    role_data = get_role_data(role_name) or list(_JOB_ROLES.values())[0]
    job_skills = role_data["skills"]

    ml_score        = ml_resume_classifier(resume_text)
    found, missing, skill_sim = skill_match_score(resume_text, job_skills)
    ats             = advanced_ats_score(resume_text)
    semantic        = semantic_similarity(resume_text, " ".join(job_skills))
    exp_years       = extract_experience_years(resume_text)
    top_roles       = find_best_roles(resume_text)
    pred_role, conf, top3 = predict_role_from_model(resume_text)
    review          = comprehensive_resume_review(resume_text)

    role_fit = int(skill_sim * 0.4 + semantic * 0.3 + ml_score * 0.2 + ats * 0.1)
    hire_prob = min(95.0, role_fit + ml_score * 0.3)
    confidence = float(np.clip(
        (role_fit * 0.5 + (conf if conf else 0) * 0.3 + ats * 0.2) / 100.0, 0.0, 1.0
    ))

    decision = (
        "EXCELLENT – HIRE" if role_fit > 85
        else "STRONG – INTERVIEW" if role_fit > 70
        else "GOOD – DEVELOP" if role_fit > 50
        else "NEEDS IMPROVEMENT"
    )

    # Explanation
    selected_reasons, rejected_reasons = [], []
    if semantic > 60:
        selected_reasons.append(f"Strong semantic skill match ({int(semantic)}% similarity).")
    elif semantic < 40:
        rejected_reasons.append(f"Weak semantic match ({int(semantic)}%). Missing key contextual experience.")
    if skill_sim >= 70:
        selected_reasons.append(f"Meets ≥70% of required technical stack ({len(found)}/{len(job_skills)} skills).")
    elif len(missing) > len(job_skills) * 0.5:
        rejected_reasons.append(f"Missing more than half of required skills ({len(missing)} missing).")
    if ats > 75:
        selected_reasons.append(f"Excellent ATS compliance ({int(ats)}/100).")
    elif ats < 50:
        rejected_reasons.append(f"Low ATS score ({int(ats)}/100). Improve formatting and action verbs.")
    if exp_years >= role_data["exp"]:
        selected_reasons.append(f"Meets/exceeds experience requirements ({exp_years} yrs vs {role_data['exp']} req).")
    else:
        rejected_reasons.append(f"Below expected experience ({exp_years} vs {role_data['exp']} yrs req).")
    if not selected_reasons:
        selected_reasons.append("Demonstrates baseline potential for the role.")
    if not rejected_reasons:
        rejected_reasons.append("No major red flags detected.")

    elapsed = time.perf_counter() - t0
    logger.info("analyze_resume completed in %.2fs | role=%s fit=%d%%", elapsed, role_name, role_fit)

    return {
        "ml_score": ml_score,
        "skill_similarity": skill_sim,
        "semantic_score": semantic,
        "ats_score": ats,
        "role_fit": float(role_fit),
        "experience": exp_years,
        "role": role_name,
        "top_roles": top_roles,
        "role_data": role_data,
        "resume_preview": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
        "full_resume": resume_text,
        "predicted_role": pred_role,
        "model_confidence": conf,
        "top3_preds": top3,
        "resume_review": review,
        "found_skills": found,
        "missing_skills": missing,
        "hire_prob": hire_prob,
        "confidence": confidence,
        "decision": decision,
        "explanation": {
            "selected_reasons": selected_reasons,
            "rejected_reasons": rejected_reasons,
            "matched_skills": found,
            "missing_skills": missing,
        },
    }
