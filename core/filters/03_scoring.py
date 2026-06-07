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

# German language requirement patterns at 4 severity levels
GERMAN_REQUIRED_PATTERNS = [
    r"\bgerman\s+required\b",
    r"\bgerman\s+must\b",
    r"\bgerman\s+essential\b",
    r"\bgerman\s+mandatory\b",
    r"\brequires\s+german\b",
    r"\bmust\s+speak\s+german\b",
    r"\bfluency\s+in\s+german\s+required\b",

    r"\bdeutsch\s+erforderlich\b",
    r"\bdeutsch\s+notwendig\b",
    r"\bdeutschkenntnisse\s+erforderlich\b",
    r"\bdeutsch\s+grundvoraussetzung\b",
    r"\bfließend\s+deutsch\b",
    r"\bfliessend\s+deutsch\b",

    # stronger real-world formulations
    r"\bverhandlungssicher(?:es|e)?\s+deutsch\b",
    r"\bsehr\s+gute\s+deutschkenntnisse\s+erforderlich\b",
    r"\bzwingend\s+deutsch\b",
    r"\bdeutsch\s+zwingend\b",
]

GERMAN_STRONG_PATTERNS = [
    r"\bfluent\s+german\b",
    r"\bvery\s+good\s+german\b",
    r"\badvanced\s+german\b",
    r"\bexcellent\s+german\b",
    r"\bstrong\s+german\b",
    r"\bfluent\s+in\s+german\b",
    r"\bhigh\s+level\s+german\b",

    r"\bsehr\s+gutes\s+deutsch\b",
    r"\bfortgeschrittenes\s+deutsch\b",
    r"\bausgezeichnete\s+deutschkenntnisse\b",
    r"\bhohes\s+deutsch\s*-\s*niveau\b",

    # real-world additions from your samples
    r"\bverhandlungssicher(?:es|e)?\s+deutsch\b",
    r"\bverhandlungssicher\s+in\s+deutsch\b",
    r"\bsehr\s+gute\s+kenntnisse\s+in\s+deutsch\b",
    r"\bsehr\s+gute\s+deutsch\s*-\s*kenntnisse\b",
    r"\bdeutsch\s+verhandlungssicher\b",
]

GERMAN_GOOD_PATTERNS = [
    r"\bgood\s+german\b",
    r"\bgerman\s+skills\b",
    r"\bworking\s+german\b",
    r"\bsolid\s+german\b",
    r"\bproficient\s+in\s+german\b",
    r"\bintermediate\s+german\b",

    r"\bgutes\s+deutsch\b",
    r"\bdeutschkenntnisse\b",
    r"\bdeutsch\s+und\s+englisch\s+kenntnisse\b",
    r"\barbeitsf[äa]higes\s+deutsch\b",
    r"\bsolide\s+deutschkenntnisse\b",

    r"\bmittleres\s+deutsch\s*-\s*niveau\b",

    # very important real-world variants
    r"\bsehr\s+gute\s+kenntnisse\s+in\s+deutsch\b",
    r"\bsehr\s+gute\s+deutsch\s+und\s+englisch\s+kenntnisse\b",
    r"\bsehr\s+gute\s+deutsch\s*-\s*und\s*englisch\s*kenntnisse\b",

    r"\bverhandlungssicher\s+in\s+deutsch\s+und\s+englisch\b",
]

GERMAN_BENEFICIAL_PATTERNS = [
    r"\bgerman\s+beneficial\b",
    r"\bgerman\s+is\s+a\s+plus\b",
    r"\bgerman\s+preferred\b",
    r"\bgerman\s+advantage\b",
    r"\bknowledge\s+of\s+german\b",

    r"\bdeutsch\s+von\s+vorteil\b",
    r"\bdeutsch\s+w[üu]nschenswert\b",
    r"\bdeutschkenntnisse\s+erw[üu]nscht\b",
    r"\bvon\s+vorteil\s+deutsch\b",
    r"\bdeutsch\s+grundkenntnisse\b",

    # your real-world cases
    r"\bgerman\s+is\s+a\s+big\s+plus\b",
    r"\bgerman\s+is\s+an\s+asset\b",
    r"\badditional\s+language.*german\b",
    r"\bgerman\s+or\s+french\s+is\s+a\s+plus\b",
    r"\bany\s+additional\s+language.*plus\b",
]

def score_job(job: dict) -> int:
    """Phase 3: Score job based on title and description"""
    title = job['title'].lower()
    description = job.get('description', '').lower()
    combined_text = title + " " + description

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
        if re.search(keyword, combined_text):
            score += 5

    for pattern, penalty in SENIORITY_NEGATIVE:
        if re.search(pattern, combined_text):
            score += penalty

    # Negative signals
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in description:
            score -= 10

    # German language requirement penalties (check in descending severity order)
    for pattern in GERMAN_REQUIRED_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score -= 40
            return score

    for pattern in GERMAN_STRONG_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score -= 25
            return score

    for pattern in GERMAN_GOOD_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score -= 15
            return score

    for pattern in GERMAN_BENEFICIAL_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            score -= 5
            return score

    return score
