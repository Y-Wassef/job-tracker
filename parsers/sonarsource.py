import re
import requests
import time
import logging
from bs4 import BeautifulSoup
from parsers.base import BaseParser

logger = logging.getLogger(__name__)


class SonarSourceParser(BaseParser):
    """Parser for SonarSource job board (Lever platform - HTML)."""

    def __init__(self, company):
        self.company = company
        self.company_name = company.get('name', 'SonarSource')
        self.base_url = 'https://jobs.lever.co/sonarsource'
        self.listing_url = f'{self.base_url}?location=Geneva'

    def fetch_jobs(self):
        """Fetch jobs from SonarSource Lever page with location filter."""
        jobs = []

        try:
            listing_html = self._fetch_page(self.listing_url)

            # Extract all job URLs from HTML (they're in static links even if minified)
            # Pattern: https://jobs.lever.co/sonarsource/{uuid}
            job_url_pattern = r'https://jobs\.lever\.co/sonarsource/[a-f0-9\-]+'
            job_urls = set(re.findall(job_url_pattern, listing_html))

            for detail_url in job_urls:
                try:
                    # Fetch description and location from detail page
                    location, title, description = self._fetch_detail(detail_url)

                    # Filter: Only keep Geneva/Switzerland jobs
                    if not self._is_location_valid(location):
                        continue

                    jobs.append({
                        'company': self.company_name,
                        'title': title,
                        'location': location,
                        'url': detail_url,
                        'description': description,
                        'parser': 'sonarsource'
                    })

                    # Small delay to avoid rate limiting
                    time.sleep(0.3)

                except Exception as e:
                    logger.error(f"Error parsing SonarSource job {detail_url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching SonarSource jobs: {e}")

        return jobs

    def _fetch_page(self, url):
        """Fetch HTML page with timeout."""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _fetch_detail(self, url):
        """Fetch and extract location, title, and description from detail page."""
        location = 'N/A'
        title = 'N/A'
        description = ''

        try:
            html = self._fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')

            # Extract title from page title or h1
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Remove company name prefix if present (e.g., "Sonar - Job Title" -> "Job Title")
                if ' - ' in title_text:
                    title = title_text.split(' - ', 1)[1]
                else:
                    title = title_text

            # Extract location from meta tags (Lever uses twitter:data1 for location)
            meta_tags = soup.find_all('meta')
            for i, meta in enumerate(meta_tags):
                if meta.get('name') == 'twitter:label1' and meta.get('value', '').lower() == 'location':
                    # Next meta tag should have the location value
                    for next_meta in meta_tags[i:]:
                        if next_meta.get('name') == 'twitter:data1':
                            location = next_meta.get('value', 'N/A')
                            break
                    break

            # Extract description from page content
            posting_content = soup.find('div', class_='posting') or soup.find('main')
            if posting_content:
                description = posting_content.get_text(separator=' ', strip=True)
            else:
                # Fallback: get all text
                description = soup.get_text(separator=' ', strip=True)

            # Clean up description (limit length)
            if description:
                description = re.sub(r'\s+', ' ', description)
                if len(description) > 5000:
                    description = description[:5000]

        except Exception as e:
            logger.error(f"Error fetching SonarSource detail from {url}: {e}")

        return location, title, description

    def _is_location_valid(self, location):
        """Check if location is Geneva or Switzerland."""
        loc_lower = location.lower()
        return any(
            keyword in loc_lower
            for keyword in ['geneva', 'switzerland', 'zurich', 'bern', 'basel', 'lausanne']
        )
