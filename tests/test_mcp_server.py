"""
Unit tests for MCP server functions with 10 Target Portals.
"""

import sys
sys.path.insert(0, r"d:\[GIT PROJECT]\Automate_Job_Apply")

from mcp_server import get_supported_portals, evaluate_job_match, search_jobs_live

def test_get_supported_portals():
    portals_info = get_supported_portals()
    assert "LinkedIn" in portals_info
    assert "Naukri.com" in portals_info
    assert "Instahyre" in portals_info
    assert "Company Career Pages" in portals_info
    assert "Indeed" in portals_info
    assert "Wellfound" in portals_info
    assert "Cutshort" in portals_info
    assert "We Work Remotely" in portals_info
    assert "FlexJobs" in portals_info
    assert "Remote.co" in portals_info

def test_evaluate_job_match_mcp():
    report = evaluate_job_match(
        job_title="Senior Python Engineer",
        company="DataCo",
        description="Looking for Python, FastAPI, Docker, and PostgreSQL developer."
    )
    assert "FIT EVALUATION REPORT" in report
    assert "Match Score" in report
