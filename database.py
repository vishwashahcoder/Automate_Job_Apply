"""
SQLite Database Manager for JobPulse AI Platform.
Stores authentic multi-platform job listings, cross-platform source links,
AI fit scores, candidate profile, and application status history.
"""

import sqlite3
import json
import os
import time
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "jobpulse.db")


class DatabaseManager:
    """SQLite Database Manager for JobPulse AI Platform."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Creates necessary tables for jobs, profile, and activity logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")

            # Profile Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    config_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Activity Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    level TEXT DEFAULT 'INFO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Jobs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    sources TEXT,
                    url TEXT NOT NULL,
                    description TEXT,
                    salary TEXT,
                    salary_min REAL,
                    salary_max REAL,
                    salary_currency TEXT DEFAULT 'USD',
                    seniority_level TEXT DEFAULT 'Mid-Level',
                    job_type TEXT DEFAULT 'Full-time',
                    is_remote INTEGER DEFAULT 0,
                    posted_date TEXT DEFAULT 'Recently',
                    posted_timestamp INTEGER DEFAULT 0,
                    tags TEXT,
                    match_score INTEGER DEFAULT 0,
                    relevance TEXT DEFAULT 'Medium',
                    matched_skills TEXT,
                    missing_skills TEXT,
                    reasoning TEXT,
                    sub_scores TEXT,
                    apply_status TEXT DEFAULT 'PENDING',
                    applied_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Dynamic migrations for any missing columns
            cursor.execute("PRAGMA table_info(jobs)")
            cols = [info[1] for info in cursor.fetchall()]
            new_columns = [
                ("sources", "TEXT"),
                ("salary_min", "REAL"),
                ("salary_max", "REAL"),
                ("salary_currency", "TEXT DEFAULT 'USD'"),
                ("seniority_level", "TEXT DEFAULT 'Mid-Level'"),
                ("job_type", "TEXT DEFAULT 'Full-time'"),
                ("is_remote", "INTEGER DEFAULT 0"),
                ("posted_date", "TEXT DEFAULT 'Recently'"),
                ("posted_timestamp", "INTEGER DEFAULT 0"),
                ("tags", "TEXT"),
                ("match_score", "INTEGER DEFAULT 0"),
                ("relevance", "TEXT DEFAULT 'Medium'"),
                ("matched_skills", "TEXT"),
                ("missing_skills", "TEXT"),
                ("reasoning", "TEXT"),
                ("sub_scores", "TEXT"),
                ("apply_status", "TEXT DEFAULT 'PENDING'"),
                ("applied_at", "TEXT")
            ]
            for col_name, col_type in new_columns:
                if col_name not in cols:
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")

            conn.commit()

    @staticmethod
    def _safe_json_loads(val: Any, default: Any) -> Any:
        """Safely parses JSON strings, returning default on failure."""
        if not val:
            return default
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return default

    def clear_all_jobs(self) -> None:
        """Deletes all stored jobs from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs")
            conn.commit()

    def save_job(self, job_dict: Dict[str, Any], match_info: Dict[str, Any]) -> None:
        """Inserts or updates a job posting and its AI match score."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            sources_json = json.dumps(job_dict.get("sources") or [{"platform": job_dict.get("platform", "Unknown"), "url": job_dict.get("url", "")}])
            matched_skills_json = json.dumps(match_info.get("matched_skills", []))
            missing_skills_json = json.dumps(match_info.get("missing_skills", []))
            sub_scores_json = json.dumps(match_info.get("sub_scores", {}))
            tags_json = json.dumps(job_dict.get("tags", []))

            cursor.execute("""
                INSERT INTO jobs (
                    job_id, title, company, location, platform, sources, url, description, salary,
                    salary_min, salary_max, salary_currency, seniority_level, job_type, is_remote,
                    posted_date, posted_timestamp, tags, match_score, relevance, matched_skills,
                    missing_skills, reasoning, sub_scores, apply_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
                ON CONFLICT(job_id) DO UPDATE SET
                    title=excluded.title,
                    company=excluded.company,
                    location=excluded.location,
                    sources=excluded.sources,
                    url=excluded.url,
                    description=excluded.description,
                    salary=excluded.salary,
                    salary_min=excluded.salary_min,
                    salary_max=excluded.salary_max,
                    salary_currency=excluded.salary_currency,
                    seniority_level=excluded.seniority_level,
                    job_type=excluded.job_type,
                    is_remote=excluded.is_remote,
                    posted_date=excluded.posted_date,
                    tags=excluded.tags,
                    match_score=excluded.match_score,
                    relevance=excluded.relevance,
                    matched_skills=excluded.matched_skills,
                    missing_skills=excluded.missing_skills,
                    reasoning=excluded.reasoning,
                    sub_scores=excluded.sub_scores
            """, (
                job_dict['job_id'],
                job_dict['title'],
                job_dict['company'],
                job_dict['location'],
                job_dict['platform'],
                sources_json,
                job_dict['url'],
                job_dict.get('description', ''),
                job_dict.get('salary', 'Not Disclosed'),
                job_dict.get('salary_min'),
                job_dict.get('salary_max'),
                job_dict.get('salary_currency', 'USD'),
                job_dict.get('seniority_level', 'Mid-Level'),
                job_dict.get('job_type', 'Full-time'),
                1 if job_dict.get('is_remote') else 0,
                job_dict.get('posted_date', 'Recently'),
                job_dict.get('posted_timestamp', int(time.time())),
                tags_json,
                match_info.get('match_score', 0),
                match_info.get('relevance', 'Medium'),
                matched_skills_json,
                missing_skills_json,
                match_info.get('reasoning', ''),
                sub_scores_json
            ))
            conn.commit()

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Retrieves all jobs ordered by match score descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY match_score DESC, created_at DESC")
            rows = cursor.fetchall()

            jobs = []
            for row in rows:
                j = dict(row)
                j['sources'] = self._safe_json_loads(j.get('sources'), [{"platform": j.get("platform", "Unknown"), "url": j.get("url", "")}])
                j['matched_skills'] = self._safe_json_loads(j.get('matched_skills'), [])
                j['missing_skills'] = self._safe_json_loads(j.get('missing_skills'), [])
                j['sub_scores'] = self._safe_json_loads(j.get('sub_scores'), {})
                j['tags'] = self._safe_json_loads(j.get('tags'), [])
                j['is_remote'] = bool(j.get('is_remote', False))
                jobs.append(j)
            return jobs

    def update_job_status(self, job_id: str, status: str, applied_at: Optional[str] = None) -> None:
        """Updates apply status (APPLIED, SAVED, PENDING, IGNORED) for a job."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs SET apply_status = ?, applied_at = ? WHERE job_id = ?
            """, (status, applied_at, job_id))
            conn.commit()

    def log_activity(self, message: str, level: str = "INFO") -> None:
        """Logs platform activity to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO activity_logs (message, level) VALUES (?, ?)", (message, level))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Calculates dashboard analytics metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 70")
            high_match = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM jobs WHERE apply_status = 'APPLIED'")
            applied = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM jobs WHERE apply_status = 'SAVED'")
            saved = cursor.fetchone()[0]

            return {
                "total_discovered": total,
                "high_match_count": high_match,
                "applications_submitted": applied,
                "jobs_saved": saved,
                "platforms_connected": 10
            }


db = DatabaseManager()
