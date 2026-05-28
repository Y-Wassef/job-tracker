import re
import requests
import time
from bs4 import BeautifulSoup
from parsers.base import BaseParser


class CernParser(BaseParser):
    """Parser for CERN careers HTML job board (careers.cern/jobs)."""

    def __init__(self, company):
        self.company = company
        self.company_name = company.get('name', 'CERN')
        self.base_url = 'https://careers.cern'
        self.listing_url = f'{self.base_url}/jobs/'

    def fetch_jobs(self):
        """Fetch jobs from CERN listing page and detail pages."""
        jobs = []

        try:
            listing_html = self._fetch_page(self.listing_url)
            soup = BeautifulSoup(listing_html, 'html.parser')

            # Find all job links (a.job-offer-teaser)
            job_links = soup.find_all('a', class_='job-offer-teaser')

            for link in job_links:
                try:
                    detail_url = link.get('href', '')
                    if not detail_url:
                        continue

                    # Extract title from h3
                    title_elem = link.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else 'N/A'

                    # Fetch description and location from detail page
                    location, description = self._fetch_detail(detail_url)

                    jobs.append({
                        'company': self.company_name,
                        'title': title,
                        'location': location,
                        'url': detail_url,
                        'description': description,
                        'parser': 'cern'
                    })

                    # Small delay to avoid rate limiting
                    time.sleep(0.3)

                except Exception as e:
                    print(f"Error parsing CERN job link: {e}")
                    continue

        except Exception as e:
            print(f"Error fetching CERN jobs: {e}")

        return jobs

    def _fetch_page(self, url):
        """Fetch HTML page with timeout."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_detail(self, url):
        """Fetch and extract location and description from detail page."""
        location = 'N/A'
        description = ''

        try:
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')

            # Try to find location - common locations in job detail pages
            # Look for text containing location indicators
            location_patterns = [
                soup.find('div', class_='location'),
                soup.find('div', class_='job-location'),
                soup.find('span', class_='location'),
                soup.find('p', string=re.compile(r'location|workplace|site', re.I))
            ]

            for loc_elem in location_patterns:
                if loc_elem:
                    location = loc_elem.get_text(strip=True)
                    if location and location != 'N/A':
                        break

            # Extract description - look for main content areas
            # Try multiple common selectors
            desc_selectors = [
                soup.find('div', class_='entry-content'),
                soup.find('div', class_='job-description'),
                soup.find('article'),
                soup.find('main')
            ]

            for desc_elem in desc_selectors:
                if desc_elem:
                    description = desc_elem.get_text(separator=' ', strip=True)
                    if description:
                        # Clean up whitespace
                        description = re.sub(r'\s+', ' ', description)
                        break

        except Exception as e:
            print(f"Error fetching CERN detail from {url}: {e}")

        return location, description
