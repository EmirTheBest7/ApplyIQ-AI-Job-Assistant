# API Key Setup Guide

This guide walks you through getting and configuring API keys for ApplyIQ.

## Option 1: OpenAI (GPT-4)

### Step 1: Get API Key

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in with your account
3. Navigate to **API Keys** page: https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Copy the key (you'll only see it once!)
6. Store it safely

### Step 2: Add to .env

```bash
# Create .env from template
cp .env.example .env

# Edit .env
nano .env
# or
vim .env
# or open in your text editor
```

Add this line:
```
OPENAI_API_KEY=sk_...your_key_here...
```

### Step 3: Verify

```bash
python main.py config check
```

Should show:
```
openai: ✓ Found
```

### Costs

- GPT-4: ~$0.06 per cover letter (more accurate)
- GPT-3.5 Turbo: ~$0.005 per letter (budget option)

Change model in `.env`:
```
LLM_MODEL=gpt-4              # High quality (default)
LLM_MODEL=gpt-3.5-turbo      # Budget option
```

---

## Option 2: Anthropic Claude

### Step 1: Get API Key

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key
6. Store it safely

### Step 2: Add to .env

```bash
# Create .env from template
cp .env.example .env

# Edit .env
nano .env
```

Add this line:
```
ANTHROPIC_API_KEY=sk-ant-...your_key_here...
```

### Step 3: Verify

```bash
python main.py config check
```

Should show:
```
anthropic: ✓ Found
```

### Costs

- Claude 3 Sonnet: ~$0.01 per cover letter (best value)
- Claude 3 Opus: ~$0.02 per letter (highest quality)
- Claude 3 Haiku: ~$0.005 per letter (budget option)

Change model in `.env`:
```
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229      # Recommended
LLM_MODEL=claude-3-opus-20240229        # Premium
LLM_MODEL=claude-3-haiku-20240307       # Budget
```

---

## Which Should I Choose?

### Use OpenAI if:
- You want maximum accuracy
- You have budget for premium models
- You want GPT-4 performance

### Use Anthropic if:
- You want best value for money
- You prefer Claude's writing style
- You want lower costs (~$0.01/letter)

### My Recommendation
**Start with Anthropic Claude 3 Sonnet** - excellent quality at ~$0.01 per letter.

---

## File: .env Format

Here's what your complete `.env` should look like:

**Option A: Using OpenAI**
```env
OPENAI_API_KEY=sk_test1234567890abcdefghij
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

**Option B: Using Anthropic**
```env
ANTHROPIC_API_KEY=sk-ant-test1234567890abcdefghij
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```

**Full Example with all options**
```env
# Primary API Key (choose one)
OPENAI_API_KEY=sk_...your_key...
# ANTHROPIC_API_KEY=sk-ant-...your_key...

# Settings
DB_PATH=applyiq.db
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ENABLE_LLM_SCORING=false
AUTO_SCORE_JOBS=true
LOG_LEVEL=INFO
```

---

## Verification Checklist

After setting up .env:

```bash
# 1. Check file exists
ls -la .env
# Should show: -rw-r--r--  .env

# 2. Check it's readable
cat .env
# Should show your keys (be careful who sees this!)

# 3. Verify with ApplyIQ
python main.py config check
# Should show: ✓ Found for your provider

# 4. Test a generation (optional)
python main.py cv setup          # Setup CV first
python main.py jobs import-jobs json --file examples/sample_jobs.json
python main.py letters generate <job_id>
```

---

## Troubleshooting

### "No API keys found"

```bash
# Check .env exists
ls .env

# Check it has your key
grep -i "API_KEY" .env

# Make sure no extra spaces:
# CORRECT: OPENAI_API_KEY=sk_123...
# WRONG:   OPENAI_API_KEY = sk_123...    (spaces!)
# WRONG:   OPENAI_API_KEY=sk_123... #comment (inline comment!)
```

### "Invalid API key" or "401 Unauthorized"

1. Verify you copied the full key (check for truncation)
2. Make sure key hasn't expired (regenerate if needed)
3. Check correct key for provider (OpenAI key won't work with Anthropic)
4. Verify no extra spaces or newlines in .env

### "Key works but generation fails"

- Check your API account has billing set up
- Verify you have sufficient credits
- Check rate limits (wait between requests)
- Try with a different provider

### ".env changes not taking effect"

```bash
# Python might be caching the old value
# Restart your terminal or:
unset OPENAI_API_KEY
unset ANTHROPIC_API_KEY
# Then run applyiq again
```

---

## Security Best Practices

### ✅ DO:
- Keep .env file private (never share)
- Add .env to .gitignore (already done)
- Rotate keys regularly
- Use dedicated API keys for this app
- Monitor API usage for unauthorized access

### ❌ DON'T:
- Commit .env to git (it's in .gitignore)
- Share .env file with others
- Paste key in chat/email
- Use production keys for testing  
- Hardcode keys in Python files

### If You Accidentally Share Your Key:
1. **Immediately regenerate** the API key
2. Remove old key from your account
3. Update .env with new key
4. No need to panic—keys are regenerated instantly

---

## Cost Tracking

### Monitor Your Usage

**OpenAI:**
```bash
# Go to: https://platform.openai.com/account/billing/overview
# Check: Usage by model
```

**Anthropic:**
```bash
# Go to: https://console.anthropic.com/usage
# Check: Tokens used
```

### Estimate Costs

**Cover letter generation:**
```
Input: Your CV (~2,000 tokens) + job description (~1,000 tokens) = 3,000 tokens
Output: Cover letter (~300 tokens) + summary (~100 tokens) = 400 tokens
Total: ~3,400 tokens per letter

OpenAI (GPT-4):
  Input: $0.03 per 1K tokens → 3,000 × 0.03 = $0.09
  Output: $0.06 per 1K tokens → 400 × 0.06 = $0.024
  Total: ~$0.11 per letter (actual ~$0.06)

Anthropic (Claude 3 Sonnet):
  Input: $0.003 per 1K tokens → 3,000 × 0.003 = $0.009
  Output: $0.015 per 1K tokens → 400 × 0.015 = $0.006
  Total: ~$0.015 per letter (actual ~$0.01)
```

---

## Getting Help

### Test Your Setup

```python
# Create this test file: test_api.py
import os
from utils import ConfigManager

config = ConfigManager()
keys = config.validate_api_keys()

for provider, available in keys.items():
    status = "✓" if available else "✗"
    print(f"{provider}: {status}")

if not any(keys.values()):
    print("NO API KEYS FOUND - Check your .env file!")
else:
    print("API setup looks good!")
```

Run it:
```bash
python test_api.py
```

### Debug Output

If generation fails, check logs:
```bash
tail -f applyiq.log
```

Look for:
- `Invalid API key`
- `Rate limit exceeded`
- `Invalid request`

---

## Next Steps

Once .env is configured:

```bash
# 1. Verify setup
python main.py config check

# 2. Setup your CV
python main.py cv setup

# 3. Import sample jobs
python main.py jobs import-jobs json --file examples/sample_jobs.json

# 4. Generate your first cover letter!
python main.py letters generate <job_id>
```

---

## Support Resources

- 📖 Full docs: [README.md](README.md)
- 🚀 Quick start: [GETTING_STARTED.md](GETTING_STARTED.md)
- 🆘 Troubleshooting: [README.md - Troubleshooting](README.md#troubleshooting)
- ✅ Testing: [TESTING.md](TESTING.md)

---

**All set? Start generating cover letters!** 🎉
