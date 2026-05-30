"""Phase 3: Job scoring based on title and description keywords."""

import re

POSITIVE_KEYWORDS = [
    "devops", "sre", "site reliability",
    "platform engineer", "infrastructure engineer",
    "cloud engineer", "systems engineer",
    "automation engineer", "build engineer", "release engineer",
    "reliability engineer",
    "ci/cd", "pipeline", "kubernetes", "docker", "terraform",
    "monitoring", "observability", "elk", "prometheus",
    "infrastructure", "automation", "release", "deployment",
    "security", "scanning", "compliance",
    "golang", "go", "python", "bash", "c++",
]

NEGATIVE_KEYWORDS = [
    "sales", "marketing", "product manager", "designer",
    "frontend", "ui/ux", "product owner",
]

SENIORITY_POSITIVE = [
    r"\bjunior\b",
    r"\bentry\b",
    r"\bentry-level\b",
    r"\bgraduate\b",
    r"\btrainee\b",
    r"\bintern\b",
    r"\bmid-?level\b",
]

SENIORITY_NEGATIVE = [
    (r"\bsenior\b", -10),
    (r"\bstaff\b", -15),
    (r"\bprincipal\b", -20),
    (r"\barchitect\b", -15),
    (r"\blead\s+engineer\b", -5),
    (r"\b\d+\+\s*years\b", -15),
    (r"\b\d+\s+or\s+more\s+years\b", -15),
    (r"\b5\s+years\b", -15),
]


def score_job(job: dict) -> int:
    """Phase 3: Score job based on title and description"""
    title = job['title'].lower()
    description = job.get('description', '').lower()

    score = 0

    # Title scoring
    if "devops" in title or "sre" in title:
        score += 50
    elif "platform" in title and "engineer" in title:
        score += 40
    elif "infrastructure" in title or "systems" in title:
        score += 35
    elif "automation" in title and "engineer" in title:
        score += 30
    elif "backend" in title:
        score += 15
    elif "software engineer" in title:
        score += 10

    # Description scoring
    for keyword in POSITIVE_KEYWORDS:
        if keyword in description:
            score += 3

    # Seniority check
    for keyword in SENIORITY_POSITIVE:
        if re.search(keyword, title + " " + description):
            score += 5

    for pattern, penalty in SENIORITY_NEGATIVE:
        if re.search(pattern, title + " " + description):
            score += penalty

    # Negative signals
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in description:
            score -= 10

    return score
