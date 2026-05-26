import requests

from parsers.base import BaseParser

class GreenhouseParser(BaseParser):

    def __init__(self, company_name, board_token):
        self.company_name = company_name
        self.board_token = board_token

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
                'description': job.get('content', '')
            })
        
        return jobs
