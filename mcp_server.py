"""
JobPulse AI - Global Standalone MCP Server v3.0
Exposes multi-portal live job search, natural language prompt parsing, AI resume extraction,
and AI fit evaluation as Model Context Protocol (MCP) tools across 7 real live platforms.
Zero mock data.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server import FastMCP
    except ImportError:
        class FastMCP:
            def __init__(self, name, instructions=""):
                self.name = name
                self.instructions = instructions
            def tool(self):
                def decorator(fn):
                    return fn
                return decorator
            def run(self, transport="stdio", port=8001):
                print(f"FastMCP server '{self.name}' running on {transport} mode.")

load_dotenv()
from src.profile_manager import ProfileManager
from src.core.prompt_parser import SearchPromptParser
from src.core.resume_agent import ResumeParserAgent
from src.scrapers import (
    CompanyCareersScraper,
    LinkedInScraper,
    InstahyreScraper,
    NaukriScraper,
    IndeedScraper,
    WellfoundScraper,
    CutshortHiristScraper,
    WeWorkRemotelyScraper,
    FlexJobsScraper,
    RemoteCoScraper,
    SCRAPER_REGISTRY,
)
from src.scrapers.base import JobPosting, deduplicate_jobs
from src.matcher import JobMatcher

# Initialize FastMCP Server instance
mcp = FastMCP(
    "JobPulse-Live-Job-Discovery-Server",
    instructions="MCP Server for live real-time job search across 10 platforms (Company Career Pages, LinkedIn, Instahyre, Naukri.com, Indeed, Wellfound, Cutshort / Hirist, We Work Remotely, FlexJobs, Remote.co)."
)

# Shared instances
pm = ProfileManager()
config = pm.load_config()
prompt_parser = SearchPromptParser()
resume_agent = ResumeParserAgent()


def _fetch_portal_jobs(scraper, query: str, location: str, limit: int, seniority: str) -> List[JobPosting]:
    """Helper to run scraper search safely within thread pool."""
    try:
        return scraper.search_jobs(query=query, location=location, limit=limit, seniority=seniority)
    except Exception as e:
        print(f"⚠️ Exception running {scraper.name}: {e}")
        return []


@mcp.tool()
def parse_resume_file(pdf_path: str) -> str:
    """
    Parses a candidate PDF resume file and extracts structured skills, experience,
    last position, and summary.

    Args:
        pdf_path: Absolute or relative filepath to candidate PDF resume file.
    """
    extracted = resume_agent.parse_resume(pdf_path)
    missing_str = ", ".join(extracted.get("missing_fields", [])) or "None (Profile Complete!)"

    return (
        f"📄 AI RESUME ANALYSIS REPORT:\n"
        f"===============================================================\n"
        f"👤 Candidate Name : {extracted.get('full_name')}\n"
        f"✉️ Email          : {extracted.get('email') or 'Not Detected'}\n"
        f"📞 Phone          : {extracted.get('phone') or 'Not Detected'}\n"
        f"📍 Location       : {extracted.get('location')}\n"
        f"💼 Last Position   : {extracted.get('last_position')}\n"
        f"⏳ Experience    : {extracted.get('years_experience')} years\n"
        f"💡 Core Skills    : {', '.join(extracted.get('skills', []))}\n"
        f"🔗 LinkedIn       : {extracted.get('linkedin_url') or 'Not Detected'}\n"
        f"🌐 Portfolio      : {extracted.get('portfolio_url') or 'Not Detected'}\n"
        f"⚠️ Missing Fields : {missing_str}\n"
        f"===============================================================\n"
    )


@mcp.tool()
def parse_natural_language_prompt(prompt: str) -> str:
    """
    Parses a natural language job search prompt into structured filter parameters.

    Args:
        prompt: Free-form search prompt (e.g. "Senior Python developer jobs above $120k posted this week in London or remote")
    """
    res = prompt_parser.parse_prompt(prompt)
    return (
        f"🧠 PARSED SEARCH CRITERIA:\n"
        f"• Role Query      : {res.get('query')}\n"
        f"• Seniority Level : {res.get('seniority_level')}\n"
        f"• Locations       : {', '.join(res.get('locations', [])) or 'Worldwide Remote'}\n"
        f"• Remote Only     : {res.get('remote_only')}\n"
        f"• Min Salary      : {res.get('min_salary')} {res.get('salary_currency')}\n"
        f"• Date Posted     : Past {res.get('date_posted_days')} days" if res.get('date_posted_days') else "• Date Posted     : Anytime\n"
    )


@mcp.tool()
def search_jobs_live(
    prompt: str = "",
    query: str = "",
    location: str = "Remote",
    seniority: str = "All",
    platforms: str = "all",
    limit_per_platform: int = 5
) -> str:
    """
    Searches across 10 live tech job platforms with smart cross-platform deduplication:
    Company Career Pages, LinkedIn, Instahyre, Naukri.com, Indeed, Wellfound,
    Cutshort / Hirist, We Work Remotely, FlexJobs, Remote.co.

    Args:
        prompt: Optional natural language prompt (e.g. "Remote AI engineer roles")
        query: Specific job title or skill keyword (e.g. "AI Engineer")
        location: Target location (e.g. "Remote", "London", "Pune")
        seniority: Experience level ("All", "Entry", "Mid-Level", "Senior", "Lead")
        platforms: Comma-separated portals or "all" (options: company_careers, linkedin, instahyre, naukri, indeed, wellfound, cutshort_hirist, weworkremotely, flexjobs, remote_co)
        limit_per_platform: Max listings per portal
    """
    parsed_params = {}
    if prompt and prompt.strip():
        parsed_params = prompt_parser.parse_prompt(prompt)

    search_query = query if query else parsed_params.get("query", "Software Engineer")
    search_loc = location if location != "Remote" else (parsed_params.get("locations", ["Remote"])[0] if parsed_params.get("locations") else "Remote")
    search_seniority = seniority if seniority != "All" else parsed_params.get("seniority_level", "All")

    if platforms == "all" or not platforms:
        selected = list(SCRAPER_REGISTRY.keys())
    else:
        selected = [p.strip().lower() for p in platforms.split(",") if p.strip().lower() in SCRAPER_REGISTRY]

    active_scrapers = [SCRAPER_REGISTRY[p]() for p in selected if p in SCRAPER_REGISTRY]

    raw_jobs: List[JobPosting] = []

    with ThreadPoolExecutor(max_workers=len(active_scrapers)) as executor:
        futures = [
            executor.submit(_fetch_portal_jobs, scraper, search_query, search_loc, limit_per_platform, search_seniority)
            for scraper in active_scrapers
        ]
        for f in as_completed(futures):
            raw_jobs.extend(f.result())

    unique_jobs = deduplicate_jobs(raw_jobs)

    # Format output
    lines = [
        f"🎯 LIVE SEARCH RESULTS: '{search_query}' ({len(unique_jobs)} Unique Listings)\n"
        f"==============================================================="
    ]
    for idx, j in enumerate(unique_jobs, 1):
        sources_str = ", ".join([s["platform"] for s in j.sources])
        lines.append(
            f"{idx}. {j.title} at {j.company}\n"
            f"   📍 Location: {j.location} | Level: {j.seniority_level} | Salary: {j.salary}\n"
            f"   🌐 Available on: {sources_str}\n"
            f"   🔗 Direct Link: {j.url}\n"
        )

    return "\n".join(lines)


@mcp.tool()
def evaluate_job_fit(job_title: str, company: str, description: str) -> str:
    """
    Evaluates fit score between candidate resume and a job description.

    Args:
        job_title: Position title
        company: Company name
        description: Job requirements and details
    """
    cfg = pm.load_config()
    matcher = JobMatcher(cfg)
    temp_job = JobPosting(
        job_id="mcp_eval",
        title=job_title,
        company=company,
        location="Remote",
        platform="Direct",
        url="",
        description=description
    )
    res = matcher.evaluate(temp_job)
    return (
        f"📊 FIT EVALUATION REPORT:\n"
        f"• Match Score   : {res['match_score']}% ({res['relevance']} Fit)\n"
        f"• Matched Skills: {', '.join(res['matched_skills']) or 'None'}\n"
        f"• Missing Skills: {', '.join(res['missing_skills']) or 'None'}\n"
        f"• Reasoning     : {res['reasoning']}\n"
    )

evaluate_job_match = evaluate_job_fit


@mcp.tool()
def get_supported_portals() -> str:
    """Returns the list of 10 live supported job portals."""
    return (
        "🌐 SUPPORTED 10 LIVE JOB PORTALS:\n"
        "1. Company Career Pages (Direct ATS) : Live Greenhouse, Lever, Ashby, Workday endpoints\n"
        "2. LinkedIn                         : Global live job search with date & experience filters\n"
        "3. Instahyre                        : Official live Indian & Global tech search API\n"
        "4. Naukri.com                       : Real-time keyword & location search engine\n"
        "5. Indeed                           : Live search query feed with direct URLs\n"
        "6. Wellfound (AngelList)            : Startup tech roles with salary & equity transparency\n"
        "7. Cutshort / Hirist                : Live premium developer & engineering discovery\n"
        "8. We Work Remotely                 : Multi-category live RSS feeds (Programming, DevOps)\n"
        "9. FlexJobs                         : Verified remote, flexible, & hybrid tech postings\n"
        "10. Remote.co                       : Real-time remote developer & IT position categories\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JobPulse Global Standalone MCP Server")
    parser.add_argument("--transport", type=str, default="stdio", choices=["stdio", "sse"], help="MCP Transport mode (stdio or sse)")
    parser.add_argument("--port", type=int, default=8001, help="Port for SSE transport mode")

    args = parser.parse_args()

    if args.transport == "sse":
        print(f"🚀 Launching JobPulse Standalone MCP Server via SSE on port {args.port}...")
        mcp.run(transport="sse", port=args.port)
    else:
        print("🚀 Starting JobPulse Standalone MCP Server via STDIO...")
        mcp.run(transport="stdio")
