import yaml

from parsers.greenhouse import GreenhouseParser

from core.database import (
    init_db,
    job_exists,
    insert_job
)

from core.notifier import send_notification

def load_companies():
    with open('config/companies.yaml', 'r') as f:
        return yaml.safe_load(f)['companies']

def main():

    init_db()

    companies = load_companies()

    new_jobs = []

    for company in companies:

        # if not company["enabled"]:
            # continue

        parser_type = company["parser"]

        if parser_type == "greenhouse":
            parser = GreenhouseParser(company["name"], company["board_token"])
        
        else:
            continue

        jobs = parser.fetch_jobs()

        for job in jobs:

            if not job_exists(job['url']):
                insert_job(job)
                new_jobs.append(job)

    if new_jobs:

        lines = ["<b>New Job Postings:</b>\n"]
        for job in new_jobs:
            lines.append(f"<b>{job['company']}</b>: <a href='{job['url']}'>{job['title']}</a> - {job['location']}")
    
        message = "\n\n".join(lines)
        send_notification(message)
        print(f"Sent notification for {len(new_jobs)} new jobs.")
    else:
        print("No new jobs found.")

if __name__ == "__main__":
    main()
            