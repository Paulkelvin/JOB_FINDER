#!/usr/bin/env python3
"""
GeoJob-Sentinel - Production-Grade GIS Job Finder
A robust CLI application to find niche GIS Specialist I/II and Analyst roles
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List
import yaml

from database import JobDatabase
from ats_fetcher import ATSFetcher
from serper_fetcher import SerperFetcher
from job_filter import JobFilter
from discord_notifier import DiscordNotifier


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('geojob_sentinel.log')
    ]
)
logger = logging.getLogger(__name__)


class GeoJobSentinel:
    """Main application class for GeoJob-Sentinel"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize GeoJob-Sentinel
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.db = JobDatabase(self.config.get('database', {}).get('path', 'geojob_sentinel.db'))
        self.job_filter = JobFilter(
            custom_required=self.config.get('filters', {}).get('required_keywords'),
            custom_negative=self.config.get('filters', {}).get('negative_keywords')
        )
        
        # Initialize Discord notifier if configured
        webhook_url = self.config.get('discord', {}).get('webhook_url')
        self.discord = DiscordNotifier(webhook_url) if webhook_url else None
        
        # Statistics tracking
        self.stats = {
            'total_scanned': 0,
            'passed_filters': 0,
            'duplicates': 0,
            'new_jobs': 0,
            'by_source': {}
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            logger.error("Please create config.yaml based on config.example.yaml")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def fetch_ats_jobs(self) -> List[Dict]:
        """Fetch jobs from ATS platforms (Greenhouse/Lever)"""
        greenhouse_slugs = self.config.get('ats', {}).get('greenhouse_slugs', [])
        lever_slugs = self.config.get('ats', {}).get('lever_slugs', [])
        
        # Backward compatibility: check old format
        if not greenhouse_slugs and not lever_slugs:
            old_slugs = self.config.get('ats', {}).get('company_slugs', [])
            if old_slugs:
                logger.warning("Using deprecated 'company_slugs' format. Please update to 'greenhouse_slugs' and 'lever_slugs'")
                greenhouse_slugs = old_slugs
        
        total_companies = len(greenhouse_slugs) + len(lever_slugs)
        
        if total_companies == 0:
            logger.warning("No company slugs configured for ATS fetching")
            return []
        
        logger.info(f"Fetching jobs from {len(greenhouse_slugs)} Greenhouse + {len(lever_slugs)} Lever companies")
        
        try:
            fetcher = ATSFetcher(greenhouse_slugs=greenhouse_slugs, lever_slugs=lever_slugs)
            jobs = fetcher.fetch_all_jobs()
            return jobs
        except Exception as e:
            logger.error(f"Error fetching ATS jobs: {e}", exc_info=True)
            if self.discord:
                self.discord.send_error(f"ATS fetch error: {str(e)}")
            return []
    
    def fetch_serper_jobs(self) -> List[Dict]:
        """Fetch jobs from Google via Serper.dev"""
        api_key = self.config.get('serper', {}).get('api_key')
        
        if not api_key:
            logger.warning("No Serper API key configured, skipping Google search")
            return []
        
        logger.info("Fetching jobs via Serper/Google")
        
        try:
            fetcher = SerperFetcher(api_key)
            
            # Use custom dorks if configured
            custom_dorks = self.config.get('serper', {}).get('custom_dorks', [])
            
            jobs = []
            
            # Default Workday search
            jobs.extend(fetcher.search_workday_jobs())
            
            # Custom dorks
            for dork in custom_dorks:
                jobs.extend(fetcher.search_custom_dork(dork))
            
            # Discovery Mode: Find NEW companies
            if self.config.get('discovery', {}).get('enabled', False):
                logger.info("🔍 Discovery Mode ENABLED - Searching for new companies...")
                
                # Search Greenhouse platform
                if self.config.get('discovery', {}).get('search_greenhouse', True):
                    greenhouse_discoveries = fetcher.discover_greenhouse_companies()
                    jobs.extend(greenhouse_discoveries)
                    if greenhouse_discoveries:
                        logger.info(f"✨ Found {len(greenhouse_discoveries)} jobs from NEW Greenhouse companies")
                
                # Search Lever platform
                if self.config.get('discovery', {}).get('search_lever', True):
                    lever_discoveries = fetcher.discover_lever_companies()
                    jobs.extend(lever_discoveries)
                    if lever_discoveries:
                        logger.info(f"✨ Found {len(lever_discoveries)} jobs from NEW Lever companies")
            else:
                logger.info("Discovery Mode disabled in config")
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching Serper jobs: {e}", exc_info=True)
            if self.discord:
                self.discord.send_error(f"Serper fetch error: {str(e)}")
            return []
    
    def process_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Process jobs through filtering and deduplication
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of new, valid jobs
        """
        self.stats['total_scanned'] += len(jobs)
        
        # Step 1: Filter by keywords
        logger.info(f"Filtering {len(jobs)} jobs...")
        filtered_jobs = self.job_filter.filter_jobs(jobs)
        self.stats['passed_filters'] += len(filtered_jobs)
        
        # Step 2: Deduplicate
        logger.info(f"Checking {len(filtered_jobs)} jobs for duplicates...")
        new_jobs = []
        
        for job in filtered_jobs:
            job_id = job.get('job_id', '')
            url = job.get('url', '')
            
            if not job_id or not url:
                logger.warning(f"Job missing ID or URL, skipping: {job.get('title')}")
                continue
            
            if self.db.is_duplicate(job_id, url):
                self.stats['duplicates'] += 1
                logger.debug(f"Duplicate job: {job.get('title')}")
                continue
            
            # Add to database
            if self.db.add_job(
                job_id=job_id,
                url=url,
                title=job.get('title', ''),
                company=job.get('company', ''),
                source=job.get('source', '')
            ):
                new_jobs.append(job)
                
                # Track by source
                source = job.get('source', 'Unknown')
                self.stats['by_source'][source] = self.stats['by_source'].get(source, 0) + 1
        
        self.stats['new_jobs'] += len(new_jobs)
        logger.info(f"Found {len(new_jobs)} new jobs after deduplication")
        
        return new_jobs
    
    def notify_new_jobs(self, jobs: List[Dict]):
        """Send notifications for new jobs"""
        if not jobs:
            logger.info("No new jobs to notify")
            return
        
        if not self.discord:
            logger.warning("Discord webhook not configured, skipping notifications")
            return
        
        # Sort jobs by priority (HIGH priority = fresh jobs first)
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'NORMAL': 2, 'LOW': 3}
        sorted_jobs = sorted(jobs, key=lambda x: priority_order.get(x.get('priority', 'NORMAL'), 2))
        
        logger.info(f"Sending {len(sorted_jobs)} job notifications to Discord (sorted by freshness)")
        
        try:
            sent = self.discord.send_batch_notification(sorted_jobs)
            logger.info(f"Successfully sent {sent} notifications")
        except Exception as e:
            logger.error(f"Error sending notifications: {e}", exc_info=True)
    
    def send_summary(self):
        """Send summary notification"""
        if not self.discord:
            return
        
        try:
            self.discord.send_summary(self.stats)
        except Exception as e:
            logger.error(f"Error sending summary: {e}", exc_info=True)
    
    def run(self):
        """Main execution method"""
        logger.info("=" * 60)
        logger.info("GeoJob-Sentinel Starting")
        logger.info("=" * 60)
        
        try:
            all_jobs = []
            
            # Fetch from all sources
            ats_jobs = self.fetch_ats_jobs()
            all_jobs.extend(ats_jobs)
            
            serper_jobs = self.fetch_serper_jobs()
            all_jobs.extend(serper_jobs)
            
            logger.info(f"Total jobs fetched: {len(all_jobs)}")
            
            # Process and filter jobs
            new_jobs = self.process_jobs(all_jobs)
            
            # Send notifications
            self.notify_new_jobs(new_jobs)
            
            # Send summary
            self.send_summary()
            
            # Display statistics
            self._display_stats()
            
            logger.info("=" * 60)
            logger.info("GeoJob-Sentinel Completed Successfully")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Fatal error during execution: {e}", exc_info=True)
            if self.discord:
                self.discord.send_error(f"Fatal error: {str(e)}")
            sys.exit(1)
    
    def _display_stats(self):
        """Display execution statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total jobs scanned:     {self.stats['total_scanned']}")
        logger.info(f"Passed filters:         {self.stats['passed_filters']}")
        logger.info(f"Duplicates filtered:    {self.stats['duplicates']}")
        logger.info(f"New jobs found:         {self.stats['new_jobs']}")
        
        if self.stats['by_source']:
            logger.info("\nJobs by source:")
            for source, count in self.stats['by_source'].items():
                logger.info(f"  {source}: {count}")
        
        # Database stats
        db_stats = self.db.get_stats()
        logger.info(f"\nTotal jobs in database: {db_stats.get('total_jobs', 0)}")
        logger.info(f"Jobs found (last 7 days): {db_stats.get('recent_7_days', 0)}")
        logger.info("=" * 60 + "\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='GeoJob-Sentinel - Find niche GIS Specialist/Analyst jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default config.yaml
  %(prog)s -c custom.yaml           # Run with custom config
  %(prog)s -v                       # Run with verbose logging
  %(prog)s --stats                  # Show database statistics only
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show database statistics and exit'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Show stats only
    if args.stats:
        db = JobDatabase()
        stats = db.get_stats()
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)
        print(f"Total jobs tracked:     {stats.get('total_jobs', 0)}")
        print(f"Jobs (last 7 days):     {stats.get('recent_7_days', 0)}")
        
        if stats.get('by_source'):
            print("\nJobs by source:")
            for source, count in stats['by_source'].items():
                print(f"  {source}: {count}")
        
        print("=" * 60 + "\n")
        return
    
    # Run the application
    sentinel = GeoJobSentinel(args.config)
    sentinel.run()


if __name__ == '__main__':
    main()
