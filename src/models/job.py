"""
Job Posting Model & Cross-Platform Smart Deduplication for JobPulse AI.
Provides structured job representation, multi-source clustering, and normalization.
"""

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Union, Optional


def make_hashable(val: Any) -> Any:
    """Recursively converts unhashable types (dicts, lists, sets) into hashable counterparts."""
    if isinstance(val, dict):
        return frozenset((k, make_hashable(v)) for k, v in val.items())
    elif isinstance(val, (list, tuple, set)):
        return tuple(make_hashable(item) for item in val)
    return val


def normalize_company_name(name: str) -> str:
    """Normalizes company names by removing legal entity suffixes and whitespace."""
    if not name:
        return ""
    clean = name.lower().strip()
    clean = re.sub(r"\b(inc|incorporated|llc|ltd|limited|corp|corporation|gmbh|pvt|private|technologies|solutions)\b", "", clean)
    clean = re.sub(r"[^\w\s]", "", clean)
    return " ".join(clean.split())


def normalize_job_title(title: str) -> str:
    """Normalizes job titles for fuzzy deduplication across platforms."""
    if not title:
        return ""
    clean = title.lower().strip()
    clean = re.sub(r"\bsr\.?\b", "senior", clean)
    clean = re.sub(r"\bjr\.?\b", "junior", clean)
    clean = re.sub(r"\bdev\b", "developer", clean)
    clean = re.sub(r"\beng\b", "engineer", clean)
    clean = re.sub(r"\bsw\b", "software", clean)
    clean = re.sub(r"[\(\[\-–—]\s*(remote|worldwide|hybrid|full[- ]time|contract|usa?|india|uk)\s*[\)\]]?", "", clean)
    clean = re.sub(r"[^\w\s]", " ", clean)
    return " ".join(clean.split())


def extract_seniority(title: str, description: str = "") -> str:
    """Extracts standardized seniority level from title and description."""
    text = (title + " " + description).lower()
    if any(k in text for k in ["lead", "principal", "staff", "head of", "director", "vp", "architect", "manager"]):
        return "Lead"
    if any(k in text for k in ["senior", "sr.", "sr ", "experienced", "5+ years", "6+ years", "7+ years", "8+ years"]):
        return "Senior"
    if any(k in text for k in ["junior", "jr.", "jr ", "intern", "internship", "entry level", "entry-level", "fresher", "graduate"]):
        return "Entry"
    return "Mid-Level"


@dataclass
class JobPosting:
    """Structured Job Posting Data Class with multi-source tracking."""
    job_id: str
    title: str
    company: str
    location: str
    platform: str
    url: str
    description: str = ""
    posted_date: str = "Recently"
    posted_timestamp: int = 0
    salary: str = "Not Disclosed"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    job_type: str = "Full-time"
    seniority_level: str = "Mid-Level"
    is_remote: bool = False
    tags: List[str] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)
    company_website: str = ""
    experience_required: str = ""
    company_summary: str = ""
    role_summary: str = ""
    apply_status: str = "PENDING"

    def __post_init__(self):
        if not self.sources and self.platform and self.url:
            self.sources = [{"platform": self.platform, "url": self.url}]
        if not self.seniority_level or self.seniority_level == "Mid-Level":
            self.seniority_level = extract_seniority(self.title, self.description)
        if not self.posted_timestamp:
            self.posted_timestamp = int(time.time())

    def __hash__(self) -> int:
        if self.job_id:
            return hash(self.job_id)
        return hash((self.title.lower().strip(), self.company.lower().strip()))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, JobPosting):
            return self.job_id == other.job_id or (
                self.title.lower().strip() == other.title.lower().strip() and
                self.company.lower().strip() == other.company.lower().strip()
            )
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Converts JobPosting to standard Python dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobPosting":
        """Instantiates a JobPosting from a dictionary safely."""
        sources = data.get("sources") or []
        if not sources and data.get("platform") and data.get("url"):
            sources = [{"platform": data.get("platform"), "url": data.get("url")}]

        return cls(
            job_id=str(data.get("job_id", "")),
            title=str(data.get("title", "")),
            company=str(data.get("company", "")),
            location=str(data.get("location", "")),
            platform=str(data.get("platform", "Unknown")),
            url=str(data.get("url", "")),
            description=str(data.get("description", "")),
            posted_date=str(data.get("posted_date", "Recently")),
            posted_timestamp=int(data.get("posted_timestamp", int(time.time()))),
            salary=str(data.get("salary", "Not Disclosed")),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=str(data.get("salary_currency", "USD")),
            job_type=str(data.get("job_type", "Full-time")),
            seniority_level=str(data.get("seniority_level", "Mid-Level")),
            is_remote=bool(data.get("is_remote", False)),
            tags=list(data.get("tags", [])),
            sources=sources,
            company_website=str(data.get("company_website", "")),
            experience_required=str(data.get("experience_required", "")),
            company_summary=str(data.get("company_summary", "")),
            role_summary=str(data.get("role_summary", "")),
            apply_status=str(data.get("apply_status", "PENDING"))
        )


def deduplicate_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    """
    Cross-Platform Smart Deduplication:
    Clusters duplicate jobs posted across multiple portals by matching
    normalized company name and normalized title.
    Combines all platform sources so the user sees all portal links on one card.
    """
    clustered: Dict[str, JobPosting] = {}

    for job in jobs:
        if not job.title or not job.company:
            continue

        norm_comp = normalize_company_name(job.company)
        norm_title = normalize_job_title(job.title)

        cluster_key = f"{norm_comp}:::{norm_title}" if norm_comp and norm_title else job.job_id

        if cluster_key not in clustered:
            clustered[cluster_key] = job
        else:
            existing = clustered[cluster_key]

            # Merge sources list
            existing_platforms = {s["platform"].lower() for s in existing.sources if "platform" in s}
            for src in job.sources:
                if src.get("platform", "").lower() not in existing_platforms:
                    existing.sources.append(src)
                    existing_platforms.add(src.get("platform", "").lower())

            # If the new listing has a richer description, keep it
            if len(job.description) > len(existing.description):
                existing.description = job.description

            # If the new listing has salary info and existing was 'Not Disclosed'
            if existing.salary == "Not Disclosed" and job.salary != "Not Disclosed":
                existing.salary = job.salary
                existing.salary_min = job.salary_min
                existing.salary_max = job.salary_max
                existing.salary_currency = job.salary_currency

            # Merge tags
            existing_tags = set(existing.tags)
            for t in job.tags:
                if t not in existing_tags:
                    existing.tags.append(t)
                    existing_tags.add(t)

            # Keep remote flag if either is remote
            if job.is_remote:
                existing.is_remote = True

    return list(clustered.values())
