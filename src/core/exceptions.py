"""
Custom Exception Classes for JobPulse AI.
"""

class JobPulseError(Exception):
    """Base exception class for JobPulse AI errors."""
    pass

class ScraperError(JobPulseError):
    """Raised when job portal scraping encounters a failure."""
    pass

class MatcherError(JobPulseError):
    """Raised when job fit evaluation fails."""
    pass

class ApplierError(JobPulseError):
    """Raised during Playwright form-fill and auto-apply failures."""
    pass

class UnhashableItemError(JobPulseError, TypeError):
    """Raised when unhashable types are used in set/dict key operations without hashing wrapper."""
    pass
