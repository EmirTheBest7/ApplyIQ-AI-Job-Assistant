# ApplyIQ - AI Job Application Assistant

> A production-ready system to manage your job search: store your CV, collect job listings from legal sources, generate personalized cover letters using LLMs, and track applications—all locally.

## Features

✨ **Key Capabilities:**
- 📋 **CV Management** - Store and version your CV in structured format
- 📊 **Job Ingestion** - Import jobs from JSON, CSV, RSS feeds, or manual entry
- 🤖 **AI Cover Letters** - Generate personalized cover letters using OpenAI GPT-4 or Anthropic Claude
- 🎯 **Job Matching** - Intelligent scoring based on skill overlap
- 💾 **Local Database** - All data stored in SQLite (private, no cloud)
- 🖥️ **CLI Interface** - Full-featured command-line tool
- ✅ **Human-in-the-loop** - Every action requires confirmation (no auto-submissions)

## Hard Constraints (Respected)

✗ **Do NOT:**
- Scrape prohibited websites (LinkedIn, Indeed without API access)
- Bypass authentication or automate login
- Auto-submit job applications
- Use data from unauthorized sources

✅ **DO:**
- Use official APIs only
- Require explicit user confirmation for all actions
- Support legal data sources (RSS, JSON, CSV, manual entry)

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Steps

```bash
# 1. Clone/navigate to the repository
cd ApplyIQ-AI-Job-Assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env

# 4. Add your API keys (at least one required)
# Edit .env with your OpenAI or Anthropic API keys
```

**Getting API Keys:**
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic Claude**: [https://console.anthropic.com/](https://console.anthropic.com/)

## Quick Start

### 1. Setup Your CV

```bash
python main.py cv setup
```

Interactive prompts for:
- Personal info (name, email, phone, location, social links)
- Skills (languages, frameworks, databases, tools)
- Experience (companies, positions, dates, descriptions)
- Education (degrees, institutions, graduation years)
- Projects (portfolio items)

### 2. Import Jobs

**From JSON:**
```bash
python main.py jobs import-jobs json --file jobs.json
```

**From CSV:**
```bash
python main.py jobs import-jobs csv --file jobs.csv
```

**From RSS Feed:**
```bash
python main.py jobs import-jobs rss --url "https://jobs.example.com/feed.xml"
```

**Manual entry:**
```bash
python main.py jobs import-jobs manual
```

### 3. Review & Score Jobs

```bash
python main.py jobs list --limit 10 --sort score
```

View full details:
```bash
python main.py jobs view job_123
```

### 4. Generate Cover Letters

```bash
python main.py letters generate job_123
```

The system will:
- Load your CV
- Analyze job description
- Generate personalized cover letter
- Show you for review
- Save only on your confirmation

### 5. Track Applications

```bash
python main.py applications update-status job_123 applied --notes "Email sent"
python main.py applications list
```

### 6. View Statistics

```bash
python main.py stats
```

## Data Format Examples

### JSON Import

```json
[
  {
    "title": "Senior Python Developer",
    "company": "TechCorp",
    "description": "We're looking for an experienced Python developer to join our team...",
    "requirements": "5+ years Python, Django, PostgreSQL, AWS, Docker",
    "url": "https://example.com/jobs/123",
    "location": "San Francisco, CA",
    "job_type": "full-time",
    "salary": "$150,000 - $200,000"
  }
]
```

### CSV Import

Required headers: `title`, `company`, `description`, `requirements`, `url`

Optional: `location`, `job_type`, `salary`, `posted_date`

```
title,company,description,requirements,url,location,job_type
Senior Python Developer,TechCorp,We're looking for...,5+ years Python,https://...,San Francisco,full-time
```

## CLI Commands Reference

### CV Management
```bash
python main.py cv setup               # Interactive setup
python main.py cv view                # Display current CV
```

### Jobs
```bash
python main.py jobs import-jobs json --file <path>       # Import JSON
python main.py jobs import-jobs csv --file <path>        # Import CSV
python main.py jobs import-jobs rss --url <url>          # Import RSS
python main.py jobs import-jobs manual                    # Manual entry
python main.py jobs list --limit 10 --sort score         # List jobs
python main.py jobs view <job_id>                         # View details
```

### Cover Letters
```bash
python main.py letters generate <job_id>      # Generate
python main.py letters view <job_id>          # View
python main.py letters export <job_id>        # Export to file
```

### Applications
```bash
python main.py applications list                    # All applications
python main.py applications list --status applied   # Filter by status
python main.py applications update-status <job_id> <status>  # Update
```

**Status options:** `draft`, `ready`, `applied`, `interview`, `rejected`

### Configuration
```bash
python main.py config check       # Check API keys
python main.py stats              # Show statistics
```

## Project Architecture

```
applyiq/
├── models.py          # Data classes (Job, CV, ApplicationRecord, etc.)
├── db.py              # SQLite database layer + CRUD
├── cv.py              # CV management and extraction
├── jobs.py            # Job ingestion (JSON, CSV, RSS)
├── scoring.py         # Job matching/ranking algorithm
├── llm.py             # LLM integration (OpenAI, Anthropic)
├── utils.py           # Config, export, validation, logging
├── cli.py             # Click-based CLI
├── main.py            # Entry point
├── requirements.txt   # Dependencies
└── .env.example       # Environment template
```

## Database Schema

**cv** - Versioned CV sections
- section_type (personal_info, skills, experience, education, projects)
- content (JSON)
- version

**jobs** - Job listings
- job_id, title, company, description, requirements, url
- location, job_type, salary, posted_date
- source (json, csv, rss, manual)
- added_at

**cover_letters** - Generated letters
- job_id, content, summary_bullets
- generated_at, model_used

**applications_status** - Application tracking
- job_id, status, applied_at, notes, cover_letter_id

**job_scores** - Match scores
- job_id, keyword_match_score, llm_relevance_score, overall_score
- matched_skills, missing_skills

## Job Matching Algorithm

**Scoring (0-100):**

1. **Keyword Matching** (primary)
   - Extracts your CV skills
   - Matches against job description
   - Calculates overlap percentage

2. **Bonus Factors** (+5-10)
   - Seniority level match
   - Remote/hybrid work

3. **Optional LLM Scoring**
   - Claude/GPT rates job fit
   - Weights combined score

Jobs sorted by score (highest first)

## Cover Letter Generation

**How it works:**

1. Loads your full CV from database
2. Reads job description + requirements
3. Sends to LLM (GPT-4 or Claude) with template
4. Generates personalized letter (3-4 paragraphs)
5. Extracts "why I fit" bullet points
6. Shows for review
7. Saves only on confirmation

**Prompt focuses on:**
- Relevant skills from your CV
- Company/role enthusiasm
- Call to action
- Professional tone
- Concise length (~250 words)

## Usage Examples

### Complete Workflow

```bash
# 1. Setup CV
python main.py cv setup

# 2. Import jobs
python main.py jobs import-jobs csv --file ~/jobs.csv

# 3. List top matches
python main.py jobs list --limit 5

# 4. Generate cover letter
python main.py letters generate job_123

# 5. Mark applied
python main.py applications update-status job_123 applied

# 6. View stats
python main.py stats
```

### Batch Processing

```bash
# Import from multiple sources
python main.py jobs import-jobs json --file data/portal1.json
python main.py jobs import-jobs rss --url "https://feed.example.com/jobs"

# Export cover letters
for job_id in job_123 job_124 job_125; do
    python main.py letters export $job_id
done
```

## Advanced Features

**Automatic Deduplication**
- Matches by URL (primary)
- Falls back to company+title

**Filtering**
```bash
python main.py jobs list --company "Google"
```

**Rate Limiting**
- Automatic delays between API calls
- Respects provider rate limits

**Error Handling**
- Retry logic for failed calls
- Graceful degradation
- Input validation

## Security & Privacy

✅ **What we protect:**
- All data stored locally (SQLite)
- API keys in `.env` only (add to `.gitignore`)
- No data sent except to LLM APIs
- No automatic submissions
- No web scraping

## Cost Estimates

- **OpenAI GPT-4**: ~$0.06 per cover letter
- **Anthropic Claude 3 Sonnet**: ~$0.01 per letter
- Disable LLM scoring to reduce costs

## Troubleshooting

**"No API keys found"**
```bash
# Verify .env has keys set
cat .env | grep API_KEY

# Check environment loaded
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

**"Database locked"**
- Only one instance can run at a time
- Delete `applyiq.db-journal` if present (safe if app not running)

**"Cover letter generation fails"**
- Verify API key validity
- Check rate limits (wait 60 sec between requests)
- Try alternate provider: `letters generate <id> --provider anthropic`

**"Duplicate jobs skipped"**
- Normal behavior—prevents duplicate entries
- Check with `jobs list` to confirm import

## Logging

Logs saved to `applyiq.log`

```bash
# Run with debug logging
python main.py --log-level DEBUG jobs list
```

## Future Enhancements

Potential additions:
- PDF export for cover letters
- Email draft generation
- Interview prep reminders
- Analytics dashboard
- Template customization
- Team collaboration features

## Contributing

Feel free to extend this tool for your needs!

## License

See LICENSE file.

---

**Built for your job search. Happy applying! 🚀**