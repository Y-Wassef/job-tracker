# Job Monitor System — Build Spec (MVP)

## 1. Overview

A lightweight automation system that periodically scans a curated list of Swiss companies’ career pages, extracts job postings, filters them based on predefined DevOps-oriented criteria, and sends a daily digest of relevant new jobs via Telegram.

The system prioritizes:
- minimal noise
- low maintenance
- HTTP-first scraping (no browser automation unless necessary)
- simple deployment
- strong deduplication of job postings

---

## 2. Goals (MVP)

### Primary goals
- Track ~20–50 curated Swiss companies (scalable to 300+ later)
- Detect new job postings automatically
- Filter jobs for DevOps/SRE/Platform/Cloud roles
- Exclude irrelevant seniority or language constraints
- Send a daily summary (Telegram)

### Non-goals (explicitly out of scope)
- Web UI/dashboard
- User accounts / authentication system
- ML model training
- Full LinkedIn/job board scraping
- Real-time alerts (MVP uses daily digest only)
- Complex orchestration systems

---

## 3. System Architecture

```
config/
    companies.yaml

core/
    scraper.py      # orchestration
    fetcher.py      # HTTP requests
    parser.py       # parsing abstraction
    matcher.py      # filtering/scoring logic
    notifier.py     # Telegram integration
    scheduler.py    # cron entrypoint

parsers/
    base.py
    greenhouse.py
    lever.py
    workday.py
    successfactors.py   # (important later)
    generic_html.py

storage/
jobs.db # SQLite database

logs/
app.log
```

---

## 4. Data Model

### 4.1 Companies (config file — YAML)

Stored in `config/companies.yaml`

```yaml
companies:
  - name: Swisscom
    url: https://careers.swisscom.ch
    parser: workday
    enabled: true
    tags: [telecom, cloud]

  - name: Sonar
    url: https://www.sonarsource.com/jobs
    parser: greenhouse
    enabled: true
    tags: [devtools, platform]
```

---

### 4.2 Jobs (SQLite)

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    title TEXT,
    url TEXT UNIQUE,
    location TEXT,
    description TEXT,
    hash TEXT,
    raw_score INTEGER DEFAULT 0,
    filtered INTEGER DEFAULT 0,
    notified INTEGER DEFAULT 0
);
```

---

### 4.3 Deduplication Strategy

A job is considered unique if:
```
hash = sha1(company + title + url)
```
or fallback:
```
hash = sha1(title + company + location)
```

---

## 5. Scraping Strategy

### 5.1 HTTP-first approach (default)

#### Steps:

1. GET careers page or API endpoint
2. Detect response type:
    - JSON → parse directly
    - HTML → parse with BeautifulSoup/selectolax
3. Extract job postings
4. Normalize fields into standard schema

For Greenhouse jobs, always prefer `?content=true` when available to enrich descriptions.

---

### 5.2 Fallback (optional later)

If job listings are not available via HTTP:

- mark company as `needs_browser = true`
- optionally use Playwright (NOT in MVP unless required)

---

## 6. Standard Job Schema

All parsers must output a normalized job object BEFORE storage:

``` python
Job {
    company: str
    title: str
    url: str
    location: str | None
    description: str | None
}
```

This ensures all downstream logic is parser-agnostic.

---

## 7. Filtering / Matching Engine

- Filtering happens BEFORE scoring and is strictly binary (pass/fail).
- Scoring only applies to already-filtered jobs.

### 7.1 Hard Filtering (NEW)

```
if no INCLUDE keyword match:
    reject job

if any EXCLUDE keyword match:
    reject job
```

### 7.2 Keyword-based scoring (MVP)

#### Positive signals:
- devops
- sre
- platform
- cloud
- kubernetes
- infrastructure
- ci/cd
- docker
- terraform
- linux

#### Negative signals:
- senior
- staff
- principal
- architect
- german required
- french required (optional rule depending on preference)
- sales
- support engineer (optional exclusion depending on strictness)

---

### 7.3 Scoring model

```
score = 0

+10 for each positive keyword match
-20 for each negative keyword match
+5 if junior/mid level detected
```

---

### 7.4 Threshold
```
score >= 10 → include in output
```

---

## 8. Notification System

### 8.1 Telegram bot
- Create bot via BotFather
- Use HTTP API

### 8.2 Message format

Daily digest:

```
📢 New DevOps-related jobs (3)

1. Platform Engineer — Swisscom
https://...

2. SRE Engineer — Sonar
https://...

3. Cloud Engineer — Adnovum
https://...
```

---

## 9. Scheduler

### Option A (recommended MVP): cron
```
0 19 * * * python3 /app/core/scraper.py
```

Runs daily at 19:00.

---

### Option B: GitHub Actions
- scheduled workflow every X hours
- runs scraper script
- sends Telegram message

Limitation: weak persistence layer (SQLite handling is awkward)

---

## 10. Deployment Options

### Option 1: VPS (recommended long-term)
- Ubuntu 24.04
- Docker optional
- systemd or cron
- persistent SQLite storage

Cost: ~5 CHF/month

---

### Option 2: GitHub Actions (MVP quick start)

Pros:

- free
- no infra setup

Cons:

- no persistent filesystem
- awkward state handling
- less control over runtime environment

---

## 11. Execution Flow

```
1. Load companies.yaml
2. For each company:
    2.1 fetch jobs
    2.2 normalize jobs
3. For each job:
    3.1 compute hash
    3.2 check if exists in DB
    3.3 if new → store raw job
    3.4 apply HARD FILTER
    3.5 compute score
4. Update last_seen for all fetched jobs
5. Collect filtered jobs above threshold
6. Send Telegram digest
```

---

## 12. Error Handling Strategy

- Network failures → retry (max 2–3 attempts)
- Parser failures → log and skip company
- Invalid HTML structure → fallback parser or mark as broken
- Rate limiting → exponential backoff

---

## 13. Logging
- log each run:
    - number of companies scanned
    - number of jobs found
    - number of new jobs
    - number of matches
- store logs in `logs/app.log`

---

## 14. MVP Timeline (7 days)

### Day 1
- project structure
- YAML config
- SQLite setup

### Day 2
- fetcher (HTTP requests)
- base parser interface

### Day 3
- Greenhouse + Lever parser

### Day 4
- job normalization + DB insertion

### Day 5
- deduplication + scoring engine

### Day 6
- Telegram bot integration

### Day 7
- scheduler (cron or GitHub Actions)
- deployment (optional VPS)

---

## 15. Optional Enhancements (post-MVP)

- Playwright fallback for JS-heavy sites
- embeddings-based matching (semantic filtering)
- simple web dashboard (FastAPI)
- job trend analytics
- auto-prioritization of companies
- multi-region expansion (EU/remote jobs)

---

## 16. Key Design Principles

- HTTP-first scraping
- deterministic filtering (no hidden AI dependency in MVP)
- minimal infrastructure
- human-curated company list
- persistent deduplication is mandatory
- notifications must be low-noise and high-signal

---

## 17. Success Criteria

MVP is successful if:

- system runs unattended daily
- <10 irrelevant jobs/day in output
- zero manual browsing of job portals needed
- consistent detection of new DevOps roles
- user spends <5 minutes/day reviewing results

---