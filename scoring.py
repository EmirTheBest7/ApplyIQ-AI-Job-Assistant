"""
Job matching and scoring module.
Ranks jobs based on skill overlap and other criteria.
"""

import logging
import re
from typing import List, Dict, Any, Set
from collections import Counter

from models import JobScore
from cv import CVManager

logger = logging.getLogger(__name__)


class JobScoringManager:
    """Manages job scoring and ranking."""

    def __init__(self, cv_manager: CVManager):
        self.cv_manager = cv_manager
        self.cv_skills = set(skill.lower() for skill in cv_manager.extract_skills())

    def calculate_keyword_match_score(self, job_description: str, job_requirements: str) -> tuple:
        """
        Calculate keyword matching score based on CV skills.
        Returns: (score 0-100, matched_skills, missing_skills)
        """
        try:
            combined_text = f"{job_description} {job_requirements}".lower()

            matched_skills = []
            for skill in self.cv_skills:
                # Match whole words only (with word boundaries)
                if re.search(rf'\b{re.escape(skill)}\b', combined_text):
                    matched_skills.append(skill)

            # Calculate match percentage
            if len(self.cv_skills) == 0:
                score = 0.0
            else:
                score = (len(matched_skills) / len(self.cv_skills)) * 100

            # Estimate missing skills (skills in job but not in CV)
            # Common tech keywords
            tech_keywords = self._extract_tech_keywords(combined_text)
            missing = [kw for kw in tech_keywords if kw.lower() not in self.cv_skills]

            return score, matched_skills, missing[:5]  # Top 5 missing skills
        except Exception as e:
            logger.error(f"Error calculating keyword match score: {e}")
            return 0.0, [], []

    def _extract_tech_keywords(self, text: str) -> List[str]:
        """Extract common tech keywords from text."""
        common_tech = {
            # Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'golang', 'rust', 'typescript',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            # Web frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'rails',
            'express', 'nextjs', 'laravel', 'aspnet',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'dynamodb', 'firestore', 'oracle', 'mssql',
            # Cloud/DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
            'terraform', 'ansible', 'cloud',
            # Data
            'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark',
            'hadoop', 'kafka', 'airflow',
            # Tools
            'git', 'linux', 'unix', 'windows', 'macos', 'vim', 'vscode', 'ide',
            'jira', 'figma', 'slack', 'json', 'xml', 'rest', 'graphql', 'api',
            # Methodologies
            'agile', 'scrum', 'kanban', 'tdd', 'bdd', 'ci/cd'
        }

        text_lower = text.lower()
        found_keywords = []

        for keyword in common_tech:
            if re.search(rf'\b{keyword}\b', text_lower):
                found_keywords.append(keyword)

        return found_keywords

    def calculate_job_score(self, job_id: str, job_title: str, job_description: str,
                           job_requirements: str, job_company: str = "") -> JobScore:
        """
        Calculate comprehensive job score.
        Combines keyword matching and other factors.
        """
        try:
            # Keyword matching (primary score)
            keyword_score, matched_skills, missing_skills = self.calculate_keyword_match_score(
                job_description, job_requirements
            )

            # Bonus factors
            bonus = 0
            # Bonus for seniority match
            if self._check_seniority_match(job_title):
                bonus += 5

            # Bonus for location preference (if stored in CV)
            location_bonus = self._check_location_bonus(job_description)
            bonus += location_bonus

            # Calculate overall score (weighted)
            overall_score = min(100, keyword_score + bonus)

            job_score = JobScore(
                job_id=job_id,
                keyword_match_score=keyword_score,
                llm_relevance_score=None,  # Can be filled by LLM-based scoring
                overall_score=overall_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills
            )

            logger.debug(f"Scored job {job_id}: {overall_score:.1f}")
            return job_score
        except Exception as e:
            logger.error(f"Error calculating job score: {e}")
            return JobScore(
                job_id=job_id,
                keyword_match_score=0.0,
                overall_score=0.0
            )

    def _check_seniority_match(self, job_title: str) -> bool:
        """Check if job seniority level matches CV experience."""
        junior_keywords = ['junior', 'entry', 'entry-level', 'graduate', 'fresher', 'intern']
        mid_keywords = ['mid', 'middle', 'intermediate', 'senior', 'lead', 'principal']
        senior_keywords = ['senior', 'lead', 'principal', 'director', 'manager', 'architect']

        title_lower = job_title.lower()

        # Simple heuristic - could be improved with actual CV experience level
        if any(kw in title_lower for kw in mid_keywords):
            return True

        return False

    def _check_location_bonus(self, job_description: str) -> float:
        """Check for remote work options (common preference)."""
        remote_keywords = ['remote', 'work from home', 'distributed', 'hybrid']
        description_lower = job_description.lower()

        if any(kw in description_lower for kw in remote_keywords):
            return 10
        return 0

    def rank_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank jobs by calculated score."""
        try:
            scored_jobs = []
            for job in jobs:
                score = self.calculate_job_score(
                    job.get('job_id'),
                    job.get('title', ''),
                    job.get('description', ''),
                    job.get('requirements', '')
                )
                job_copy = job.copy()
                job_copy['score'] = score.overall_score
                job_copy['matched_skills'] = score.matched_skills
                job_copy['missing_skills'] = score.missing_skills
                scored_jobs.append(job_copy)

            # Sort by score descending
            scored_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
            return scored_jobs
        except Exception as e:
            logger.error(f"Error ranking jobs: {e}")
            return jobs

    def get_skill_gaps(self, job_description: str, job_requirements: str) -> List[str]:
        """Identify skill gaps for a specific job."""
        try:
            _, _, missing = self.calculate_keyword_match_score(job_description, job_requirements)
            return missing
        except Exception as e:
            logger.error(f"Error getting skill gaps: {e}")
            return []
