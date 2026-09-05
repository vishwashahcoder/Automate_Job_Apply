import sys
from typing import Dict, Any
from src.scrapers.base import JobPosting
from src.notifier.base import BaseNotifier

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class CLINotifier(BaseNotifier):
    """Interactive Command-Line Notification Interface."""

    def send_application_prompt(self, job: JobPosting, match_info: Dict[str, Any]) -> bool:
        score = match_info.get("match_score", 0)
        relevance = match_info.get("relevance", "N/A")
        sub_scores = match_info.get("sub_scores", {})
        matched_skills = ", ".join(match_info.get("matched_skills", []))
        missing_skills = ", ".join(match_info.get("missing_skills", []))
        exp_req = match_info.get("required_experience", job.experience_required or "Open to All")

        print("\n" + "=" * 70)
        print(f"🎯 NEW MATCHED JOB OPPORTUNITY FOUND! [{job.platform}]")
        print("=" * 70)
        print(f"📌 Position         : {job.title}")
        print(f"🏢 Company          : {job.company}")
        print(f"📍 Location         : {job.location}")
        print(f"💰 Salary           : {job.salary}")
        print(f"🎓 Experience Req   : {exp_req}")
        print(f"📊 Fit Score        : {score}% ({relevance} Match)")
        
        if sub_scores:
            print("   ├─ Skill Match (40%)  : " + str(sub_scores.get('skill_match_40', 0)) + " / 40.0")
            print("   ├─ Title Match (20%)  : " + str(sub_scores.get('title_match_20', 0)) + " / 20.0")
            print("   ├─ Exp Fit (15%)      : " + str(sub_scores.get('experience_fit_15', 0)) + " / 15.0")
            print("   ├─ Salary Fit (15%)   : " + str(sub_scores.get('salary_fit_15', 0)) + " / 15.0")
            print("   └─ Prompt Match (10%) : " + str(sub_scores.get('prompt_match_10', 0)) + " / 10.0")

        print(f"👥 Company Employees: {job.company_employee_count}")
        print(f"💼 Role Headcount   : {job.role_headcount}")
        print(f"📞 HR Contact No    : {job.hr_contact_number}")
        print(f"🌐 Company Website  : {job.company_website or 'Not Listed'}")
        print(f"✅ Matched Skills   : {matched_skills or 'General Profile'}")
        if missing_skills:
            print(f"⚠️ Missing Skills   : {missing_skills}")
        print(f"💡 Explainable Note : {match_info.get('reasoning', '')}")
        print(f"🔗 Job Posting URL  : {job.url}")
        print("-" * 70)

        # Ask user for decision
        while True:
            response = input("👉 Would you like to automatically apply to this job? (y/n/v for view): ").strip().lower()
            if response in ['y', 'yes']:
                print(f"✅ [APPROVED] User accepted application for '{job.title}' at {job.company}.")
                return True
            elif response in ['n', 'no']:
                print(f"❌ [SKIPPED] User declined application for '{job.title}' at {job.company}.")
                return False
            elif response == 'v':
                print(f"\n--- Job Description ---\n{job.description}\n-----------------------")
            else:
                print("Invalid choice. Please enter 'y' to apply or 'n' to skip.")
