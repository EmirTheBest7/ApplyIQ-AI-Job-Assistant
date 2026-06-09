# ApplyIQ Quick Reference Card

Print this card for quick command reference!

---

## Installation (First Time)

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key
```

---

## Setup (One-Time)

```bash
# Setup your CV
python main.py cv setup

# Verify API keys are configured
python main.py config check
```

---

## Common Workflows

### Import & Review Jobs

```bash
# Import from JSON
python main.py jobs import-jobs json --file jobs.json

# Import from CSV
python main.py jobs import-jobs csv --file jobs.csv

# Import from RSS feed
python main.py jobs import-jobs rss --url "https://jobs.example.com/feed"

# List and sort by match score
python main.py jobs list --limit 10 --sort score

# View job details
python main.py jobs view <job_id>
```

### Generate Cover Letters

```bash
# Generate
python main.py letters generate <job_id>

# View saved
python main.py letters view <job_id>

# Export to file
python main.py letters export <job_id>
```

### Track Applications

```bash
# Mark as applied
python main.py applications update-status <job_id> applied

# Add notes
python main.py applications update-status <job_id> applied --notes "Email sent"

# List all
python main.py applications list

# Filter by status
python main.py applications list --status applied
```

### Get Insights

```bash
# Statistics
python main.py stats

# View your CV
python main.py cv view
```

---

## Status Values

```
draft      → Working on it
ready      → Cover letter ready to submit
applied    → Submitted
interview  → Got interview
rejected   → Did not advance
```

---

## Common Troubleshooting

```bash
# Check API keys
python main.py config check

# View logs
tail -f applyiq.log

# Reset database
rm applyiq.db  # ⚠️ WARNING: Deletes all data

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

---

## File Locations

```
~/.env                 API keys (SECRET!)
applyiq.db            Database (backup regularly!)
applyiq.log           Debug logs
exports/              Generated cover letters
examples/             Sample job data
```

---

## Tips & Tricks

✅ **Do:**
- Review ALL generated cover letters
- Keep CV updated with latest skills
- Use RSS feeds for job import
- Export cover letters for records
- Check statistics monthly

❌ **Don't:**
- Skip review of cover letters
- Scrape protected websites
- Share your .env file
- Auto-submit applications
- Delete applyiq.db without backup

---

## Example Session

```bash
# 1. Setup
python main.py cv setup

# 2. Import
python main.py jobs import-jobs json --file myjobs.json

# 3. Review
python main.py jobs list --limit 5

# 4. Generate
for job in job_1 job_2 job_3; do
    python main.py letters generate $job
done

# 5. Track
python main.py applications update-status job_1 applied

# 6. Monitor
python main.py stats
```

---

## API Cost Estimate

| Provider | Cost/Letter | Status |
|----------|------------|--------|
| OpenAi GPT-4 | ~$0.06 | Accurate |
| Claude 3 Sonnet | ~$0.01 | Great value |
| Claude 3 Opus | ~$0.02 | High quality |
| GPT-3.5 Turbo | ~$0.005 | Budget option |

---

## Support

- 📖 Full docs: `README.md`
- 🚀 Quick start: `GETTING_STARTED.md`
- 🏗️ Architecture: `ARCHITECTURE.md`
- ✅ Testing: `TESTING.md`
- 📋 Structure: `PROJECT_STRUCTURE.md`

---

**Happy job hunting! 🎉**
