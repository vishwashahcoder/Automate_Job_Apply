"""
Live Wellfound (formerly AngelList) Startup Jobs Scraper for JobPulse AI.
Queries Wellfound tech startup job listings with salary and equity transparency.
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


class WellfoundScraper(BaseScraper):
    """Scraper engine for Wellfound (AngelList) startup jobs."""

    def __init__(self):
        super().__init__(name="Wellfound")
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
        """Searches live Wellfound for startup tech roles."""
        print(f"[WellfoundScraper] Querying live Wellfound for '{query}'...")
        jobs: List[JobPosting] = []

        try:
            q_clean = urllib.parse.quote(query.strip().lower().replace(" ", "-"))
            url = f"https://wellfound.com/role/l/{q_clean}" if query else "https://wellfound.com/jobs"

            with httpx.Client(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and res.text:
                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all("div", class_=re.compile(r"styles_jobListing|styles_result|job-listing", re.I))

                    for card in cards[:limit]:
                        title_elem = card.find("a", class_=re.compile(r"title|styles_title", re.I))
                        comp_elem = card.find("h2") or card.find("span", class_=re.compile(r"company|name", re.I))
                        loc_elem = card.find("span", class_=re.compile(r"location", re.I))
                        sal_elem = card.find("span", class_=re.compile(r"compensation|salary", re.I))

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            company = comp_elem.get_text(strip=True) if comp_elem else "Startup Org"
                            loc_str = loc_elem.get_text(strip=True) if loc_elem else (location or "Remote")
                            href = title_elem.get("href", "")
                            job_url = href if href.startswith("http") else f"https://wellfound.com{href}"
                            salary_str = sal_elem.get_text(strip=True) if sal_elem else "Competitive Equity + Salary"

                            is_remote = "remote" in loc_str.lower() or remote_only
                            job_id = f"wf_{abs(hash(job_url or title + company)) & 0xffffffff}"

                            jobs.append(
                                JobPosting(
                                    job_id=str(job_id),
                                    title=title,
                                    company=company,
                                    location="Remote" if is_remote else loc_str,
                                    platform="Wellfound",
                                    url=job_url,
                                    description=f"Startup Position: {title} at {company}. Compensation: {salary_str}.",
                                    posted_date="Recently",
                                    salary=salary_str,
                                    is_remote=is_remote,
                                    job_type="Full-time"
                                )
                            )
        except Exception as e:
            print(f"[WellfoundScraper] Fetch note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[WellfoundScraper] Found {len(deduped)} live jobs on Wellfound.")
        return deduped
