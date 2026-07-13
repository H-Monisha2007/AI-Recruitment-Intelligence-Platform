"""
Unit tests — ML service functions (no DB, no HTTP).
"""
import pytest

from app.services.ml_service import (
    advanced_ats_score,
    clean_resume,
    comprehensive_resume_review,
    extract_experience_years,
    find_best_roles,
    ml_resume_classifier,
    semantic_similarity,
    skill_match_score,
)

SAMPLE_ML_RESUME = """
John Doe | john@example.com | +1-555-123-4567 | github.com/johndoe
Summary: ML Engineer with 5 years of experience in deep learning and NLP.
Skills: Python, TensorFlow, PyTorch, scikit-learn, machine learning, NLP, computer vision, Docker
Experience: 5 years at AI Corp — developed deep learning models, deployed production ML pipelines.
Education: M.Sc. Computer Science, Stanford University
Projects: Built BERT-based NER system; deployed YOLO object detection API.
"""

SAMPLE_DEV_RESUME = """
Jane Smith | jane@example.com | +44-20-1234-5678 | linkedin.com/in/janesmith
Summary: Full Stack Developer with 3 years of experience.
Skills: React, Node.js, JavaScript, HTML, CSS, MongoDB, Docker, Python
Experience: Developed 10+ web applications using React and Django. Increased performance by 40%.
"""


# ── clean_resume ──────────────────────────────────────────────────────────────

def test_clean_resume_removes_urls():
    dirty = "Visit https://example.com and http://foo.bar for info."
    result = clean_resume(dirty)
    assert "http" not in result


def test_clean_resume_lowercases():
    result = clean_resume("Python TensorFlow BERT")
    assert result == result.lower()


def test_clean_resume_empty_input():
    assert clean_resume("") == ""
    assert clean_resume(None) == ""  # type: ignore[arg-type]


# ── extract_experience_years ──────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("5 years of experience in machine learning", 5),
    ("I have 3+ years experience", 3),
    ("10 yrs of hands-on work", 10),
    ("No experience mentioned here", 0),
])
def test_extract_experience_years(text, expected):
    assert extract_experience_years(text) == expected


# ── ml_resume_classifier ──────────────────────────────────────────────────────

def test_ml_resume_classifier_high_score():
    score = ml_resume_classifier(SAMPLE_ML_RESUME)
    assert score > 30, "ML-heavy resume should score well"


def test_ml_resume_classifier_low_score():
    score = ml_resume_classifier("I like excel and powerpoint presentations")
    assert score < 20


def test_ml_resume_classifier_capped_at_100():
    score = ml_resume_classifier(SAMPLE_ML_RESUME * 10)
    assert score <= 100


# ── advanced_ats_score ────────────────────────────────────────────────────────

def test_ats_score_well_formatted():
    score = advanced_ats_score(SAMPLE_ML_RESUME)
    assert score > 40


def test_ats_score_empty():
    assert advanced_ats_score("") == 0.0


def test_ats_score_max_100():
    assert advanced_ats_score(SAMPLE_ML_RESUME * 5) <= 100


# ── skill_match_score ─────────────────────────────────────────────────────────

def test_skill_match_all_found():
    found, missing, pct = skill_match_score("python django flask", ["python", "django", "flask"])
    assert len(found) == 3
    assert len(missing) == 0
    assert pct == 100.0


def test_skill_match_none_found():
    found, missing, pct = skill_match_score("java spring hibernate", ["react", "vue", "angular"])
    assert len(found) == 0
    assert pct == 0.0


def test_skill_match_partial():
    found, missing, pct = skill_match_score("python react", ["python", "react", "docker"])
    assert len(found) == 2
    assert len(missing) == 1
    assert 60 < pct < 70


# ── semantic_similarity ────────────────────────────────────────────────────────

def test_semantic_similarity_same_text():
    score = semantic_similarity("machine learning engineer python", "machine learning engineer python")
    assert score > 90


def test_semantic_similarity_different():
    score = semantic_similarity("python developer react", "deep sea fishing trawler nets")
    assert score < 60


def test_semantic_similarity_range():
    score = semantic_similarity(SAMPLE_ML_RESUME, "machine learning pytorch tensorflow nlp")
    assert 0 <= score <= 100


# ── comprehensive_resume_review ───────────────────────────────────────────────

def test_resume_review_detects_sections():
    review = comprehensive_resume_review(SAMPLE_ML_RESUME)
    assert "Experience" in review["sections_found"]
    assert "Education" in review["sections_found"]
    assert "Skills" in review["sections_found"]


def test_resume_review_has_contact():
    review = comprehensive_resume_review(SAMPLE_ML_RESUME)
    assert review["has_contact"] is True


def test_resume_review_has_github():
    review = comprehensive_resume_review(SAMPLE_ML_RESUME)
    assert review["has_github"] is True


def test_resume_review_tech_stack():
    review = comprehensive_resume_review(SAMPLE_ML_RESUME)
    assert "ML/AI" in review["tech_stack"] or "Python" in review["tech_stack"]


# ── find_best_roles ───────────────────────────────────────────────────────────

def test_find_best_roles_returns_5():
    roles = find_best_roles(SAMPLE_ML_RESUME)
    assert len(roles) == 5


def test_find_best_roles_ml_on_top():
    roles = find_best_roles(SAMPLE_ML_RESUME)
    top_role = roles[0][0]
    # ML-heavy resume should rank an ML/DS role first
    assert any(kw in top_role for kw in ["ML", "Data", "AI", "NLP", "Vision"])
