import re
from core.database import get_location_status, add_location

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

# Seniority patterns
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

LOCATION_PLACEHOLDERS = [
    r"^\d+\s+locations?$",
    r"^multiple\s+locations?$",
    r"^various$",
    r"^tbd$",
    r"^to\s+be\s+determined$",
]


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def is_relevant(job: dict) -> bool:
    """Phase 1: Title-based relevance filter"""
    return contains_any_keyword(job.get('title', '').lower().strip(), INCLUDE_KEYWORDS)


def matching_keywords(title: str) -> list[str]:
    title = title.lower().strip()
    return [keyword for keyword in INCLUDE_KEYWORDS if keyword in title]


def is_placeholder_location(location: str) -> bool:
    """Check if location is a placeholder (not a real location)"""
    loc_lower = location.lower().strip()
    return any(re.match(pattern, loc_lower) for pattern in LOCATION_PLACEHOLDERS)


def location_filter(job: dict, interactive: bool = False) -> list[str]:
    """
    Phase 2: Location filtering.
    Returns list of approved locations from job['location'].
    On interactive mode, prompts user for unknown locations.
    """
    location_str = job.get('location', '').strip()
    if not location_str:
        return []

    # Split locations by common delimiters
    locations = re.split(r'[;,/]', location_str)
    locations = [loc.strip() for loc in locations if loc.strip()]

    approved_locs = []
    for loc in locations:
        # Skip placeholder locations automatically
        # if is_placeholder_location(loc):
            # continue

        status = get_location_status(loc)

        if status == 1:  # Approved
            approved_locs.append(loc)
        elif status == 0:  # Rejected
            continue
        elif status is None:  # Unknown
            if interactive:
                response = input(f"New location: '{loc}' - Include? (y/n): ").strip().lower()
                is_approved = response == 'y'
                add_location(loc, 1 if is_approved else 0)
                if is_approved:
                    approved_locs.append(loc)
            else:
                # Cloud mode: include unknown locations
                approved_locs.append(loc)

    return approved_locs


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
