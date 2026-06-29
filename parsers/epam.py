import requests
import logging

from parsers.base import BaseParser
from core.utils.html import clean_html_text

logger = logging.getLogger(__name__)


class EpamParser(BaseParser):
    """Parser for EPAM Systems jobs API."""

    API_URL = "https://careers.epam.com/api/jobs/v2/search/careers-i18n"

    def __init__(self, company):
        self.company = company
        self.company_name = company.get("name", "EPAM")

    def fetch_jobs(self) -> list[dict]:
        jobs = []

        try:
            jobs_data = self._fetch_data()

            for job in jobs_data:
                try:
                    jobs.append(self._normalize_job(job))
                except Exception as e:
                    logger.error(f"Error parsing EPAM job '{job.get('name', 'Unknown')}': {e}")

        except Exception as e:
            logger.error(f"Error fetching EPAM jobs: {e}")

        return jobs

    def _fetch_data(self) -> list[dict]:
        all_jobs = []
        offset = 0
        size = 100

        headers = {
            "x-anywhere-tenant": "anywhere"
        }

        while True:
            params = {
                "facets": "country=4000741400009107797",  # Switzerland
                "from": offset,
                "size": size,
                "lang": "de,fr,en",
                "sortBy": "relevance",
                "websiteLocale": "en-us",
            }

            response = requests.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json().get("data", {})

            batch = data.get("jobs", [])
            total = data.get("total", 0)

            if not batch:
                break

            all_jobs.extend(batch)

            if len(all_jobs) >= total:
                break

            offset += size

        return all_jobs

    def _normalize_job(self, job: dict) -> dict:
        return {
            "company": self.company_name,
            "title": job.get("name", "").strip(),
            "location": self._extract_location(job),
            "url": self._build_url(job),
            "description": clean_html_text(self._extract_description(job)),
            "parser": "epam",
        }

    def _extract_location(self, job: dict) -> str:
        locations = []

        for city in (job.get("city") or []):
            city_name = city.get("name", "").strip()

            if city_name:
                locations.append(city_name)

        return "; ".join(locations)

    def _build_url(self, job: dict) -> str:
        seo = job.get("seo", {})

        path = seo.get("url")

        if path:
            return f"https://careers.epam.com{path}"

        uid = job.get("uid")

        if uid:
            return f"https://careers.epam.com/en/jobs/{uid}"

        return "https://careers.epam.com"

    def _extract_description(self, job: dict) -> str:
        parts = []

        description = job.get("description")
        if description:
            parts.append(description)

        category = job.get("category", {})

        section_names = {
            "responsibilities": "Responsibilities",
            "requirements": "Requirements",
            "nice_to_have": "Nice to Have",
            "technologies": "Technologies",
            "about_the_project": "About the Project",
            "about_the_customer": "About the Customer",
        }

        for key, title in section_names.items():
            values = category.get(key)

            if not values:
                continue

            if isinstance(values, list):
                parts.append(f"\n{title}:")
                parts.extend(values)

            elif isinstance(values, str):
                parts.append(f"\n{title}:")
                parts.append(values)

        return "\n".join(parts).strip()