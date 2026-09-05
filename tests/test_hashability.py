"""
Tests for hashability and dictionary deduplication to verify 'TypeError: unhashable type: dict' is completely resolved.
"""

import pytest
from src.models.job import JobPosting, make_hashable, deduplicate_jobs

def test_job_posting_hashable():
    job1 = JobPosting(job_id="j1", title="Python Engineer", company="TechCorp", location="Remote", platform="LinkedIn", url="http://example.com/1", description="Backend engineer")
    job2 = JobPosting(job_id="j1", title="Python Engineer", company="TechCorp", location="Remote", platform="LinkedIn", url="http://example.com/1", description="Backend engineer")
    job3 = JobPosting(job_id="j2", title="AI Developer", company="DataInc", location="Pune", platform="Naukri", url="http://example.com/2", description="AI engineer")

    job_set = {job1, job2, job3}
    assert len(job_set) == 2
    assert job1 in job_set
    assert job3 in job_set

def test_make_hashable():
    dict_item = {"a": 1, "b": [1, 2, {"c": 3}]}
    hashable_res = make_hashable(dict_item)
    
    # Should not raise TypeError
    set_obj = {hashable_res}
    assert hashable_res in set_obj

def test_deduplicate_jobs_with_dicts_and_objects():
    job_obj = JobPosting(job_id="j100", title="DevOps", company="CloudCo", location="Remote", platform="LinkedIn", url="http://ex.com", description="")
    job_dict_dup = {"job_id": "j100", "title": "DevOps", "company": "CloudCo"}
    job_dict_unique = {"job_id": "j200", "title": "FullStack", "company": "WebCorp"}
    raw_dict_no_id = {"title": "Data Scientist", "company": "AI Core"}
    raw_dict_no_id_dup = {"title": "Data Scientist", "company": "AI Core"}

    items = [job_obj, job_dict_dup, job_dict_unique, raw_dict_no_id, raw_dict_no_id_dup]

    # Must deduplicate without throwing TypeError: unhashable type: 'dict'
    deduped = deduplicate_jobs(items)
    assert len(deduped) == 3
