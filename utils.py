"""
Utility functions for the Job Application Assistant.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration and settings."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "db_path": "applyiq.db",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "enable_llm_scoring": False,
            "auto_score_jobs": True,
            "log_level": "INFO"
        }

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value

    def validate_api_keys(self) -> Dict[str, bool]:
        """Check if required API keys are available."""
        return {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY"))
        }


class ExportManager:
    """Manages export functionality."""

    @staticmethod
    def export_cover_letter_to_file(content: str, job_title: str, company: str,
                                   output_dir: str = "exports") -> str:
        """Export cover letter to a text file."""
        try:
            Path(output_dir).mkdir(exist_ok=True)

            # Create filename
            safe_title = "".join(c for c in job_title if c.isalnum() or c in "-_ ")
            safe_company = "".join(c for c in company if c.isalnum() or c in "-_ ")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_company}_{safe_title}_{timestamp}.txt"
            filepath = Path(output_dir) / filename

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Cover Letter for {job_title} at {company}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)

            logger.info(f"Cover letter exported to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting cover letter: {e}")
            return ""

    @staticmethod
    def export_to_json(data: Dict[str, Any], filename: str = "export.json") -> str:
        """Export data to JSON file."""
        try:
            output_dir = Path("exports")
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Data exported to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return ""

    @staticmethod
    def export_jobs_to_csv(jobs: list, filename: str = "jobs_export.csv") -> str:
        """Export jobs to CSV file."""
        try:
            import csv
            output_dir = Path("exports")
            output_dir.mkdir(exist_ok=True)
            filepath = output_dir / filename

            if not jobs:
                logger.warning("No jobs to export")
                return ""

            # Extract keys from first job
            fieldnames = list(jobs[0].keys())

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs)

            logger.info(f"Jobs exported to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return ""


class ValidationManager:
    """Validates input data."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        import re
        pattern = r'^https?://'
        return re.match(pattern, url) is not None

    @staticmethod
    def validate_job_data(job_dict: Dict[str, Any]) -> tuple:
        """
        Validate job data.
        Returns: (is_valid, error_message)
        """
        required_fields = {'title', 'company', 'description', 'requirements', 'url'}
        missing_fields = required_fields - set(job_dict.keys())

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        if not job_dict['title'].strip():
            return False, "Job title cannot be empty"

        if not job_dict['company'].strip():
            return False, "Company name cannot be empty"

        if not ValidationManager.validate_url(job_dict['url']):
            return False, "Invalid URL format"

        return True, ""

    @staticmethod
    def validate_cv_data(cv_dict: Dict[str, Any]) -> tuple:
        """
        Validate CV data.
        Returns: (is_valid, error_message)
        """
        if not cv_dict:
            return False, "CV data is empty"

        if "personal_info" in cv_dict:
            personal = cv_dict["personal_info"]
            if not personal.get("full_name"):
                return False, "Full name is required in personal info"
            if not personal.get("email"):
                return False, "Email is required in personal info"
            if not ValidationManager.validate_email(personal["email"]):
                return False, f"Invalid email format: {personal['email']}"

        return True, ""


class FileManager:
    """Manages file operations."""

    @staticmethod
    def ensure_data_dir(dir_path: str = "data") -> Path:
        """Ensure data directory exists."""
        path = Path(dir_path)
        path.mkdir(exist_ok=True, parents=True)
        return path

    @staticmethod
    def ensure_exports_dir(dir_path: str = "exports") -> Path:
        """Ensure exports directory exists."""
        path = Path(dir_path)
        path.mkdir(exist_ok=True, parents=True)
        return path

    @staticmethod
    def read_file(filepath: str) -> Optional[str]:
        """Read file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return None
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return None

    @staticmethod
    def write_file(filepath: str, content: str) -> bool:
        """Write content to file."""
        try:
            Path(filepath).parent.mkdir(exist_ok=True, parents=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return False


class FormatterUtil:
    """Text formatting utilities."""

    @staticmethod
    def format_cover_letter_for_display(cover_letter: str, max_width: int = 80) -> str:
        """Format cover letter for terminal display."""
        lines = cover_letter.split('\n')
        formatted = []
        for line in lines:
            if len(line) > max_width:
                # Simple word wrapping
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) < max_width:
                        current_line += word + " "
                    else:
                        if current_line:
                            formatted.append(current_line.rstrip())
                        current_line = word + " "
                if current_line:
                    formatted.append(current_line.rstrip())
            else:
                formatted.append(line)
        return "\n".join(formatted)

    @staticmethod
    def format_job_preview(job: Dict[str, Any], truncate: int = 300) -> str:
        """Format job for preview display."""
        preview = []
        preview.append(f"Title: {job.get('title', 'N/A')}")
        preview.append(f"Company: {job.get('company', 'N/A')}")
        preview.append(f"Location: {job.get('location', 'N/A')}")

        desc = job.get('description', 'N/A')
        if len(desc) > truncate:
            preview.append(f"Description: {desc[:truncate]}...")
        else:
            preview.append(f"Description: {desc}")

        preview.append(f"URL: {job.get('url', 'N/A')}")
        if 'score' in job:
            preview.append(f"Match Score: {job['score']:.1f}%")

        return "\n".join(preview)

    @staticmethod
    def format_table(headers: list, rows: list, max_col_width: int = 30) -> str:
        """Format data as a table."""
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], min(len(str(cell)), max_col_width))

        # Format header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        separator = "-+-".join("-" * w for w in col_widths)

        # Format rows
        table_lines = [header_row, separator]
        for row in rows:
            row_str = " | ".join(str(c).ljust(w)[:w] for c, w in zip(row, col_widths))
            table_lines.append(row_str)

        return "\n".join(table_lines)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = "applyiq.log") -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_format)
        root_logger.addHandler(file_handler)

    logger.info(f"Logging configured at level: {logging.getLevelName(log_level)}")
