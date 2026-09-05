"""
Unit tests for ResumeParserAgent with GitHub & LinkedIn URL extraction.
"""

import io
import pytest
from pypdf import PdfWriter
from src.core.resume_agent import ResumeParserAgent


@pytest.fixture
def sample_pdf_bytes():
    """Generates a simple sample PDF file in memory for testing."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_resume_parser_agent_extraction(sample_pdf_bytes):
    agent = ResumeParserAgent()
    text = agent.extract_text_from_pdf(sample_pdf_bytes)
    assert isinstance(text, str)


def test_resume_parser_agent_urls_extraction():
    agent = ResumeParserAgent()
    resume_text = """
    Vishwa Shah
    Email: vishwa.shah@example.com
    LinkedIn: linkedin.com/in/vishwa-shah-ai
    GitHub: github.com/vishwa-shah
    Location: Ahmedabad, India
    
    Summary:
    Senior AI/ML Engineer with 4 years experience building Python, FastAPI, Docker, and LLM Agentic systems.
    
    Experience:
    Senior AI Engineer at TechCorp Innovations (2022 - Present)
    """

    parsed = agent._fallback_parse(resume_text)
    assert parsed["full_name"] == "Vishwa Shah"
    assert parsed["email"] == "vishwa.shah@example.com"
    assert "https://linkedin.com/in/vishwa-shah-ai" in parsed["linkedin_url"]
    assert "https://github.com/vishwa-shah" in parsed["portfolio_url"]
    assert "Python" in parsed["skills"]
    assert parsed["years_experience"] == 4
