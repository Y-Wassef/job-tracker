import re
import requests
import time
import logging
from bs4 import BeautifulSoup
from parsers.base import BaseParser

logger = logging.getLogger(__name__)


class SixGroupParser(BaseParser):
    """Parser for Six-Group HTML job board (jobs.six-group.com)."""

    def __init__(self, company):
        self.company = company
        self.company_name = company.get('name', 'Six-Group')
        self.base_url = 'https://jobs.six-group.com'
        self.listing_url = f'{self.base_url}/search/'

    def fetch_jobs(self):
        """Fetch jobs from Six-Group listing page and detail pages."""
        jobs = []

        try:
            listing_html = self._fetch_page(self.listing_url)
            soup = BeautifulSoup(listing_html, 'html.parser')

            # Find all job rows
            job_rows = soup.find_all('tr', class_='data-row')

            for row in job_rows:
                try:
                    # Extract title and detail URL
                    title_link = row.find('a', class_='jobTitle-link')
                    if not title_link:
                        continue

                    title = title_link.get_text(strip=True)
                    detail_path = title_link.get('href', '')
                    detail_url = f'{self.base_url}{detail_path}' if detail_path else None

                    # Extract location
                    location_span = row.find('span', class_='jobLocation')
                    location = location_span.get_text(strip=True) if location_span else 'N/A'

                    # Fetch description from detail page
                    description = ''
                    if detail_url:
                        description = self._fetch_description(detail_url)

                    jobs.append({
                        'company': self.company_name,
                        'title': title,
                        'location': location,
                        'url': detail_url or self.listing_url,
                        'description': description,
                        'parser': 'sixgroup'
                    })
                except Exception as e:
                    logger.error(f"Error parsing job row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Six-Group jobs: {e}")

        return jobs

    def _fetch_page(self, url):
        """Fetch HTML page with timeout."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_description(self, url):
        """Fetch and extract job description from detail page."""
        try:
            html = self._fetch_page(url)
            time.sleep(0.5)  # Be respectful to the server
            soup = BeautifulSoup(html, 'html.parser')

            # Find description in jobdescription span
            desc_span = soup.find('span', class_='jobdescription')
            if desc_span:
                description = desc_span.get_text(separator=' ', strip=True)
                # Clean up HTML tags and extra whitespace
                description = re.sub(r'\s+', ' ', description)
                return description.strip()
        except Exception as e:
            logger.error(f"Error fetching description from {url}: {e}")

        return ''
