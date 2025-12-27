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
                "q": query,
                "num": 100,
                "gl": "us",
                "hl": "en"
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
                
                # Get freshness and competition data
                freshness_data = self._estimate_freshness(url, snippet)
                
                jobs.append({
                    'job_id': self._extract_workday_job_id(url),
                    'title': title,
                    'company': company,
                    'url': url,
                    'location': self._extract_location(snippet),
                    'source': 'Serper/Google',
                    'snippet': snippet,
                    'category': self._categorize_job(title, snippet),
                    'freshness': freshness_data['freshness'],
                    'priority': freshness_data['priority'],
                    'competition': self._estimate_competition(url, snippet)
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
    
    def _categorize_job(self, title: str, snippet: str) -> str:
        """Categorize job by niche area"""
        text = (title + ' ' + snippet).lower()
        
        # Categorization keywords
        if any(kw in text for kw in ['remote sensing', 'satellite', 'imagery', 'aerial', 'drone']):
            return '🛰️ Remote Sensing'
        elif any(kw in text for kw in ['web', 'mapping', 'javascript', 'leaflet', 'mapbox']):
            return '🗺️ Web Mapping'
        elif any(kw in text for kw in ['government', 'federal', 'state', 'municipal', 'county']):
            return '🏛️ Government'
        elif any(kw in text for kw in ['environmental', 'conservation', 'wildlife', 'ecology']):
            return '🌲 Environmental'
        elif any(kw in text for kw in ['engineering', 'civil', 'infrastructure', 'transportation']):
            return '🏗️ Engineering'
        elif any(kw in text for kw in ['agriculture', 'farming', 'precision ag', 'crop']):
            return '🌾 Agriculture'
        elif any(kw in text for kw in ['research', 'university', 'academic', 'science']):
            return '🎓 Research'
        else:
            return '📊 General GIS'
    
    def _estimate_freshness(self, url: str, snippet: str) -> dict:
        """Estimate how fresh/recent the job posting is"""
        text = snippet.lower()
        
        # Look for time indicators in snippet
        if any(word in text for word in ['today', 'just posted', 'new']):
            return {'freshness': '🔥 Very Fresh', 'hours': 24, 'priority': 'HIGH'}
        elif any(word in text for word in ['yesterday', '1 day']):
            return {'freshness': '🟢 Fresh', 'hours': 48, 'priority': 'HIGH'}
        elif any(word in text for word in ['2 days', '3 days', 'this week']):
            return {'freshness': '🟡 Recent', 'hours': 168, 'priority': 'MEDIUM'}
        else:
            return {'freshness': '🔵 Standard', 'hours': 720, 'priority': 'NORMAL'}
    
    def _estimate_competition(self, url: str, snippet: str) -> str:
        """Estimate competition level based on source"""
        url_lower = url.lower()
        
        # Government/edu/non-profit = low competition
        if any(domain in url_lower for domain in ['governmentjobs.com', 'usajobs.gov', '.edu', 'idealist.org']):
            return '🟢 Low Competition (~10-30 applicants)'
        
        # Reddit/HN = very low competition
        elif any(domain in url_lower for domain in ['reddit.com', 'news.ycombinator.com']):
            return '🟢 Very Low (~5-15 applicants)'
        
        # Greenhouse/Lever = medium competition
        elif any(domain in url_lower for domain in ['greenhouse.io', 'lever.co']):
            return '🟡 Medium (~50-100 applicants)'
        
        # LinkedIn = high competition
        elif 'linkedin.com' in url_lower:
            return '🟠 Higher (~100-300 applicants)'
        
        # Workday = medium-high
        elif 'myworkdayjobs.com' in url_lower:
            return '🟡 Medium-High (~75-150 applicants)'
        
        else:
            return '🔵 Unknown'
    
    def search_custom_dork(self, dork: str) -> List[Dict]:
        """
        Execute a custom Google dork
        
        Args:
            dork: Custom Google dork query
            
        Returns:
            List of job dictionaries
        """
        return self.search_workday_jobs(query=dork)
    
    def discover_greenhouse_companies(self) -> List[Dict]:
        """
        Discovery Mode: Find NEW companies on Greenhouse that aren't in your config
        Searches the entire Greenhouse platform for GIS jobs
        
        Returns:
            List of job dictionaries from discovered companies
        """
        query = 'site:boards.greenhouse.io "GIS Specialist" OR "GIS Analyst" OR "Geospatial" after:2025-01-01'
        
        jobs = []
        
        try:
            logger.info(f"🔍 DISCOVERY MODE: Searching ALL Greenhouse companies...")
            
            payload = {
                'q': query,
                'num': 100,
                'gl': 'us',
                'hl': 'en'
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            for result in data.get('organic', []):
                title = result.get('title', '')
                url = result.get('link', '')
                snippet = result.get('snippet', '')
                
                # Extract company from Greenhouse URL
                company = self._extract_company_from_greenhouse_url(url)
                
                if company:
                    freshness_data = self._estimate_freshness(url, snippet)
                    
                    jobs.append({
                        'job_id': f"discovered_greenhouse_{hash(url)}",
                        'title': title,
                        'company': company,
                        'url': url,
                        'location': self._extract_location(snippet),
                        'source': 'Discovery/Greenhouse',
                        'snippet': snippet,
                        'category': self._categorize_job(title, snippet),
                        'freshness': freshness_data['freshness'],
                        'priority': freshness_data['priority'],
                        'competition': self._estimate_competition(url, snippet)
                    })
            
            logger.info(f"🎯 Discovered {len(jobs)} jobs from NEW Greenhouse companies")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Greenhouse discovery: {e}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Greenhouse discovery response: {e}")
        
        return jobs
    
    def discover_lever_companies(self) -> List[Dict]:
        """
        Discovery Mode: Find NEW companies on Lever that aren't in your config
        Searches the entire Lever platform for GIS jobs
        
        Returns:
            List of job dictionaries from discovered companies
        """
        query = 'site:jobs.lever.co "GIS" OR "Geospatial" OR "Spatial Analyst" after:2025-01-01'
        
        jobs = []
        
        try:
            logger.info(f"🔍 DISCOVERY MODE: Searching ALL Lever companies...")
            
            payload = {
                'q': query,
                'num': 100,
                'gl': 'us',
                'hl': 'en'
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            for result in data.get('organic', []):
                title = result.get('title', '')
                url = result.get('link', '')
                snippet = result.get('snippet', '')
                
                # Extract company from Lever URL
                company = self._extract_company_from_lever_url(url)
                
                if company:
                    freshness_data = self._estimate_freshness(url, snippet)
                    
                    jobs.append({
                        'job_id': f"discovered_lever_{hash(url)}",
                        'title': title,
                        'company': company,
                        'url': url,
                        'location': self._extract_location(snippet),
                        'source': 'Discovery/Lever',
                        'snippet': snippet,
                        'category': self._categorize_job(title, snippet),
                        'freshness': freshness_data['freshness'],
                        'priority': freshness_data['priority'],
                        'competition': self._estimate_competition(url, snippet)
                    })
            
            logger.info(f"🎯 Discovered {len(jobs)} jobs from NEW Lever companies")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Lever discovery: {e}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing Lever discovery response: {e}")
        
        return jobs
    
    def _extract_company_from_greenhouse_url(self, url: str) -> str:
        """
        Extract company name from Greenhouse URL
        Example: https://boards.greenhouse.io/esri/jobs/123 → Esri
        """
        try:
            import re
            # Match pattern: boards.greenhouse.io/COMPANY_NAME/
            match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
            if match:
                company_slug = match.group(1)
                # Clean up slug to readable name
                return company_slug.replace('-', ' ').title()
            return "Unknown Company"
        except Exception as e:
            logger.warning(f"Error extracting company from Greenhouse URL {url}: {e}")
            return "Unknown Company"
    
    def _extract_company_from_lever_url(self, url: str) -> str:
        """
        Extract company name from Lever URL
        Example: https://jobs.lever.co/mapbox/123 → Mapbox
        """
        try:
            import re
            # Match pattern: jobs.lever.co/COMPANY_NAME/
            match = re.search(r'jobs\.lever\.co/([^/]+)', url)
            if match:
                company_slug = match.group(1)
                # Clean up slug to readable name
                return company_slug.replace('-', ' ').title()
            return "Unknown Company"
        except Exception as e:
            logger.warning(f"Error extracting company from Lever URL {url}: {e}")
            return "Unknown Company"
