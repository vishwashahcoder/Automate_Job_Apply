"""
Unit tests for the 10 User-Specified Live Scrapers and Smart Cross-Platform Deduplication:
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

import sys
sys.path.insert(0, r"d:\[GIT PROJECT]\Automate_Job_Apply")

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
from src.models.job import JobPosting, deduplicate_jobs


def test_cross_platform_deduplication():
    j1 = JobPosting(
        job_id="li_101",
        title="Senior Python Engineer",
        company="Stripe Inc.",
        location="Remote",
        platform="LinkedIn",
        url="https://linkedin.com/jobs/view/101",
        description="Short description"
    )
    j2 = JobPosting(
        job_id="inst_202",
        title="Sr. Python Engineer (Remote)",
        company="Stripe",
        location="Worldwide Remote",
        platform="Instahyre",
        url="https://www.instahyre.com/job/202",
        description="Much richer and more detailed description of the Python position at Stripe.",
        salary="$150,000 - $180,000 USD"
    )

    clustered = deduplicate_jobs([j1, j2])
    assert len(clustered) == 1
    unified = clustered[0]
    assert len(unified.sources) == 2
    platforms = {s["platform"] for s in unified.sources}
    assert "LinkedIn" in platforms
    assert "Instahyre" in platforms
    assert unified.salary == "$150,000 - $180,000 USD"
    assert "richer and more detailed" in unified.description


def test_company_careers_scraper():
    scraper = CompanyCareersScraper()
    jobs = scraper.search_jobs(query="Developer", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_linkedin_scraper():
    scraper = LinkedInScraper()
    jobs = scraper.search_jobs(query="Python", location="Remote", limit=2)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_instahyre_scraper():
    scraper = InstahyreScraper()
    jobs = scraper.search_jobs(query="Python", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_naukri_scraper():
    scraper = NaukriScraper()
    jobs = scraper.search_jobs(query="Python Developer", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_indeed_scraper():
    scraper = IndeedScraper()
    jobs = scraper.search_jobs(query="Python", location="Remote", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_wellfound_scraper():
    scraper = WellfoundScraper()
    jobs = scraper.search_jobs(query="Python", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_cutshort_hirist_scraper():
    scraper = CutshortHiristScraper()
    jobs = scraper.search_jobs(query="Python", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_weworkremotely_scraper():
    scraper = WeWorkRemotelyScraper()
    jobs = scraper.search_jobs(query="Python", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_flexjobs_scraper():
    scraper = FlexJobsScraper()
    jobs = scraper.search_jobs(query="Python", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_remote_co_scraper():
    scraper = RemoteCoScraper()
    jobs = scraper.search_jobs(query="Developer", limit=3)
    assert isinstance(jobs, list)
    assert all(isinstance(j, JobPosting) for j in jobs)
