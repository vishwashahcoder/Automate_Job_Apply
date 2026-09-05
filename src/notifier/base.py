from abc import ABC, abstractmethod
from typing import Dict, Any
from src.scrapers.base import JobPosting

class BaseNotifier(ABC):
    """Abstract Base Class for Notification Interfaces."""

    @abstractmethod
    def send_application_prompt(self, job: JobPosting, match_info: Dict[str, Any]) -> bool:
        """
        Notifies user of job match and requests approval to apply.
        Returns True if user approves application, False if rejected/skipped.
        """
        pass
