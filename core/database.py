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
