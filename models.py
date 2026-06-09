"""
Data models and types for the Job Application Assistant.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ApplicationStatus(Enum):
    """Status of a job application."""
    DRAFT = "draft"
    READY = "ready"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    CLOSED = "closed"


class JobSource(Enum):
    """Source of the job listing."""
    JSON_IMPORT = "json"
    CSV_IMPORT = "csv"
    RSS_FEED = "rss"
    API = "api"
    MANUAL = "manual"


@dataclass
class CVSection:
    """CV section with structured data."""
    section_type: str  # personal_info, skills, experience, education, projects
    content: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_type": self.section_type,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
        }


@dataclass
class Person:
    """Personal information."""
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Experience:
    """Work experience entry."""
    company: str
    position: str
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None
    technologies: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Education:
    """Education entry."""
    institution: str
    degree: str
    field: str
    graduation_year: int
    gpa: Optional[float] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Project:
    """Project entry."""
    name: str
    description: str
    url: Optional[str] = None
    technologies: Optional[List[str]] = None
    date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Job:
    """Job listing."""
    title: str
    company: str
    description: str
    requirements: str
    url: str
    job_id: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    source: JobSource = JobSource.MANUAL
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    added_at: datetime = field(default_factory=datetime.now)
    match_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "requirements": self.requirements,
            "url": self.url,
            "location": self.location,
            "job_type": self.job_type,
            "salary": self.salary,
            "posted_date": self.posted_date,
            "source": self.source.value,
            "source_metadata": self.source_metadata,
            "added_at": self.added_at.isoformat(),
            "match_score": self.match_score,
        }


@dataclass
class CoverLetter:
    """Generated cover letter."""
    job_id: str
    content: str
    summary_bullets: Optional[List[str]] = None
    generated_at: datetime = field(default_factory=datetime.now)
    model_used: str = "gpt-4"
    prompt_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "content": self.content,
            "summary_bullets": self.summary_bullets,
            "generated_at": self.generated_at.isoformat(),
            "model_used": self.model_used,
            "prompt_version": self.prompt_version,
        }


@dataclass
class ApplicationRecord:
    """Application tracking record."""
    job_id: str
    status: ApplicationStatus
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    cover_letter_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "notes": self.notes,
            "cover_letter_id": self.cover_letter_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class JobScore:
    """Job matching score."""
    job_id: str
    keyword_match_score: float
    llm_relevance_score: Optional[float] = None
    overall_score: float = 0.0
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "keyword_match_score": self.keyword_match_score,
            "llm_relevance_score": self.llm_relevance_score,
            "overall_score": self.overall_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "calculated_at": self.calculated_at.isoformat(),
        }
