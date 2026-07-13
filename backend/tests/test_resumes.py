"""
API tests — Resume endpoints.
"""
import io
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SAMPLE_TXT = b"""
John Doe  |  john@example.com  |  +1-555-0100
5 years of experience in machine learning and NLP.
Skills: Python, TensorFlow, PyTorch, scikit-learn, NLP, Docker
Experience: Developed deep-learning models for production. Led team of 4 engineers.
Education: M.Sc. Computer Science
Projects: github.com/johndoe/nlp-project
"""


async def test_resume_upload_success(client: AsyncClient, auth_headers: dict):
    files = {"file": ("resume.txt", io.BytesIO(SAMPLE_TXT), "text/plain")}
    resp = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "resume_id" in data
    assert data["word_count"] > 0


async def test_resume_upload_unauthenticated(client: AsyncClient):
    files = {"file": ("resume.txt", io.BytesIO(SAMPLE_TXT), "text/plain")}
    resp = await client.post("/api/v1/resumes/upload", files=files)
    assert resp.status_code == 401


async def test_resume_analyze_success(client: AsyncClient, auth_headers: dict):
    files = {"file": ("resume.txt", io.BytesIO(SAMPLE_TXT), "text/plain")}
    data  = {"selected_role": "ML Engineer", "save_result": "false"}
    resp  = await client.post("/api/v1/resumes/analyze", files=files, data=data, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert 0 <= body["role_fit"] <= 100
    assert 0 <= body["ats_score"] <= 100
    assert "decision" in body
    assert isinstance(body["found_skills"], list)
    assert isinstance(body["missing_skills"], list)
    assert "explanation" in body


async def test_resume_analyze_missing_file(client: AsyncClient, auth_headers: dict):
    data = {"selected_role": "ML Engineer"}
    resp = await client.post("/api/v1/resumes/analyze", data=data, headers=auth_headers)
    assert resp.status_code == 422


async def test_resume_list(client: AsyncClient, auth_headers: dict):
    # Upload one first
    files = {"file": ("resume.txt", io.BytesIO(SAMPLE_TXT), "text/plain")}
    await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    resp = await client.get("/api/v1/resumes/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["total"] >= 1


async def test_skill_gap_analysis(client: AsyncClient, auth_headers: dict):
    payload = {
        "resume_text": "Python developer with experience in Django, Flask, and PostgreSQL. Built REST APIs.",
        "job_skills": ["python", "django", "react", "kubernetes", "graphql"],
    }
    resp = await client.post("/api/v1/resumes/skill-gap", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "found_skills" in body
    assert "missing_skills" in body
    assert 0 <= body["coverage_percent"] <= 100
