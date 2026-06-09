# ApplyIQ Project Structure

## Core Application Files

```
ApplyIQ-AI-Job-Assistant/
│
├── main.py                    # Entry point - run this: python main.py
├── cli.py                     # Click-based CLI commands
│
├── models.py                  # Data models with type hints
├── db.py                      # SQLite database layer
├── cv.py                      # CV management
├── jobs.py                    # Job ingestion from JSON/CSV/RSS
├── scoring.py                 # Job matching/ranking algorithm
├── llm.py                     # OpenAI & Anthropic integration
├── utils.py                   # Utilities: config, export, validation, logging
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template (copy to .env)
├── .gitignore                 # Git ignore patterns
│
├── README.md                  # Complete documentation
├── GETTING_STARTED.md         # Quick start guide (read this first!)
├── ARCHITECTURE.md            # Detailed architecture & design
│
├── examples/
│   ├── sample_jobs.json       # Sample job data in JSON format
│   └── sample_jobs.csv        # Sample job data in CSV format
│
├── exports/                   # Generated cover letters (created on first export)
├── data/                      # Data directory (created automatically)
└── applyiq.db                 # SQLite database (created on first run)
```

## File Descriptions

### Application Core

| File | Purpose | Key Classes/Functions |
|------|---------|---------------------|
| `main.py` | Entry point | `if __name__ == '__main__'` |
| `cli.py` | CLI interface | `@cli` groups: cv, jobs, letters, applications |
| `models.py` | Data structures | Job, CoverLetter, ApplicationRecord, JobScore, etc. |
| `db.py` | Database operations | Database class with CRUD methods |
| `cv.py` | CV management | CVManager - store, retrieve, export CV |
| `jobs.py` | Job ingestion | JobIngestionManager - parse JSON/CSV/RSS |
| `scoring.py` | Job matching | JobScoringManager - calculate relevance |
| `llm.py` | AI integration | OpenAIProvider, AnthropicProvider, CoverLetterGenerator |
| `utils.py` | Utilities | ConfigManager, ExportManager, ValidationManager, etc. |

### Configuration

| File | Purpose |
|------|---------|
| `requirements.txt` | List all Python dependencies |
| `.env.example` | Template for environment variables (API keys) |
| `.gitignore` | Files to exclude from git (databases, logs, .env, etc.) |

### Documentation

| File | Purpose | Read When |
|------|---------|-----------|
| `README.md` | Complete reference guide | Need full documentation |
| `GETTING_STARTED.md` | Quick start (5 minutes) | First time setup |
| `ARCHITECTURE.md` | Detailed system design | Contributing or extending |

### Examples

| File | Purpose | Usage |
|------|---------|-------|
| `examples/sample_jobs.json` | Sample jobs in JSON | `python main.py jobs import-jobs json --file examples/sample_jobs.json` |
| `examples/sample_jobs.csv` | Sample jobs in CSV | `python main.py jobs import-jobs csv --file examples/sample_jobs.csv` |

### Generated (Created at Runtime)

| Path | Contents | Notes |
|------|----------|-------|
| `applyiq.db` | SQLite database | Created on first run, stores everything |
| `applyiq.log` | Application logs | Debug information |
| `.env` | Your secrets | Copy from `.env.example`, add API keys |
| `exports/` | Exported cover letters | Text files of generated letters |
| `data/` | Imported data | Optional data storage |

## Quick Reference

### Run Commands

```bash
# Show help
python main.py --help

# Setup CV (interactive)
python main.py cv setup

# View CV
python main.py cv view

# Import jobs
python main.py jobs import-jobs json --file examples/sample_jobs.json
python main.py jobs import-jobs csv --file examples/sample_jobs.csv

# List jobs (sorted by match score)
python main.py jobs list --limit 10 --sort score

# View job details
python main.py jobs view <job_id>

# Generate cover letter (interactive review)
python main.py letters generate <job_id>

# View saved cover letter
python main.py letters view <job_id>

# Export cover letter to file
python main.py letters export <job_id>

# Track applications
python main.py applications list
python main.py applications update-status <job_id> applied

# View statistics
python main.py stats

# Check API configuration
python main.py config check
```

## Key Architecture Patterns

### Database Pattern
- Single `Database` class with connection management
- Each method opens/closes connection
- Row factory for dict-like access

### LLM Pattern
- Abstract `LLMProvider` base class
- Concrete implementations: `OpenAIProvider`, `AnthropicProvider`
- `LLMFactory` for provider creation
- `CoverLetterGenerator` as high-level API

### CLI Pattern
- Click CLI framework
- Command groups for organization
- Interactive prompts with validation
- Formatted output

### Utilities Pattern
- Static methods for stateless operations
- ConfigManager for settings
- ExportManager for file operations
- ValidationManager for input validation

## Type Hints Coverage

All modules use type hints:

```python
# models.py, cv.py, jobs.py
- Dataclasses with type annotations
- Enums for fixed values
- Optional[] for nullable fields

# db.py
- Dict[str, Any] for database rows
- List[Dict] for query results
- Tuple for return values

# llm.py
- Abstract methods with full signatures
- Generator functions for streaming

# cli.py
- Click type hints
- @click.pass_context for dependency injection
```

## Environment Variables

```
# Required (at least one)
OPENAI_API_KEY=sk_...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
DB_PATH=applyiq.db
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
ENABLE_LLM_SCORING=false
LOG_LEVEL=INFO
```

## Database Tables

```sql
cv (id, section_type, content, version, created_at, updated_at)
jobs (id, job_id, title, company, description, requirements, url, ...)
cover_letters (id, job_id, content, summary_bullets, generated_at, ...)
applications_status (id, job_id, status, applied_at, notes, ...)
job_scores (id, job_id, keyword_match_score, overall_score, ...)
```

## Development Notes

### Adding a New Command

1. Add function to appropriate group in `cli.py`
2. Use `@group.command()` decorator
3. Add `@click.argument()` and `@click.option()` as needed
4. Implement logic using existing modules
5. Provide formatted user feedback

### Adding a New Job Source

1. Add static method to `JobIngestionManager` in `jobs.py`
2. Return list of `Job` objects
3. Add command to `cli.py` jobs group
4. Handle errors gracefully
5. Test with sample data

### Adding a New LLM Provider

1. Create class extending `LLMProvider` in `llm.py`
2. Implement abstract methods
3. Add to `LLMFactory.create_provider()`
4. Test with sample cover letter generation
5. Update documentation

## Performance Considerations

- Database has indexes on frequently queried columns
- Batch operations for imports
- Rate limiting for API calls
- Deduplication with sets (O(1) lookup)

## Security Best Practices

✅ Do:
- Store API keys in `.env` only
- Add `.env` to `.gitignore`
- Validate all user input
- Use https for API calls
- Log errors only (not sensitive data)

❌ Don't:
- Commit `.env` to git
- Log API responses with sensitive data
- Store credentials in code
- Make unauthorized API calls
- Scrape protected websites

## Testing Checklist

- [ ] Setup CV successfully
- [ ] Import jobs from JSON
- [ ] Import jobs from CSV
- [ ] List and filter jobs
- [ ] Generate cover letter (requires API key)
- [ ] Save and export cover letter
- [ ] Track application status
- [ ] View statistics
- [ ] Check config with no API keys
- [ ] Handle API errors gracefully
- [ ] Export cover letter to file
- [ ] Deduplication works

---

**All set! Read GETTING_STARTED.md next to get running in 5 minutes.** 🚀
