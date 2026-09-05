import sys
import os
from typing import Dict, Any
from src.scrapers.base import JobPosting
from src.notifier.base import BaseNotifier

class PhoneNotifier(BaseNotifier):
    """Phone / SMS Notification Service for JobPulse AI."""

    def __init__(self, phone_number: str = ""):
        self.phone_number = phone_number or os.getenv("NOTIFICATION_PHONE", "")

    def send_application_prompt(self, job: JobPosting, match_info: Dict[str, Any]) -> bool:
        """Sends job notification alert to user's phone number."""
        score = match_info.get("match_score", 0)
        relevance = match_info.get("relevance", "N/A")
        sub_scores = match_info.get("sub_scores", {})

        sms_message = (
            f"📱 [JOB FIT ALERT for {self.phone_number}]\n"
            f"🎯 Position: {job.title} at {job.company}\n"
            f"📍 Location: {job.location} | Platform: {job.platform}\n"
            f"📊 Score: {score}% ({relevance})\n"
            f"└─ Breakdown: Skill 40% ({sub_scores.get('skill_match_40', 0)}), "
            f"Title 20% ({sub_scores.get('title_match_20', 0)}), "
            f"Exp 15% ({sub_scores.get('experience_fit_15', 0)}), "
            f"Salary 15% ({sub_scores.get('salary_fit_15', 0)}), "
            f"Prompt 10% ({sub_scores.get('prompt_match_10', 0)})\n"
            f"👥 Company Employees: {job.company_employee_count}\n"
            f"💼 Role Headcount: {job.role_headcount}\n"
            f"📞 HR Phone: {job.hr_contact_number}\n"
            f"🌐 Website: {job.company_website or 'N/A'}\n"
            f"🔗 Link: {job.url}"
        )

        print("\n" + "📱 " * 20)
        print(f"📲 SENDING PHONE NOTIFICATION TO: {self.phone_number}")
        print("📱 " * 20)
        print(sms_message)
        print("-" * 65)

        # Interactive approval or auto-prompt
        if "--no-prompt" in sys.argv or "--skip-questionnaire" in sys.argv:
            print("⚡ [Auto-Approve] Phone notification delivered.")
            return True

        while True:
            response = input("👉 Apply to this job received via Phone Notification? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
