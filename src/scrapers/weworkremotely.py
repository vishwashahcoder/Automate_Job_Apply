"""
Live WeWorkRemotely RSS Scraper for JobPulse AI.
Fetches real-time programming, DevOps, AI, and full-stack positions from WeWorkRemotely feeds.
Zero mock data - returns 100% authentic live postings or empty list.
"""

import sys
import xml.etree.ElementTree as ET
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, JobPosting, deduplicate_jobs

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class WeWorkRemotelyScraper(BaseScraper):
    """Scraper engine for WeWorkRemotely RSS feeds."""

    def __init__(self):
        super().__init__(name="WeWorkRemotely")
        self.feed_urls = [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
            "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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
        """Searches live WeWorkRemotely feeds matching query keywords."""
        print(f"[WeWorkRemotelyScraper] Searching WeWorkRemotely RSS for '{query}'...")
        jobs: List[JobPosting] = []
        query_terms = [t.lower() for t in query.split() if len(t) > 2]

        for feed_url in self.feed_urls:
            if len(jobs) >= limit:
                break
            try:
                with httpx.Client(timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                    res = client.get(feed_url)
                    if res.status_code == 200 and res.content:
                        root = ET.fromstring(res.content)
                        channel = root.find("channel")
                        items = channel.findall("item") if channel is not None else []

                        for item in items:
                            if len(jobs) >= limit:
                                break

                            title_elem = item.find("title")
                            link_elem = item.find("link")
                            desc_elem = item.find("description")
                            pub_elem = item.find("pubDate")

                            full_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                            job_url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                            raw_desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
                            pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else "Recently"

                            clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()

                            company = "Remote Company"
                            job_title = full_title
                            if ":" in full_title:
                                parts = full_title.split(":", 1)
                                company = parts[0].strip()
                                job_title = parts[1].strip()

                            search_corpus = f"{job_title.lower()} {company.lower()} {clean_desc.lower()}"

                            if not query_terms or any(term in search_corpus for term in query_terms):
                                job_id = f"wwr_{abs(hash(job_url or full_title)) & 0xffffffff}"

                                jobs.append(
                                    JobPosting(
                                        job_id=job_id,
                                        title=job_title,
                                        company=company,
                                        location="Worldwide Remote",
                                        platform="WeWorkRemotely",
                                        url=job_url,
                                        description=clean_desc[:500] + "..." if len(clean_desc) > 500 else clean_desc,
                                        posted_date=pub_date[:16] if len(pub_date) > 16 else pub_date,
                                        is_remote=True,
                                        job_type="Full-time"
                                    )
                                )
            except Exception as e:
                print(f"[WeWorkRemotelyScraper] Feed note ({feed_url}): {e}")

        deduped = deduplicate_jobs(jobs)
        print(f"[WeWorkRemotelyScraper] Found {len(deduped)} live jobs on WeWorkRemotely.")
        return deduped
