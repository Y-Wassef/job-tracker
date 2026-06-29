import requests
import html
import re

from parsers.base import BaseParser
from core.utils.html import clean_html_text

class GreenhouseParser(BaseParser):

    def __init__(self, company):
        self.company_name = company.get('name')
        self.board_token = company.get('board_token')

    def fetch_jobs(self):
        url = f'https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true'

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        jobs = []

        for job in data.get('jobs', []):
            jobs.append({
                'company': self.company_name,
                'title': job.get('title'),
                'location': job.get('location', {}).get('name'),
                'url': job.get('absolute_url'),
                'description': clean_html_text(job.get('content', '')),
                'parser': 'greenhouse'
            })

        return jobs
