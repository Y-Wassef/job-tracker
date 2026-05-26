import yaml
import argparse


from parsers.greenhouse import GreenhouseParser
from parsers.workday import WorkdayParser

from core.database import (
    init_db,
    job_exists,
    insert_job
)

from core.notifier import send_notification
from core.filter import is_relevant, matching_keywords

def load_companies():
    with open('config/companies.yaml', 'r') as f:
        return yaml.safe_load(f)['companies']
    
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()

def main(dry_run=False):

    init_db()

    companies = load_companies()

    new_jobs = []

    for company in companies:

        if not company.get("enabled", True):
            continue      

        parser_type = company["parser"]

        #switch-case for parser types
        switcher = {
            "workday": WorkdayParser,
            "greenhouse": GreenhouseParser,
            # "generic_html": GenericHTMLParser
        }

        parser_class = switcher.get(parser_type)
        if not parser_class:
            print(f"Unknown parser type '{parser_type}' for company {company['name']}. Skipping.")
            continue
        parser = parser_class(company)

        jobs = parser.fetch_jobs()

        for job in jobs:

            if not is_relevant(job):
                continue

            if not job_exists(job["url"]):

                if dry_run:
                    print(
                        # f"[MATCH] "
                        # f"{job['company']} | "
                        f"{job['title']} | "
                        # f"{job['location']}"
                        f"Keywords: {', '.join(matching_keywords(job['title']))}"
                    )
                else:
                    insert_job(job)

                new_jobs.append(job)

    if new_jobs:
        if not dry_run:
            lines = ["<b>New Job Postings:</b>\n"]
            for job in new_jobs:
                lines.append(f"<b>{job['company']}</b>: <a href='{job['url']}'>{job['title']}</a> - {job['location']}")
        
            message = "\n\n".join(lines)
            send_notification(message)
            print(f"Sent notification for {len(new_jobs)} new jobs.")
        else:
            print(f"[DRY] Found {len(new_jobs)} new jobs.")
    else:
        print("No new jobs found.")

if __name__ == "__main__":
    args = get_args()
    main(dry_run=args.dry_run)
            