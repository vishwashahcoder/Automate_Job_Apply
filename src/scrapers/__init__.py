"""
Scraper Registry and Factory for JobPulse AI.
Includes ONLY the user's specified portals:
1. Company Career Pages (Direct ATS)
2. LinkedIn
3. Instahyre
4. Naukri.com
5. Indeed
6. Wellfound
7. Cutshort / Hirist
8. We Work Remotely
9. FlexJobs
10. Remote.co
"""

from typing import Dict, Type
from src.scrapers.base import BaseScraper, JobPosting, deduplicate_jobs
from src.scrapers.company_careers import CompanyCareersScraper
from src.scrapers.linkedin import LinkedInScraper
from src.scrapers.instahyre import InstahyreScraper
from src.scrapers.naukri import NaukriScraper
from src.scrapers.indeed import IndeedScraper
from src.scrapers.wellfound import WellfoundScraper
from src.scrapers.cutshort_hirist import CutshortHiristScraper
from src.scrapers.weworkremotely import WeWorkRemotelyScraper
from src.scrapers.flexjobs import FlexJobsScraper
from src.scrapers.remote_co import RemoteCoScraper

SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {
    "company_careers": CompanyCareersScraper,
    "linkedin": LinkedInScraper,
    "instahyre": InstahyreScraper,
    "naukri": NaukriScraper,
    "indeed": IndeedScraper,
    "wellfound": WellfoundScraper,
    "cutshort_hirist": CutshortHiristScraper,
    "weworkremotely": WeWorkRemotelyScraper,
    "flexjobs": FlexJobsScraper,
    "remote_co": RemoteCoScraper,
}

__all__ = [
    "BaseScraper",
    "JobPosting",
    "deduplicate_jobs",
    "SCRAPER_REGISTRY",
    "CompanyCareersScraper",
    "LinkedInScraper",
    "InstahyreScraper",
    "NaukriScraper",
    "IndeedScraper",
    "WellfoundScraper",
    "CutshortHiristScraper",
    "WeWorkRemotelyScraper",
    "FlexJobsScraper",
    "RemoteCoScraper",
]
