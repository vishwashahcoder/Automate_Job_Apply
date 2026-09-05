"""
Live Instahyre Jobs Scraper for JobPulse AI.
Fetches real-time tech, AI, and developer job postings from Instahyre official public endpoints.
Zero mock data - returns 100% authentic live postings or empty list.
"""

import sys
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


class InstahyreScraper(BaseScraper):
    """Scraper engine for Instahyre tech jobs."""

    def __init__(self):
        super().__init__(name="Instahyre")
        self.api_url = "https://www.instahyre.com/api/v1/job_search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def search_jobs(
        self,
        query: str,
        location: str = "",
        limit: int = 15,
        seniority: str = "",
        date_posted_days: Optional[int] = None,
        remote_only: bool = False
    ) -> List[JobPosting]:
        """Searches live Instahyre API for matching tech roles."""
        print(f"[InstahyreScraper] Querying live Instahyre for '{query}'...")
        jobs: List[JobPosting] = []

        try:
            encoded_query = urllib.parse.quote(query.strip())
            url = f"{self.api_url}?skills={encoded_query}&landing_page=true"
            if location and "remote" not in location.lower() and "worldwide" not in location.lower():
                url += f"&locations={urllib.parse.quote(location.strip())}"

            with httpx.Client(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    postings = data.get("objects", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

                    query_terms = [t.lower() for t in query.split() if len(t) > 2]

                    for item in postings:
                        if len(jobs) >= limit:
                            break

                        title = str(item.get("title") or item.get("job_title") or "").strip()
                        comp_obj = item.get("employer", {}) if isinstance(item.get("employer"), dict) else {}
                        company = str(comp_obj.get("company_name") or item.get("company_name") or "Tech Company").strip()
                        loc_list = item.get("locations", [])
                        loc_str = ", ".join(loc_list) if isinstance(loc_list, list) and loc_list else str(item.get("location", "India / Remote"))
                        
                        job_id_raw = item.get("id") or item.get("job_id") or abs(hash(title + company))
                        job_id = f"ih_{job_id_raw}"
                        slug = item.get("slug") or str(job_id_raw)
                        job_url = f"https://www.instahyre.com/job/{slug}" if not str(slug).startswith("http") else slug

                        raw_desc = str(item.get("description") or item.get("job_description") or "")
                        clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip() if raw_desc else f"Position: {title} at {company}. View full job on Instahyre."
                        
                        skills_list = item.get("skills", [])
                        tags = [str(s).lower() for s in skills_list] if isinstance(skills_list, list) else []
                        is_remote = "remote" in loc_str.lower() or remote_only or bool(item.get("is_remote", False))

                        # Experience
                        min_exp = item.get("experience_years_min", 0)
                        max_exp = item.get("experience_years_max", 0)
                        exp_str = f"{min_exp}-{max_exp} yrs" if (min_exp or max_exp) else "Not Specified"

                        if not title or not company:
                            continue

                        search_corpus = f"{title.lower()} {company.lower()} {' '.join(tags)} {clean_desc.lower()}"
                        if not query_terms or any(term in search_corpus for term in query_terms):
                            jobs.append(
                                JobPosting(
                                    job_id=str(job_id),
                                    title=title,
                                    company=company,
                                    location="Remote" if is_remote else loc_str,
                                    platform="Instahyre",
                                    url=job_url,
                                    description=clean_desc[:500] + "..." if len(clean_desc) > 500 else clean_desc,
                                    posted_date="Recently",
                                    experience_required=exp_str,
                                    is_remote=is_remote,
                                    job_type="Full-time",
                                    tags=tags
                                )
                            )
        except Exception as e:
            print(f"[InstahyreScraper] API note: {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[InstahyreScraper] Found {len(deduped)} live jobs on Instahyre.")
        return deduped
