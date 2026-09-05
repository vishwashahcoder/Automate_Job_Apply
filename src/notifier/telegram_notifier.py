import requests
from typing import Dict, Any
from src.scrapers.base import JobPosting
from src.notifier.base import BaseNotifier
from src.notifier.cli_notifier import CLINotifier

class TelegramNotifier(BaseNotifier):
    """Telegram Bot API Notification Interface."""

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.fallback_cli = CLINotifier()

    def send_application_prompt(self, job: JobPosting, match_info: Dict[str, Any]) -> bool:
        if not self.bot_token or not self.chat_id:
            print("ℹ️ [TelegramNotifier] Bot Token or Chat ID not configured in config.yaml. Falling back to Interactive CLI.")
            return self.fallback_cli.send_application_prompt(job, match_info)

        score = match_info.get("match_score", 0)
        text = (
            f"🎯 <b>NEW MATCHED JOB OPPORTUNITY</b>\n\n"
            f"📌 <b>Position:</b> {job.title}\n"
            f"🏢 <b>Company:</b> {job.company}\n"
            f"📍 <b>Location:</b> {job.location}\n"
            f"💰 <b>Salary:</b> {job.salary}\n"
            f"📊 <b>Fit Score:</b> {score}%\n\n"
            f"💡 <i>{match_info.get('reasoning', '')}</i>\n\n"
            f"🔗 <a href='{job.url}'>View Job Posting</a>"
        )
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                print(f"📱 [TelegramNotifier] Sent job notification to Telegram chat: {self.chat_id}")
            else:
                print(f"⚠️ [TelegramNotifier] Failed to send Telegram message: {res.text}")
        except Exception as e:
            print(f"⚠️ [TelegramNotifier] Error sending notification: {e}")

        # Standard approval interaction via CLI fallback
        return self.fallback_cli.send_application_prompt(job, match_info)
