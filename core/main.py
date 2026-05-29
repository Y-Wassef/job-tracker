import yaml
import argparse


from parsers.greenhouse import GreenhouseParser
from parsers.workday import WorkdayParser
from parsers.successfactors import SuccessFactorsParser
from parsers.sixgroup import SixGroupParser
from parsers.cern import CernParser
from parsers.epam import EpamParser
from parsers.sonarsource import SonarSourceParser

from core.database import (
    init_db,
    job_exists,
    insert_job
)

from core.notifier import send_notification
from core.filter import is_relevant, matching_keywords, location_filter, score_job

def load_companies():
    with open('config/companies.yaml', 'r') as f:
        return yaml.safe_load(f)['companies']
    
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the script without inserting jobs into the database or sending notifications."
    )
    parser.add_argument(
        "--respect-db",
        action="store_true",
        help="In dry-run mode, skip jobs that already exist in the database."
    )
    parser.add_argument(
        "--companies",
        nargs="+",
        help="Run only selected companies."
    )
    parser.add_argument(
        "--interactive-locations",
        action="store_true",
        help="Prompt for unknown job locations (local mode only)."
    )

    return parser.parse_args()

def main(dry_run=False, respect_db=False, selected_companies=None, interactive_locations=False):

    init_db()

    companies = load_companies()

    if selected_companies:
        companies = [c for c in companies if c["name"] in selected_companies]
        if not companies:
            print("No matching companies found for the specified names.")
            return

    new_jobs = []

    for company in companies:

        if not selected_companies and not company.get("enabled", True):
            continue

        parser_type = company["parser"]

        PARSER_MAP = {
            "workday": WorkdayParser,
            "greenhouse": GreenhouseParser,
            "successfactors": SuccessFactorsParser,
            "sixgroup": SixGroupParser,
            "cern": CernParser,
            "epam": EpamParser,
            "sonarsource": SonarSourceParser,
        }

        parser_class = PARSER_MAP.get(parser_type)
        if not parser_class:
            print(f"Unknown parser type '{parser_type}' for company {company['name']}. Skipping.")
            continue
        parser = parser_class(company)

        jobs = parser.fetch_jobs()

        for job in jobs:

            if not is_relevant(job):
                continue

            approved_locs = location_filter(job, interactive=interactive_locations)
            if not approved_locs:
                continue

            exists = job_exists(job["url"])

            if dry_run:

                if respect_db and exists:
                    continue

                score = score_job(job)
                prefix = "[SEEN]" if exists else "[NEW]"
                print(
                    f"{prefix} "
                    f"{job['company']} | "
                    f"{job['title']} | "
                    f"{job['location']} | "
                    f"Score: {score} | "
                    f"Keywords: {', '.join(matching_keywords(job['title']))}"
                )

                new_jobs.append((job, score))

            else:

                if exists:
                    continue

                score = score_job(job)
                insert_job(job)
                new_jobs.append((job, score))

    if new_jobs:
        if not dry_run:
            lines = ["<b>New Job Postings:</b>\n"]
            for job, score in new_jobs:
                lines.append(f"<b>{job['company']}</b>: <a href='{job['url']}'>{job['title']}</a> - {job['location']} (Score: {score})")

            message = "\n\n".join(lines)
            send_notification(message)
            print(f"Sent notification for {len(new_jobs)} new jobs.")
        else:
            print(f"[DRY] Found {len(new_jobs)} new jobs.")
    else:
        print("No new jobs found.")


if __name__ == "__main__":
    args = get_args()
    main(
        dry_run=args.dry_run,
        respect_db=args.respect_db,
        selected_companies=args.companies,
        interactive_locations=args.interactive_locations
    )
            