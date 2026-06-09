"""
Job ingestion module.
Handles importing jobs from various sources: JSON, CSV, RSS feeds.
"""

import csv
import json
import logging
import feedparser
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import requests
from datetime import datetime

from models import Job, JobSource

logger = logging.getLogger(__name__)


class JobIngestionManager:
    """Manages job ingestion from various sources."""

    @staticmethod
    def import_from_json(json_data: str) -> List[Job]:
        """
        Import jobs from JSON string.
        Expected format: List of job objects with: title, company, description, requirements, url
        """
        try:
            jobs_list = json.loads(json_data)
            if not isinstance(jobs_list, list):
                logger.error("JSON data must be a list of jobs")
                return []

            jobs = []
            for job_dict in jobs_list:
                job = Job(
                    title=job_dict.get("title", ""),
                    company=job_dict.get("company", ""),
                    description=job_dict.get("description", ""),
                    requirements=job_dict.get("requirements", ""),
                    url=job_dict.get("url", ""),
                    job_id=job_dict.get("job_id") or str(uuid.uuid4()),
                    location=job_dict.get("location"),
                    job_type=job_dict.get("job_type"),
                    salary=job_dict.get("salary"),
                    posted_date=job_dict.get("posted_date"),
                    source=JobSource.JSON_IMPORT,
                    source_metadata={
                        "original_data": job_dict
                    }
                )
                if job.title and job.company and job.url:
                    jobs.append(job)
                else:
                    logger.warning(f"Skipping incomplete job entry: {job_dict}")

            logger.info(f"Successfully imported {len(jobs)} jobs from JSON")
            return jobs
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            return []
        except Exception as e:
            logger.error(f"Error importing from JSON: {e}")
            return []

    @staticmethod
    def import_from_json_file(file_path: str) -> List[Job]:
        """Import jobs from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = f.read()
            return JobIngestionManager.import_from_json(json_data)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return []

    @staticmethod
    def import_from_csv(csv_data: str) -> List[Job]:
        """
        Import jobs from CSV data.
        Expected columns: title, company, description, requirements, url (+ optional: location, job_type, salary, posted_date)
        """
        try:
            lines = csv_data.strip().split('\n')
            reader = csv.DictReader(lines)

            required_fields = {'title', 'company', 'description', 'requirements', 'url'}
            if not reader.fieldnames or not required_fields.issubset(set(reader.fieldnames)):
                logger.error(f"CSV must have columns: {', '.join(required_fields)}")
                return []

            jobs = []
            for row in reader:
                job = Job(
                    title=row.get("title", "").strip(),
                    company=row.get("company", "").strip(),
                    description=row.get("description", "").strip(),
                    requirements=row.get("requirements", "").strip(),
                    url=row.get("url", "").strip(),
                    job_id=str(uuid.uuid4()),
                    location=row.get("location", "").strip() or None,
                    job_type=row.get("job_type", "").strip() or None,
                    salary=row.get("salary", "").strip() or None,
                    posted_date=row.get("posted_date", "").strip() or None,
                    source=JobSource.CSV_IMPORT,
                    source_metadata={"csv_row": row}
                )
                if job.title and job.company and job.url:
                    jobs.append(job)

            logger.info(f"Successfully imported {len(jobs)} jobs from CSV")
            return jobs
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return []

    @staticmethod
    def import_from_csv_file(file_path: str) -> List[Job]:
        """Import jobs from a CSV file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_data = f.read()
            return JobIngestionManager.import_from_csv(csv_data)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

    @staticmethod
    def import_from_rss_feed(rss_url: str, feed_name: str = "RSS Feed") -> List[Job]:
        """
        Import jobs from RSS feed.
        Parses RSS feed and extracts job-related information from entries.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(rss_url, timeout=10, headers=headers)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"RSS feed parsing issue: {feed.bozo_exception}")

            jobs = []
            for entry in feed.entries:
                # Try to extract job information from feed entry
                job = Job(
                    title=entry.get('title', 'Unknown Position'),
                    company=entry.get('author', 'Unknown Company'),
                    description=entry.get('summary', entry.get('description', '')),
                    requirements=JobIngestionManager._extract_requirements_from_text(
                        entry.get('summary', entry.get('description', ''))
                    ),
                    url=entry.get('link', ''),
                    job_id=str(uuid.uuid4()),
                    posted_date=entry.get('published', None),
                    source=JobSource.RSS_FEED,
                    source_metadata={
                        "feed_url": rss_url,
                        "feed_name": feed_name,
                        "source_id": entry.get('id', '')
                    }
                )
                if job.title and job.url:
                    jobs.append(job)

            logger.info(f"Successfully imported {len(jobs)} jobs from RSS feed: {feed_name}")
            return jobs
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
            return []

    @staticmethod
    def _extract_requirements_from_text(text: str) -> str:
        """
        Simple extraction of requirements from text.
        Looks for common patterns like "Requirements:", "Skills:", etc.
        """
        if not text:
            return ""

        text_lower = text.lower()

        # Look for requirements section
        keywords = ['requirement', 'skill', 'qualification', 'must have', 'nice to have']
        for keyword in keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Return text from keyword onwards
                return text[idx:idx+500]  # First 500 chars of requirements section

        # If no specific section, return first 300 chars as summary
        return text[:300]

    @staticmethod
    def import_manual_job(title: str, company: str, description: str, 
                         requirements: str, url: str, **kwargs) -> Job:
        """Create a job entry from manual input."""
        job = Job(
            title=title,
            company=company,
            description=description,
            requirements=requirements,
            url=url,
            job_id=str(uuid.uuid4()),
            location=kwargs.get('location'),
            job_type=kwargs.get('job_type'),
            salary=kwargs.get('salary'),
            posted_date=kwargs.get('posted_date'),
            source=JobSource.MANUAL,
            source_metadata={"manual_entry": True}
        )
        logger.info(f"Created manual job entry: {title} at {company}")
        return job

    @staticmethod
    def deduplicate_jobs(jobs: List[Job]) -> List[Job]:
        """Remove duplicate jobs based on URL and company+title combination."""
        seen = set()
        unique_jobs = []

        for job in jobs:
            # Create a composite key: url is primary, company+title is secondary
            url_key = job.url.lower().strip()
            composite_key = f"{job.company.lower()}|{job.title.lower()}"

            if url_key and url_key not in seen:
                seen.add(url_key)
                unique_jobs.append(job)
            elif composite_key not in seen:
                seen.add(composite_key)
                unique_jobs.append(job)

        logger.info(f"Deduplicated {len(jobs)} jobs to {len(unique_jobs)} unique entries")
        return unique_jobs
