# ApplyIQ Architecture & Design

## System Overview

```
┌─────────────────────────────────────────────────┐
│           CLI Interface (main.py, cli.py)       │
│  Interactive commands for all operations       │
└──────────────────┬──────────────────────────────┘
                   │
        ┌─────────┬┴─────────┬─────────┐
        │         │          │         │
        ▼         ▼          ▼         ▼
    ┌───────┐ ┌────────┐ ┌──────┐ ┌───────┐
    │       │ │        │ │      │ │       │
    │ CV    │ │ Jobs   │ │ LLM  │ │Scoring│
    │       │ │        │ │      │ │       │
    └───┬───┘ └────┬───┘ └──┬───┘ └───┬───┘
        │          │        │         │
        └──────────┴────┬───┴────┬────┘
                        │        │
                        ▼        ▼
                    ┌──────────────────┐
                    │   SQLite DB      │
                    │  (applyiq.db)    │
                    └──────────────────┘
```

## Module Responsibilities

### `models.py` - Data Models
**Purpose:** Define all data structures with type hints

**Key Classes:**
- `Job` - Job listing
- `CoverLetter` - Generated cover letter
- `ApplicationRecord` - Application status tracking
- `JobScore` - Match scores
- `CVSection` - CV data sections
- `Person`, `Experience`, `Education`, `Project` - CV components

**Design Principles:**
- Dataclasses for type safety
- Enums for status/source types
- Type hints throughout
- `to_dict()` methods for serialization

### `db.py` - Database Layer
**Purpose:** All database operations (CRUD)

**Responsibilities:**
- Schema initialization
- Connection management
- CRUD for all entities
- Batch operations
- Queries with filters
- Statistics aggregation

**Architecture:**
- Single `Database` class
- Context manager pattern (connect/disconnect)
- Row factory for dict-like access
- Indexes for performance

**Key Methods:**
```python
Database()
  ├── init_db()
  ├── add_job(), add_jobs_batch()
  ├── list_jobs(), get_job()
  ├── add_cover_letter(), get_cover_letter_by_job()
  ├── add_application_status(), list_applications()
  ├── add_job_score(), get_top_jobs_by_score()
  └── get_statistics()
```

### `cv.py` - CV Management
**Purpose:** Store, retrieve, and export CV data

**Responsibilities:**
- Add CV sections (personal, skills, experience, etc.)
- Extract skills for matching
- Convert CV to plain text for LLM
- Manage versioning

**Design:**
- Works with `Database` instance
- Lazy loading of sections
- Skill extraction for job matching
- Text export for LLM context

**Key Methods:**
```python
CVManager()
  ├── setup_personal_info()
  ├── add_skills(), add_experience()
  ├── extract_skills()
  ├── extract_experience_text()
  └── export_cv_text()
```

### `jobs.py` - Job Ingestion
**Purpose:** Import jobs from multiple sources

**Supports:**
- JSON files/strings
- CSV files/strings
- RSS feeds
- Manual entry

**Responsibilities:**
- Parse various formats
- Validate job data
- Generate unique IDs
- Deduplicate jobs
- Extract metadata

**Design:**
- Static methods for flexibility
- No database coupling
- Format-specific parsing
- Deduplication logic

**Key Methods:**
```python
JobIngestionManager()
  ├── import_from_json()
  ├── import_from_csv()
  ├── import_from_rss_feed()
  ├── import_manual_job()
  └── deduplicate_jobs()
```

### `scoring.py` - Job Matching
**Purpose:** Score and rank jobs

**Algorithm:**
1. Extract skills from CV
2. Match against job description/requirements
3. Calculate keyword match percentage (0-100)
4. Add bonus factors (remote work, seniority, etc.)
5. Optional LLM-based scoring

**Scoring Formula:**
```
keyword_score = (matched_skills / total_cv_skills) * 100
bonus = remote_work_bonus + seniority_bonus
overall_score = min(100, keyword_score + bonus)
```

**Design:**
- Works with `CVManager` for skills extraction
- Uses regex for word boundary matching
- Tech keyword database for extraction
- Extensible bonus system

### `llm.py` - LLM Integration  
**Purpose:** AI-powered cover letter generation

**Providers:**
- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic Claude (Claude 3 family)

**Architecture:**
```
LLMProvider (ABC)
  ├── OpenAIProvider
  └── AnthropicProvider

CoverLetterGenerator (high-level API)
├── Uses LLMProvider
├── Adds rate limiting
└── Error handling/retries

LLMFactory (creation & selection)
```

**Key Features:**
- Abstract base class for providers
- Factory pattern for provider selection
- Rate limiting between requests
- Error handling with fallbacks
- Prompt engineering for quality output

**Methods:**
```python
LLMProvider
  ├── generate_cover_letter()
  └── calculate_job_relevance()

CoverLetterGenerator
  ├── generate() - with error handling
  └── calculate_relevance()
```

### `cli.py` - Command-Line Interface
**Purpose:** User-facing commands

**Command Groups:**
- `cv` - CV management
- `jobs` - Job operations
- `letters` - Cover letter management
- `applications` - Track applications
- `config` - Configuration

**Design:**
- Click for CLI framework
- Organized by domain (cv, jobs, letters)
- Interactive prompts with validation
- Formatted output
- Error messages with context

**Key Commands:**
```
applyiq cv setup/view
applyiq jobs import-jobs/list/view
applyiq letters generate/view/export
applyiq applications list/update-status
applyiq config check
applyiq stats
```

### `utils.py` - Utilities
**Purpose:** Cross-cutting concerns

**Components:**
- `ConfigManager` - Config file handling
- `ExportManager` - File exports
- `ValidationManager` - Input validation
- `FileManager` - File operations
- `FormatterUtil` - Text formatting
- `setup_logging()` - Logging configuration

**Design:**
- Static methods for utilities
- No state required
- Reusable across modules
- Single responsibility

## Data Flow Examples

### Workflow 1: Import and Score Jobs

```
User Input (JSON file)
  ↓
jobs.py: JobIngestionManager.import_from_json()
  ├─ Parse JSON
  ├─ Validate data
  └─ Create Job objects
  ↓
cli.py: Deduplication check
  ↓
User Confirmation
  ↓
db.py: Database.add_jobs_batch()
  ├─ Insert jobs
  └─ Handle duplicates
  ↓
scoring.py: JobScoringManager.calculate_job_score()
  ├─ Extract CV skills
  ├─ Match keywords
  ├─ Calculate score
  └─ Add bonuses
  ↓
db.py: Database.add_job_score()
  └─ Store scores
```

### Workflow 2: Generate Cover Letter

```
User requests: letters generate job_123
  ↓
cli.py: Get job from database
  └─ Validate exists
  ↓
cv.py: CVManager.export_cv_text()
  ├─ Load all CV sections
  └─ Format as text
  ↓
llm.py: CoverLetterGenerator.generate()
  ├─ Select provider (OpenAI/Claude)
  ├─ Rate limit wait
  ├─ Call LLM API
  └─ Parse response
  ↓
cli.py: Show results to user
cli.py: Preview formatting
  ↓
User Review
  ↓
If approved:
  ├─ db.py: Add cover letter
  ├─ db.py: Link to application
  └─ Export to file
```

## Database Schema

```sql
-- CV storage (versioned)
cv (
  id INTEGER PRIMARY KEY,
  section_type TEXT,
  content TEXT (JSON),
  version INTEGER
)

-- Jobs
jobs (
  id INTEGER PRIMARY KEY,
  job_id TEXT UNIQUE,
  title, company, description, requirements, url,
  location, job_type, salary, posted_date,
  source TEXT,
  source_metadata TEXT (JSON),
  added_at TIMESTAMP
)

-- Cover letters (linked to jobs)
cover_letters (
  id INTEGER PRIMARY KEY,
  job_id TEXT FOREIGN KEY,
  content TEXT,
  summary_bullets TEXT (JSON),
  generated_at TIMESTAMP,
  model_used TEXT,
  prompt_version INTEGER
)

-- Application tracking
applications_status (
  id INTEGER PRIMARY KEY,
  job_id TEXT UNIQUE FOREIGN KEY,
  status TEXT ENUM,
  applied_at TIMESTAMP,
  notes TEXT,
  cover_letter_id INTEGER FOREIGN KEY,
  created_at, updated_at TIMESTAMPS
)

-- Job scores
job_scores (
  id INTEGER PRIMARY KEY,
  job_id TEXT UNIQUE FOREIGN KEY,
  keyword_match_score REAL,
  llm_relevance_score REAL,
  overall_score REAL,
  matched_skills TEXT (JSON),
  missing_skills TEXT (JSON),
  calculated_at TIMESTAMP
)
```

## Error Handling Strategy

**Levels:**
1. **Input Validation** - models, utils, cli
2. **API Errors** - llm.py with retries
3. **Database Errors** - db.py with transaction rollback
4. **File I/O** - utils.py with fallbacks

**Principles:**
- Fail fast on invalid input
- Retry on transient API failures
- Log all errors
- Provide user-friendly messages
- Graceful degradation

## Security Considerations

**API Keys:**
- Stored only in `.env` (not in code)
- Loaded via `python-dotenv`
- Never logged

**Data Privacy:**
- All data stays local
- No external storage
- SQLite is file-based
- Easy to backup/delete

**Content Safety:**
- No web scraping
- No credential stealing
- No session hijacking
- All actions user-initiated

## Performance Optimizations

**Database:**
- Indexes on frequently queried columns
- Connection pooling via context managers
- Batch operations for imports

**LLM:**
- Rate limiting to prevent quota issues
- Caching of CV text
- Shared provider instances

**Deduplication:**
- URL-based primary matching
- Company+title fallback
- Set-based lookups (O(1))

## Scalability Considerations

**Current Limitations:**
- Single-user local application
- SQLite file-based (not enterprise)
- Runs synchronously

**Potential Improvements:**
- Async/await for API calls
- Background job processing
- Multiple database support
- Team collaboration features
- Cloud storage option

## Testing Strategy

**Unit Tests needed for:**
- Job parsing (JSON, CSV, RSS)
- Scoring algorithm
- CV extraction
- Data validation
- Export formatting

**Integration Tests:**
- Full workflows (import → score → generate)
- Database operations
- LLM provider switching

**Manual Tests:**
- CLI interface usability
- Error messages clarity
- Performance with large datasets
- API cost estimation

## Deployment Options

**Local Development:**
```bash
python main.py [command]
```

**Systemd Service** (Linux):
```ini
[Unit]
Description=ApplyIQ Job Assistant

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/main.py
```

**Docker:**
```dockerfile
FROM python:3.11
COPY . /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "main.py"]
```

## Configuration Hierarchy

1. Default values in `utils.py`
2. Config file (`config.json`) if exists
3. Environment variables (`.env`)
4. CLI options (highest priority)

```python
ConfigManager()
  ├─ Load defaults
  ├─ Merge config file
  ├─ Override with env vars
  └─ CLI arguments win
```

## Future Architecture Improvements

1. **Plugin System** - Custom job sources
2. **Template System** - Cover letter variations
3. **Analytics** - Success rates, applying patterns
4. **Notifications** - Email/slack updates
5. **Integration** - Calendar, email sync
6. **Mobile** - Mobile app for review
7. **Collaboration** - Share with coaches/mentors
