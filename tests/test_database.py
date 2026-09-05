"""
Unit tests for DatabaseManager.
"""

import os
import tempfile
import pytest
from database import DatabaseManager

@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_jobpulse.db")
    db_mgr = DatabaseManager(db_path=db_path)
    yield db_mgr

def test_save_and_retrieve_job(temp_db):
    job_dict = {
        "job_id": "test_db_101",
        "title": "Backend Python Engineer",
        "company": "DataCorp",
        "location": "Ahmedabad",
        "platform": "LinkedIn",
        "url": "http://example.com/test",
        "description": "Python, SQL, REST APIs",
        "salary": "₹15,000,000 PA"
    }

    match_info = {
        "match_score": 85,
        "relevance": "High",
        "matched_skills": ["Python", "SQL"],
        "missing_skills": ["Kafka"],
        "reasoning": "Excellent candidate alignment."
    }

    temp_db.save_job(job_dict, match_info)
    all_jobs = temp_db.get_all_jobs()

    assert len(all_jobs) == 1
    assert all_jobs[0]["job_id"] == "test_db_101"
    assert all_jobs[0]["match_score"] == 85
    assert all_jobs[0]["matched_skills"] == ["Python", "SQL"]

    stats = temp_db.get_stats()
    assert stats["total_discovered"] == 1
    assert stats["high_match_count"] == 1
