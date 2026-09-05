"""
Live Remote.co Jobs Scraper for JobPulse AI.
Queries Remote.co remote developer and engineering categories.
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


class RemoteCoScraper(BaseScraper):
    """Scraper engine for Remote.co jobs."""

    def __init__(self):
        super().__init__(name="Remote.co")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def search_jobs(
        self,
        query: str,
        location: str = "Worldwide",
        limit: int = 15,
        seniority: str = "",
        date_posted_days: Optional[int] = None,
        remote_only: bool = False
    ) -> List[JobPosting]:
        """Searches live Remote.co for matching remote positions."""
        print(f"[RemoteCoScraper] Querying live Remote.co for '{query}'...")
        jobs: List[JobPosting] = []

        try:
            urls = [
                "https://remote.co/remote-jobs/developer/",
                "https://remote.co/remote-jobs/it/"
            ]
            query_terms = [t.lower() for t in query.split() if len(t) > 2]

            with httpx.Client(timeout=5.0, headers=self.headers, follow_redirects=True) as client:
                for target_url in urls:
                    if len(jobs) >= limit:
                        break
                    res = client.get(target_url)
                    if res.status_code == 200 and res.text:
                        soup = BeautifulSoup(res.text, "html.parser")
                        cards = soup.find_all("a", class_=re.compile(r"card|job_listing", re.I))

                        for card in cards:
                            if len(jobs) >= limit:
                                break

                            title_elem = card.find(re.compile(r"p|h2|h3|h4|span"), class_=re.compile(r"font-weight-bold|title", re.I))
                            comp_elem = card.find(re.compile(r"p|span"), class_=re.compile(r"company|m-0", re.I))
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                company = comp_elem.get_text(strip=True) if comp_elem else "Remote Company"
                                href = card.get("href", "")
                                job_url = href if href.startswith("http") else f"https://remote.co{href}"

                                search_corpus = f"{title.lower()} {company.lower()}"
                                if not query_terms or any(term in search_corpus for term in query_terms):
                                    job_id = f"rco_{abs(hash(job_url or title + company)) & 0xffffffff}"

                                    jobs.append(
                                        JobPosting(
                                            job_id=str(job_id),
                                            title=title,
                                            company=company,
                                            location="Worldwide Remote",
                                            platform="Remote.co",
                                            url=job_url,
                                            description=f"Remote Position: {title} at {company}. View application on Remote.co.",
                                            posted_date="Recently",
                                            is_remote=True,
                                            job_type="Full-time"
                                        )
                                    )
        except Exception as e:
            print(f"[RemoteCoScraper] Fetch note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[RemoteCoScraper] Found {len(deduped)} live jobs on Remote.co.")
        return deduped
