import sqlite3
from pathlib import Path

DB_PATH = Path("storage/jobs.db")

def init_db():

    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()


def job_exists(url):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def insert_job(job):

    conn = sqlite3.connect(DB_PATH)
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
    conn.close()


def get_location_status(location: str) -> int | None:
    """Returns is_relevant value: 1=approved, 0=rejected, None=unknown"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT is_relevant FROM locations WHERE location = ?", (location,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def add_location(location: str, is_relevant: int):
    """Store location decision: 1=approved, 0=rejected"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO locations (location, is_relevant)
        VALUES (?, ?)
    """, (location, is_relevant))
    conn.commit()
    conn.close()


def get_unknown_locations() -> list[str]:
    """Get all locations with unknown status (NULL)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT location FROM locations WHERE is_relevant IS NULL ORDER BY added_date")
    results = cursor.fetchall()
    conn.close()
    return [r[0] for r in results]
