"""
GeoJob-Sentinel Job Filtering Module
Implements keyword guard and negative filtering for job titles
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class JobFilter:
    """Filters jobs based on title keywords and seniority level"""
    
    # Required keywords - at least one must be present
    REQUIRED_KEYWORDS = [
        'gis',
        'geospatial',
        'spatial',
        'mapping'
    ]
    
    # Negative keywords - any of these disqualifies the job
    NEGATIVE_KEYWORDS = [
        'senior',
        'sr.',
        'sr ',
        'iii',
        'iv',
        'lead',
        'manager',
        'director',
        'principal',
        'chief',
        'head of',
        'vp',
        'vice president',
        'executive',
        'architect',  # Usually senior role
        # Sales/marketing roles (non-technical, lower quality for GIS professionals)
        'sales',
        'account executive',
        'account manager',
        'business development',
        'marketing',
        'solutions specialist',
        'customer success',
        # Field/manual labor roles
        'field technician',
        'surveyor',
        'field crew',
        'field data collector',
        'field services'
        # REMOVED: intern, internship, co-op, temporary, contract, freelance
        # User wants contract/freelance opportunities!
    ]
    
    def __init__(self, custom_required: List[str] = None, custom_negative: List[str] = None):
        """
        Initialize filter with optional custom keywords
        
        Args:
            custom_required: Additional required keywords
            custom_negative: Additional negative keywords
        """
        self.required_keywords = self.REQUIRED_KEYWORDS.copy()
        self.negative_keywords = self.NEGATIVE_KEYWORDS.copy()
        
        if custom_required:
            self.required_keywords.extend([kw.lower() for kw in custom_required])
        
        if custom_negative:
            self.negative_keywords.extend([kw.lower() for kw in custom_negative])
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        return text.lower().strip()
    
    def has_required_keyword(self, title: str) -> bool:
        """
        Check if title contains at least one required keyword
        
        Args:
            title: Job title
            
        Returns:
            True if contains required keyword, False otherwise
        """
        normalized_title = self._normalize_text(title)
        
        for keyword in self.required_keywords:
            # Use word boundary regex to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized_title):
                logger.debug(f"Found required keyword '{keyword}' in: {title}")
                return True
        
        logger.debug(f"No required keyword found in: {title}")
        return False
    
    def has_negative_keyword(self, title: str) -> bool:
        """
        Check if title contains any negative keyword
        
        Args:
            title: Job title
            
        Returns:
            True if contains negative keyword, False otherwise
        """
        normalized_title = self._normalize_text(title)
        
        for keyword in self.negative_keywords:
            # Use word boundary regex for most keywords
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized_title):
                logger.debug(f"Found negative keyword '{keyword}' in: {title}")
                return True
        
        return False
    
    def is_valid_job(self, job: Dict) -> bool:
        """
        Validate a job against all filter criteria
        
        Args:
            job: Job dictionary with at least a 'title' key
            
        Returns:
            True if job passes all filters, False otherwise
        """
        title = job.get('title', '')
        
        if not title:
            logger.debug("Job has no title, filtering out")
            return False
        
        # Must have at least one required keyword
        if not self.has_required_keyword(title):
            logger.debug(f"Filtered out (no required keyword): {title}")
            return False
        
        # Must not have any negative keywords
        if self.has_negative_keyword(title):
            logger.debug(f"Filtered out (has negative keyword): {title}")
            return False
        
        logger.info(f"✓ Job passed filters: {title}")
        return True
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter a list of jobs
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Filtered list of jobs
        """
        filtered = [job for job in jobs if self.is_valid_job(job)]
        
        logger.info(f"Filtered {len(jobs)} jobs → {len(filtered)} jobs remain")
        
        return filtered
    
    def get_filter_stats(self, jobs: List[Dict]) -> Dict:
        """
        Get statistics about filtering results
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Dictionary with filter statistics
        """
        total = len(jobs)
        passed = len(self.filter_jobs(jobs))
        failed = total - passed
        
        # Count failures by reason
        no_required = sum(1 for job in jobs if not self.has_required_keyword(job.get('title', '')))
        has_negative = sum(1 for job in jobs if self.has_negative_keyword(job.get('title', '')))
        
        return {
            'total_jobs': total,
            'passed_filters': passed,
            'failed_filters': failed,
            'no_required_keyword': no_required,
            'has_negative_keyword': has_negative,
            'pass_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%"
        }
