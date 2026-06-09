"""
CLI interface for the AI Job Application Assistant.
Built with Click for a clean, intuitive command-line experience.
"""

import click
import json
import sys
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from db import Database
from cv import CVManager
from jobs import JobIngestionManager
from llm import LLMFactory, CoverLetterGenerator
from scoring import JobScoringManager
from models import ApplicationRecord, ApplicationStatus, CoverLetter
from utils import (
    ConfigManager, ExportManager, ValidationManager, FormatterUtil,
    FileManager, setup_logging
)

logger = logging.getLogger(__name__)


@click.group()
@click.option('--db', default='applyiq.db', help='Database path')
@click.option('--log-level', default='INFO', help='Logging level')
@click.pass_context
def cli(ctx, db, log_level):
    """ApplyIQ - AI Job Application Assistant"""
    setup_logging(log_level)
    ctx.ensure_object(dict)
    ctx.obj['db'] = Database(db)


# ==================== CV Management ====================

@cli.group()
def cv():
    """CV Management commands"""
    pass


@cv.command()
@click.pass_context
def setup(ctx):
    """Setup CV with personal information and skills"""
    db = ctx.obj['db']
    cv_manager = CVManager(db)

    click.echo("=== CV Setup ===\n")

    # Personal Info
    click.echo("Personal Information:")
    full_name = click.prompt("Full name", type=str)
    email = click.prompt("Email", type=str)

    if not ValidationManager.validate_email(email):
        click.echo(click.style("Invalid email format!", fg='red'))
        return

    phone = click.prompt("Phone (optional)", default="", type=str)
    location = click.prompt("Location (optional)", default="", type=str)
    linkedin = click.prompt("LinkedIn URL (optional)", default="", type=str)
    github = click.prompt("GitHub URL (optional)", default="", type=str)

    personal_info = {
        "full_name": full_name,
        "email": email,
        "phone": phone or None,
        "location": location or None,
        "linkedin_url": linkedin or None,
        "github_url": github or None
    }

    cv_manager.setup_personal_info(type('Person', (), personal_info)())

    # Skills
    click.echo("\nSkills (enter as comma-separated values):")
    languages = click.prompt("Programming Languages", default="", type=str)
    frameworks = click.prompt("Frameworks", default="", type=str)
    databases = click.prompt("Databases", default="", type=str)
    tools = click.prompt("Tools/DevOps", default="", type=str)

    skills = {
        "languages": [s.strip() for s in languages.split(',') if s.strip()],
        "frameworks": [s.strip() for s in frameworks.split(',') if s.strip()],
        "databases": [s.strip() for s in databases.split(',') if s.strip()],
        "tools": [s.strip() for s in tools.split(',') if s.strip()]
    }

    cv_manager.add_skills(skills)

    # Experience
    click.echo("\nExperience (enter one entry at a time, type 'done' when finished):")
    experiences = []
    while True:
        if experiences or click.confirm("Add experience?", default=True):
            company = click.prompt("Company", default="", type=str)
            if company.lower() == 'done':
                break
            if not company:
                continue

            position = click.prompt("Position")
            start_date = click.prompt("Start date (YYYY-MM)", type=str)
            end_date = click.prompt("End date (YYYY-MM or 'Present')", default="Present", type=str)
            description = click.prompt("Description (optional)", default="", type=str)
            tech = click.prompt("Technologies used (comma-separated, optional)", default="", type=str)

            exp = {
                "company": company,
                "position": position,
                "start_date": start_date,
                "end_date": end_date,
                "description": description or None,
                "technologies": [t.strip() for t in tech.split(',') if t.strip()] if tech else None
            }
            experiences.append(exp)
        else:
            break

    if experiences:
        cv_manager.add_experience(experiences)

    # Education
    click.echo("\nEducation (enter one entry at a time):")
    education = []
    while True:
        if education or click.confirm("Add education?", default=False):
            institution = click.prompt("Institution", default="", type=str)
            if not institution:
                break

            degree = click.prompt("Degree")
            field = click.prompt("Field of study")
            year = click.prompt("Graduation year", type=int)

            edu = {
                "institution": institution,
                "degree": degree,
                "field": field,
                "graduation_year": year
            }
            education.append(edu)
        else:
            break

    if education:
        cv_manager.add_education(education)

    click.echo(click.style("\n✓ CV setup complete!", fg='green'))


@cv.command()
@click.pass_context
def view(ctx):
    """View current CV"""
    db = ctx.obj['db']
    cv_manager = CVManager(db)

    cv_text = cv_manager.export_cv_text()
    if cv_text:
        click.echo(cv_text)
    else:
        click.echo(click.style("No CV data found. Run 'applyiq cv setup' first.", fg='yellow'))


# ==================== Jobs Management ====================

@cli.group()
def jobs():
    """Job Management commands"""
    pass


@jobs.command()
@click.argument('source', type=click.Choice(['json', 'csv', 'rss', 'manual']))
@click.option('--file', help='File path for JSON/CSV import')
@click.option('--url', help='RSS feed URL')
@click.pass_context
def import_jobs(ctx, source, file, url):
    """Import jobs from various sources"""
    db = ctx.obj['db']
    imported_jobs = []

    try:
        if source == 'json' and file:
            imported_jobs = JobIngestionManager.import_from_json_file(file)
        elif source == 'csv' and file:
            imported_jobs = JobIngestionManager.import_from_csv_file(file)
        elif source == 'rss' and url:
            feed_name = click.prompt("Feed name (optional)", default=url)
            imported_jobs = JobIngestionManager.import_from_rss_feed(url, feed_name)
        elif source == 'manual':
            title = click.prompt("Job title")
            company = click.prompt("Company name")
            description = click.prompt("Job description")
            requirements = click.prompt("Key requirements")
            job_url = click.prompt("Job URL")
            location = click.prompt("Location (optional)", default="", type=str)
            job_type = click.prompt("Job type - full-time/part-time/contract (optional)", default="", type=str)

            job = JobIngestionManager.import_manual_job(
                title, company, description, requirements, job_url,
                location=location or None, job_type=job_type or None
            )
            imported_jobs = [job]
        else:
            click.echo(click.style("Missing required option for this source type", fg='red'))
            return

        if not imported_jobs:
            click.echo(click.style("No jobs imported", fg='yellow'))
            return

        # Deduplicate
        imported_jobs = JobIngestionManager.deduplicate_jobs(imported_jobs)

        # Let user review before adding
        click.echo(f"\nFound {len(imported_jobs)} jobs. Preview:")
        for i, job in enumerate(imported_jobs[:5], 1):
            click.echo(f"\n[{i}] {job.title}")
            click.echo(f"    Company: {job.company}")
            click.echo(f"    URL: {job.url[:60]}...")

        if len(imported_jobs) > 5:
            click.echo(f"\n    ... and {len(imported_jobs) - 5} more")

        if click.confirm("\nImport these jobs?"):
            success, duplicates = db.add_jobs_batch(imported_jobs)
            click.echo(click.style(f"\n✓ Imported {success} jobs", fg='green'))
            if duplicates:
                click.echo(click.style(f"  (Skipped {duplicates} duplicates)", fg='yellow'))
        else:
            click.echo("Import cancelled")

    except Exception as e:
        click.echo(click.style(f"Error importing jobs: {e}", fg='red'))
        logger.error(f"Import error: {e}")


@jobs.command()
@click.option('--limit', default=10, help='Number of jobs to display')
@click.option('--offset', default=0, help='Offset for pagination')
@click.option('--company', help='Filter by company name')
@click.option('--sort', type=click.Choice(['score', 'date']), default='score')
@click.pass_context
def list(ctx, limit, offset, company, sort):
    """List jobs"""
    db = ctx.obj['db']
    cv_manager = CVManager(db)
    score_manager = JobScoringManager(cv_manager)

    jobs_list = db.list_jobs(limit=limit, offset=offset, company=company)

    if not jobs_list:
        click.echo(click.style("No jobs found", fg='yellow'))
        return

    # Score jobs if not already scored
    for job in jobs_list:
        if not job.get('overall_score'):
            score = score_manager.calculate_job_score(
                job['job_id'],
                job['title'],
                job['description'],
                job['requirements']
            )
            db.add_job_score(score)
            job['score'] = score.overall_score

    # Sort by score if requested
    if sort == 'score':
        jobs_list = sorted(jobs_list, key=lambda x: x.get('score', 0) if x.get('score') else 0, reverse=True)

    click.echo(f"\n{len(jobs_list)} Job(s) found:\n")

    for i, job in enumerate(jobs_list, 1):
        status = "✓" if i % 2 == 0 else "◆"
        clickable_id = job.get('job_id', str(i))
        score = job.get('score', 0)
        score_color = 'green' if score > 70 else 'yellow' if score > 50 else 'red'

        click.echo(f"{status} [{clickable_id}]")
        click.echo(f"  {job['title']} at {job['company']}")
        click.echo(f"  Score: {click.style(f'{score:.0f}%', fg=score_color)}")
        click.echo()

    total = db.count_jobs(company=company)
    if total > limit:
        click.echo(f"Showing {len(jobs_list)} of {total} jobs")


@jobs.command()
@click.argument('job_id')
@click.pass_context
def view(ctx, job_id):
    """View job details"""
    db = ctx.obj['db']

    job = db.get_job(job_id)
    if not job:
        click.echo(click.style(f"Job not found: {job_id}", fg='red'))
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"Title: {job['title']}")
    click.echo(f"Company: {job['company']}")
    click.echo(f"Location: {job.get('location', 'N/A')}")
    click.echo(f"Type: {job.get('job_type', 'N/A')}")
    click.echo(f"Salary: {job.get('salary', 'N/A')}")
    click.echo(f"URL: {job['url']}")
    click.echo(f"\n{'Description:':‾}")
    click.echo(job['description'])
    click.echo(f"\n{'Requirements:':‾}")
    click.echo(job['requirements'])
    click.echo(f"{'='*60}\n")

    # Show action options
    if click.confirm("Generate cover letter?"):
        ctx.invoke(generate_letter, job_id=job_id)


# ==================== Cover Letters ====================

@cli.group()
def letters():
    """Cover Letter Management commands"""
    pass


@letters.command()
@click.argument('job_id')
@click.option('--provider', type=click.Choice(['openai', 'anthropic']), help='LLM provider')
@click.pass_context
def generate(ctx, job_id, provider):
    """Generate cover letter for a job"""
    db = ctx.obj['db']
    cv_manager = CVManager(db)

    # Check if CV exists
    cv_text = cv_manager.export_cv_text()
    if not cv_text:
        click.echo(click.style("No CV found. Run 'applyiq cv setup' first.", fg='red'))
        return

    # Get job details
    job = db.get_job(job_id)
    if not job:
        click.echo(click.style(f"Job not found: {job_id}", fg='red'))
        return

    try:
        click.echo("Generating cover letter...")
        click.echo("(This may take a moment)")

        # Get or determine LLM provider
        if not provider:
            from utils import ConfigManager
            config = ConfigManager()
            provider = config.get('llm_provider', 'openai')

        # Initialize LLM
        llm = LLMFactory.create_provider(provider)
        generator = CoverLetterGenerator(llm)

        # Generate
        result = generator.generate(
            cv_text,
            job['title'],
            job['company'],
            job['description']
        )

        if result['success']:
            cover_letter = result['cover_letter']
            click.echo("\n" + "="*60)
            click.echo("GENERATED COVER LETTER")
            click.echo("="*60 + "\n")
            click.echo(FormatterUtil.format_cover_letter_for_display(cover_letter))
            click.echo("\n" + "="*60)

            # Show summary bullets
            if result['summary_bullets']:
                click.echo("\nWhy you fit:")
                for bullet in result['summary_bullets']:
                    click.echo(f"  • {bullet}")

            # Save to database
            if click.confirm("\nSave this cover letter?"):
                letter = CoverLetter(
                    job_id=job_id,
                    content=cover_letter,
                    summary_bullets=result['summary_bullets'],
                    model_used=result['model']
                )
                letter_id = db.add_cover_letter(letter)

                # Link to application
                app_status = db.get_application_status(job_id)
                if not app_status:
                    app_record = ApplicationRecord(
                        job_id=job_id,
                        status=ApplicationStatus.READY,
                        cover_letter_id=letter_id
                    )
                else:
                    from models import ApplicationStatus
                    app_record = ApplicationRecord(
                        job_id=job_id,
                        status=ApplicationStatus(app_status['status']),
                        cover_letter_id=letter_id
                    )

                db.add_application_status(app_record)
                click.echo(click.style("✓ Cover letter saved!", fg='green'))

                # Export option
                if click.confirm("Export to file?"):
                    path = ExportManager.export_cover_letter_to_file(
                        cover_letter, job['title'], job['company']
                    )
                    click.echo(f"Saved to: {path}")

        else:
            click.echo(click.style(f"Error generating cover letter: {result['error']}", fg='red'))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        logger.error(f"Generation error: {e}")


@letters.command()
@click.argument('job_id')
@click.pass_context
def view(ctx, job_id):
    """View saved cover letter"""
    db = ctx.obj['db']

    letter = db.get_cover_letter_by_job(job_id)
    if not letter:
        click.echo(click.style(f"No cover letter found for job {job_id}", fg='yellow'))
        return

    click.echo("\n" + "="*60)
    click.echo("COVER LETTER")
    click.echo("="*60 + "\n")
    click.echo(FormatterUtil.format_cover_letter_for_display(letter['content']))
    click.echo("\n" + "="*60)

    if letter.get('summary_bullets'):
        bullets = json.loads(letter['summary_bullets']) if isinstance(letter['summary_bullets'], str) else letter['summary_bullets']
        if bullets:
            click.echo("\nSummary:")
            for bullet in bullets:
                click.echo(f"  • {bullet}")


@letters.command()
@click.argument('job_id')
@click.pass_context
def export(ctx, job_id):
    """Export cover letter to file"""
    db = ctx.obj['db']

    letter = db.get_cover_letter_by_job(job_id)
    if not letter:
        click.echo(click.style(f"No cover letter found", fg='red'))
        return

    job = db.get_job(job_id)
    if not job:
        return

    path = ExportManager.export_cover_letter_to_file(
        letter['content'],
        job['title'],
        job['company']
    )
    click.echo(f"Exported to: {path}")


# ==================== Applications ====================

@cli.group()
def applications():
    """Application Status commands"""
    pass


@applications.command()
@click.option('--status', type=click.Choice(['draft', 'ready', 'applied', 'interview', 'rejected']), help='Filter by status')
@click.pass_context
def list(ctx, status):
    """List applications"""
    db = ctx.obj['db']

    apps = db.list_applications(status=status)
    if not apps:
        click.echo(click.style("No applications found", fg='yellow'))
        return

    click.echo(f"\n{len(apps)} Application(s):\n")

    for app in apps:
        status_color = {
            'draft': 'blue',
            'ready': 'yellow',
            'applied': 'cyan',
            'interview': 'green',
            'rejected': 'red'
        }.get(app['status'], 'white')

        click.echo(f"[{app['job_id']}] {app['title']} at {app['company']}")
        click.echo(f"  Status: {click.style(app['status'].upper(), fg=status_color)}")
        click.echo()


@applications.command()
@click.argument('job_id')
@click.argument('status_new', type=click.Choice(['draft', 'ready', 'applied', 'interview', 'rejected']))
@click.option('--notes', help='Add notes')
@click.pass_context
def update_status(ctx, job_id, status_new, notes):
    """Update application status"""
    db = ctx.obj['db']

    job = db.get_job(job_id)
    if not job:
        click.echo(click.style(f"Job not found: {job_id}", fg='red'))
        return

    old_app = db.get_application_status(job_id)
    old_status = old_app['status'] if old_app else 'draft'

    app_record = ApplicationRecord(
        job_id=job_id,
        status=ApplicationStatus(status_new),
        notes=notes,
        cover_letter_id=old_app['cover_letter_id'] if old_app else None,
        applied_at=datetime.now() if status_new == 'applied' else (old_app['applied_at'] if old_app else None)
    )

    db.add_application_status(app_record)
    click.echo(click.style(f"✓ Updated: {old_status} → {status_new}", fg='green'))

    if notes:
        click.echo(f"Notes: {notes}")


# ==================== Stats ====================

@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics"""
    db = ctx.obj['db']

    stats = db.get_statistics()

    click.echo("\n=== ApplyIQ Statistics ===\n")
    click.echo(f"Total Jobs: {stats.get('total_jobs', 0)}")
    click.echo(f"Total Companies: {stats.get('total_companies', 0)}")
    click.echo(f"Cover Letters Generated: {stats.get('cover_letters_generated', 0)}")

    if stats.get('jobs_by_source'):
        click.echo("\nJobs by Source:")
        for source, count in stats['jobs_by_source'].items():
            click.echo(f"  {source}: {count}")

    if stats.get('applications_by_status'):
        click.echo("\nApplications by Status:")
        for status, count in stats['applications_by_status'].items():
            click.echo(f"  {status}: {count}")


# ==================== Config ====================

@cli.group()
def config():
    """Configuration commands"""
    pass


@config.command()
@click.pass_context
def check(ctx):
    """Check API key configuration"""
    config_mgr = ConfigManager()
    keys = config_mgr.validate_api_keys()

    click.echo("\n=== API Key Status ===\n")
    for provider, available in keys.items():
        status = click.style("✓ Found", fg='green') if available else click.style("✗ Not found", fg='red')
        click.echo(f"{provider.upper()}: {status}")

    if not any(keys.values()):
        click.echo(click.style("\n⚠ No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY", fg='red'))


if __name__ == '__main__':
    cli(obj={})
