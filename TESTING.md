# ApplyIQ Testing & Validation Guide

This guide helps you verify that ApplyIQ is working correctly and test all features end-to-end.

## Pre-Test Checklist

```bash
# 1. Verify all files exist
ls -la models.py db.py cv.py jobs.py scoring.py llm.py utils.py cli.py main.py

# 2. Check Python version
python --version
# Should be 3.8 or higher

# 3. Verify dependencies installed
pip list | grep -E "click|requests|feedparser|openai|anthropic"

# 4. Check environment setup
cat .env
# Should have at least one API key

# 5. Test basic import
python -c "import models; import db; print('✓ Imports OK')"
```

## Test Suite

### Test 1: Database Initialization

**Objective:** Verify database creates correctly

```bash
rm -f applyiq.db              # Clean start
python -c "from db import Database; db = Database(); print('✓ DB initialized')"
ls -la applyiq.db              # Should exist now
```

**Expected:** Database file created with all tables

### Test 2: CV Setup

**Objective:** Test CV creation and retrieval

```bash
# Create test data
python << 'EOF'
from db import Database
from cv import CVManager
from models import Person

db = Database("applyiq.db")
cv_mgr = CVManager(db)

# Add personal info
person = Person(
    full_name="Test Developer",
    email="test@example.com",
    phone="555-1234",
    location="San Francisco",
    linkedin_url="https://linkedin.com/in/test"
)
cv_mgr.setup_personal_info(person)

# Add skills
skills = {
    "languages": ["Python", "JavaScript", "Go"],
    "frameworks": ["Django", "React", "FastAPI"],
    "databases": ["PostgreSQL", "MongoDB"],
    "tools": ["Docker", "Kubernetes", "AWS"]
}
cv_mgr.add_skills(skills)

# Add experience
experience = [{
    "company": "TechCorp",
    "position": "Senior Developer",
    "start_date": "2021-01",
    "end_date": "Present",
    "description": "Built scalable systems",
    "technologies": ["Python", "Django", "PostgreSQL"]
}]
cv_mgr.add_experience(experience)

# Verify
full_cv = cv_mgr.get_full_cv()
print(f"✓ CV has {len(full_cv)} sections")
print(f"✓ Found {len(cv_mgr.extract_skills())} skills")
print(f"✓ CV export: {len(cv_mgr.export_cv_text())} chars")
EOF
```

**Expected:**
```
✓ CV has 3 sections
✓ Found 8 skills
✓ CV export: ~500+ chars
```

### Test 3: Job Import (JSON)

**Objective:** Import and store jobs from JSON

```bash
python << 'EOF'
from db import Database
from jobs import JobIngestionManager

# Import sample jobs
jobs = JobIngestionManager.import_from_json_file("examples/sample_jobs.json")
print(f"✓ Imported {len(jobs)} jobs")

# Add to database
db = Database("applyiq.db")
success, duplicates = db.add_jobs_batch(jobs)
print(f"✓ Saved {success} jobs ({duplicates} duplicates)")

# Verify retrieval
all_jobs = db.list_jobs(limit=5)
print(f"✓ Retrieved {len(all_jobs)} jobs")
for job in all_jobs[:2]:
    print(f"  - {job['title']} at {job['company']}")
EOF
```

**Expected:**
```
✓ Imported 5 jobs
✓ Saved 5 jobs (0 duplicates)
✓ Retrieved 5 jobs
  - Senior Python Developer at TechCorp
  - Machine Learning Engineer at DataAI
```

### Test 4: Job Scoring

**Objective:** Calculate job match scores

```bash
python << 'EOF'
from db import Database
from cv import CVManager
from scoring import JobScoringManager

db = Database("applyiq.db")
cv_mgr = CVManager(db)
score_mgr = JobScoringManager(cv_mgr)

# Get a job and score it
jobs = db.list_jobs(limit=1)
if jobs:
    job = jobs[0]
    score = score_mgr.calculate_job_score(
        job['job_id'],
        job['title'],
        job['description'],
        job['requirements']
    )
    print(f"✓ Scored job: {job['title']}")
    print(f"  Overall Score: {score.overall_score:.1f}%")
    print(f"  Keyword Match: {score.keyword_match_score:.1f}%")
    print(f"  Matched Skills: {', '.join(score.matched_skills[:3])}")
    print(f"  Missing Skills: {', '.join(score.missing_skills[:3])}")
EOF
```

**Expected:**
```
✓ Scored job: Senior Python Developer
  Overall Score: 75.0%
  Keyword Match: 75.0%
  Matched Skills: python, django, postgresql
  Missing Skills: kubernetes, cloud, microservices
```

### Test 5: Job Deduplication

**Objective:** Verify duplicate detection works

```bash
python << 'EOF'
from jobs import JobIngestionManager
from models import Job, JobSource

# Create test jobs
jobs = [
    Job(
        title="Python Dev",
        company="TechCorp",
        description="Build systems",
        requirements="Python",
        url="https://example.com/job1",
        source=JobSource.JSON_IMPORT
    ),
    Job(
        title="Python Dev",
        company="TechCorp",
        description="Build systems",
        requirements="Python",
        url="https://example.com/job1",  # Duplicate URL
        source=JobSource.JSON_IMPORT
    ),
    Job(
        title="Python Dev at TechCorp",
        company="TechCorp",
        description="Build systems",
        requirements="Python",
        url="https://example.com/job2",  # Different URL, same company+title
        source=JobSource.JSON_IMPORT
    )
]

deduplicated = JobIngestionManager.deduplicate_jobs(jobs)
print(f"✓ Deduplicated {len(jobs)} jobs → {len(deduplicated)} unique jobs")
EOF
```

**Expected:**
```
✓ Deduplicated 3 jobs → 2 unique jobs
```

### Test 6: Application Status Tracking

**Objective:** Track application workflow

```bash
python << 'EOF'
from db import Database
from models import ApplicationRecord, ApplicationStatus
from datetime import datetime

db = Database("applyiq.db")

# Get a job_id to track
jobs = db.list_jobs(limit=1)
if jobs:
    job_id = jobs[0]['job_id']
    
    # Create application record
    app = ApplicationRecord(
        job_id=job_id,
        status=ApplicationStatus.DRAFT
    )
    db.add_application_status(app)
    print(f"✓ Created application: {job_id} - DRAFT")
    
    # Update status
    app = ApplicationRecord(
        job_id=job_id,
        status=ApplicationStatus.APPLIED,
        applied_at=datetime.now(),
        notes="Email sent on Jan 15"
    )
    db.add_application_status(app)
    print(f"✓ Updated application: APPLIED")
    
    # Verify
    saved = db.get_application_status(job_id)
    print(f"✓ Status: {saved['status']}")
    print(f"  Notes: {saved['notes']}")
EOF
```

**Expected:**
```
✓ Created application: ... - DRAFT
✓ Updated application: APPLIED
✓ Status: applied
  Notes: Email sent on Jan 15
```

### Test 7: Statistics

**Objective:** Verify stats aggregation

```bash
python << 'EOF'
from db import Database

db = Database("applyiq.db")
stats = db.get_statistics()

print("✓ Database Statistics:")
print(f"  Total Jobs: {stats['total_jobs']}")
print(f"  Total Companies: {stats['total_companies']}")
print(f"  Jobs by Source: {stats['jobs_by_source']}")
print(f"  Cover Letters Generated: {stats['cover_letters_generated']}")
print(f"  Applications by Status: {stats['applications_by_status']}")
EOF
```

**Expected:**
```
✓ Database Statistics:
  Total Jobs: 5
  Total Companies: 5
  Jobs by Source: {'json': 5}
  Cover Letters Generated: 0
  Applications by Status: {'applied': 1, 'draft': 4}
```

### Test 8: Configuration Management

**Objective:** Test config and API key validation

```bash
python << 'EOF'
from utils import ConfigManager

config = ConfigManager()

# Check environment
env_status = config.validate_api_keys()
print("✓ API Key Status:")
for provider, available in env_status.items():
    status = "✓ Available" if available else "✗ Missing"
    print(f"  {provider.upper()}: {status}")

# Get config values
db_path = config.get('db_path')
print(f"✓ DB Path: {db_path}")
EOF
```

**Expected:**
```
✓ API Key Status:
  openai: ✓ Available
  anthropic: ✗ Missing
✓ DB Path: applyiq.db
```

### Test 9: File Validation

**Objective:** Test input validators

```bash
python << 'EOF'
from utils import ValidationManager

# Test email validation
print("✓ Email Validation:")
print(f"  valid@example.com: {ValidationManager.validate_email('valid@example.com')}")
print(f"  invalid: {ValidationManager.validate_email('invalid')}")

# Test URL validation
print("✓ URL Validation:")
print(f"  https://example.com: {ValidationManager.validate_url('https://example.com')}")
print(f"  example.com: {ValidationManager.validate_url('example.com')}")

# Test job validation
print("✓ Job Validation:")
valid_job = {
    "title": "Dev",
    "company": "Corp",
    "description": "Job desc",
    "requirements": "Skills",
    "url": "https://example.com"
}
is_valid, msg = ValidationManager.validate_job_data(valid_job)
print(f"  Valid job: {is_valid}")

invalid_job = {"title": "Dev"}
is_valid, msg = ValidationManager.validate_job_data(invalid_job)
print(f"  Invalid job: {not is_valid} - {msg}")
EOF
```

**Expected:**
```
✓ Email Validation:
  valid@example.com: True
  invalid: False
✓ URL Validation:
  https://example.com: True
  example.com: False
✓ Job Validation:
  Valid job: True
  Invalid job: True - Missing required fields: ...
```

### Test 10: CSV Import

**Objective:** Import jobs from CSV

```bash
python << 'EOF'
from jobs import JobIngestionManager

jobs = JobIngestionManager.import_from_csv_file("examples/sample_jobs.csv")
print(f"✓ Imported {len(jobs)} jobs from CSV")
if jobs:
    print(f"  First job: {jobs[0].title} at {jobs[0].company}")
EOF
```

**Expected:**
```
✓ Imported 5 jobs from CSV
  First job: Senior Go Developer at GoSystems
```

### Test 11: LLM Provider Initialization

**Objective:** Verify LLM providers can initialize

```bash
python << 'EOF'
from llm import LLMFactory
import os

# Check available providers
if os.getenv('OPENAI_API_KEY'):
    try:
        provider = LLMFactory.create_provider('openai')
        print(f"✓ OpenAI provider initialized")
    except Exception as e:
        print(f"✗ OpenAI error: {e}")

if os.getenv('ANTHROPIC_API_KEY'):
    try:
        provider = LLMFactory.create_provider('anthropic')
        print(f"✓ Anthropic provider initialized")
    except Exception as e:
        print(f"✗ Anthropic error: {e}")

# Get default provider
try:
    default = LLMFactory.get_default_provider()
    print(f"✓ Default provider: {default}")
except Exception as e:
    print(f"✗ No providers configured: {e}")
EOF
```

**Expected:**
```
✓ OpenAI provider initialized
✓ Default provider: openai
```

### Test 12: CLI Commands (Manual)

**Objective:** Test CLI interface interactively

```bash
# Help command
python main.py --help

# Config check
python main.py config check

# List jobs
python main.py jobs list --limit 5

# Stats
python main.py stats

# CV view
python main.py cv view
```

## Integration Test: Complete Workflow

**Objective:** Full end-to-end test

```bash
# 1. Clean start
rm -f applyiq.db applyiq.log

# 2. Setup CV
python main.py cv setup
# Follow prompts with sample data

# 3. Import jobs
python main.py jobs import-jobs json --file examples/sample_jobs.json

# 4. List jobs (should be scored)
python main.py jobs list --limit 5

# 5. View specific job
JOB_ID=$(python -c "from db import Database; db = Database(); jobs = db.list_jobs(limit=1); print(jobs[0]['job_id'])")
python main.py jobs view "$JOB_ID"

# 6. Generate cover letter (requires API key)
python main.py letters generate "$JOB_ID"

# 7. View statistics
python main.py stats
```

## Performance Testing

```bash
# Time job import
time python main.py jobs import-jobs json --file examples/sample_jobs.json

# Time scoring
time python -c "
from db import Database; from cv import CVManager; from scoring import JobScoringManager
db = Database()
cv = CVManager(db)
score = JobScoringManager(cv)
jobs = db.list_jobs(limit=100)
for j in jobs: score.calculate_job_score(j['job_id'], j['title'], j['description'], j['requirements'])
"

# Database size
du -h applyiq.db
```

## Stress Testing

```bash
# Import large batch
python << 'EOF'
from jobs import JobIngestionManager
import json

# Create 1000 test jobs
large_batch = []
for i in range(1000):
    large_batch.append({
        "title": f"Developer {i}",
        "company": f"Company {i % 10}",
        "description": f"Job description {i}",
        "requirements": f"Requirements {i}",
        "url": f"https://example.com/job/{i}"
    })

jobs = JobIngestionManager.import_from_json(json.dumps(large_batch))
print(f"✓ Created {len(jobs)} test jobs")
EOF
```

## Cleanup

```bash
# Remove test data
rm -f applyiq.db applyiq.log

# Remove generated files
rm -rf exports/

# Clean Python cache
find . -pycache -type d -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Troubleshooting Tests

**Test fails with "module not found":**
```bash
pip install -r requirements.txt
```

**Database locked:**
```bash
# Kill any running processes
killall python

# Remove lock file
rm -f applyiq.db-journal
```

**API key errors:**
```bash
# Verify .env file
cat .env

# Check environment is loaded
python -c "import os; print(os.getenv('OPENAI_API_KEY')[:10]+'...')"
```

**CLI commands fail:**
```bash
# Check Click is installed
pip install click>=8.1.0

# Test basic CLI
python main.py --help
```

## Success Criteriaß

All tests should output `✓` markers. If any test fails:

1. **Check error message** - Usually tells you what's wrong
2. **Check debug logs** - `tail -f applyiq.log`
3. **Verify dependencies** - `pip install -r requirements.txt`
4. **Check environment** - Verify `.env` has API keys
5. **Clean and retry** - Remove `applyiq.db` and start fresh

---

**All tests passing? You're ready to use ApplyIQ!** 🎉
