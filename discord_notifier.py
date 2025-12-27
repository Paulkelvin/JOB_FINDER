"""
GeoJob-Sentinel Discord Notification Module
Sends rich embed notifications to Discord webhook
"""

import requests
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Sends job alerts to Discord via webhook"""
    
    # Discord color codes (in decimal)
    COLOR_SUCCESS = 5763719   # Green
    COLOR_INFO = 3447003      # Blue
    COLOR_WARNING = 16776960  # Yellow
    COLOR_ERROR = 15158332    # Red
    
    # Source-specific colors
    SOURCE_COLORS = {
        'Greenhouse': 3066993,   # Dark Green
        'Lever': 10181046,       # Purple
        'Serper/Google': 15844367,  # Gold
        'Workday': 3426654,      # Teal
        'Discovery/Greenhouse': 16734296,  # Bright Orange (NEW!)
        'Discovery/Lever': 16734296        # Bright Orange (NEW!)
    }
    
    def __init__(self, webhook_url: str):
        """
        Initialize Discord notifier
        
        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url
    
    def _create_job_embed(self, job: Dict) -> Dict:
        """
        Create a Discord embed for a job posting
        
        Args:
            job: Job dictionary
            
        Returns:
            Discord embed dictionary
        """
        source = job.get('source', 'Unknown')
        color = self.SOURCE_COLORS.get(source, self.COLOR_INFO)
        
        # Check if this is a discovered company (new find)
        is_discovery = source.startswith('Discovery/')
        
        embed = {
            'title': ('🆕 NEW COMPANY! ' if is_discovery else '') + job.get('title', 'Unknown Title'),
            'url': job.get('url', ''),
            'color': color,
            'fields': [
                {
                    'name': '🏢 Company',
                    'value': job.get('company', 'Unknown') + (' 🌟 (Discovered!)' if is_discovery else ''),
                    'inline': True
                },
                {
                    'name': '📍 Location',
                    'value': job.get('location', 'Not specified'),
                    'inline': True
                },
                {
                    'name': '🔍 Source',
                    'value': source,
                    'inline': True
                }
            ],
            'footer': {
                'text': 'GeoJob-Sentinel' + (' - Discovery Mode' if is_discovery else '')
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add snippet if available (from Google results)
        if job.get('snippet'):
            embed['description'] = job['snippet'][:200] + '...' if len(job.get('snippet', '')) > 200 else job.get('snippet', '')
        
        return embed
    
    def send_job_notification(self, job: Dict) -> bool:
        """
        Send a single job notification
        
        Args:
            job: Job dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            embed = self._create_job_embed(job)
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Sent Discord notification for: {job.get('title')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False
    
    def send_batch_notification(self, jobs: List[Dict], max_per_message: int = 10) -> int:
        """
        Send multiple jobs in batched messages
        Discord allows up to 10 embeds per message
        
        Args:
            jobs: List of job dictionaries
            max_per_message: Maximum embeds per message (max 10)
            
        Returns:
            Number of successfully sent notifications
        """
        max_per_message = min(max_per_message, 10)  # Discord limit
        sent_count = 0
        
        # Split jobs into batches
        for i in range(0, len(jobs), max_per_message):
            batch = jobs[i:i + max_per_message]
            
            try:
                embeds = [self._create_job_embed(job) for job in batch]
                
                payload = {
                    'embeds': embeds
                }
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                
                sent_count += len(batch)
                logger.info(f"Sent batch of {len(batch)} jobs to Discord")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending batch notification: {e}")
        
        return sent_count
    
    def send_summary(self, stats: Dict) -> bool:
        """
        Send a summary message about the scan
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            True if sent successfully
        """
        try:
            embed = {
                'title': '📊 GeoJob-Sentinel Scan Summary',
                'color': self.COLOR_INFO,
                'fields': [
                    {
                        'name': 'New Jobs Found',
                        'value': str(stats.get('new_jobs', 0)),
                        'inline': True
                    },
                    {
                        'name': 'Total Scanned',
                        'value': str(stats.get('total_scanned', 0)),
                        'inline': True
                    },
                    {
                        'name': 'Duplicates Filtered',
                        'value': str(stats.get('duplicates', 0)),
                        'inline': True
                    }
                ],
                'footer': {
                    'text': 'GeoJob-Sentinel'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add source breakdown if available
            if stats.get('by_source'):
                source_text = '\n'.join([f"{k}: {v}" for k, v in stats['by_source'].items()])
                embed['fields'].append({
                    'name': 'Jobs by Source',
                    'value': source_text,
                    'inline': False
                })
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Sent summary notification to Discord")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending summary notification: {e}")
            return False
    
    def send_error(self, error_message: str) -> bool:
        """
        Send an error notification
        
        Args:
            error_message: Error message to send
            
        Returns:
            True if sent successfully
        """
        try:
            embed = {
                'title': '⚠️ GeoJob-Sentinel Error',
                'description': error_message,
                'color': self.COLOR_ERROR,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            payload = {
                'embeds': [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
