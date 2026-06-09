# ApplyIQ Getting Started Guide

This guide will help you get up and running with ApplyIQ in 5 minutes.

## Step 1: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

**What gets installed:**
- `click` - CLI framework
- `requests` - HTTP library for RSS feeds
- `feedparser` - RSS/Atom parsing
- `openai` - OpenAI API client
- `anthropic` - Anthropic Claude API client
- `python-dotenv` - Environment variable management

## Step 2: Setup API Keys (2 minutes)

### Option A: OpenAI (GPT-4)

1. Get your API key: https://platform.openai.com/api-keys
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add:
   ```
   OPENAI_API_KEY=sk_...your_key...
   ```

### Option B: Anthropic Claude

1. Get your API key: https://console.anthropic.com/
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add:
   ```
   ANTHROPIC_API_KEY=sk-ant-...your_key...
   ```

### Verify Setup

```bash
python main.py config check
```

You should see:
```
=== API Key Status ===

openai: ✓ Found         (or ✗ Not found)
anthropic: ✓ Found      (or ✗ Not found)
```

## Step 3: Setup Your CV (1 minute)

```bash
python main.py cv setup
```

Follow the interactive prompts:
- **Name & Contact**: Your full name, email, phone, location
- **Skills**: Programming languages, frameworks, databases, tools
- **Experience**: Previous jobs, positions, dates
- **Education**: Schools, degrees, graduation year (optional)
- **Projects**: Portfolio projects (optional)

### Example Input

```
Full name: John Developer
Email: john@example.com
Phone: 555-1234
Location: San Francisco, CA
LinkedIn URL: https://linkedin.com/in/johndeveloper
GitHub URL: https://github.com/johndeveloper

Programming Languages: Python,JavaScript,Go
Frameworks: Django,FastAPI,React,Next.js
Databases: PostgreSQL,MongoDB,Redis
Tools/DevOps: Docker,Kubernetes,AWS,Git

Add experience? y
Company: TechCorp
Position: Senior Python Developer
Start date (YYYY-MM): 2021-01
End date: Present
Technologies used: Django,PostgreSQL,Docker,AWS
done

Add education? y
Institution: State University
Degree: Bachelor of Science
Field of study: Computer Science
Graduation year: 2020
```

## Step 4: Import Sample Jobs (1 minute)

We've included sample job data to get you started.

### Option A: JSON Import

```bash
python main.py jobs import-jobs json --file examples/sample_jobs.json
```

### Option B: CSV Import

```bash
python main.py jobs import-jobs csv --file examples/sample_jobs.csv
```

Choose import when prompted.

## Step 5: Generate Your First Cover Letter (2 minutes)

1. List available jobs:
   ```bash
   python main.py jobs list
   ```

2. View a specific job:
   ```bash
   python main.py jobs view JOB_ID
   ```
   (Replace JOB_ID with one from the list)

3. Generate cover letter:
   ```bash
   python main.py letters generate JOB_ID
   ```

4. Review the generated letter and choose to save it

**Sample output:**
```
Title: Senior Python Developer
Company: TechCorp
[Cover letter content...]

Why you fit:
  • 5+ years Python experience, exactly matching requirements
  • Proficient with Django and FastAPI, key frameworks mentioned
  • Experience with microservices and scalable systems architecture
  • Strong AWS and Docker background aligned with tech stack
  
Save this cover letter? [Y/n]: y
✓ Cover letter saved!
Export to file? [Y/n]: y
Saved to: exports/TechCorp_Senior_Python_Developer_20240115_143022.txt
```

## Common Next Steps

### View Your CV

```bash
python main.py cv view
```

### List All Jobs

```bash
python main.py jobs list --limit 10
```

### Sort by Best Match

```bash
python main.py jobs list --sort score
```

### Track an Application

```bash
python main.py applications update-status JOB_ID applied --notes "Email sent to HR"
```

### View Application Status

```bash
python main.py applications list
```

### View Statistics

```bash
python main.py stats
```

## Tips for Best Results

### CV Quality
- Include specific skills and technologies
- List actual companies and positions
- Be specific about dates (YYYY-MM format)
- Add key projects and achievements

### Job Import
- Use RSS feeds when available
- Manually import from LinkedIn/Indeed (copy + paste)
- Deduplicate before saving
- Review jobs before marking applied

### Cover Letter Generation
- Always review generated letters
- Edit if needed before sending
- Save to exports for later reference
- Test with sample jobs first

### API Costs
- **OpenAI GPT-4**: ~$0.06/letter (accurate, more expensive)
- **Claude 3 Sonnet**: ~$0.01/letter (great quality, affordable)
- Start with Anthropic to save costs

## Troubleshooting

### "No API keys found"

Make sure `.env` file exists and has your API key:

```bash
# Check if .env exists
cat .env

# Verify format
grep OPENAI_API_KEY .env
# or
grep ANTHROPIC_API_KEY .env
```

### "ImportError: No module named 'click'"

Install dependencies again:

```bash
pip install -r requirements.txt
```

### "Error: Invalid value for '--file': File 'jobs.json' does not exist"

Check the file path:

```bash
# For sample files
ls examples/

# For your own files
ls jobs.json
```

### "Invalid email format"

Email must be valid format (user@domain.com)

### Cover letter won't generate

- Check API key is valid
- Verify rate limits (wait between requests)
- Try different provider if one fails
- Check logs: `grep ERROR applyiq.log`

## Next: Import Real Jobs

Once you're comfortable with the sample jobs:

### From your bookmarks/emails
1. Copy job listings (title, company, url, description, requirements)
2. Save as JSON or CSV
3. Import: `python main.py jobs import-jobs {format} --file your_file.{json|csv}`

### From RSS feeds
Find the job board RSS feed URL and:

```bash
python main.py jobs import-jobs rss --url "https://example.com/jobs/feed"
```

### Manual entry

```bash
python main.py jobs import-jobs manual
```

Then answer interactive prompts for each job.

## Advanced: Batch Processing

Generate multiple cover letters:

```bash
# List top 5 jobs
python main.py jobs list --limit 5

# Generate letter for each (write a script or do manually)
for job in job_1 job_2 job_3; do
    python main.py letters generate $job
done
```

Export all cover letters:

```bash
ls exports/*.txt
```

## Next Steps

1. **Import your real job search data** from job boards, emails, RSS feeds
2. **Generate cover letters** for your top matches
3. **Track applications** as you submit them
4. **Review statistics** to monitor your progress
5. **Adjust skills** in CV as you learn and apply

## Getting Help

**View command documentation:**
```bash
python main.py --help
python main.py cv --help
python main.py jobs --help
python main.py letters --help
```

**Check logs for errors:**
```bash
tail -f applyiq.log
```

**Review configuration:**
```bash
python main.py config check
```

## Happy Job Hunting! 🚀

You're all set! Start importing jobs and generating personalized cover letters.

Remember: ApplyIQ is your assistant—review everything before marking as applied!
