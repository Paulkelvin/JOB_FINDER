"""
GeoJob-Sentinel Google Dork Module
Uses Serper.dev API to find GIS jobs via Google dorks
"""

import requests
import logging
import re
from typing import List, Dict
from fake_useragent import UserAgent
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class SerperFetcher:
    """Fetches jobs using Serper.dev Google Search API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Serper fetcher
        
        Args:
            api_key: Serper.dev API key
        """
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.ua = UserAgent()
    
    def _get_headers(self) -> dict:
        """Generate headers for Serper API"""
        return {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': self.ua.random
        }
    
    def _extract_workday_job_id(self, url: str) -> str:
        """Extract job ID from Workday URL"""
        try:
            # Workday URLs typically contain job IDs in the path
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            
            # Look for job ID patterns
            for part in reversed(path_parts):
                if part and len(part) > 10:  # Job IDs are usually long
                    return f"workday_{part}"
            
            # Fallback: use the entire URL as hash
            return f"workday_{hash(url)}"
        except Exception as e:
            logger.warning(f"Error extracting job ID from {url}: {e}")
            return f"workday_{hash(url)}"
    
    def search_workday_jobs(self, query: str = None) -> List[Dict]:
        """
        Search for GIS jobs on Workday sites
        
        Args:
            query: Custom search query (optional)
            
        Returns:
            List of job dictionaries
        """
        # Default dork for Workday GIS jobs
        if not query:
            query = 'site:myworkdayjobs.com "GIS Specialist" OR "GIS Analyst" -senior -lead after:2025-01-01'
        
        jobs = []
        
        try:
            logger.info(f"Searching Google via Serper: {query}")
            
            payload = {
                'q': query,
                'num': 100,  # Maximum results
                'gl': 'us',   # Geographic location
                'hl': 'en'    # Language
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Process organic results
            for result in data.get('organic', []):
                title = result.get('title', '')
                url = result.get('link', '')
                snippet = result.get('snippet', '')
                
                # Extract company name from URL or title
                company = self._extract_company_from_workday_url(url)
                
                jobs.append({
                    'job_id': self._extract_workday_job_id(url),
                    'title': title,
                    'company': company,
                    'url': url,
                    'location': self._extract_location(snippet),
                    'source': 'Serper/Google',
                    'snippet': snippet
                })
            
            logger.info(f"Found {len(jobs)} jobs from Serper search")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Serper API: {e}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Serper response: {e}")
        
        return jobs
    
    def _extract_company_from_workday_url(self, url: str) -> str:
        """Extract company name from Workday URL"""
        try:
            # Workday URLs format: https://company.wd1.myworkdayjobs.com/...
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if hostname and 'myworkdayjobs.com' in hostname:
                # Extract subdomain (company name)
                parts = hostname.split('.')
                if len(parts) >= 2:
                    company = parts[0]
                    # Clean up company name
                    return company.replace('-', ' ').title()
            
            return "Unknown Company"
            
        except Exception as e:
            logger.warning(f"Error extracting company from {url}: {e}")
            return "Unknown Company"
    
    def _extract_location(self, text: str) -> str:
        """Try to extract location from snippet text"""
        # Common location patterns
        location_patterns = [
            r'(?:Remote|Hybrid|On-site)',
            r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})',  # City, ST
            r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # City name
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return "Location Not Specified"
    
    def search_custom_dork(self, dork: str) -> List[Dict]:
        """
        Execute a custom Google dork
        
        Args:
            dork: Custom Google dork query
            
        Returns:
            List of job dictionaries
        """
        return self.search_workday_jobs(query=dork)
