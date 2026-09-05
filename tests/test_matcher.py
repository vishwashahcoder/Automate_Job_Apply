"""
Unit tests for JobMatcher.
"""

from src.matcher import JobMatcher
from src.models.job import JobPosting

def test_job_matcher_heuristic():
    config = {
        "resume_profile": {
            "skills": ["Python", "FastAPI", "Docker"],
            "years_experience": 3
        },
        "matching": {"min_fit_score": 70}
    }
    matcher = JobMatcher(config)
    
    job = JobPosting(
        job_id="test_1",
        title="Python Software Engineer",
        company="Tech Inc",
        location="Remote",
        platform="Test",
        url="http://test.com",
        description="Looking for Python and FastAPI developer with Docker experience."
    )

    result = matcher.evaluate(job)
    assert isinstance(result, dict)
    assert "match_score" in result
    assert result["match_score"] >= 70
    assert result["should_apply"] is True
