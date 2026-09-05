"""
Explainable Job Fit-Scoring Engine for JobPulse AI.
Evaluates candidate fit score (0-100) based on authentic skills, title overlap,
experience level, and user search criteria.
Zero synthetic or fabricated data.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from src.models.job import JobPosting


class JobMatcher:
    """
    Explainable Multi-Factor Job Fit-Scoring Engine (0-100).
    
    Weights:
    - Skill Match: 40%
    - Title/Role Match: 25%
    - Seniority/Experience Fit: 15%
    - Salary Expectation Fit: 10%
    - Prompt-Criteria Match: 10%
    """

    def __init__(self, config: Dict[str, Any], prompt_criteria: Dict[str, Any] = None):
        self.config = config
        self.resume_profile = config.get("resume_profile", {})
        self.user_skills = [s.lower() for s in self.resume_profile.get("skills", []) if s]
        self.min_score = config.get("matching", {}).get("min_fit_score", 40)
        self.prompt_criteria = prompt_criteria or {}
        self.prompt_query = self.prompt_criteria.get("query", "").strip()

    def evaluate(self, job: JobPosting) -> Dict[str, Any]:
        """Calculates explainable job fit score and returns detailed breakdown."""
        # 1. Skill Match Score (0 - 100) -> 40%
        skill_score, matched_skills, missing_skills = self._calc_skill_match(job)

        # 2. Title/Role Match Score (0 - 100) -> 25%
        title_score = self._calc_title_match(job)

        # 3. Seniority/Experience Fit Score (0 - 100) -> 15%
        exp_score, exp_reason = self._calc_experience_fit(job)

        # 4. Salary Fit Score (0 - 100) -> 10%
        salary_score = self._calc_salary_fit(job)

        # 5. Prompt Criteria Match (0 - 100) -> 10%
        prompt_score = self._calc_prompt_match(job)

        # Combined Weighted Score
        final_fit = (
            0.40 * skill_score +
            0.25 * title_score +
            0.15 * exp_score +
            0.10 * salary_score +
            0.10 * prompt_score
        )

        score_int = int(round(final_fit))
        score_int = min(max(score_int, 0), 100)

        relevance = "High" if score_int >= 75 else ("Medium" if score_int >= 50 else "Low")
        should_save = score_int >= self.min_score

        sub_scores = {
            "skill_match_40": round(skill_score * 0.40, 1),
            "title_match_25": round(title_score * 0.25, 1),
            "experience_fit_15": round(exp_score * 0.15, 1),
            "salary_fit_10": round(salary_score * 0.10, 1),
            "prompt_match_10": round(prompt_score * 0.10, 1),
            "raw_sub_scores": {
                "skill_100": round(skill_score, 1),
                "title_100": round(title_score, 1),
                "experience_100": round(exp_score, 1),
                "salary_100": round(salary_score, 1),
                "prompt_100": round(prompt_score, 1)
            }
        }

        # Reason generator
        reason_parts = []
        if matched_skills:
            reason_parts.append(f"Matched core skills: {', '.join(matched_skills[:4])}")
        if title_score >= 70:
            reason_parts.append(f"Strong role title alignment with candidate background")
        if exp_reason:
            reason_parts.append(exp_reason)

        reasoning = ". ".join(reason_parts) if reason_parts else "General alignment with search criteria."

        return {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "platform": job.platform,
            "match_score": score_int,
            "relevance": relevance,
            "sub_scores": sub_scores,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills[:4],
            "seniority_level": job.seniority_level,
            "reasoning": reasoning,
            "should_save": should_save
        }

    def _calc_skill_match(self, job: JobPosting) -> Tuple[float, List[str], List[str]]:
        """Calculates 0-100 skill overlap between candidate skills and job description/tags."""
        desc_text = (job.description + " " + job.title + " " + " ".join(job.tags)).lower()
        matched = []
        missing = []

        for skill in self.user_skills:
            if not skill or len(skill) < 2:
                continue
            pattern = r"\b" + re.escape(skill) + r"\b" if len(skill) <= 3 else re.escape(skill)
            if re.search(pattern, desc_text, re.IGNORECASE):
                display = skill.upper() if skill in ["c", "c++", "sql", "ai", "ml", "rag", "aws", "gcp", "llm"] else skill.capitalize()
                if display not in matched:
                    matched.append(display)
            else:
                missing.append(skill.capitalize())

        # Also check common tech tags if user skills list is short
        known_tech = [
            "python", "javascript", "typescript", "c++", "java", "sql", "fastapi", "flask", "django",
            "react", "node", "docker", "kubernetes", "aws", "gcp", "azure", "ai", "ml", "rag", "langchain",
            "llm", "pytorch", "tensorflow", "git", "rest api"
        ]
        for tech in known_tech:
            pattern = r"\b" + re.escape(tech) + r"\b" if len(tech) <= 3 else re.escape(tech)
            if re.search(pattern, desc_text, re.IGNORECASE):
                disp = tech.upper() if tech in ["c++", "sql", "ai", "ml", "rag", "aws", "gcp", "llm"] else tech.capitalize()
                if disp not in matched and tech in self.user_skills:
                    matched.append(disp)

        ratio = len(matched) / max(len(self.user_skills), 1) if self.user_skills else 0.7
        score = min(ratio * 100.0 + 20.0, 100.0) if matched else (60.0 if not self.user_skills else 30.0)
        return (score, matched, missing)

    def _calc_title_match(self, job: JobPosting) -> float:
        """Calculates 0-100 title match score with word boundaries and tech acronym support."""
        target_query = self.prompt_query.lower() or self.resume_profile.get("last_position", "").lower() or "developer"
        job_title_lower = job.title.lower()

        stop_words = {"job", "jobs", "role", "roles", "looking", "for", "related", "any", "some", "with", "the", "and", "in", "at", "to"}
        query_words = [w for w in re.findall(r"\w+", target_query) if (len(w) >= 2 or w in ["c", "r"]) and w not in stop_words]
        if not query_words:
            return 75.0

        matches = sum(1 for word in query_words if re.search(r"\b" + re.escape(word) + r"\b", job_title_lower))
        if matches == len(query_words):
            return 100.0
        elif matches > 0:
            return 60.0 + (matches / len(query_words)) * 35.0
        else:
            desc_matches = sum(1 for word in query_words if re.search(r"\b" + re.escape(word) + r"\b", job.description.lower()))
            return 40.0 if desc_matches > 0 else 15.0

    def _calc_experience_fit(self, job: JobPosting) -> Tuple[float, str]:
        """Calculates experience and seniority fit."""
        candidate_years = float(self.resume_profile.get("years_experience", 0))
        target_seniority = self.prompt_criteria.get("seniority_level", "All")

        if target_seniority != "All":
            if target_seniority.lower() == job.seniority_level.lower():
                return (100.0, f"Seniority matches targeted level ({job.seniority_level})")
            else:
                return (65.0, f"Job level is {job.seniority_level}")

        if job.seniority_level == "Entry":
            return (100.0, "Entry level / Fresher friendly")
        elif job.seniority_level == "Mid-Level":
            return (90.0 if candidate_years >= 1 else 70.0, "Mid-level position")
        elif job.seniority_level == "Senior":
            return (100.0 if candidate_years >= 3 else 60.0, "Senior role")
        elif job.seniority_level == "Lead":
            return (100.0 if candidate_years >= 5 else 50.0, "Lead / Leadership position")

        return (80.0, "")

    def _parse_salary_from_text(self, text: str) -> Tuple[Optional[float], Optional[float], str]:
        """Extracts numeric salary range and currency from unstructured text."""
        if not text:
            return (None, None, "USD")

        # INR LPA detection: "15-20 LPA", "15 LPA", "15 Lakhs"
        lpa_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*(?:lpa|lakhs?|lac|lacs)\b", text, re.IGNORECASE)
        if lpa_match:
            min_v = float(lpa_match.group(1)) * 100000
            max_v = float(lpa_match.group(2)) * 100000 if lpa_match.group(2) else min_v
            return (min_v, max_v, "INR")

        inr_match = re.search(r"[₹\u20B9]\s*(\d[\d,]+)\s*(?:-|to)?\s*(?:[₹\u20B9]\s*)?(\d[\d,]+)?", text)
        if inr_match:
            min_v = float(inr_match.group(1).replace(",", ""))
            max_v = float(inr_match.group(2).replace(",", "")) if inr_match.group(2) else min_v
            return (min_v, max_v, "INR")

        # USD detection: "$120k - $150k", "$120,000", "120k USD"
        usd_k_match = re.search(r"\$\s*(\d+)\s*k?\s*(?:-|to)?\s*\$?\s*(\d+)?\s*k\b", text, re.IGNORECASE)
        if usd_k_match:
            min_v = float(usd_k_match.group(1)) * 1000 if float(usd_k_match.group(1)) < 1000 else float(usd_k_match.group(1))
            max_v = float(usd_k_match.group(2)) * 1000 if usd_k_match.group(2) and float(usd_k_match.group(2)) < 1000 else min_v
            return (min_v, max_v, "USD")

        usd_match = re.search(r"\$\s*(\d[\d,]+)\s*(?:-|to)?\s*(?:\$\s*)?(\d[\d,]+)?", text)
        if usd_match:
            min_v = float(usd_match.group(1).replace(",", ""))
            max_v = float(usd_match.group(2).replace(",", "")) if usd_match.group(2) else min_v
            return (min_v, max_v, "USD")

        return (None, None, "USD")

    def _calc_salary_fit(self, job: JobPosting) -> float:
        """Calculates salary expectations match with multi-currency and LPA normalization."""
        min_salary_target = float(self.prompt_criteria.get("min_salary", 0))
        target_currency = self.prompt_criteria.get("salary_currency", "INR")

        if min_salary_target <= 0 or job.salary == "Not Disclosed":
            return 75.0

        sal_min = job.salary_min
        sal_max = job.salary_max
        job_curr = job.salary_currency or "USD"

        if sal_min is None and sal_max is None:
            sal_min, sal_max, job_curr = self._parse_salary_from_text(f"{job.salary} {job.description}")

        if sal_min is None and sal_max is None:
            return 75.0

        # Currency conversion for comparison (1 USD ~ 85 INR)
        rate_usd_to_inr = 85.0
        if target_currency == "INR" and job_curr == "USD":
            if sal_min: sal_min *= rate_usd_to_inr
            if sal_max: sal_max *= rate_usd_to_inr
        elif target_currency == "USD" and job_curr == "INR":
            if sal_min: sal_min /= rate_usd_to_inr
            if sal_max: sal_max /= rate_usd_to_inr

        job_top = sal_max if sal_max is not None else sal_min
        job_low = sal_min if sal_min is not None else sal_max

        if job_top is not None and job_top >= min_salary_target:
            return 100.0
        elif job_low is not None and job_low >= min_salary_target * 0.85:
            return 85.0
        elif job_top is not None and job_top >= min_salary_target * 0.70:
            return 60.0
        else:
            return 30.0

    def _calc_prompt_match(self, job: JobPosting) -> float:
        """Calculates match against user free-text query with word boundaries."""
        if not self.prompt_query:
            return 80.0

        corpus = (job.title + " " + job.description + " " + job.location + " " + " ".join(job.tags)).lower()
        stop_words = {"job", "jobs", "role", "roles", "looking", "for", "related", "any", "some", "with", "the", "and", "in", "at", "to"}
        words = [w for w in re.findall(r"\w+", self.prompt_query.lower()) if (len(w) >= 2 or w in ["c", "r"]) and w not in stop_words]
        if not words:
            return 80.0

        matches = sum(1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", corpus))
        ratio = matches / len(words)
        return min(ratio * 100.0 + 20.0, 100.0) if matches > 0 else 20.0
