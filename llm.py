"""
LLM integration module.
Handles OpenAI and Anthropic Claude API calls for cover letter generation.
"""

import logging
import os
import time
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_cover_letter(self, cv_text: str, job_title: str, 
                            company_name: str, job_description: str) -> tuple:
        """Generate cover letter. Returns (content, summary_bullets)."""
        pass

    @abstractmethod
    def calculate_job_relevance(self, cv_text: str, job_description: str,
                               job_requirements: str) -> float:
        """Calculate LLM-based job relevance score."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4 / GPT-3.5-turbo provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        try:
            import openai
            openai.api_key = self.api_key
            self.client = openai
            logger.info(f"OpenAI provider initialized with model: {model}")
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    def generate_cover_letter(self, cv_text: str, job_title: str,
                            company_name: str, job_description: str) -> tuple:
        """Generate personalized cover letter using GPT."""
        try:
            prompt = self._build_cover_letter_prompt(cv_text, job_title, company_name, job_description)

            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cover letter writer. Write compelling, tailored cover letters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            cover_letter = response['choices'][0]['message']['content'].strip()

            # Extract bullet points summary
            bullets = self._extract_summary_bullets(cv_text, job_description)

            logger.info(f"Generated cover letter for {job_title} at {company_name}")
            return cover_letter, bullets

        except Exception as e:
            logger.error(f"Error generating cover letter with OpenAI: {e}")
            raise

    def calculate_job_relevance(self, cv_text: str, job_description: str,
                               job_requirements: str) -> float:
        """Calculate relevance score using GPT."""
        try:
            prompt = f"""
Based on the following CV and job description, rate how well the candidate matches this role.
Score from 0-100, where 100 means perfect match.

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}

JOB REQUIREMENTS:
{job_requirements}

Respond with ONLY a number between 0 and 100. No explanation.
"""

            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=10
            )

            score_text = response['choices'][0]['message']['content'].strip()
            score = float(score_text)
            score = max(0, min(100, score))  # Ensure 0-100 range

            logger.info(f"LLM relevance score calculated: {score}")
            return score

        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def _build_cover_letter_prompt(self, cv_text: str, job_title: str,
                                   company_name: str, job_description: str) -> str:
        """Build the prompt for cover letter generation."""
        return f"""
Write a professional cover letter based on this candidate's CV and job details.

CANDIDATE CV:
{cv_text}

JOB DETAILS:
- Title: {job_title}
- Company: {company_name}
- Description: {job_description}

REQUIREMENTS FOR THE COVER LETTER:
1. Professional and formal tone
2. 3-4 paragraphs
3. Highlight relevant skills from CV that match the job
4. Show enthusiasm for the role and company
5. Include a call to action
6. Keep it concise (under 250 words)

Write the cover letter directly without any preamble or explanation.
"""

    def _extract_summary_bullets(self, cv_text: str, job_description: str) -> List[str]:
        """Extract 'why I fit' bullet points."""
        try:
            prompt = f"""
Given this CV and job description, extract 3-4 key reasons why this person is a good fit.
Format as a bullet list with specific skills/experiences mentioned.

CV:
{cv_text}

JOB:
{job_description}

Provide exactly 3-4 bullet points. Format: "• [reason]"
"""

            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )

            bullets_text = response['choices'][0]['message']['content'].strip()
            bullets = [b.strip('•').strip() for b in bullets_text.split('\n') if b.strip()]
            return bullets[:4]

        except Exception as e:
            logger.error(f"Error extracting summary bullets: {e}")
            return []


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic provider initialized with model: {model}")
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

    def generate_cover_letter(self, cv_text: str, job_title: str,
                            company_name: str, job_description: str) -> tuple:
        """Generate personalized cover letter using Claude."""
        try:
            prompt = self._build_cover_letter_prompt(cv_text, job_title, company_name, job_description)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            cover_letter = message.content[0].text.strip()
            bullets = self._extract_summary_bullets(cv_text, job_description)

            logger.info(f"Generated cover letter for {job_title} at {company_name}")
            return cover_letter, bullets

        except Exception as e:
            logger.error(f"Error generating cover letter with Claude: {e}")
            raise

    def calculate_job_relevance(self, cv_text: str, job_description: str,
                               job_requirements: str) -> float:
        """Calculate relevance score using Claude."""
        try:
            prompt = f"""
Based on the following CV and job description, rate how well the candidate matches this role.
Score from 0-100, where 100 means perfect match.

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}

JOB REQUIREMENTS:
{job_requirements}

Respond with ONLY a number between 0 and 100. No explanation.
"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            score_text = message.content[0].text.strip()
            score = float(score_text)
            score = max(0, min(100, score))  # Ensure 0-100 range

            logger.info(f"LLM relevance score calculated: {score}")
            return score

        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def _build_cover_letter_prompt(self, cv_text: str, job_title: str,
                                   company_name: str, job_description: str) -> str:
        """Build the prompt for cover letter generation."""
        return f"""
Write a professional cover letter based on this candidate's CV and job details.

CANDIDATE CV:
{cv_text}

JOB DETAILS:
- Title: {job_title}
- Company: {company_name}
- Description: {job_description}

REQUIREMENTS FOR THE COVER LETTER:
1. Professional and formal tone
2. 3-4 paragraphs
3. Highlight relevant skills from CV that match the job
4. Show enthusiasm for the role and company
5. Include a call to action
6. Keep it concise (under 250 words)

Write the cover letter directly without any preamble or explanation.
"""

    def _extract_summary_bullets(self, cv_text: str, job_description: str) -> List[str]:
        """Extract 'why I fit' bullet points."""
        try:
            prompt = f"""
Given this CV and job description, extract 3-4 key reasons why this person is a good fit.
Format as a bullet list with specific skills/experiences mentioned.

CV:
{cv_text}

JOB:
{job_description}

Provide exactly 3-4 bullet points. Format: "• [reason]"
"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=250,
                messages=[{"role": "user", "content": prompt}]
            )

            bullets_text = message.content[0].text.strip()
            bullets = [b.strip('•').strip() for b in bullets_text.split('\n') if b.strip()]
            return bullets[:4]

        except Exception as e:
            logger.error(f"Error extracting summary bullets: {e}")
            return []


class LLMFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(provider: str = "openai", **kwargs) -> LLMProvider:
        """Create and return an LLM provider instance."""
        provider_lower = provider.lower()

        if provider_lower == "openai":
            return OpenAIProvider(**kwargs)
        elif provider_lower in ["anthropic", "claude"]:
            return AnthropicProvider(**kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: openai, anthropic")

    @staticmethod
    def get_default_provider() -> str:
        """Get default provider based on environment variables."""
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        else:
            raise ValueError("No LLM API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")


class CoverLetterGenerator:
    """High-level cover letter generation interface."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.rate_limit_delay = 2  # seconds between requests

    def generate(self, cv_text: str, job_title: str, company_name: str,
                job_description: str, include_bullets: bool = True) -> Dict[str, Any]:
        """
        Generate cover letter with error handling and retries.
        """
        try:
            logger.info(f"Generating cover letter for {job_title} at {company_name}")

            # Add rate limiting
            time.sleep(self.rate_limit_delay)

            cover_letter, bullets = self.llm.generate_cover_letter(
                cv_text, job_title, company_name, job_description
            )

            result = {
                "success": True,
                "cover_letter": cover_letter,
                "summary_bullets": bullets if include_bullets else None,
                "model": self.llm.model if hasattr(self.llm, 'model') else "unknown"
            }

            logger.info(f"Successfully generated cover letter ({len(cover_letter)} chars)")
            return result

        except Exception as e:
            logger.error(f"Failed to generate cover letter: {e}")
            return {
                "success": False,
                "error": str(e),
                "cover_letter": None,
                "summary_bullets": None
            }

    def calculate_relevance(self, cv_text: str, job_description: str,
                           job_requirements: str) -> float:
        """Calculate LLM-based job relevance score."""
        try:
            return self.llm.calculate_job_relevance(cv_text, job_description, job_requirements)
        except Exception as e:
            logger.error(f"Failed to calculate relevance: {e}")
            return 0.0
