"""
CV management module.
Handles storing, editing, and versioning of user CV.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from db import Database
from models import CVSection, Person, Experience, Education, Project

logger = logging.getLogger(__name__)


class CVManager:
    """Manages CV operations."""

    def __init__(self, db: Database):
        self.db = db
        self.current_version = 1

    def setup_personal_info(self, personal_info: Person) -> bool:
        """Setup personal information section."""
        try:
            content = personal_info.to_dict()
            self.db.add_cv_section("personal_info", content, version=self.current_version)
            logger.info("Personal info added to CV")
            return True
        except Exception as e:
            logger.error(f"Error adding personal info: {e}")
            return False

    def add_skills(self, skills_dict: Dict[str, List[str]]) -> bool:
        """
        Add skills section.
        Expected format: {
            "languages": ["Python", "JavaScript"],
            "frameworks": ["Django", "React"],
            "databases": ["PostgreSQL", "MongoDB"],
            "tools": ["Git", "Docker"]
        }
        """
        try:
            self.db.add_cv_section("skills", skills_dict, version=self.current_version)
            logger.info("Skills added to CV")
            return True
        except Exception as e:
            logger.error(f"Error adding skills: {e}")
            return False

    def add_experience(self, experiences: List[Dict[str, Any]]) -> bool:
        """Add experience section."""
        try:
            content = {"experiences": experiences}
            self.db.add_cv_section("experience", content, version=self.current_version)
            logger.info(f"Added {len(experiences)} experience entries")
            return True
        except Exception as e:
            logger.error(f"Error adding experience: {e}")
            return False

    def add_education(self, education_list: List[Dict[str, Any]]) -> bool:
        """Add education section."""
        try:
            content = {"education": education_list}
            self.db.add_cv_section("education", content, version=self.current_version)
            logger.info(f"Added {len(education_list)} education entries")
            return True
        except Exception as e:
            logger.error(f"Error adding education: {e}")
            return False

    def add_projects(self, projects: List[Dict[str, Any]]) -> bool:
        """Add projects section."""
        try:
            content = {"projects": projects}
            self.db.add_cv_section("projects", content, version=self.current_version)
            logger.info(f"Added {len(projects)} projects")
            return True
        except Exception as e:
            logger.error(f"Error adding projects: {e}")
            return False

    def get_section(self, section_type: str) -> Optional[Dict[str, Any]]:
        """Get a CV section."""
        try:
            section = self.db.get_cv_section(section_type)
            if section:
                return json.loads(section['content'])
            return None
        except Exception as e:
            logger.error(f"Error retrieving section {section_type}: {e}")
            return None

    def get_full_cv(self) -> Dict[str, Any]:
        """Get complete CV."""
        try:
            cv_data = self.db.get_full_cv()
            return cv_data
        except Exception as e:
            logger.error(f"Error retrieving full CV: {e}")
            return {}

    def extract_skills(self) -> List[str]:
        """Extract all skills from CV for matching."""
        try:
            skills_section = self.get_section("skills")
            if not skills_section:
                return []

            all_skills = []
            for category, skill_list in skills_section.items():
                if isinstance(skill_list, list):
                    all_skills.extend(skill_list)

            return all_skills
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return []

    def extract_experience_text(self) -> str:
        """Extract experience as formatted text."""
        try:
            exp_section = self.get_section("experience")
            if not exp_section or "experiences" not in exp_section:
                return ""

            text_parts = []
            for exp in exp_section["experiences"]:
                text_parts.append(f"{exp.get('position')} at {exp.get('company')}")
                if exp.get('description'):
                    text_parts.append(exp['description'])
                if exp.get('technologies'):
                    text_parts.append(f"Technologies: {', '.join(exp['technologies'])}")
                text_parts.append("")

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting experience: {e}")
            return ""

    def extract_education_text(self) -> str:
        """Extract education as formatted text."""
        try:
            edu_section = self.get_section("education")
            if not edu_section or "education" not in edu_section:
                return ""

            text_parts = []
            for edu in edu_section["education"]:
                degree = f"{edu.get('degree')} in {edu.get('field')}"
                institution = edu.get('institution')
                text_parts.append(f"{degree} from {institution} ({edu.get('graduation_year')})")

            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting education: {e}")
            return ""

    def export_cv_text(self) -> str:
        """Export CV as formatted plain text for LLM context."""
        try:
            cv_data = self.get_full_cv()
            output_parts = []

            # Personal Info
            if "personal_info" in cv_data:
                personal = cv_data["personal_info"]
                output_parts.append(f"NAME: {personal.get('full_name')}")
                output_parts.append(f"EMAIL: {personal.get('email')}")
                if personal.get('phone'):
                    output_parts.append(f"PHONE: {personal.get('phone')}")
                if personal.get('location'):
                    output_parts.append(f"LOCATION: {personal.get('location')}")
                output_parts.append("")

            # Skills
            if "skills" in cv_data:
                output_parts.append("SKILLS:")
                skills = cv_data["skills"]
                for category, skill_list in skills.items():
                    if isinstance(skill_list, list):
                        output_parts.append(f"  {category.title()}: {', '.join(skill_list)}")
                output_parts.append("")

            # Experience
            if "experience" in cv_data:
                output_parts.append("EXPERIENCE:")
                exp_section = cv_data["experience"]
                for exp in exp_section.get("experiences", []):
                    output_parts.append(f"  {exp.get('position')} at {exp.get('company')} ({exp.get('start_date')} - {exp.get('end_date', 'Present')})")
                    if exp.get('description'):
                        output_parts.append(f"    {exp['description']}")
                    if exp.get('technologies'):
                        output_parts.append(f"    Tech: {', '.join(exp['technologies'])}")
                output_parts.append("")

            # Education
            if "education" in cv_data:
                output_parts.append("EDUCATION:")
                edu_section = cv_data["education"]
                for edu in edu_section.get("education", []):
                    output_parts.append(f"  {edu.get('degree')} in {edu.get('field')}")
                    output_parts.append(f"    {edu.get('institution')} ({edu.get('graduation_year')})")
                output_parts.append("")

            # Projects
            if "projects" in cv_data:
                output_parts.append("PROJECTS:")
                proj_section = cv_data["projects"]
                for proj in proj_section.get("projects", []):
                    output_parts.append(f"  {proj.get('name')}: {proj.get('description')}")
                    if proj.get('technologies'):
                        output_parts.append(f"    Tech: {', '.join(proj['technologies'])}")
                output_parts.append("")

            return "\n".join(output_parts)
        except Exception as e:
            logger.error(f"Error exporting CV: {e}")
            return ""
