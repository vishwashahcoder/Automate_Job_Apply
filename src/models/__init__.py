"""
Data models package for JobPulse AI.
"""

from src.models.job import JobPosting, make_hashable, deduplicate_jobs
from src.models.profile import CandidateProfile, SearchPreferences

__all__ = [
    "JobPosting",
    "make_hashable",
    "deduplicate_jobs",
    "CandidateProfile",
    "SearchPreferences",
]
