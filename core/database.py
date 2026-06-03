import sqlite3
from pathlib import Path

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

