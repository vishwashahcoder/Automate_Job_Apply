"""
Integration tests for FastAPI endpoints in app.py.
"""

import sys
sys.path.insert(0, r"d:\[GIT PROJECT]\Automate_Job_Apply")

import io
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_read_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "JobPulse AI" in response.text


def test_get_profile():
    response = client.get("/api/profile")
    assert response.status_code == 200
    json_data = response.json()
    assert "preferences" in json_data
    assert "resume_profile" in json_data


def test_get_jobs():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total_discovered" in stats
    assert "platforms_connected" in stats


def test_parse_prompt_endpoint():
    response = client.post(
        "/api/parse-prompt",
        json={"prompt": "Remote Senior AI Engineer jobs above $120k posted this week in London or worldwide"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("query") == "Senior AI Engineer" or "AI Engineer" in data.get("query")
    assert data.get("seniority_level") == "Senior"
    assert data.get("date_posted_days") == 7


def test_update_job_status():
    response = client.post(
        "/api/job/test_job_101/status",
        json={"status": "SAVED"}
    )
    assert response.status_code == 200
    assert response.json()["new_status"] == "SAVED"


def test_upload_resume_endpoint():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    pdf_bytes = io.BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    response = client.post(
        "/api/upload-resume",
        files={"file": ("test_resume.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert "extracted_profile" in json_data
