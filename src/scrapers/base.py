"""
Abstract Base Scraper module for JobPulse AI.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.job import JobPosting, deduplicate_jobs


class BaseScraper(ABC):
    """Abstract Base Class for all Job Platform Scrapers."""
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search_jobs(
        self,
        query: str,
        location: str = "",
        limit: int = 15,
        seniority: str = "",
        date_posted_days: Optional[int] = None,
        remote_only: bool = False
    ) -> List[JobPosting]:
        """Performs search on the job platform and returns structured JobPosting list."""
        pass
