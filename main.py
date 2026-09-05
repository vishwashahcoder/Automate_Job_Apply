"""
CLI Entrypoint for JobPulse AI - Multi-Platform Job Discovery & Fit Engine.
Supports the 10 target platforms:
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

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.profile_manager import ProfileManager
from src.scrapers import SCRAPER_REGISTRY
from src.scrapers.base import JobPosting, deduplicate_jobs
from src.matcher import JobMatcher
from src.core.prompt_parser import SearchPromptParser
from src.notifier.cli_notifier import CLINotifier


def print_banner():
    print("""
    ===================================================================
       🚀 JOBPULSE AI - MULTI-PLATFORM TECH JOB DISCOVERY ENGINE v4.0
       🎯 10 Live Portals | Smart Cross-Platform Deduplication | Fit AI
    ===================================================================
    """, flush=True)


def _fetch_safe(scraper, query: str, location: str, limit: int) -> List[JobPosting]:
    """Helper to run scraper search safely within thread pool."""
    try:
        return scraper.search_jobs(query=query, location=location, limit=limit)
    except Exception as e:
        print(f"⚠️ [Search Note] {scraper.name}: {e}", flush=True)
        return []


def main():
    print_banner()

    # 1. Initialize Profile Manager & Questionnaire
    pm = ProfileManager()

    # Check if non-interactive / fast-run flag is passed
    if "--skip-questionnaire" not in sys.argv and "--no-prompt" not in sys.argv:
        pm.ask_user_questions()

    pm.print_summary()
    config = pm.load_config()

    prefs = config.get("preferences", {})
    job_titles = prefs.get("job_titles", ["Python Developer", "AI Engineer"])
    locations = prefs.get("locations", ["Remote", "Worldwide"])
    platforms_pref = [p.lower().strip() for p in prefs.get("platforms", list(SCRAPER_REGISTRY.keys()))]

    # 2. Select Active Scrapers
    active_scrapers = []
    for key, scraper_cls in SCRAPER_REGISTRY.items():
        if key in platforms_pref or not platforms_pref:
            active_scrapers.append(scraper_cls())

    if not active_scrapers:
        active_scrapers = [scraper_cls() for scraper_cls in SCRAPER_REGISTRY.values()]

    print(f"📡 Active Platforms ({len(active_scrapers)}): {', '.join([s.name for s in active_scrapers])}\n", flush=True)

    # 3. Matcher & Notifier
    matcher = JobMatcher(config)

    all_found_jobs: List[JobPosting] = []

    # 4. Perform Parallel Multi-Platform Discovery
    tasks = []
    with ThreadPoolExecutor(max_workers=len(active_scrapers) * 2) as executor:
        for title in job_titles[:1]: # primary role
            for loc in locations[:1]: # primary location
                for scraper in active_scrapers:
                    tasks.append(executor.submit(_fetch_safe, scraper, title, loc, 3))

        for f in as_completed(tasks):
            jobs = f.result()
            if jobs:
                all_found_jobs.extend(jobs)

    # 5. Smart Cross-Platform Deduplication
    unique_jobs = deduplicate_jobs(all_found_jobs)

    print(f"\n✨ Total Authentic Jobs Discovered: {len(all_found_jobs)} -> Clustered to {len(unique_jobs)} Unique Listings\n", flush=True)

    # 6. Evaluate Fit Scores & Application Tracker
    for idx, job in enumerate(unique_jobs, 1):
        print(f"\n🔍 [{idx}/{len(unique_jobs)}] Posting: '{job.title}' at {job.company} [{job.location}]", flush=True)
        
        # Display Cross-Platform Sources
        sources_str = ", ".join([s["platform"] for s in job.sources])
        print(f"   🔗 Available on: {sources_str} | Direct URL: {job.url}", flush=True)

        match_info = matcher.evaluate(job)
        score = match_info['match_score']
        sub = match_info.get("sub_scores", {})

        print(f"   📊 AI Fit Score: {score}% ({match_info['relevance']} Fit)", flush=True)
        print(f"      ├─ Skill Match (40%): {sub.get('skill_match_40', 0)} / 40.0", flush=True)
        print(f"      ├─ Title Match (25%): {sub.get('title_match_25', 0)} / 25.0", flush=True)
        print(f"      ├─ Seniority   (15%): {sub.get('experience_fit_15', 0)} / 15.0 ({job.seniority_level})", flush=True)
        print(f"      └─ Salary Fit  (10%): {sub.get('salary_fit_10', 0)} / 10.0 ({job.salary})", flush=True)
        print(f"   💡 Reasoning: {match_info.get('reasoning', '')}", flush=True)

    print("\n===================================================================", flush=True)
    print("                    🎉 JOB SEARCH SUMMARY                          ", flush=True)
    print("===================================================================", flush=True)
    print(f"Total Unique Listings Found: {len(unique_jobs)}", flush=True)
    print("To search with interactive UI, run: python app.py and open http://localhost:8000", flush=True)
    print("===================================================================\n", flush=True)


if __name__ == "__main__":
    main()
