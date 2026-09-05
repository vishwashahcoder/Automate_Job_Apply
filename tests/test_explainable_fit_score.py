"""
Unit tests for JobMatcher explainable fit scoring without mock data.
"""

import sys
sys.path.insert(0, r"d:\[GIT PROJECT]\Automate_Job_Apply")

import unittest
from src.models.job import JobPosting
from src.matcher import JobMatcher


class TestExplainableFitScore(unittest.TestCase):

    def setUp(self):
        self.config = {
            "preferences": {
                "job_titles": ["AI Engineer", "Software Developer"],
                "locations": ["Pune", "Remote"],
                "platforms": ["company_careers", "linkedin", "instahyre", "naukri", "weworkremotely"]
            },
            "resume_profile": {
                "full_name": "Candidate",
                "years_experience": 2,
                "last_position": "Python Developer",
                "skills": ["Python", "Machine Learning", "SQL", "FastAPI"]
            },
            "matching": {
                "min_fit_score": 50
            }
        }
        self.matcher = JobMatcher(self.config, prompt_criteria={"query": "AI Engineer"})

    def test_weighted_sub_scores_calculation(self):
        """Test explainable fit formula: 40% skill + 25% title + 15% seniority + 10% salary + 10% prompt."""
        job = JobPosting(
            job_id="test_ai_job",
            title="Senior AI Engineer",
            company="Tech Corp",
            location="Remote",
            platform="LinkedIn",
            url="https://linkedin.com/jobs/view/101",
            description="Seeking AI Engineer with strong Python, FastAPI, and Machine Learning skills.",
            salary="$120,000 - $150,000 USD",
            seniority_level="Senior"
        )

        res = self.matcher.evaluate(job)
        sub = res.get("sub_scores", {})

        self.assertIn("skill_match_40", sub)
        self.assertIn("title_match_25", sub)
        self.assertIn("experience_fit_15", sub)
        self.assertIn("salary_fit_10", sub)

        total_sum = (
            sub["skill_match_40"] +
            sub["title_match_25"] +
            sub["experience_fit_15"] +
            sub["salary_fit_10"] +
            sub.get("prompt_match_10", 0)
        )

        self.assertAlmostEqual(res["match_score"], round(total_sum), delta=1)
        self.assertIn("Python", res["matched_skills"])


if __name__ == "__main__":
    unittest.main()
