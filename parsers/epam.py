import re
import json
import requests
import logging
from parsers.base import BaseParser

logger = logging.getLogger(__name__)


class EpamParser(BaseParser):
    """Parser for EPAM Systems job board (JSON API - Next.js)."""

    def __init__(self, company):
        self.company = company
        self.company_name = company.get('name', 'EPAM')
        self.api_url = 'https://careers.epam.com/_next/data/RJVBhPXDErufhnQ9bJk4z/en/jobs/switzerland.json'

    def fetch_jobs(self):
        """Fetch jobs from EPAM Switzerland endpoint."""
        jobs = []

        try:
            # Use a larger limit to get all jobs in one request
            response = requests.get(
                self.api_url,
                params={'sort_by': 'relevance', 'slug': 'switzerland'},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            jobs_data = data.get('pageProps', {}).get('jobs', {})
            job_list = jobs_data.get('jobs', [])

            for job in job_list:
                try:
                    title = job.get('name', 'N/A')
                    location = self._extract_location(job)

                    # Filter: Only Switzerland jobs
                    if not self._is_switzerland_job(job):
                        continue

                    description = self._extract_description(job.get('description', ''))

                    # Build job URL
                    uid = job.get('uid', '')
                    job_url = f"https://careers.epam.com/en/jobs/{uid}" if uid else "https://careers.epam.com/en/jobs/"

                    jobs.append({
                        'company': self.company_name,
                        'title': title,
                        'location': location,
                        'url': job_url,
                        'description': description,
                        'parser': 'epam'
                    })
                except Exception as e:
                    logger.error(f"Error parsing EPAM job: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching EPAM jobs: {e}")

        return jobs

    def _extract_location(self, job):
        """Extract location from job city and country."""
        cities = job.get('city', [])
        if cities:
            city_info = cities[0]
            city_name = city_info.get('name', '')
            state = city_info.get('state', {})
            state_name = state.get('name', '') if isinstance(state, dict) else ''

            parts = [city_name]
            if state_name:
                parts.append(state_name)

            return ', '.join(parts) if parts else 'Switzerland'

        return 'Switzerland'

    def _is_switzerland_job(self, job):
        """Check if job is in Switzerland."""
        cities = job.get('city', [])
        if cities:
            city_info = cities[0]
            country = city_info.get('country', {})
            country_name = country.get('name', '') if isinstance(country, dict) else ''
            return 'switzerland' in country_name.lower()
        return False

    def _extract_description(self, description_html):
        """Extract and clean description from HTML."""
        if not description_html:
            return ''

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', description_html)
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
