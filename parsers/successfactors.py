import requests
from parsers.base import BaseParser
import re

class SuccessFactorsParser(BaseParser):
    """
    Parser for SuccessFactors-based job boards (PostFinance, SwissPost, etc).

    Configure filters in companies.yaml:
      - filter_brand: Brand name to filter by (e.g., "PostFinance")
      - filter_appTemplateId: Template ID to filter by (e.g., "25")
      - filter_division: Division name to filter by (optional)

    The parser automatically deduplicates by base jobId (removes language suffixes).
    """

    def __init__(self, company):
        self.company = company
        self.company_name = company.get('name', 'PostFinance')
        self.api_url = company.get('api_url', 'https://production.api.recruiting-solutions.org/search')
        self.customer_id = company.get('customer_id', 'sp-prod')

    def fetch_jobs(self):
        """Fetch jobs from SuccessFactors API."""
        headers = {
            'customerid': self.customer_id,
        }

        payload = {
            'count': True,
            'facets': [],
            'filter': '',
            'search': '*',
            'skip': 0,
            'top': 2000
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        all_jobs = data.get('value', [])

        # Filter jobs based on UI selection logic
        filtered_jobs = self._filter_jobs(all_jobs)

        # Normalize to standard schema
        jobs = []
        for job in filtered_jobs:
            jobs.append({
                'company': self.company_name,
                'title': job.get('title'),
                'location': self._extract_location(job),
                'url': job.get('link') or job.get('privateExternalLink', '').replace('{brand}', job.get('brand', '')).replace('{jobId}', job.get('jobId', '')).replace('{locale}', job.get('language', 'en_US')),
                'description': self._extract_description(job),
                'parser': 'successfactors'
            })

        return jobs

    def _filter_jobs(self, jobs):
        """
        Apply filtering logic based on configuration.
        Default: brand and appTemplateId filters.
        """
        # Get filter criteria from company config
        filter_brand = self.company.get('filter_brand')
        filter_template_id = self.company.get('filter_appTemplateId')
        filter_division = self.company.get('filter_division')

        # If no filters configured, return all jobs
        if not any([filter_brand, filter_template_id, filter_division]):
            return jobs

        # Apply filters
        filtered = jobs
        if filter_brand:
            filtered = [j for j in filtered if j.get('brand') == filter_brand]
        if filter_template_id:
            filtered = [j for j in filtered if j.get('appTemplateId') == filter_template_id]
        if filter_division:
            filtered = [j for j in filtered if j.get('division') == filter_division]

        # Deduplicate by base jobId (remove language suffix)
        seen_ids = set()
        deduplicated = []
        for job in filtered:
            base_id = job.get('jobId', '').split('-')[0]
            if base_id and base_id not in seen_ids:
                seen_ids.add(base_id)
                deduplicated.append(job)

        return deduplicated

    def _extract_location(self, job):
        """Extract primary location from job addresses."""
        addresses = job.get('addresses', [])
        if addresses:
            primary = next((a for a in addresses if a.get('isPrimary')), addresses[0])
            parts = []
            if primary.get('city'):
                parts.append(primary['city'])
            if primary.get('state'):
                parts.append(primary['state'])
            return ', '.join(parts) if parts else 'N/A'
        return 'N/A'

    def _extract_description(self, job):
        """Extract description from job, fallback to alternative fields."""
        description = job.get('description', '')

        # Fallback to other fields if description is empty or deprecated
        if not description:
            return f"{job.get('jobType', '')} - {job.get('category', '')}".strip(' -')
       
        # cleaning up html tags if present (basic)
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', description)
        return cleantext.strip()
