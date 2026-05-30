"""Phase 1: Relevance filtering based on job title keywords."""

INCLUDE_KEYWORDS = [
    # DevOps / Reliability
    "devops",
    "sre",
    "site reliability",

    # Infra / Platform
    "platform engineer",
    "infrastructure engineer",
    "cloud engineer",
    "systems engineer",
    "reliability engineer",

    # Automation / Delivery
    "automation engineer",
    "build engineer",
    "release engineer",

    # Broader SWE (backend-focused)
    "software engineer",
    "backend engineer",

    # Linux / Systems
    "linux engineer",

    # Platform tooling
    "developer platform",
]


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_relevant(job: dict) -> bool:
    """Phase 1: Title-based relevance filter"""
    return contains_any_keyword(job.get('title', '').lower().strip(), INCLUDE_KEYWORDS)


def matching_keywords(title: str) -> list[str]:
    title = title.lower().strip()
    return [keyword for keyword in INCLUDE_KEYWORDS if keyword in title]
