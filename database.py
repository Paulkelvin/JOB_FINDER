"""
GeoJob-Sentinel Database Module
Handles job deduplication using SQLite
"""

import sqlite3
import hashlib
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class JobDatabase:
    """Manages the SQLite database for job deduplication"""
    
    def __init__(self, db_path: str = "geojob_sentinel.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        source TEXT NOT NULL,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        url_hash TEXT UNIQUE NOT NULL
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_hash ON jobs(url_hash)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate SHA256 hash of URL for deduplication"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def is_duplicate(self, job_id: str, url: str) -> bool:
        """
        Check if a job already exists in the database
        
        Args:
            job_id: Unique job identifier
            url: Job posting URL
            
        Returns:
            True if job exists, False otherwise
        """
        try:
            url_hash = self._generate_url_hash(url)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE job_id = ? OR url_hash = ?
                """, (job_id, url_hash))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error checking duplicate: {e}")
            return False  # On error, assume not duplicate to avoid missing jobs
    
    def add_job(self, job_id: str, url: str, title: str, company: str, source: str) -> bool:
        """
        Add a new job to the database
        
        Args:
            job_id: Unique job identifier
            url: Job posting URL
            title: Job title
            company: Company name
            source: Source of the job (e.g., 'Greenhouse', 'Serper', 'Workday')
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            url_hash = self._generate_url_hash(url)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO jobs (job_id, url, title, company, source, url_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (job_id, url, title, company, source, url_hash))
                
                conn.commit()
                logger.info(f"Added job to database: {title} at {company}")
                return True
                
        except sqlite3.IntegrityError:
            logger.debug(f"Job already exists in database: {job_id}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding job to database: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get statistics about the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total jobs
                cursor.execute("SELECT COUNT(*) FROM jobs")
                total = cursor.fetchone()[0]
                
                # Jobs by source
                cursor.execute("""
                    SELECT source, COUNT(*) 
                    FROM jobs 
                    GROUP BY source
                """)
                by_source = dict(cursor.fetchall())
                
                # Recent jobs (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE first_seen >= datetime('now', '-7 days')
                """)
                recent = cursor.fetchone()[0]
                
                return {
                    'total_jobs': total,
                    'by_source': by_source,
                    'recent_7_days': recent
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {}
