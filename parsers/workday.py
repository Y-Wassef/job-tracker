import requests
import re
import time
import logging
from urllib.parse import urlparse
from parsers.base import BaseParser
from core.utils.html import clean_html_text

logger = logging.getLogger(__name__)

class WorkdayParser(BaseParser):

    def __init__(self, company: dict):

        self.company = company["name"]
        self.careers_url = company["url"]

        self.base_url, self.tenant, self.site, self.path_segment = self._derive_workday_params(self.careers_url)
        self.endpoint = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/jobs"
        self.detail_endpoint_template = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/job"

    def fetch_jobs(self) -> list[dict]:

        jobs = []

        data = self._fetch_data()

        for job in data.get("jobPostings", []):
            normalized = self._normalize_job(job)
            if normalized:
                jobs.append(normalized)
        return jobs


    def _fetch_data(self):

        try:
            all_jobs = []
            offset = 0
            limit = 20
            total = None

            while True:
                payload = {
                    "appliedFacets": {},
                    "limit": limit,
                    "offset": offset,
                    "searchText": ""
                }
                response = requests.post(self.endpoint, timeout=15, json=payload)
                response.raise_for_status()
                data = response.json()

                batch = data.get("jobPostings", [])

                # Capture total from first response only
                if total is None:
                    total = data.get("total", 0)

                if not batch:
                    break

                all_jobs.extend(batch)

                if len(all_jobs) >= total:
                    break

                offset += limit

            return {"jobPostings": all_jobs}
        except requests.RequestException as e:
            logger.error(f"[Workday] Failed to fetch data for {self.company}: {e}")
            return {"jobPostings": []}

    def _normalize_job(self, job) -> dict:

        try:
            # Extract job ID from externalPath: /job/Zurich/SAP-IS-H-Consultant_R-0003595
            external_path = job.get('externalPath', '')
            job_posting_id = external_path.split('/')[-1] if external_path else ''

            # Fetch full details (location + description) from detail endpoint
            location, description = self._fetch_job_details(job_posting_id) if job_posting_id else ("", "")

            return {
                "company": self.company,
                "title": job.get("title", "").strip(),
                "url": self._build_job_url(job),
                "location": location,
                "description": description,
                "parser": "workday"
            }
        except KeyError as e:
            logger.warning(f"[Workday] Missing expected field {e} in job data for {self.company}")
            return None

    def _build_job_url(self, job: dict) -> str:
        """
        Workday uses relative paths like:
        /job/Zurich/..._R-000123
        """
        return f"{self.base_url}/{self.path_segment}{job.get('externalPath', '')}"

    def _fetch_job_details(self, job_posting_id: str) -> tuple[str, str]:
        """
        Fetch job detail endpoint to get location and description.
        Returns (location_string, description_string).
        location_string: semicolon-separated (primary; additional1; additional2)
        description_string: HTML cleaned plain text
        """
        try:
            detail_url = f"{self.detail_endpoint_template}/{job_posting_id}"
            response = requests.get(detail_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            job_info = data.get("jobPostingInfo", {})

            # Extract location + additionalLocations
            location = job_info.get("location", "").strip()
            additional = job_info.get("additionalLocations", [])
            locations = [location] if location else []
            locations.extend([loc.strip() for loc in additional if loc.strip()])
            location_str = "; ".join(locations) if locations else ""

            # Extract and clean description
            description_html = job_info.get("jobDescription", "")
            description = clean_html_text(description_html)

            # Small delay to avoid rate limiting
            time.sleep(0.1)

            return location_str, description

        except Exception as e:
            logger.error(f"[Workday] Failed to fetch details for {job_posting_id}: {e}")
            return "", ""


    def _derive_workday_params(self, url: str) -> tuple[str, str, str, str]:

        parsed = urlparse(url)

        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Extract the path segment (e.g., "en-US/SwisscomExternalCareers")
        path_segment = parsed.path.strip("/") if parsed.path else ""

        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) < 2:
            raise ValueError(f"Unexpected Workday URL format: {url}")

        site = path_parts[-1]
        tenant = parsed.netloc.split(".")[0]  # e.g. swisscom

        return base_url, tenant, site, path_segment
        