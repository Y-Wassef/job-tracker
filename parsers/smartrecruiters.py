import logging
import requests

from parsers.base import BaseParser
from core.utils.html import clean_html_text

logger = logging.getLogger(__name__)


class SmartRecruitersParser(BaseParser):

    BASE_URL = "https://api.smartrecruiters.com/v1"

    def __init__(self, company: dict):

        self.company = company
        self.company_name = company["name"]
        self.company_id = company["company_id"]

    def fetch_jobs(self) -> list[dict]:

        jobs = []

        try:
            postings = self._fetch_postings()

            for posting in postings:

                try:
                    details = self._fetch_details(posting["id"])

                    normalized = self._normalize_job(details)

                    if normalized:
                        jobs.append(normalized)

                except Exception as e:
                    logger.error(
                        f"[SmartRecruiters] Failed parsing job "
                        f"{posting.get('id')}: {e}"
                    )

        except Exception as e:
            logger.error(
                f"[SmartRecruiters] Failed fetching jobs for "
                f"{self.company_name}: {e}"
            )

        return jobs

    def _fetch_postings(self) -> list:

        jobs = []
        offset = 0
        limit = 100

        while True:

            response = requests.get(
                f"{self.BASE_URL}/companies/{self.company_id}/postings",
                params={
                    "offset": offset,
                    "limit": limit
                },
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            batch = data.get("content", [])

            if not batch:
                break

            jobs.extend(batch)

            if len(batch) < limit:
                break

            offset += limit

        return jobs

    def _fetch_details(self, posting_id: str) -> dict:

        response = requests.get(
            f"{self.BASE_URL}/companies/{self.company_id}/postings/{posting_id}",
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    def _normalize_job(self, posting: dict) -> dict:

        title = posting.get("name", "").strip()

        location = (
            posting.get("location", {})
                   .get("fullLocation", "")
        )

        url = posting.get("postingUrl", "")

        description = self._extract_description(posting)

        return {
            "company": self.company_name,
            "title": title,
            "location": location,
            "url": url,
            "description": description,
            "parser": "smartrecruiters"
        }

    def _extract_description(self, posting: dict) -> str:

        sections = (
            posting.get("jobAd", {})
                   .get("sections", {})
        )

        parts = []

        for section in sections.values():

            if not isinstance(section, dict):
                continue

            text = section.get("text")

            if text:
                parts.append(text)

        return clean_html_text("\n\n".join(parts))