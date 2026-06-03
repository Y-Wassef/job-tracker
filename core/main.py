import yaml
import argparse
import logging

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
    insert_job,
    get_jobs_to_delete,
    delete_jobs
)

from core.notifier import send_notification
from core.filters import is_relevant, matching_keywords, location_filter, score_job
from core.logging_config import setup_logging, get_logger

logger = get_logger("job-tracker")

def load_companies():
    with open('config/companies.yaml', 'r') as f:
        return yaml.safe_load(f)['companies']


def handle_prune(prune_args, execute):
    """Handle pruning operations. prune_args is a list: [company|'all'] or [company|'all', hours]"""
    if len(prune_args) == 1:
        hours = None
    elif len(prune_args) == 2:
        try:
            hours = int(prune_args[1])
        except ValueError:
            logger.error(f"Hours must be an integer, got: {prune_args[1]}")
            return
    else:
        logger.error("--prune requires 1 or 2 arguments: [company|'all'] [hours]")
        return 

    company = prune_args[0].lower()
    
    if not execute:
        jobs_to_delete = get_jobs_to_delete(company, hours)
        if jobs_to_delete:
            logger.info(f"Jobs that would be deleted ({len(jobs_to_delete)}):")
            for job in jobs_to_delete:
                logger.info(f"- {job['company']} | {job['title']} | ID: {job['id']}")
            confirm = input("Would you like to proceed with deletion? Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                logger.info("Aborting prune operation.")
                return
        else:
            logger.info("No jobs would be deleted based on the given criteria.")
            return

    if company == "all" and hours is None:
        confirm = input("You are about to delete ALL jobs from the database. Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Aborting prune operation.")
            return
        else:
            logger.warning("Executing full prune of ALL jobs from ALL companies.")
    else:
        logger.info(f"Executing prune operation for company='{company}' with hours='{hours}'")
    
    count = delete_jobs(company, hours)
    logger.info(f"Deleted {count} jobs from database.")


    
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
    parser.add_argument(
        "--score-threshold",
        type=int,
        default=0,
        help="Minimum job score to insert into database (default: 0 - no filtering). Recommended: 25"
    )
    parser.add_argument(
        "--show-url",
        action="store_true",
        help="Show job URL in logs (for debugging, not recommended for regular use)."
    )
    parser.add_argument(
        "--prune",
        nargs="+",
        help="Usage: --prune <company|all> [hours]. Delete old jobs for a specific company or all companies, optionally filtered by past X hours."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform the deletion without prompting for confirmation (use with caution, especially with --prune all)."
    )

    return parser.parse_args()


def validate_args(args):
    if args.prune:
       # no other arguments should be used with --prune except --execute
        if any([args.dry_run, args.respect_db, args.companies,
                args.interactive_locations, args.score_threshold > 0, args.show_url]):
            logger.error("--prune cannot be used with other arguments except --execute.")
            exit(1)



def main(dry_run=False, respect_db=False, selected_companies=None, interactive_locations=False, score_threshold=0, show_url=False, prune=None, execute=False):

    setup_logging()
    init_db()

    if prune:
        handle_prune(prune, execute)
        return

    companies = load_companies()

    if selected_companies:
        companies = [c for c in companies if c["name"].lower() in [name.lower() for name in selected_companies]]
        if not companies:
            logger.warning("No matching companies found for the specified names.")
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
            logger.warning(f"Unknown parser type '{parser_type}' for company {company['name']}. Skipping.")
            continue
        parser = parser_class(company)

        jobs = parser.fetch_jobs()

        for job in jobs:

            if not is_relevant(job):
                continue

            approved_locs = location_filter(job, interactive=interactive_locations)
            if not approved_locs:
                continue

            score = score_job(job)
            if score_threshold > 0 and score < score_threshold:
                logger.debug(f"Job filtered by score threshold ({score} < {score_threshold}): {job['title']}")
                continue

            exists = job_exists(job["url"])

            if dry_run:

                if respect_db and exists:
                    continue

                prefix = "[SEEN]" if exists else "[NEW]"
                url_part = f"URL: {job['url']} | " if show_url else ""
                logger.info(
                    f"{prefix} "
                    f"{job['company']} | "
                    f"{job['title']} | "
                    f"{job['location']} | "
                    f"Score: {score} | "
                    f"{url_part}"
                    f"Parser: {parser_type} | "
                    f"Keywords: {', '.join(matching_keywords(job['title']))}"
                )
                logger.debug(f"Full URL: {job['url']}")
                logger.debug(f"Full job: {job}")

                new_jobs.append((job, score))

            else:

                if exists:
                    continue

                insert_job(job)
                new_jobs.append((job, score))

    # if new_jobs:
    #     if not dry_run:
    #         lines = ["<b>New Job Postings:</b>\n"]
    #         for job, score in new_jobs:
    #             lines.append(f"<b>{job['company']}</b>: <a href='{job['url']}'>{job['title']}</a> - {job['location']} (Score: {score})")

    #         message = "\n\n".join(lines)
    #         send_notification(message)
    #         logger.info(f"Sent notification for {len(new_jobs)} new jobs.")
    #     else:
    #         logger.info(f"[DRY] Found {len(new_jobs)} new jobs.")
    # else:
    #     logger.info("No new jobs found.")


if __name__ == "__main__":
    args = get_args()
    validate_args(args)

    main(
        dry_run=args.dry_run,
        respect_db=args.respect_db,
        selected_companies=args.companies,
        interactive_locations=args.interactive_locations,
        score_threshold=args.score_threshold,
        show_url=args.show_url,
        prune=args.prune,
        execute=args.execute
    )
            