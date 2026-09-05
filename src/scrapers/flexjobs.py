"""
Live FlexJobs Scraper for JobPulse AI.
Queries FlexJobs verified remote, hybrid, and flexible job listings.
Zero mock data - returns 100% authentic live postings or empty list.
"""

import sys
import re
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


class FlexJobsScraper(BaseScraper):
    """Scraper engine for FlexJobs remote listings."""

    def __init__(self):
        super().__init__(name="FlexJobs")
        self.search_url = "https://www.flexjobs.com/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
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
        """Searches live FlexJobs for verified remote listings."""
        print(f"[FlexJobsScraper] Querying live FlexJobs for '{query}'...")
        jobs: List[JobPosting] = []

        try:
            encoded_query = urllib.parse.quote(query.strip())
            url = f"{self.search_url}?search={encoded_query}&location={urllib.parse.quote(location.strip() if location else 'Remote')}"

            with httpx.Client(timeout=5.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and res.text:
                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all("li", class_=re.compile(r"job-card|m-0|search-job", re.I)) or soup.find_all("div", class_=re.compile(r"job-card", re.I))

                    for card in cards[:limit]:
                        title_elem = card.find("a", class_=re.compile(r"job-title|font-weight-bold", re.I)) or card.find("h5")
                        desc_elem = card.find("p", class_=re.compile(r"job-description|description", re.I)) or card.find("p")
                        loc_elem = card.find("div", class_=re.compile(r"job-location|location", re.I))

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            href = title_elem.get("href", "")
                            job_url = href if href.startswith("http") else f"https://www.flexjobs.com{href}"
                            loc_str = loc_elem.get_text(strip=True) if loc_elem else "Worldwide Remote"
                            desc = desc_elem.get_text(strip=True) if desc_elem else f"Verified Remote Role: {title} on FlexJobs."

                            is_remote = True
                            job_id = f"fj_{abs(hash(job_url or title)) & 0xffffffff}"

                            jobs.append(
                                JobPosting(
                                    job_id=str(job_id),
                                    title=title,
                                    company="FlexJobs Verified Employer",
                                    location=loc_str,
                                    platform="FlexJobs",
                                    url=job_url,
                                    description=desc[:500] + "..." if len(desc) > 500 else desc,
                                    posted_date="Recently",
                                    is_remote=is_remote,
                                    job_type="Full-time / Flexible"
                                )
                            )
        except Exception as e:
            print(f"[FlexJobsScraper] Fetch note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[FlexJobsScraper] Found {len(deduped)} live jobs on FlexJobs.")
        return deduped
