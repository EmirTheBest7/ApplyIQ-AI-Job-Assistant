"""
Database layer for SQLite operations.
Handles schema creation, CRUD operations for all entities.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from models import (
    Job, CoverLetter, ApplicationRecord, JobScore,
    ApplicationStatus, JobSource, CVSection, Person, Experience, Education, Project
)

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = "applyiq.db"):
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
        self.init_db()

    def connect(self) -> None:
        """Create database connection."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def disconnect(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def init_db(self) -> None:
        """Initialize database schema."""
        self.connect()
        try:
            self._create_tables()
            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            self.disconnect()

    def _create_tables(self) -> None:
        """Create all tables."""
        # CV table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_type TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(section_type, version)
        )
        """)

        # Jobs table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            url TEXT NOT NULL,
            location TEXT,
            job_type TEXT,
            salary TEXT,
            posted_date TEXT,
            source TEXT NOT NULL,
            source_metadata TEXT,
            added_at TEXT NOT NULL,
            UNIQUE(url, company, title)
        )
        """)

        # Cover Letters table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            content TEXT NOT NULL,
            summary_bullets TEXT,
            generated_at TEXT NOT NULL,
            model_used TEXT,
            prompt_version INTEGER DEFAULT 1,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        )
        """)

        # Applications Status table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL,
            applied_at TEXT,
            notes TEXT,
            cover_letter_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
            FOREIGN KEY (cover_letter_id) REFERENCES cover_letters(id) ON DELETE SET NULL,
            UNIQUE(job_id)
        )
        """)

        # Job Scores table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            keyword_match_score REAL NOT NULL,
            llm_relevance_score REAL,
            overall_score REAL NOT NULL,
            matched_skills TEXT,
            missing_skills TEXT,
            calculated_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
            UNIQUE(job_id)
        )
        """)

        # Indexes for performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_added_at ON jobs(added_at)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications_status(status)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_scores_overall ON job_scores(overall_score)")

    # ==================== CV Operations ====================

    def add_cv_section(self, section_type: str, content: Dict[str, Any], version: int = 1) -> int:
        """Add or update a CV section."""
        self.connect()
        try:
            now = datetime.now().isoformat()
            self.cursor.execute("""
            INSERT OR REPLACE INTO cv (section_type, content, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """, (section_type, json.dumps(content), version, now, now))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def get_cv_section(self, section_type: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a CV section."""
        self.connect()
        try:
            if version is None:
                self.cursor.execute(
                    "SELECT * FROM cv WHERE section_type = ? ORDER BY version DESC LIMIT 1",
                    (section_type,)
                )
            else:
                self.cursor.execute(
                    "SELECT * FROM cv WHERE section_type = ? AND version = ?",
                    (section_type, version)
                )
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    def get_full_cv(self) -> Dict[str, Any]:
        """Get complete CV data."""
        self.connect()
        try:
            self.cursor.execute("""
            SELECT DISTINCT section_type, row_number() OVER (PARTITION BY section_type ORDER BY version DESC) as rn
            FROM cv
            WHERE row_number() OVER (PARTITION BY section_type ORDER BY version DESC) = 1
            """)
            
            cv_data = {}
            for row in self.cursor.fetchall():
                section_type = row[0]
                section = self.get_cv_section(section_type)
                if section:
                    cv_data[section_type] = json.loads(section['content'])
            return cv_data
        finally:
            self.disconnect()

    # ==================== Jobs Operations ====================

    def add_job(self, job: Job) -> int:
        """Add a job to the database."""
        self.connect()
        try:
            self.cursor.execute("""
            INSERT INTO jobs (job_id, title, company, description, requirements, 
                            url, location, job_type, salary, posted_date, 
                            source, source_metadata, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id,
                job.title,
                job.company,
                job.description,
                job.requirements,
                job.url,
                job.location,
                job.job_type,
                job.salary,
                job.posted_date,
                job.source.value,
                json.dumps(job.source_metadata),
                job.added_at.isoformat()
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            logger.warning(f"Duplicate job detected: {e}")
            self.conn.rollback()
            return -1
        finally:
            self.disconnect()

    def add_jobs_batch(self, jobs: List[Job]) -> Tuple[int, int]:
        """Add multiple jobs. Returns (success_count, duplicate_count)."""
        success_count = 0
        duplicate_count = 0
        for job in jobs:
            result = self.add_job(job)
            if result > 0:
                success_count += 1
            else:
                duplicate_count += 1
        return success_count, duplicate_count

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    def list_jobs(self, limit: int = 50, offset: int = 0, 
                  company: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs with optional filters."""
        self.connect()
        try:
            query = "SELECT j.*, s.overall_score FROM jobs j LEFT JOIN job_scores s ON j.job_id = s.job_id WHERE 1=1"
            params = []

            if company:
                query += " AND j.company LIKE ?"
                params.append(f"%{company}%")
            if source:
                query += " AND j.source = ?"
                params.append(source)

            query += " ORDER BY j.added_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            self.cursor.execute(query, params)
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    def count_jobs(self, company: Optional[str] = None, source: Optional[str] = None) -> int:
        """Count total jobs."""
        self.connect()
        try:
            query = "SELECT COUNT(*) FROM jobs WHERE 1=1"
            params = []

            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")
            if source:
                query += " AND source = ?"
                params.append(source)

            self.cursor.execute(query, params)
            return self.cursor.fetchone()[0]
        finally:
            self.disconnect()

    # ==================== Cover Letters Operations ====================

    def add_cover_letter(self, cover_letter: CoverLetter) -> int:
        """Add a cover letter."""
        self.connect()
        try:
            self.cursor.execute("""
            INSERT INTO cover_letters (job_id, content, summary_bullets, 
                                      generated_at, model_used, prompt_version)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cover_letter.job_id,
                cover_letter.content,
                json.dumps(cover_letter.summary_bullets) if cover_letter.summary_bullets else None,
                cover_letter.generated_at.isoformat(),
                cover_letter.model_used,
                cover_letter.prompt_version
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def get_cover_letter(self, cover_letter_id: int) -> Optional[Dict[str, Any]]:
        """Get a cover letter by ID."""
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM cover_letters WHERE id = ?", (cover_letter_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    def get_cover_letter_by_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent cover letter for a job."""
        self.connect()
        try:
            self.cursor.execute("""
            SELECT * FROM cover_letters WHERE job_id = ? 
            ORDER BY generated_at DESC LIMIT 1
            """, (job_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    # ==================== Application Status Operations ====================

    def add_application_status(self, app_record: ApplicationRecord) -> int:
        """Add or update application status."""
        self.connect()
        try:
            now = datetime.now().isoformat()
            self.cursor.execute("""
            INSERT OR REPLACE INTO applications_status 
            (job_id, status, applied_at, notes, cover_letter_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                app_record.job_id,
                app_record.status.value,
                app_record.applied_at.isoformat() if app_record.applied_at else None,
                app_record.notes,
                app_record.cover_letter_id,
                app_record.created_at.isoformat() if app_record.created_at else now,
                now
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def get_application_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get application status for a job."""
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM applications_status WHERE job_id = ?", (job_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    def list_applications(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List applications with optional status filter."""
        self.connect()
        try:
            if status:
                self.cursor.execute("""
                SELECT a.*, j.title, j.company FROM applications_status a
                JOIN jobs j ON a.job_id = j.job_id
                WHERE a.status = ?
                ORDER BY a.updated_at DESC
                """, (status,))
            else:
                self.cursor.execute("""
                SELECT a.*, j.title, j.company FROM applications_status a
                JOIN jobs j ON a.job_id = j.job_id
                ORDER BY a.updated_at DESC
                """)
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    # ==================== Job Scores Operations ====================

    def add_job_score(self, score: JobScore) -> int:
        """Add or update job score."""
        self.connect()
        try:
            self.cursor.execute("""
            INSERT OR REPLACE INTO job_scores
            (job_id, keyword_match_score, llm_relevance_score, overall_score,
             matched_skills, missing_skills, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                score.job_id,
                score.keyword_match_score,
                score.llm_relevance_score,
                score.overall_score,
                json.dumps(score.matched_skills),
                json.dumps(score.missing_skills),
                score.calculated_at.isoformat()
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        finally:
            self.disconnect()

    def get_job_score(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job score."""
        self.connect()
        try:
            self.cursor.execute("SELECT * FROM job_scores WHERE job_id = ?", (job_id,))
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.disconnect()

    def get_top_jobs_by_score(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top-ranked jobs."""
        self.connect()
        try:
            self.cursor.execute("""
            SELECT j.*, s.overall_score, s.matched_skills, s.missing_skills
            FROM jobs j
            LEFT JOIN job_scores s ON j.job_id = s.job_id
            ORDER BY s.overall_score DESC NULLS LAST
            LIMIT ?
            """, (limit,))
            return [dict(row) for row in self.cursor.fetchall()]
        finally:
            self.disconnect()

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        self.connect()
        try:
            stats = {}

            # Jobs stats
            self.cursor.execute("SELECT COUNT(*) FROM jobs")
            stats['total_jobs'] = self.cursor.fetchone()[0]

            self.cursor.execute("SELECT COUNT(DISTINCT company) FROM jobs")
            stats['total_companies'] = self.cursor.fetchone()[0]

            self.cursor.execute("""
            SELECT source, COUNT(*) as count FROM jobs 
            GROUP BY source ORDER BY count DESC
            """)
            stats['jobs_by_source'] = {row[0]: row[1] for row in self.cursor.fetchall()}

            # Applications stats
            self.cursor.execute("""
            SELECT status, COUNT(*) as count FROM applications_status
            GROUP BY status ORDER BY count DESC
            """)
            stats['applications_by_status'] = {row[0]: row[1] for row in self.cursor.fetchall()}

            # Cover letters generated
            self.cursor.execute("SELECT COUNT(*) FROM cover_letters")
            stats['cover_letters_generated'] = self.cursor.fetchone()[0]

            return stats
        finally:
            self.disconnect()
