"""
Candidate Profile & Preferences Model for JobPulse AI.
Zero static defaults - all attributes dynamically extracted from candidate resume.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CandidateProfile:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    portfolio_url: str = ""
    linkedin_url: str = ""
    years_experience: int = 0
    last_position: str = ""
    skills: List[str] = field(default_factory=list)
    summary: str = ""
    resume_pdf_path: str = ""
    missing_fields: List[str] = field(default_factory=list)

@dataclass
class SearchPreferences:
    job_titles: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=lambda: [
        "company_careers",
        "linkedin",
        "instahyre",
        "naukri",
        "indeed",
        "wellfound",
        "cutshort_hirist",
        "weworkremotely",
        "flexjobs",
        "remote_co"
    ])
