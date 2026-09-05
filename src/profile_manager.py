import os
import sys
import yaml
from typing import Dict, Any
from src.core.config import DEFAULT_CONFIG_PATH, load_app_config, sanitize_config

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class ProfileManager:
    """Manages user preferences, resume profile data, and system configuration."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads YAML configuration file with path sanitization."""
        return load_app_config(self.config_path)

    def save_config(self) -> None:
        """Saves current configuration to YAML file."""
        sanitized = sanitize_config(self.config)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(sanitized, f, default_flow_style=False, sort_keys=False)

    def ask_user_questions(self, skip_if_filled: bool = False) -> None:
        """
        Interactive Questionnaire asking the user all candidate & job preference details.
        Allows keeping existing/default values by pressing Enter.
        """
        print("\n" + "=" * 65)
        print("   📋 CANDIDATE PROFILE & JOB PREFERENCE QUESTIONNAIRE")
        print("   (Press [Enter] to keep current default value)")
        print("=" * 65 + "\n")

        prefs = self.config.setdefault("preferences", {})
        profile = self.config.setdefault("resume_profile", {})

        # --- Candidate Personal Details ---
        print("--- 1. Personal & Contact Details ---")
        curr_name = profile.get("full_name", "")
        new_name = input(f"• Full Name [{curr_name}]: ").strip()
        if new_name:
            profile["full_name"] = new_name

        curr_email = profile.get("email", "")
        new_email = input(f"• Email Address [{curr_email}]: ").strip()
        if new_email:
            profile["email"] = new_email

        curr_phone = profile.get("phone", "")
        new_phone = input(f"• Phone Number [{curr_phone}]: ").strip()
        if new_phone:
            profile["phone"] = new_phone

        curr_loc = profile.get("location", "")
        new_loc = input(f"• Current City / Country [{curr_loc}]: ").strip()
        if new_loc:
            profile["location"] = new_loc

        curr_portfolio = profile.get("portfolio_url", "")
        new_portfolio = input(f"• Portfolio / GitHub URL [{curr_portfolio}]: ").strip()
        if new_portfolio:
            profile["portfolio_url"] = new_portfolio

        curr_linkedin = profile.get("linkedin_url", "")
        new_linkedin = input(f"• LinkedIn Profile URL [{curr_linkedin}]: ").strip()
        if new_linkedin:
            profile["linkedin_url"] = new_linkedin

        # --- Professional Details ---
        print("\n--- 2. Professional & Resume Details ---")
        curr_exp_yrs = str(profile.get("years_experience", 3))
        new_exp_yrs = input(f"• Total Years of Experience [{curr_exp_yrs}]: ").strip()
        if new_exp_yrs:
            try:
                profile["years_experience"] = int(new_exp_yrs)
            except ValueError:
                pass

        curr_skills = ", ".join(profile.get("skills", []))
        new_skills = input(f"• Key Technical Skills [{curr_skills}]: ").strip()
        if new_skills:
            profile["skills"] = [s.strip() for s in new_skills.split(",") if s.strip()]

        curr_summary = profile.get("summary", "")
        new_summary = input(f"• Brief Professional Summary [{curr_summary}]: ").strip()
        if new_summary:
            profile["summary"] = new_summary

        curr_resume = profile.get("resume_pdf_path", "./resume.pdf")
        new_resume = input(f"• Resume PDF File Path [{curr_resume}]: ").strip()
        if new_resume:
            profile["resume_pdf_path"] = new_resume

        # --- Job Search Preferences ---
        print("\n--- 3. Job Search Preferences ---")
        curr_titles = ", ".join(prefs.get("job_titles", []))
        new_titles = input(f"• Target Job Titles (e.g. Python Dev, AI Engineer) [{curr_titles}]: ").strip()
        if new_titles:
            prefs["job_titles"] = [t.strip() for t in new_titles.split(",") if t.strip()]

        curr_job_locs = ", ".join(prefs.get("locations", []))
        new_job_locs = input(f"• Preferred Work Locations (e.g. Remote, Bangalore, Delhi) [{curr_job_locs}]: ").strip()
        if new_job_locs:
            prefs["locations"] = [l.strip() for l in new_job_locs.split(",") if l.strip()]

        curr_exp_level = prefs.get("experience_level", "Mid-Level")
        new_exp_level = input(f"• Target Experience Level (Entry-Level / Mid-Level / Senior) [{curr_exp_level}]: ").strip()
        if new_exp_level:
            prefs["experience_level"] = new_exp_level

        curr_platforms = ", ".join(prefs.get("platforms", ["linkedin", "naukri"]))
        new_platforms = input(f"• Job Portals to Search (linkedin, naukri) [{curr_platforms}]: ").strip()
        if new_platforms:
            prefs["platforms"] = [p.strip().lower() for p in new_platforms.split(",") if p.strip()]

        self.save_config()
        print("\n✅ Candidate Profile & Job Preferences successfully saved to config.yaml!\n")

    def print_summary(self) -> None:
        """Prints formatted summary of user profile and search parameters."""
        prefs = self.config.get("preferences", {})
        profile = self.config.get("resume_profile", {})

        print("\n" + "=" * 65)
        print("             👤 CANDIDATE PROFILE SUMMARY             ")
        print("=" * 65)
        print(f"• Name           : {profile.get('full_name')}")
        print(f"• Email          : {profile.get('email')}")
        print(f"• Phone          : {profile.get('phone')}")
        print(f"• Experience     : {profile.get('years_experience')} years")
        print(f"• Core Skills    : {', '.join(profile.get('skills', []))}")
        print(f"• Resume File    : {profile.get('resume_pdf_path')}")
        print("-" * 65)
        print(f"• Target Titles  : {', '.join(prefs.get('job_titles', []))}")
        print(f"• Locations      : {', '.join(prefs.get('locations', []))}")
        print(f"• Portals        : {', '.join(prefs.get('platforms', [])).title()}")
        print("=" * 65 + "\n")

if __name__ == "__main__":
    pm = ProfileManager()
    pm.ask_user_questions()
    pm.print_summary()
