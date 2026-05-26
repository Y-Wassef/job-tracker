import requests
from urllib.parse import urlparse
from parsers.base import BaseParser

class WorkdayParser(BaseParser):

    def __init__(self, company: dict):

        self.company = company["name"]
        self.careers_url = company["url"]

        self.base_url, self.tenant, self.site = self._derive_workday_params(self.careers_url)
        self.endpoint = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}/jobs"

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
            print(f"[Workday] Failed to fetch data for {self.company}: {e}")
            return {"jobPostings": []}

    def _normalize_job(self, job) -> dict:

        try:
            return {
                "company": self.company,
                "title": job.get("title", "").strip(),
                "url": self._build_job_url(job),
                "location": job.get("locationsText", ""),
                "description": "",
                "parser": "workday"
            }
        except KeyError as e:
            print(f"[Workday] Missing expected field {e} in job data for {self.company}")
            return None

    def _build_job_url(self, job: dict) -> str:
        """
        Workday uses relative paths like:
        /job/Zurich/..._R-000123
        """
        return f"{self.base_url}{job.get('externalPath', '')}"

    def _derive_workday_params(self, url: str) -> tuple[str, str, str]:
        
        parsed = urlparse(url)

        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # path example: /en-US/SwisscomExtenalCareers

        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) < 2:
            raise ValueError(f"Unexpected Workday URL format: {url}")

        site = path_parts[-1]
        tenant = parsed.netloc.split(".")[0]  # e.g. swisscom

        return base_url, tenant, site
        