"""
Live LinkedIn Jobs Scraper for JobPulse AI.
Queries LinkedIn public search endpoints using structured URL parameters and BeautifulSoup parsing.
Zero mock data - returns 100% authentic live postings or empty list.
"""

import sys
import re
import time
import urllib.parse
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, JobPosting, deduplicate_jobs

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LinkedInScraper(BaseScraper):
    """Live search scraper for LinkedIn Jobs."""

    def __init__(self):
        super().__init__(name="LinkedIn")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }

    def search_jobs(
        self,
        query: str,
        location: str = "Remote",
        limit: int = 15,
        seniority: str = "",
        date_posted_days: Optional[int] = None,
        remote_only: bool = False
    ) -> List[JobPosting]:
        """Searches LinkedIn public job listings live."""
        print(f"[LinkedInScraper] Querying live LinkedIn jobs for '{query}' in '{location}'...")
        jobs: List[JobPosting] = []

        encoded_query = urllib.parse.quote(query.strip())
        loc_str = "Worldwide" if (remote_only and not location) else (location or "Remote")
        encoded_loc = urllib.parse.quote(loc_str)

        # Build LinkedIn Filter Parameters
        time_param = ""
        if date_posted_days:
            if date_posted_days <= 1:
                time_param = "&f_TPR=r86400"
            elif date_posted_days <= 7:
                time_param = "&f_TPR=r604800"
            elif date_posted_days <= 30:
                time_param = "&f_TPR=r2592000"

        exp_param = ""
        seniority_lower = seniority.lower() if seniority else ""
        if "entry" in seniority_lower or "fresher" in seniority_lower or "junior" in seniority_lower:
            exp_param = "&f_E=1,2"
        elif "mid" in seniority_lower:
            exp_param = "&f_E=3,4"
        elif "senior" in seniority_lower or "lead" in seniority_lower:
            exp_param = "&f_E=4,5"

        remote_param = "&f_WT=2" if (remote_only or "remote" in location.lower()) else ""

        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&location={encoded_loc}&start=0{time_param}{exp_param}{remote_param}"

        try:
            with httpx.Client(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and res.text:
                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all("li")
                    for card in cards[:limit]:
                        title_elem = card.find("h3", class_="base-search-card__title")
                        company_elem = card.find("h4", class_="base-search-card__subtitle")
                        loc_elem = card.find("span", class_="job-search-card__location")
                        link_elem = card.find("a", class_="base-card__full-link")
                        time_elem = card.find("time", class_="job-search-card__listdate") or card.find("time", class_="job-search-card__listdate--new")

                        if title_elem and company_elem:
                            job_title = title_elem.text.strip()
                            company = company_elem.text.strip()
                            job_loc = loc_elem.text.strip() if loc_elem else loc_str
                            job_url = link_elem["href"].strip() if link_elem and "href" in link_elem.attrs else ""
                            posted_str = time_elem.text.strip() if time_elem else "Recently"

                            if "?" in job_url:
                                job_url = job_url.split("?")[0]

                            clean_title_comp = f"{job_title}_{company}"
                            job_id = f"li_{abs(hash(job_url or clean_title_comp)) & 0xffffffff}"

                            is_job_remote = "remote" in job_loc.lower() or remote_only or "remote" in job_title.lower()

                            jobs.append(
                                JobPosting(
                                    job_id=job_id,
                                    title=job_title,
                                    company=company,
                                    location=job_loc,
                                    platform="LinkedIn",
                                    url=job_url,
                                    description=f"{job_title} at {company} ({job_loc}). View full posting on LinkedIn.",
                                    posted_date=posted_str,
                                    is_remote=is_job_remote,
                                    job_type="Full-time"
                                )
                            )
        except Exception as e:
            print(f"[LinkedInScraper] Fetch note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[LinkedInScraper] Found {len(deduped)} live jobs on LinkedIn.")
        return deduped
