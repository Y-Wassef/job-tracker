import re
from core.database import get_location_status, add_location
from core.scoring import is_relevant, score_job

LOCATION_PLACEHOLDERS = [
    r"^\d+\s+locations?$",
    r"^multiple\s+locations?$",
    r"^various$",
    r"^tbd$",
    r"^to\s+be\s+determined$",
]


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
