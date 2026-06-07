import sqlite3
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("storage/jobs.db")

def init_db():

    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                description TEXT,
                parser TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT UNIQUE NOT NULL,
                is_relevant INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


def job_exists(url):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
    return exists


def insert_job(job):

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (
                company,
                url,
                title,
                location,
                description,
                parser
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job['company'],
            job['url'],
            job['title'],
            job['location'],
            job['description'],
            job['parser']
        ))

        conn.commit()


def get_location_status(location: str) -> int | None:
    """Returns is_relevant value: 1=approved, 0=rejected, None=unknown"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_relevant FROM locations WHERE location = ?", (location,))
        result = cursor.fetchone()
    return result[0] if result else None


def add_location(location: str, is_relevant: int):
    """Store location decision: 1=approved, 0=rejected"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO locations (location, is_relevant)
            VALUES (?, ?)
        """, (location, is_relevant))
        conn.commit()


def get_unknown_locations() -> list[str]:
    """Get all locations with unknown status (NULL)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT location FROM locations WHERE is_relevant IS NULL ORDER BY added_date")
        results = cursor.fetchall()
    return [r[0] for r in results]


def get_jobs_to_delete(company: str, hours: int | None) -> list[dict]:
    """Get jobs that would be deleted for a specific company or all companies, optionally filtered by past X hours"""
    if company == "all":
        company = "%"  # SQL wildcard to match all companies
    if hours is not None:
        time_filter = "AND date_added > datetime('now', '-' || ? || ' hours')"
        params = (company, hours)
    else:
        time_filter = ""
        params = (company,)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT id, company, title, url FROM jobs
            WHERE company LIKE ? {time_filter}
        """, params)
        return [dict(row) for row in cursor.fetchall()]


def delete_jobs(company: str, hours: int | None = None) -> int:
    """Delete all jobs from a specific company. Returns count of deleted jobs. If hours is None and company is 'all', requires confirmation before deleting all jobs."""
    if company == "all":
        company = "%"  # SQL wildcard to match all companies
    if hours is not None:
        time_filter = "AND date_added > datetime('now', '-' || ? || ' hours')"
        params = (company, hours)
    else:
        time_filter = ""
        params = (company,)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            DELETE FROM jobs
            WHERE company LIKE ? {time_filter}
        """, params)
        conn.commit()
        return cursor.rowcount


def import_locations_from_json(json_path: str) -> int:
    """Import locations from a JSON file with structure: [{"location": "Location Name", "is_relevant": 1}, ...]
    Returns the number of locations imported."""
    try:
        with open(json_path, 'r') as f:
            locations = json.load(f)
        for loc in locations:
            if get_location_status(loc['location']) is None:
                add_location(loc['location'], loc['is_relevant'])
        Path(json_path).unlink(missing_ok=True)
        return len(locations)
    except FileNotFoundError:
        logger.warning(f"Import JSON file not found: {json_path}. No locations imported.")
        return 0
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in import file: {json_path}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return 0


def export_locations_to_json(json_path: str) -> int:
    """Export all locations from the database to a JSON file with structure: [{"location": "Location Name", "is_relevant": 1}, ...]
    Returns the number of locations exported."""
    if Path(json_path).exists():
        logger.info(f"JSON file already exists: {json_path}. Importing existing locations before export.")
        import_locations_from_json(json_path)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT location, is_relevant FROM locations")
            locations = [{"location": row[0], "is_relevant": row[1]} for row in cursor.fetchall()]
        with open(json_path, 'w') as f:
            json.dump(locations, f, indent=4)
        return len(locations)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return 0