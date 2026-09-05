"""
Core Configuration Manager for JobPulse AI.
Handles YAML configuration loading, path sanitization, and empty dynamic defaults.
"""

import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")

def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes configuration values, removing extraneous surrounding quotes in paths."""
    if not isinstance(config, dict):
        return {}

    resume_profile = config.get("resume_profile", {})
    if isinstance(resume_profile, dict):
        path = resume_profile.get("resume_pdf_path")
        if isinstance(path, str):
            cleaned = path.strip("\"'")
            resume_profile["resume_pdf_path"] = cleaned

    return config


def load_app_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Loads and sanitizes YAML configuration without static hardcoded dummy data."""
    if not os.path.exists(config_path):
        return {
            "preferences": {
                "job_titles": [],
                "locations": [],
                "experience_level": "",
                "platforms": [
                    "company_careers",
                    "linkedin",
                    "instahyre",
                    "naukri",
                    "indeed",
                    "wellfound",
                    "cutshort_hirist",
                    "weworkremotely",
                    "flexjobs",
                    "remote_co"
                ]
            },
            "resume_profile": {
                "full_name": "",
                "email": "",
                "phone": "",
                "location": "",
                "portfolio_url": "",
                "linkedin_url": "",
                "years_experience": 0,
                "last_position": "",
                "skills": [],
                "summary": "",
                "resume_pdf_path": ""
            },
            "notification": {"mode": "cli"},
            "matching": {"min_fit_score": 70}
        }

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    creds = data.get("credentials", {})
    if isinstance(creds, dict):
        if creds.get("aws_region"):
            os.environ["AWS_REGION"] = creds["aws_region"]
        if creds.get("aws_access_key_id"):
            os.environ["AWS_ACCESS_KEY_ID"] = creds["aws_access_key_id"]
        if creds.get("aws_secret_access_key"):
            os.environ["AWS_SECRET_ACCESS_KEY"] = creds["aws_secret_access_key"]
        if creds.get("triage_model_id"):
            os.environ["TRIAGE_MODEL_ID"] = creds["triage_model_id"]
        if creds.get("drafting_model_id"):
            os.environ["DRAFTING_MODEL_ID"] = creds["drafting_model_id"]

    return sanitize_config(data)
