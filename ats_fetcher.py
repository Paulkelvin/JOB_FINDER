"""
GeoJob-Sentinel ATS (Applicant Tracking System) Module
Handles Greenhouse and Lever job board API scraping
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class ATSFetcher:
    """Fetches jobs from Greenhouse and Lever APIs"""
    
    def __init__(self, company_slugs: List[str]):
        """
        Initialize ATS fetcher
        
        Args:
            company_slugs: List of company slugs to query
        """
        self.company_slugs = company_slugs
        self.ua = UserAgent()
        self.session = requests.Session()
        
    def _get_headers(self) -> dict:
        """Generate random headers for stealth"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def _random_sleep(self, min_sec: int = 10, max_sec: int = 30):
        """Implement exponential backoff with randomization"""
        sleep_time = random.uniform(min_sec, max_sec)
        logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    def fetch_greenhouse_jobs(self, slug: str) -> List[Dict]:
        """
        Fetch jobs from Greenhouse API
        
        Args:
            slug: Company slug (e.g., 'company-name')
            
        Returns:
            List of job dictionaries
        """
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        jobs = []
        
        try:
            logger.info(f"Fetching Greenhouse jobs for: {slug}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Greenhouse returns jobs directly or in a 'jobs' key
            job_list = data.get('jobs', data) if isinstance(data, dict) else data
            
            for job in job_list:
                jobs.append({
                    'job_id': f"greenhouse_{slug}_{job.get('id')}",
                    'title': job.get('title', ''),
                    'company': slug.replace('-', ' ').title(),
                    'url': job.get('absolute_url', ''),
                    'location': job.get('location', {}).get('name', 'Remote'),
                    'source': 'Greenhouse',
                    'raw_data': job
                })
            
            logger.info(f"Found {len(jobs)} jobs from Greenhouse ({slug})")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Greenhouse jobs for {slug}: {e}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Greenhouse response for {slug}: {e}")
        
        return jobs
    
    def fetch_lever_jobs(self, slug: str) -> List[Dict]:
        """
        Fetch jobs from Lever API
        
        Args:
            slug: Company slug (e.g., 'company-name')
            
        Returns:
            List of job dictionaries
        """
        url = f"https://api.lever.co/v0/postings/{slug}"
        jobs = []
        
        try:
            logger.info(f"Fetching Lever jobs for: {slug}")
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=30,
                params={'mode': 'json'}
            )
            response.raise_for_status()
            
            job_list = response.json()
            
            for job in job_list:
                jobs.append({
                    'job_id': f"lever_{slug}_{job.get('id')}",
                    'title': job.get('text', ''),
                    'company': slug.replace('-', ' ').title(),
                    'url': job.get('hostedUrl', ''),
                    'location': job.get('categories', {}).get('location', 'Remote'),
                    'source': 'Lever',
                    'raw_data': job
                })
            
            logger.info(f"Found {len(jobs)} jobs from Lever ({slug})")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Lever jobs for {slug}: {e}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Lever response for {slug}: {e}")
        
        return jobs
    
    def fetch_all_jobs(self) -> List[Dict]:
        """
        Fetch jobs from all configured companies
        
        Returns:
            Combined list of all jobs
        """
        all_jobs = []
        
        for slug in self.company_slugs:
            # Try Greenhouse first
            greenhouse_jobs = self.fetch_greenhouse_jobs(slug)
            all_jobs.extend(greenhouse_jobs)
            
            self._random_sleep()
            
            # If Greenhouse returns nothing, try Lever
            if not greenhouse_jobs:
                lever_jobs = self.fetch_lever_jobs(slug)
                all_jobs.extend(lever_jobs)
                self._random_sleep()
        
        logger.info(f"Total jobs fetched from ATS: {len(all_jobs)}")
        return all_jobs
