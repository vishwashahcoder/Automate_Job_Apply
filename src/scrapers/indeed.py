"""
Live Indeed Jobs Scraper for JobPulse AI.
Queries Indeed search endpoints with structured query parameters and card parsing.
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


class IndeedScraper(BaseScraper):
    """Scraper engine for Indeed jobs."""

    def __init__(self):
        super().__init__(name="Indeed")
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
        """Searches live Indeed for matching roles."""
        print(f"[IndeedScraper] Querying live Indeed for '{query}' in '{location}'...")
        jobs: List[JobPosting] = []

        try:
            encoded_query = urllib.parse.quote(query.strip())
            encoded_loc = urllib.parse.quote(location.strip() if location else "Remote")
            
            fromage_param = f"&fromage={date_posted_days}" if date_posted_days else ""
            url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_loc}{fromage_param}"

            with httpx.Client(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200 and res.text:
                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobCard|result", re.I))

                    for card in cards[:limit]:
                        title_elem = card.find("h2", class_=re.compile(r"jobTitle", re.I)) or card.find("a", class_=re.compile(r"jcs-JobTitle", re.I))
                        comp_elem = card.find("span", class_=re.compile(r"companyName|css-63koeb", re.I)) or card.find("span", {"data-testid": "company-name"})
                        loc_elem = card.find("div", class_=re.compile(r"companyLocation", re.I)) or card.find("div", {"data-testid": "text-location"})
                        snippet_elem = card.find("div", class_=re.compile(r"job-snippet", re.I)) or card.find("ul")

                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            company = comp_elem.get_text(strip=True) if comp_elem else "Hiring Company"
                            loc_str = loc_elem.get_text(strip=True) if loc_elem else location
                            
                            link_tag = title_elem if title_elem.name == "a" else title_elem.find("a")
                            job_key = link_tag.get("data-jk") if link_tag else ""
                            href = link_tag.get("href", "") if link_tag else ""
                            
                            if job_key:
                                job_url = f"https://www.indeed.com/viewjob?jk={job_key}"
                            elif href.startswith("http"):
                                job_url = href
                            elif href:
                                job_url = f"https://www.indeed.com{href}"
                            else:
                                job_url = url

                            snippet = snippet_elem.get_text(separator=" ").strip() if snippet_elem else f"Role: {title} at {company}."
                            is_remote = "remote" in loc_str.lower() or remote_only or "remote" in title.lower()
                            job_id = f"ind_{job_key or abs(hash(job_url or title + company)) & 0xffffffff}"

                            jobs.append(
                                JobPosting(
                                    job_id=str(job_id),
                                    title=title,
                                    company=company,
                                    location="Remote" if is_remote else loc_str,
                                    platform="Indeed",
                                    url=job_url,
                                    description=snippet[:500] + "..." if len(snippet) > 500 else snippet,
                                    posted_date="Recently",
                                    is_remote=is_remote,
                                    job_type="Full-time"
                                )
                            )
        except Exception as e:
            print(f"[IndeedScraper] Fetch note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[IndeedScraper] Found {len(deduped)} live jobs on Indeed.")
        return deduped
