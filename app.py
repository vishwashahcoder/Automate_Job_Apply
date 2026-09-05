"""
JobPulse AI - Multi-Platform Job Search & Aggregation Engine.
FastAPI Backend providing live multi-source job discovery, LinkedIn-style search logic,
cross-platform smart deduplication, prompt-to-filter parsing, and application tracking.
Zero mock data.
"""

import os
import sys
import json
import time
import asyncio
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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
from database import db

app = FastAPI(
    title="JobPulse AI - Multi-Platform Job Discovery Engine",
    version="4.0.0",
    description="High-accuracy job aggregator querying 10 live platforms, smart cross-platform deduplication, and AI prompt search."
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# SSE Event Log Queue
event_queue = asyncio.Queue()


async def broadcast_log(message: str, level: str = "INFO"):
    """Pushes activity message to SSE queue and SQLite database."""
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    db.log_activity(formatted_msg, level)
    await event_queue.put({"message": formatted_msg, "level": level})


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serves main Web App Dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/profile")
async def get_profile():
    """Gets candidate profile and search preferences."""
    pm = ProfileManager()
    return pm.load_config()


@app.post("/api/profile")
async def update_profile(data: Dict[str, Any]):
    """Updates candidate profile and search parameters."""
    pm = ProfileManager()
    pm.config = data
    pm.save_config()
    await broadcast_log("✅ Candidate profile updated successfully.")
    return {"status": "success", "message": "Profile updated."}


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Accepts PDF resume upload, extracts candidate profile using AI Resume Agent,
    and updates profile preferences.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resume files (.pdf) are supported.")

    file_bytes = await file.read()

    # Clean up previous files in uploads/
    for existing_file in glob.glob(os.path.join(UPLOADS_DIR, "*.pdf")):
        try:
            os.remove(existing_file)
        except Exception:
            pass

    save_path = os.path.join(UPLOADS_DIR, "candidate_resume.pdf")
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    await broadcast_log(f"📄 New PDF resume uploaded ('{file.filename}'). Extracting candidate profile...")

    agent = ResumeParserAgent()
    extracted = agent.parse_resume(file_bytes)

    pm = ProfileManager()
    config = pm.load_config()

    new_prof = {
        "full_name": extracted.get("full_name", ""),
        "email": extracted.get("email", ""),
        "phone": extracted.get("phone", ""),
        "location": extracted.get("location", ""),
        "portfolio_url": extracted.get("portfolio_url", ""),
        "linkedin_url": extracted.get("linkedin_url", ""),
        "years_experience": extracted.get("years_experience", 0),
        "last_position": extracted.get("last_position", ""),
        "skills": extracted.get("skills", []),
        "summary": extracted.get("summary", ""),
        "resume_pdf_path": save_path,
        "resume_filename": file.filename,
        "missing_fields": extracted.get("missing_fields", [])
    }
    config["resume_profile"] = new_prof
    pm.config = config
    pm.save_config()

    await broadcast_log(
        f"🤖 Resume analyzed! Candidate: {new_prof.get('full_name')} ({new_prof.get('last_position')}) | {len(new_prof.get('skills', []))} Skills extracted.",
        level="SUCCESS"
    )

    return {
        "status": "success",
        "message": "Resume uploaded and analyzed.",
        "extracted_profile": new_prof,
        "missing_fields": extracted.get("missing_fields", [])
    }


@app.get("/api/download-resume")
async def download_resume():
    """Serves the active uploaded PDF resume file for preview."""
    pm = ProfileManager()
    config = pm.load_config()
    prof = config.get("resume_profile", {})
    resume_path = prof.get("resume_pdf_path", "")

    if not resume_path or not os.path.exists(resume_path):
        default_path = os.path.join(UPLOADS_DIR, "candidate_resume.pdf")
        if os.path.exists(default_path):
            resume_path = default_path
        else:
            raise HTTPException(status_code=404, detail="No resume file uploaded yet.")

    filename = prof.get("resume_filename") or os.path.basename(resume_path)
    return FileResponse(
        path=resume_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@app.post("/api/parse-prompt")
async def parse_search_prompt(payload: Dict[str, Any]):
    """Parses natural language prompt into structured search filter parameters."""
    prompt_text = payload.get("prompt", "")
    parser = SearchPromptParser()
    parsed = parser.parse_prompt(prompt_text)
    return parsed


@app.get("/api/jobs")
async def list_jobs(
    status: str = "ALL",
    platform: Optional[str] = None,
    seniority: Optional[str] = None,
    min_score: int = 0
):
    """Returns stored jobs from database with optional filtering."""
    jobs = db.get_all_jobs()
    if status != "ALL":
        jobs = [j for j in jobs if j.get("apply_status") == status]
    if platform and platform != "ALL":
        jobs = [j for j in jobs if platform.lower() in [s.get("platform", "").lower() for s in j.get("sources", [])] or platform.lower() in j.get("platform", "").lower()]
    if seniority and seniority != "ALL":
        jobs = [j for j in jobs if j.get("seniority_level", "").lower() == seniority.lower()]
    if min_score > 0:
        jobs = [j for j in jobs if j.get("match_score", 0) >= min_score]
    return jobs


@app.get("/api/stats")
async def get_dashboard_stats():
    """Returns analytics and dashboard statistics."""
    return db.get_stats()


@app.post("/api/job/{job_id}/status")
async def update_job_status(job_id: str, payload: Dict[str, Any]):
    """Updates job application stage (APPLIED, SAVED, PENDING, IGNORED)."""
    status = payload.get("status", "PENDING").upper()
    applied_time = time.strftime("%Y-%m-%d %H:%M:%S") if status == "APPLIED" else None
    db.update_job_status(job_id, status, applied_time)
    await broadcast_log(f"📌 Job status updated: '{job_id}' is now {status}.")
    return {"status": "success", "job_id": job_id, "new_status": status}


active_search_cancelled = False


@app.post("/api/search")
async def run_job_search(payload: Optional[Dict[str, Any]] = None, background_tasks: BackgroundTasks = None):
    """Launches live parallel job discovery across 7 platforms with smart deduplication."""
    global active_search_cancelled
    active_search_cancelled = False
    filters = payload or {}
    background_tasks.add_task(perform_search_task, filters)
    return {"status": "initiated", "message": "Live job discovery started."}


@app.post("/api/stop-search")
async def stop_job_search():
    """Cancels any currently running background job discovery task."""
    global active_search_cancelled
    active_search_cancelled = True
    await broadcast_log("🛑 Active job discovery stopped by user.", level="WARNING")
    return {"status": "cancelled", "message": "Search process stopped."}


def _run_scraper_safe(scraper, query: str, location: str, limit: int, seniority: str, date_days: Optional[int], remote_only: bool) -> List[JobPosting]:
    """Helper to run scraper search safely in thread pool."""
    try:
        return scraper.search_jobs(
            query=query,
            location=location,
            limit=limit,
            seniority=seniority,
            date_posted_days=date_days,
            remote_only=remote_only
        )
    except Exception as e:
        print(f"⚠️ Exception running {scraper.name}: {e}")
        return []


async def perform_search_task(filter_payload: Dict[str, Any]):
    """Task orchestrator for live multi-platform search, smart deduplication, and AI scoring."""
    global active_search_cancelled
    try:
        pm = ProfileManager()
        config = pm.load_config()
        profile = config.get("resume_profile", {})

        prompt_text = filter_payload.get("prompt", "").strip()
        prompt_parser = SearchPromptParser()
        parsed_prompt = prompt_parser.parse_prompt(prompt_text) if prompt_text else {}

        # Merge explicit UI filters with parsed prompt criteria
        query = filter_payload.get("query") or parsed_prompt.get("query", "").strip()
        if not query:
            last_pos = profile.get("last_position", "").strip()
            user_skills = [s for s in profile.get("skills", []) if s and len(s) > 2]
            query = last_pos if (last_pos and len(last_pos) > 2) else (user_skills[0] if user_skills else "Software Engineer")

        locations = filter_payload.get("locations") or parsed_prompt.get("locations") or ["Worldwide Remote", "Remote"]
        seniority = filter_payload.get("seniority_level") or parsed_prompt.get("seniority_level", "All")
        remote_only = filter_payload.get("remote_only") if "remote_only" in filter_payload else parsed_prompt.get("remote_only", False)
        date_days = filter_payload.get("date_posted_days") if "date_posted_days" in filter_payload else parsed_prompt.get("date_posted_days")
        selected_platforms = filter_payload.get("platforms") or parsed_prompt.get("platforms") or list(SCRAPER_REGISTRY.keys())
        min_fit_score = filter_payload.get("min_fit_score", 40)

        # Instantiate selected live scrapers
        active_scrapers = []
        for plat_key in selected_platforms:
            scraper_cls = SCRAPER_REGISTRY.get(plat_key.lower())
            if scraper_cls:
                active_scrapers.append(scraper_cls())

        if not active_scrapers:
            active_scrapers = [cls() for cls in SCRAPER_REGISTRY.values()]

        # AI Intent & Search Criteria Synthesis
        source_priority = "User Prompt (Primary)" if prompt_text else ("Dashboard Filter" if filter_payload.get("query") else "Resume Profile Context")
        min_sal = filter_payload.get("min_salary") or parsed_prompt.get("min_salary", 0)
        sal_curr = filter_payload.get("salary_currency") or parsed_prompt.get("salary_currency", "INR")
        
        sal_display = f"{min_sal/100000:.1f} LPA ({sal_curr})" if (sal_curr == "INR" and min_sal >= 100000) else (f"${min_sal:,.0f} ({sal_curr})" if min_sal > 0 else "Any")
        loc_display = ", ".join(locations) if isinstance(locations, list) else str(locations)

        await broadcast_log(
            f"🧠 AI Intent Synthesized: Target Role: '{query}' | Location: '{loc_display}' | Seniority: {seniority} | Min Salary: {sal_display} | Priority: {source_priority}",
            level="SUCCESS"
        )

        platform_names = ", ".join([s.name for s in active_scrapers])
        await broadcast_log(f"🚀 Starting live search for '{query}' across {len(active_scrapers)} platforms ({platform_names})...")

        raw_jobs: List[JobPosting] = []

        # Parallel Execution across scrapers
        with ThreadPoolExecutor(max_workers=len(active_scrapers)) as executor:
            futures = []
            for scraper in active_scrapers:
                loc = locations[0] if locations else "Remote"
                futures.append(
                    executor.submit(
                        _run_scraper_safe,
                        scraper,
                        query,
                        loc,
                        15,
                        seniority if seniority != "All" else "",
                        date_days,
                        remote_only
                    )
                )

            for future in as_completed(futures):
                if active_search_cancelled:
                    break
                res_jobs = future.result()
                raw_jobs.extend(res_jobs)
                await asyncio.sleep(0.05)

        if active_search_cancelled:
            await broadcast_log("🛑 Search cancelled.", level="WARNING")
            return

        # Clear previous search results
        db.clear_all_jobs()

        # Smart Cross-Platform Deduplication
        unique_jobs = deduplicate_jobs(raw_jobs)

        # Filter by remote if remote_only is strictly set
        if remote_only:
            unique_jobs = [j for j in unique_jobs if j.is_remote or "remote" in j.location.lower() or "worldwide" in j.location.lower()]

        # Filter by Seniority if specified
        if seniority and seniority != "All":
            unique_jobs = [j for j in unique_jobs if j.seniority_level.lower() == seniority.lower() or j.seniority_level == "Mid-Level"]

        # Platform Breakdown Statistics
        platform_counts: Dict[str, int] = {}
        multi_source_count = 0
        for j in unique_jobs:
            for src in j.sources:
                plat = src.get("platform", "Unknown")
                platform_counts[plat] = platform_counts.get(plat, 0) + 1
            if len(j.sources) > 1:
                multi_source_count += 1

        breakdown_text = ", ".join([f"{plat}: {count}" for plat, count in platform_counts.items()])
        await broadcast_log(
            f"📊 Found {len(unique_jobs)} unique listings ({breakdown_text}). {multi_source_count} cross-platform duplicates clustered!",
            level="SUCCESS"
        )

        # AI Fit Evaluation
        matcher = JobMatcher(
            config,
            prompt_criteria={
                "query": query,
                "seniority_level": seniority,
                "min_salary": min_sal,
                "salary_currency": sal_curr,
                "locations": locations
            }
        )

        high_matches = 0
        for idx, job in enumerate(unique_jobs, 1):
            match_info = matcher.evaluate(job)
            db.save_job(job.to_dict(), match_info)

            if match_info.get("match_score", 0) >= min_fit_score:
                high_matches += 1

        await broadcast_log(
            f"🎉 Search Complete! Saved {len(unique_jobs)} jobs ({high_matches} matches fitting your profile).",
            level="SUCCESS"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        await broadcast_log(f"⚠️ Search error: {str(e)}", level="WARNING")


@app.get("/api/stream")
async def event_stream(request: Request):
    """Server-Sent Events endpoint streaming live log updates."""
    async def log_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(event_queue.get(), timeout=0.5)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    continue
        except (asyncio.CancelledError, GeneratorExit):
            pass

    return StreamingResponse(log_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
