"""
AI Resume Parser Agent for JobPulse AI.
Extracts text from PDF resumes using pypdf and synthesizes 100% dynamic profile data
including Candidate Name, Phone, Email, LinkedIn, GitHub, Skills, and Last Position.
"""

import os
import re
import json
import io
from typing import Dict, Any, List, Union, BinaryIO
from pypdf import PdfReader


class ResumeParserAgent:
    """Agentic PDF Resume Parser and Candidate Profile Synthesizer."""

    def __init__(self, api_key: str = None):
        if not api_key:
            from src.core.config import load_app_config
            creds = load_app_config().get("credentials", {})
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or creds.get("gemini_api_key") or creds.get("google_api_key")
        self.api_key = api_key

    def _normalize_pdf_text(self, text: str) -> str:
        """Normalizes PDF text, collapsing spaced-out characters found in Canva and stylized PDF exports (e.g. 'S H A R Y A')."""
        if not text:
            return ""
        lines = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            words = stripped.split()
            single_char_words = [w for w in words if len(w) == 1 and w.isalnum()]
            if len(words) > 3 and len(single_char_words) / len(words) > 0.35:
                stripped = re.sub(r'(\d)\s+([a-zA-Z])', r'\1  \2', stripped)
                stripped = re.sub(r'(m|m \.)\s+(w|h t t p)', r'\1  \2', stripped)
                normalized = re.sub(r'  +', ' \x00 ', stripped)
                normalized = re.sub(r'(?<=\b[A-Za-z0-9@._\-\+]) (?=[A-Za-z0-9@._\-\+]\b)', '', normalized)
                normalized = normalized.replace('\x00', ' ')
                stripped = normalized.strip()
            stripped = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', stripped)
            stripped = re.sub(r'\b(com|org|net|io|dev|in|ai)([a-zA-Z])', r'\1 \2', stripped)
            stripped = re.sub(r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,4})', r'\1@\2.\3', stripped)
            stripped = re.sub(r'\b(www|https?)\s*\.\s*([\w.-]+)\s*\.\s*([a-zA-Z]{2,4})', r'\1.\2.\3', stripped)
            stripped = re.sub(r'(\+)\s*(\d)', r'\1\2', stripped)
            stripped = re.sub(r'(\d)\s*-\s*(\d)', r'\1-\2', stripped)
            stripped = re.sub(r'[ \t]+', ' ', stripped)
            lines.append(stripped)
        return "\n".join(lines).strip()

    def extract_text_from_pdf(self, source: Union[str, bytes, BinaryIO]) -> str:
        """Extracts raw text content from a PDF file path, bytes, or file stream."""
        try:
            if isinstance(source, str):
                if not os.path.exists(source):
                    return ""
                reader = PdfReader(source)
            elif isinstance(source, bytes):
                reader = PdfReader(io.BytesIO(source))
            else:
                reader = PdfReader(source)

            extracted_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)

            raw = "\n".join(extracted_text).strip()
            return self._normalize_pdf_text(raw)
        except Exception as e:
            print(f"⚠️ [ResumeParserAgent] Error extracting text from PDF: {e}")
            return ""

    def parse_resume(self, pdf_source: Union[str, bytes, BinaryIO]) -> Dict[str, Any]:
        """
        Extracts PDF text and parses candidate details into structured JSON.
        Identifies missing fields requiring user input.
        """
        raw_text = self.extract_text_from_pdf(pdf_source)
        if not raw_text:
            return self._fallback_parse("")

        res = None
        if self.api_key:
            try:
                res = self._parse_with_gemini(raw_text)
            except Exception as e:
                print(f"⚠️ [ResumeParserAgent] Gemini parsing note ({e}), using heuristic fallback.")

        if not res:
            res = self._fallback_parse(raw_text)

        # Fallback fill phone if empty
        if not res.get("phone"):
            fb = self._fallback_parse(raw_text)
            if fb.get("phone"):
                res["phone"] = fb["phone"]
                if "phone" in res.get("missing_fields", []):
                    res["missing_fields"].remove("phone")

        return res

    def _extract_candidate_name(self, text: str, lines: List[str], linkedin_url: str = "", email: str = "") -> str:
        """Extracts candidate full name cleanly without matching document titles or random noise words."""
        ignore_terms = {
            "resume", "curriculum vitae", "cv", "bio-data", "biodata", "contact",
            "profile", "page 1", "personal details", "candidate profile", "summary",
            "objective", "long-term", "email", "phone", "linkedin", "github", "data", "information",
            "about me", "education", "experience", "skills", "references", "work experience",
            "web accessibility", "version control", "color theory", "seo fundamentals",
            "ui / ux design", "ui/ux design", "typography", "front - end", "front end",
            "web design tools", "ceo of wardiere company", "hrd of wardiere company"
        }
        title_pattern = r"\b(?:AI/ML|AI|ML|GenAI|LLM|Backend|Frontend|Full\s*Stack|Data|Software|Cloud|DevOps|Systems|Web)\s+(?:Engineer|Developer|Scientist|Architect|Intern|Lead|Manager|Consultant|Specialist|Designer)\b.*$"

        search_lines = lines[:15] + lines[-10:]

        # Pass 1: Look for ALL CAPS lines of 2-4 words (e.g., "SHARYA SINGH", "DHARMIK RAVAL")
        for line in search_lines:
            clean_line = line.strip()
            lower_line = clean_line.lower()

            if lower_line in ignore_terms or any(term == lower_line for term in ignore_terms):
                continue
            if "@" in clean_line or "http" in clean_line or ":" in clean_line or re.search(r"\d", clean_line):
                continue

            words = clean_line.split()
            if 2 <= len(words) <= 4 and all(w.isupper() and w.isalpha() and len(w) >= 2 for w in words):
                if not any(w.lower() in ignore_terms for w in words):
                    return " ".join(words).title()

        # Pass 2: Look for Title Case lines
        for line in search_lines:
            clean_line = line.strip()
            lower_line = clean_line.lower()

            if any(term == lower_line or term in lower_line for term in ignore_terms):
                continue
            if "@" in clean_line or "http" in clean_line or ":" in clean_line or re.search(r"\d", clean_line):
                continue
            if any(kw in lower_line for kw in ["university", "school", "company", "studio", "college", "institute", "high"]):
                continue

            segment = re.split(r"[|•@]", clean_line)[0].strip()
            segment = re.sub(title_pattern, "", segment, flags=re.IGNORECASE).strip()

            words = [w for w in segment.split() if w.isalpha() and w.lower() not in ignore_terms]
            if 2 <= len(words) <= 4 and all(len(w) >= 2 and w[0].isupper() for w in words):
                return " ".join(words).title()

        # Strategy 3: LinkedIn URL slug (e.g. linkedin.com/in/vishwa-shah-54a189210 -> Vishwa Shah)
        if linkedin_url:
            slug_match = re.search(r"linkedin\.com/in/([a-zA-Z]+[-_][a-zA-Z]+)", linkedin_url, re.IGNORECASE)
            if slug_match:
                name_parts = slug_match.group(1).replace("-", " ").replace("_", " ").split()
                valid_parts = [p.capitalize() for p in name_parts if p.lower() not in ignore_terms]
                if valid_parts:
                    return " ".join(valid_parts)

        # Strategy 4: Email address prefix (e.g. candidate@example.com -> Candidate Name)
        if email:
            email_prefix = email.split("@")[0]
            prefix_clean = re.sub(r"\d+", "", email_prefix)
            if "." in prefix_clean or "_" in prefix_clean:
                name_parts = re.split(r"[._]", prefix_clean)
                return " ".join(p.capitalize() for p in name_parts if len(p) > 1)

        return ""

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Smart regex/heuristic resume parser for Name, Phone, Email, LinkedIn, GitHub, skills, experience, and position."""
        if not text:
            return {
                "full_name": "", "email": "", "phone": "", "location": "",
                "portfolio_url": "", "linkedin_url": "", "years_experience": 0,
                "last_position": "", "skills": [], "summary": "",
                "missing_fields": ["full_name", "email", "phone", "location", "last_position"]
            }

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_single_line = " ".join(text.split())

        # 1. Extract Email
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        email = email_match.group(0).strip() if email_match else ""

        # 2. Robust Phone Extraction (US, Indian, & International formats)
        phone_patterns = [
            r"(\+?\d{1,3}[\s.-]*\d{10})",
            r"(?:\+?91[\s.-]*)?\b[6-9]\d{9}\b",
            r"(\+?\d{1,3}[\s.-]*\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4})",
            r"\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b",
            r"(?:phone|mobile|tel|contact|cell)[\s:]*([+\d\s.-]{7,20})",
            r"\b\d{10}\b"
        ]
        phone = ""
        for pat in phone_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand_p = m.group(1) if (m.groups() and m.group(1)) else m.group(0)
                clean_digits = re.sub(r"[^\d+]", "", cand_p)
                if len(re.sub(r"[^\d]", "", clean_digits)) >= 7:
                    phone = cand_p.strip()
                    break

        # 3. Robust LinkedIn URL Extraction
        linkedin_match = re.search(r"(?:https?://)?(?:[a-zA-Z0-9-]+\.)?linkedin\.com/in/[\w-]+/?", text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else ""
        if linkedin and not linkedin.startswith("http"):
            linkedin = "https://" + linkedin.lstrip("/")

        # 4. Robust GitHub / Portfolio URL Extraction
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", text, re.IGNORECASE)
        portfolio = github_match.group(0) if github_match else ""
        if not portfolio:
            dev_site_match = re.search(r"(?:https?://)?(?:www\.)?[\w-]+\.(?:github\.io|dev|io|me|com)\b/?", text, re.IGNORECASE)
            if dev_site_match and not any(domain in dev_site_match.group(0) for domain in ["gmail.com", "yahoo.com", "linkedin.com"]):
                portfolio = dev_site_match.group(0)

        if portfolio and not portfolio.startswith("http"):
            portfolio = "https://" + portfolio.lstrip("/")

        # 5. Robust Candidate Name Extraction
        full_name = self._extract_candidate_name(text, lines, linkedin_url=linkedin, email=email)

        # 6. Last Position / Recent Role Extraction
        last_pos = ""
        role_match = re.search(r"\b(?:AI/ML|AI|ML|GenAI|Backend|Frontend|Full\s*Stack|Data|Software|Cloud|DevOps|Web)\s+(?:Engineer|Developer|Scientist|Architect|Intern|Designer)\b", clean_single_line, re.IGNORECASE)
        if role_match:
            last_pos = role_match.group(0).strip().title()
        else:
            title_patterns = ["engineer", "developer", "architect", "lead", "manager", "data scientist", "consultant", "analyst", "intern", "designer"]
            for line in lines:
                line_lower = line.lower()
                if any(title in line_lower for title in title_patterns) and not any(kw in line_lower for kw in ["summary", "skills", "education", "experience", "projects", "certifications", "references"]):
                    if len(line) < 70 and not re.search(r"\d{4}", line):
                        last_pos = line.strip().title()
                        break

        # 7. Location Extraction
        location = ""
        cities = ["Ahmedabad", "Pune", "Gandhinagar", "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Gurgaon", "Noida", "Hyderabad", "Chennai", "New York", "London", "San Francisco"]
        for city in cities:
            if re.search(r"\b" + re.escape(city) + r"\b", text, re.IGNORECASE):
                location = f"{city}, India" if city in ["Ahmedabad", "Pune", "Gandhinagar", "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Gurgaon", "Noida", "Hyderabad", "Chennai"] else city
                break

        # 8. Extract Summary from CV section text
        summary = self._extract_summary_from_text(text)

        # 9. Extract Technical Skills from CV section text + comprehensive keywords
        found_skills = self._extract_skills_from_text(text)

        # Filter noise items out of fallback skills list
        noise_skill_items = {full_name.lower(), "phone", "social", "references", "education", "experience", "skills"}
        found_skills = [s for s in found_skills if s.lower() not in noise_skill_items and not re.search(r"^\d+[\s.-]*\d+", s)]

        # 10. Experience calculation in Months & Years (Handles Freshers, Interns, & Mid/Senior)
        exp_months = 0
        is_fresher = False

        month_match = re.search(r"(\d+)\+?\s*months?\s*(of)?\s*(experience|internship)?", text, re.IGNORECASE)
        year_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?\s*(of)?\s*experience", text, re.IGNORECASE)

        if month_match:
            exp_months = int(month_match.group(1))
        elif year_match:
            exp_months = int(float(year_match.group(1)) * 12)
        elif "intern" in clean_single_line.lower() or "internship" in clean_single_line.lower():
            exp_months = 6
        elif any(kw in clean_single_line.lower() for kw in ["fresher", "graduate", "student", "entry level", "entry-level"]):
            exp_months = 0
            is_fresher = True

        years_exp = round(exp_months / 12.0, 1)

        # Clean last_pos if it captured an objective sentence or noise text
        if last_pos:
            last_pos_lower = last_pos.lower()
            if any(verb in last_pos_lower for verb in ["seeking", "to leverage", "results -", "results-", "driven", "looking for", "proven track"]) or len(last_pos) > 40 or "." in last_pos or "," in last_pos:
                # Extract actual title phrase from text (e.g., Executive Engineer, Robotics Specialist, Project Manager, Software Engineer)
                clean_title_match = re.search(r"\b(?:Executive|Robotics|Mechanical|Electrical|Civil|Project|Product|Software|AI|ML|Backend|Frontend|Sales|Marketing|Data|Systems|Quality|Automation)\s+(?:Engineer|Executive|Manager|Lead|Director|Consultant|Architect|Analyst|Specialist|Developer)\b", text, re.IGNORECASE)
                if clean_title_match:
                    last_pos = clean_title_match.group(0).strip().title()
                else:
                    # Clean out noise verbs
                    cleaned_phrase = re.sub(r"^(?:to\s+leverage|seeking\s+a|results\s*-\s*oriented|seeking|looking\s+to)\s+", "", last_pos, flags=re.IGNORECASE).strip(" .")
                    words = [w for w in cleaned_phrase.split() if w.lower() not in ["and", "or", "to", "in", "for", "with", "a", "an", "the", "drive", "leverage"]]
                    last_pos = " ".join(words[:3]).title() if words else "Engineering Executive"

        if not last_pos:
            if is_fresher or exp_months == 0:
                last_pos = "Fresher"
            elif exp_months <= 12 and "intern" in clean_single_line.lower():
                last_pos = "Intern"

        display_exp = "Fresher (0 Yrs)" if (is_fresher or exp_months == 0) else (f"{exp_months} Months" if exp_months < 12 else f"{years_exp} Yrs")

        if not summary and (last_pos or found_skills):
            summary = f"{last_pos} candidate specializing in {', '.join(found_skills[:5])}."

        # Detect Missing Fields (Do NOT mark last_position missing for freshers)
        missing_fields = []
        if not full_name:
            missing_fields.append("full_name")
        if not email:
            missing_fields.append("email")
        if not phone:
            missing_fields.append("phone")
        if not linkedin:
            missing_fields.append("linkedin_url")
        if not portfolio:
            missing_fields.append("portfolio_url")
        if not location:
            missing_fields.append("location")
        if not last_pos and not is_fresher:
            missing_fields.append("last_position")

        return {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "location": location,
            "portfolio_url": portfolio,
            "linkedin_url": linkedin,
            "experience_months": exp_months,
            "years_experience": years_exp,
            "display_experience": display_exp,
            "is_fresher": is_fresher or (exp_months == 0),
            "last_position": last_pos,
            "skills": found_skills,
            "summary": summary,
            "missing_fields": missing_fields
        }

    def _extract_summary_from_text(self, text: str) -> str:
        """Extracts candidate professional summary section directly from PDF text."""
        lines = text.split("\n")
        summary_lines = []
        capturing = False

        section_headers = [
            "professional experience", "work experience", "experience",
            "technical skills", "skills", "projects", "education",
            "certifications", "licenses"
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            lower_line = stripped.lower()

            # Detect Summary Header
            if not capturing:
                if re.search(r"^(?:SUMMARY|PROFESSIONAL\s+SUMMARY|CAREER\s+SUMMARY|CAREER\s+OBJECTIVE|PROFILE|ABOUT\s+ME)\b", stripped, re.IGNORECASE):
                    capturing = True
                    # Check if summary header has content on same line (e.g. SUMMARY - Experienced engineer...)
                    after_colon = re.sub(r"^(?:SUMMARY|PROFESSIONAL\s+SUMMARY|CAREER\s+SUMMARY|CAREER\s+OBJECTIVE|PROFILE|ABOUT\s+ME)\s*[-:]?\s*", "", stripped, flags=re.IGNORECASE).strip()
                    if after_colon:
                        summary_lines.append(after_colon)
                    continue

            # If capturing, stop when next section header is reached
            if capturing:
                if any(re.match(r"^(?:" + re.escape(hdr) + r")\b", lower_line) for hdr in section_headers):
                    break
                summary_lines.append(stripped)

        clean_summary = " ".join(summary_lines).strip()
        # Clean bullet artifacts
        clean_summary = re.sub(r"^[●•\-\*]\s*", "", clean_summary)
        return clean_summary

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extracts technical skills by parsing dedicated resume section and matching expanded tech dictionary."""
        skills_set = set()

        # 1. Section Parsing: Extract text under TECHNICAL SKILLS or SKILLS
        lines = text.split("\n")
        capturing = False
        skills_section_text = []

        stop_headers = [
            "professional experience", "work experience", "experience",
            "projects", "education", "certifications", "summary", "profile"
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            lower_line = stripped.lower()

            if not capturing:
                if re.match(r"^(?:TECHNICAL\s+SKILLS|SKILLS\s+&\s+TOOLS|SKILLS\s+&\s+ABILITIES|SKILLS|CORE\s+COMPETENCIES)\b", stripped, re.IGNORECASE):
                    capturing = True
                    after_header = re.sub(r"^(?:TECHNICAL\s+SKILLS|SKILLS\s+&\s+TOOLS|SKILLS\s+&\s+ABILITIES|SKILLS|CORE\s+COMPETENCIES)\s*[-:]?\s*", "", stripped, flags=re.IGNORECASE).strip()
                    if after_header:
                        skills_section_text.append(after_header)
                    continue

            if capturing:
                if any(re.match(r"^(?:" + re.escape(hdr) + r")\b", lower_line) for hdr in stop_headers):
                    break
                skills_section_text.append(stripped)

        # Process section text lines (e.g., "Programming: Python, JavaScript, C, C++, HTML, CSS, SQL")
        for line in skills_section_text:
            # If category format "Category: skill1, skill2"
            content = line.split(":", 1)[1] if ":" in line else line
            # Split items by comma, pipe, bullet, slash
            raw_items = re.split(r"[,|•\*\/]", content)
            for item in raw_items:
                clean_item = item.strip().strip(".")
                # Filter noise words
                if clean_item and 1 < len(clean_item) < 35:
                    if clean_item.lower() not in ["and", "etc", "tool", "tools", "skills", "technologies"]:
                        skills_set.add(clean_item)

        # 2. Comprehensive Tech Keywords matching across entire CV
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "C", "C++", "Java", "Go", "Rust", "HTML", "CSS", "SQL",
            "Django", "FastAPI", "Flask", "React", "Node.js", "Express", "Angular", "Vue", "Next.js",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "PostgreSQL", "MongoDB", "Redis", "Kafka",
            "Machine Learning", "Deep Learning", "LLM", "PyTorch", "TensorFlow", "Pandas", "Scikit-Learn",
            "Git", "REST API", "GraphQL", "Playwright", "Selenium", "CI/CD", "Postman", "Linux",
            "GenAI", "RAG", "Qdrant", "ChromaDB", "LangChain", "LangGraph", "AutoML", "XGBoost", "n8n",
            "Agentic AI", "Prompt Engineering", "LiteLLM", "Hugging Face", "Vector Databases",
            "Claude Code", "OpenAI Codex", "Cursor", "OpenCV"
        ]

        for kw in tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                skills_set.add(kw)

        # Deduplicate skills case-insensitively while preserving clean capitalization
        deduped = {}
        for s in skills_set:
            key = s.lower()
            if key not in deduped:
                deduped[key] = s

        return list(deduped.values())

    def _parse_with_gemini(self, text: str) -> Dict[str, Any]:
        from google import genai
        client = genai.Client(api_key=self.api_key)

        prompt = f"""
        You are an expert AI HR & Resume Parsing Agent. Analyze the candidate resume text below:

        RESUME TEXT:
        {text[:4500]}

        Extract candidate details. CRITICAL INSTRUCTIONS:
        1. "full_name": MUST be the candidate's personal name (e.g. "Vishwa Shah"). Do NOT return section titles or random words like "long-term", "Resume", "CV", or "Data.".
        2. "phone": Extract full phone number including country code if present (e.g. "+91 87807 28939").
        3. "last_position": Extract most recent job title (e.g. "AI Engineer" or "AI/ML Engineer Intern").
        4. If a field is not found in the text, return "".

        Return ONLY a JSON object with these exact keys:
        {{
          "full_name": string (the candidate's personal name),
          "email": string,
          "phone": string,
          "location": string,
          "portfolio_url": string (GitHub or portfolio URL e.g. "https://github.com/username"),
          "linkedin_url": string (LinkedIn profile URL e.g. "https://linkedin.com/in/username"),
          "years_experience": integer (total years experience),
          "last_position": string (most recent job title & company),
          "skills": list of strings,
          "summary": string professional summary,
          "missing_fields": list of missing attribute names from ["full_name", "email", "phone", "linkedin_url", "portfolio_url", "location", "last_position"] if empty or absent in resume
        }}
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        out_text = response.text.strip()
        if "```json" in out_text:
            out_text = out_text.split("```json")[1].split("```")[0].strip()

        data = json.loads(out_text)
        return data
