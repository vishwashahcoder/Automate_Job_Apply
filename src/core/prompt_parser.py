"""
Natural Language Search Prompt Parser for JobPulse AI.
Parses free-form user prompts into structured search & filter parameters.
Targeting exclusively:
Company Career Pages, LinkedIn, Instahyre, Naukri.com, Indeed, Wellfound,
Cutshort / Hirist, We Work Remotely, FlexJobs, Remote.co
"""

import os
import sys
import re
import json
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORTALS_LIST = [
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


class SearchPromptParser:
    """Parses natural language search prompts into structured job search parameters."""

    def __init__(self, api_key: str = None):
        if not api_key:
            from src.core.config import load_app_config
            creds = load_app_config().get("credentials", {})
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or creds.get("gemini_api_key") or creds.get("google_api_key")
        self.api_key = api_key

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parses prompt into structured search parameters using Bedrock Nova, Gemini, or smart heuristic parser."""
        if not prompt or not prompt.strip():
            return self._default_parameters()

        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            try:
                return self._parse_with_bedrock_nova(prompt)
            except Exception as e:
                print(f"[PromptParser] Bedrock LLM note ({e}), falling back to heuristic parser.")

        if self.api_key:
            try:
                return self._parse_with_gemini(prompt)
            except Exception as e:
                print(f"[PromptParser] Gemini prompt note ({e}), falling back to heuristic parser.")

        return self._parse_heuristic(prompt)

    def _default_parameters(self) -> Dict[str, Any]:
        return {
            "query": "",
            "locations": [],
            "seniority_level": "All",
            "job_types": ["Full-time"],
            "remote_only": False,
            "min_salary": 0,
            "salary_currency": "USD",
            "date_posted_days": None,
            "platforms": PORTALS_LIST
        }

    def _parse_heuristic(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()

        # 1. Remote detection
        is_remote = any(term in p_lower for term in ["remote", "work from home", "wfh", "worldwide", "anywhere", "global"])

        # 2. Seniority detection
        seniority = "All"
        if any(term in p_lower for term in ["lead", "principal", "staff", "head of", "director", "architect"]):
            seniority = "Lead"
        elif any(term in p_lower for term in ["senior", "sr.", "sr ", "experienced"]):
            seniority = "Senior"
        elif any(term in p_lower for term in ["junior", "jr.", "entry", "fresher", "intern", "internship", "graduate"]):
            seniority = "Entry"
        elif any(term in p_lower for term in ["mid", "mid-level", "mid level"]):
            seniority = "Mid-Level"

        # 3. Date Posted (Freshness) detection
        date_posted_days: Optional[int] = None
        if any(term in p_lower for term in ["today", "past 24h", "last 24 hours", "24 hours", "past 24 hours", "just now"]):
            date_posted_days = 1
        elif any(term in p_lower for term in ["this week", "past week", "last 7 days", "past 7 days", "past 7d", "recent"]):
            date_posted_days = 7
        elif any(term in p_lower for term in ["this month", "past month", "last 30 days", "past 30 days"]):
            date_posted_days = 30

        # 4. Salary Expectations Parsing
        min_salary = 0
        salary_currency = "USD"

        # USD detection: $120k, $120,000, 120k usd, 150000 usd
        if "$" in prompt or "usd" in p_lower:
            salary_currency = "USD"
            usd_num = re.search(r"\$?\s*(\d+)\s*k?\b", p_lower)
            if usd_num:
                val = int(usd_num.group(1))
                min_salary = val * 1000 if val < 1000 else val

        # INR detection: 15 lpa, 20 lakhs, 1500000, 20 lac
        if not min_salary:
            lpa_match = re.search(r"(\d+(\.\d+)?)\s*(lpa|lakh|lakhs|lac|lacs)", p_lower)
            if lpa_match:
                salary_currency = "INR"
                lpa_val = float(lpa_match.group(1))
                min_salary = int(lpa_val * 100000)
            else:
                num_match = re.search(r"(\d{6,8})", p_lower)
                if num_match:
                    salary_currency = "INR"
                    min_salary = int(num_match.group(1))

        # 5. Location extraction
        known_cities = [
            "ahmedabad", "pune", "gandhinagar", "bangalore", "bengaluru", "mumbai",
            "delhi", "noida", "gurgaon", "hyderabad", "chennai", "kolkata",
            "london", "new york", "san francisco", "austin", "seattle", "berlin", "canada", "germany", "india", "usa"
        ]
        locations = []
        found_city_terms = []
        for city in known_cities:
            if re.search(r"\b" + re.escape(city) + r"\b", p_lower):
                locations.append(city.capitalize() if city not in ["india", "usa"] else city.upper())
                found_city_terms.append(city)

        if is_remote or "worldwide" in p_lower or "global" in p_lower:
            locations.append("Worldwide Remote" if is_remote else "Remote")

        # 6. Job type extraction
        job_types = []
        if any(term in p_lower for term in ["fulltime", "full-time", "full time"]):
            job_types.append("Full-time")
        if any(term in p_lower for term in ["contract", "freelance", "contractor"]):
            job_types.append("Contract")
        if any(term in p_lower for term in ["parttime", "part-time", "part time"]):
            job_types.append("Part-time")
        if any(term in p_lower for term in ["intern", "internship"]):
            job_types.append("Internship")
        if not job_types:
            job_types = ["Full-time"]

        # 7. Platforms Selection
        platforms = PORTALS_LIST

        # 8. Clean Role / Keyword Extraction
        # 8. Clean Role / Keyword Extraction
        known_roles = [
            "ai/ml engineer", "ai engineer", "genai developer", "generative ai engineer",
            "ml engineer", "machine learning engineer", "python developer", "python engineer",
            "backend developer", "backend engineer", "full stack developer", "full stack engineer",
            "data scientist", "data engineer", "devops engineer", "cloud engineer", "software engineer", "frontend developer",
            "react developer", "node developer", "golang developer", "go engineer", "rust developer",
            "ai", "ml", "genai", "generative ai", "deep learning", "llm", "nlp", "computer vision"
        ]

        matched_queries = []
        for role in known_roles:
            if re.search(r"\b" + re.escape(role) + r"\b", p_lower):
                clean_title = " ".join([w.upper() if w in ["ai", "ml", "genai", "go", "llm", "nlp", "cv"] else w.capitalize() for w in role.split()])
                matched_queries.append(clean_title)

        if matched_queries:
            primary_query = matched_queries[0]
        else:
            clean_text = p_lower
            for city_term in found_city_terms:
                clean_text = re.sub(r"\b" + re.escape(city_term) + r"\b", " ", clean_text)

            noise_patterns = [
                r"\bwant\s+to\s+search\b", r"\bto\s+search\b", r"\blooking\s+for\b", r"\bsearch\s+for\b", r"\bfind\s+me\b", r"\bi\s+want\b",
                r"\bany\s+roles?\s+related\s+to\b", r"\broles?\s+related\s+to\b", r"\brelated\s+to\b", r"\brelated\b",
                r"\bremote\s+job[s]?\b", r"\bremote\b", r"\bwork\s+from\s+home\b", r"\bwfh\b", r"\bworldwide\b",
                r"\bfull[- ]?time\b", r"\bpart[- ]?time\b", r"\bcontract\b", r"\binternship\b",
                r"\bsenior\b", r"\bjr\b", r"\bsr\b", r"\bjunior\b", r"\blead\b", r"\bprincipal\b",
                r"\btoday\b", r"\bthis\s+week\b", r"\bpast\s+week\b", r"\blast\s+7\s+days\b", r"\bthis\s+month\b",
                r"\bmore\s+than\b", r"\babove\b", r"\bpaying\b", r"\bminimum\b", r"\bmin\b", r"\bsalary\b", r"\blpa\b", r"\blakh[s]?\b", r"\busd\b",
                r"\bjob[s]?\b", r"\brole[s]?\b", r"\bposition[s]?\b", r"\bopening[s]?\b", r"\bin\b", r"\bfor\b", r"\bat\b", r"\band\b", r"\bto\b",
                r"\b\d+\b"
            ]
            for pat in noise_patterns:
                clean_text = re.sub(pat, " ", clean_text, flags=re.IGNORECASE)

            stop_words = {"as", "also", "should", "me", "then", "give", "want", "like", "tell", "can", "could", "please", "search", "show", "find", "need", "get", "more", "than", "only", "with", "or", "any", "some", "job", "jobs", "role", "roles", "position", "positions", "related", "to", "about"}
            words = [w.strip() for w in clean_text.split() if len(w.strip()) >= 2 and not w.isdigit() and w.lower() not in stop_words]
            formatted_words = []
            for w in words:
                if w.lower() in ["ai", "ml", "genai", "llm", "rag", "sql", "aws", "gcp", "api", "nlp", "cv", "bi", "go"]:
                    formatted_words.append(w.upper())
                else:
                    formatted_words.append(w.capitalize())
            primary_query = " ".join(formatted_words) if formatted_words else ""

        return {
            "query": primary_query,
            "locations": list(dict.fromkeys(locations)),
            "seniority_level": seniority,
            "job_types": job_types,
            "remote_only": is_remote,
            "min_salary": min_salary,
            "salary_currency": salary_currency,
            "date_posted_days": date_posted_days,
            "platforms": platforms
        }

    def _parse_with_bedrock_nova(self, prompt: str) -> Dict[str, Any]:
        import boto3
        region = os.getenv("AWS_REGION", "us-east-1")
        ak = os.getenv("AWS_ACCESS_KEY_ID")
        sk = os.getenv("AWS_SECRET_ACCESS_KEY")
        model_id = os.getenv("TRIAGE_MODEL_ID", "us.amazon.nova-lite-v1:0")

        client = boto3.client("bedrock-runtime", region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
        instructions = f"""
        Extract job search criteria from this user prompt: "{prompt}"
        Return ONLY valid JSON with keys: query (string), locations (list), seniority_level (string: All, Entry, Mid-Level, Senior, Lead), job_types (list), remote_only (bool), min_salary (int), salary_currency (string: USD or INR), date_posted_days (int or null), platforms (list from {PORTALS_LIST}).
        """
        payload = {
            "inferenceConfig": {"max_new_tokens": 1000, "temperature": 0.1},
            "messages": [{"role": "user", "content": [{"text": instructions}]}]
        }
        res = client.invoke_model(modelId=model_id, body=json.dumps(payload))
        res_body = json.loads(res["body"].read().decode("utf-8"))
        text = res_body["output"]["message"]["content"][0]["text"].strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        data = json.loads(text)
        return data

    def _parse_with_gemini(self, prompt: str) -> Dict[str, Any]:
        from google import genai
        client = genai.Client(api_key=self.api_key)
        sys_prompt = f"""
        Extract structured job search and filter criteria from this user prompt: "{prompt}"
        Return ONLY valid JSON with keys:
        - "query": string (clean job title or tech stack, e.g. "AI Engineer" or "Python Developer")
        - "locations": list of strings (e.g. ["Remote", "London", "Pune"])
        - "seniority_level": string from ["All", "Entry", "Mid-Level", "Senior", "Lead"]
        - "job_types": list of strings from ["Full-time", "Contract", "Part-time", "Internship"]
        - "remote_only": boolean
        - "min_salary": integer (minimum annual salary, 0 if not mentioned)
        - "salary_currency": string ("USD" or "INR")
        - "date_posted_days": integer or null (1 for past 24h, 7 for past week, 30 for past month, null if not mentioned)
        - "platforms": list of strings from {PORTALS_LIST}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=sys_prompt,
        )
        out_text = response.text.strip()
        if "```json" in out_text:
            out_text = out_text.split("```json")[1].split("```")[0].strip()
        data = json.loads(out_text)
        return data
