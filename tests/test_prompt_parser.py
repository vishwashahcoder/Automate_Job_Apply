"""
Unit tests for SearchPromptParser with 10 Target Portals and salary expectation parsing.
"""

from src.core.prompt_parser import SearchPromptParser

def test_prompt_parser_heuristic():
    parser = SearchPromptParser()
    prompt = "I want remote AI engineer jobs from all over world and full-time for ahmedabad, pune"
    
    result = parser._parse_heuristic(prompt)
    assert isinstance(result, dict)
    assert "query" in result
    assert "locations" in result
    assert "job_types" in result
    assert result["remote_only"] is True
    assert "Ahmedabad" in result["locations"]
    assert "Pune" in result["locations"]
    assert "Full-time" in result["job_types"]
    assert "company_careers" in result["platforms"]
    assert "weworkremotely" in result["platforms"]
    assert "linkedin" in result["platforms"]


def test_prompt_parser_salary_expectations_inr():
    parser = SearchPromptParser()
    prompt = "Remote Python developer in Pune minimum 20 LPA"
    
    result = parser.parse_prompt(prompt)
    assert result["min_salary"] == 2000000
    assert result["salary_currency"] == "INR"


def test_prompt_parser_salary_expectations_usd():
    parser = SearchPromptParser()
    prompt = "Senior AI Engineer worldwide remote paying above $130k USD"
    
    result = parser.parse_prompt(prompt)
    assert result["min_salary"] == 130000
    assert result["salary_currency"] == "USD"
