"""Job filtering pipeline with three stages: relevance, location, scoring."""

import importlib

_relevance = importlib.import_module('.01_relevance', package='core.filters')
_location = importlib.import_module('.02_location', package='core.filters')
_scoring = importlib.import_module('.03_scoring', package='core.filters')

# Phase 1: Relevance
is_relevant = _relevance.is_relevant
matching_keywords = _relevance.matching_keywords
INCLUDE_KEYWORDS = _relevance.INCLUDE_KEYWORDS

# Phase 2: Location
location_filter = _location.location_filter
is_placeholder_location = _location.is_placeholder_location
LOCATION_PLACEHOLDERS = _location.LOCATION_PLACEHOLDERS

# Phase 3: Scoring
score_job = _scoring.score_job
POSITIVE_KEYWORDS = _scoring.POSITIVE_KEYWORDS
NEGATIVE_KEYWORDS = _scoring.NEGATIVE_KEYWORDS
SENIORITY_POSITIVE = _scoring.SENIORITY_POSITIVE
SENIORITY_NEGATIVE = _scoring.SENIORITY_NEGATIVE

__all__ = [
    # Phase 1: Relevance
    "is_relevant",
    "matching_keywords",
    "INCLUDE_KEYWORDS",
    # Phase 2: Location
    "location_filter",
    "is_placeholder_location",
    "LOCATION_PLACEHOLDERS",
    # Phase 3: Scoring
    "score_job",
    "POSITIVE_KEYWORDS",
    "NEGATIVE_KEYWORDS",
    "SENIORITY_POSITIVE",
    "SENIORITY_NEGATIVE",
]
