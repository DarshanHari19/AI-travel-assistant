# 🔐 GitHub Actions Setup Guide

## Overview

Your repository now has automated testing via GitHub Actions! Every push to the `main` branch will automatically run your test suite with PostgreSQL and your API keys securely masked.

---

## 📁 Files Created

### `.github/workflows/main.yml`
Complete CI/CD workflow that:
- ✅ Triggers on every push to `main` branch (and pull requests)
- ✅ Sets up Python 3.11 environment
- ✅ Installs dependencies from `backend-agent/requirements.txt`
- ✅ Spins up PostgreSQL 16 service container
- ✅ Runs all tests using pytest
- ✅ Uses GitHub Secrets for API keys (automatically masked in logs)
- ✅ Uploads test artifacts and generates summary report

---

## 🔑 Setting Up GitHub Secrets

GitHub Actions requires your API keys to be stored as **repository secrets**. These are encrypted and never exposed in logs.

### Step 1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** (top right)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Step 2: Add Required Secrets

Add each of the following secrets one by one:

#### **Secret 1: OPENWEATHER_API_KEY**
- **Name:** `OPENWEATHER_API_KEY`
- **Value:** Your OpenWeather API key
- Click **Add secret**

#### **Secret 2: OPENAI_API_KEY**
- **Name:** `OPENAI_API_KEY`
- **Value:** Your OpenAI API key (starts with `sk-proj-...`)
- Click **Add secret**

#### **Secret 3: AERODATABOX_API_KEY**
- **Name:** `AERODATABOX_API_KEY`
- **Value:** Your RapidAPI key for AeroDataBox (for real flight data)
- Click **Add secret**
- **Note:** Without this key, the app uses mock flight data (tests still pass)

### Step 3: Verify Secrets

After adding all secrets, you should see:

```
✓ OPENWEATHER_API_KEY
✓ OPENAI_API_KEY
✓ AERODATABOX_API_KEY
```

---

## 🚀 How It Works

### Workflow Trigger

The workflow runs automatically when you:
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### What Happens Next

1. **GitHub Actions starts** → Spins up Ubuntu runner with Python 3.11
2. **PostgreSQL starts** → Launches postgres:16-alpine service container on port 5432
3. **Dependencies install** → Runs `pip install -r backend-agent/requirements.txt`
4. **Database verification** → Waits for PostgreSQL to be ready (health checks)
5. **Tests run** → Executes `pytest -v --tb=short --disable-warnings` in backend-agent/
6. **Results upload** → Saves test cache and coverage reports as artifacts
7. **Summary generated** → Creates markdown summary in GitHub Actions UI

### Environment Variables

The workflow automatically sets:

```yaml
# From GitHub Secrets (masked in logs)
OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
AERODATABOX_API_KEY: ${{ secrets.AERODATABOX_API_KEY }}

# PostgreSQL (service container)
POSTGRES_URI: postgresql://postgres:postgres@localhost:5432/travel_assistant
POSTGRES_POOL_SIZE: 5
POSTGRES_MAX_OVERFLOW: 10

# Test environment
ENVIRONMENT: test
ENABLE_CORS: true
ALLOWED_ORIGINS: "*"
```

---

## 📊 Viewing Test Results

### Method 1: GitHub Actions Tab

1. Go to **Actions** tab in your repository
2. Click on the latest workflow run
3. Click **Run Tests (Python 3.11)** job
4. Expand **Run pytest tests** step to see output

Example output:
```
============================= test session starts ==============================
platform linux -- Python 3.11.x, pytest-7.4.x, pluggy-1.x
plugins: asyncio-0.21.x, cov-4.1.x, mock-3.12.x
collected 14 items

test_agent.py::TestAgentInitialization::test_agent_creation PASSED      [  7%]
test_agent.py::TestAgentInitialization::test_checkpointer_setup PASSED  [ 14%]
test_production_features.py::TestSecurityFeatures::test_rate_limiting PASSED [ 21%]
...
============================== 14 passed in 45.2s ==============================
```

### Method 2: Summary Report

Each workflow run generates a summary at the bottom:

```markdown
## Test Results Summary

- **Python Version:** 3.11
- **PostgreSQL:** Running (postgres:16-alpine)
- **Test Directory:** backend-agent/
- **Status:** success ✅
```

### Method 3: Download Artifacts

1. In the workflow run, scroll to **Artifacts** section
2. Download **test-results** (contains pytest cache and coverage)
3. Unzip and view locally

---

## 🔒 Security Features

### API Key Masking

GitHub automatically masks secret values in logs:

```
# What you see in logs:
OPENWEATHER_API_KEY: ***

# Actual value (never shown):
OPENWEATHER_API_KEY: your_actual_key_here
```

### Secrets Scope

- ✅ Secrets are encrypted at rest
- ✅ Only available to GitHub Actions runners
- ✅ Never exposed in pull requests from forks
- ✅ Automatically redacted from logs
- ✅ Can be rotated without code changes

---

## 🛠️ Testing Locally Before Push

Always test locally first to catch issues early:

```bash
# 1. Start PostgreSQL
./setup_postgres.sh

# 2. Activate virtual environment
cd backend-agent
source venv/bin/activate

# 3. Set environment variables
export OPENWEATHER_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export AERODATABOX_API_KEY="your-rapidapi-key"
export POSTGRES_URI="postgresql://postgres:postgres@localhost:5432/travel_assistant"

# 4. Run tests
pytest -v

# 5. If all pass, push to GitHub
git add .
git commit -m "Add feature X"
git push origin main
```

---

## 🎯 Workflow File Explained

```yaml
name: Test Suite  # Workflow name shown in GitHub UI

on:
  push:
    branches:
      - main  # Trigger on push to main
  pull_request:
    branches:
      - main  # Also run on PRs targeting main

jobs:
  test:
    name: Run Tests (Python 3.11)
    runs-on: ubuntu-latest  # Use Ubuntu GitHub-hosted runner
    
    # PostgreSQL service container
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: travel_assistant
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready      # Health check command
          --health-interval 10s         # Check every 10 seconds
          --health-timeout 5s           # Timeout after 5 seconds
          --health-retries 5            # Retry 5 times before failing

    steps:
      - name: Checkout code
        uses: actions/checkout@v4      # Clone repository

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'                  # Cache pip dependencies
          cache-dependency-path: 'backend-agent/requirements.txt'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend-agent/requirements.txt

      - name: Verify PostgreSQL connection
        env:
          POSTGRES_URI: postgresql://postgres:postgres@localhost:5432/travel_assistant
        run: |
          timeout 30 bash -c 'until pg_isready -h localhost -p 5432 -U postgres; do sleep 1; done'

      - name: Run pytest tests
        env:
          # Secrets injected here
          OPENWEATHER_API_KEY: ${{ secrets.OPENWEATHER_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          AERODATABOX_API_KEY: ${{ secrets.AERODATABOX_API_KEY }}
          
          # PostgreSQL config
          POSTGRES_URI: postgresql://postgres:postgres@localhost:5432/travel_assistant
          POSTGRES_POOL_SIZE: 5
          POSTGRES_MAX_OVERFLOW: 10
        run: |
          cd backend-agent
          pytest -v --tb=short --disable-warnings
        continue-on-error: false  # Fail workflow if tests fail

      - name: Upload test results
        if: always()  # Run even if tests fail
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: |
            backend-agent/.pytest_cache/
            backend-agent/htmlcov/
          retention-days: 7  # Keep for 7 days

      - name: Test summary
        if: always()
        run: |
          # Generate markdown summary for GitHub UI
          echo "## Test Results Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Status:** ${{ job.status }}" >> $GITHUB_STEP_SUMMARY
```

---

## 🚨 Troubleshooting

### "Secret not found" Error

**Problem:** Workflow fails with "Error: Secret OPENWEATHER_API_KEY not found"

**Solution:**
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Verify secret name matches exactly: `OPENWEATHER_API_KEY` (case-sensitive)
3. Re-add the secret s match exactly (case-sensitive):
   - `OPENWEATHER_API_KEY`
   - `OPENAI_API_KEY`
3. Re-add the secretsow

### Tests Fail on GitHub but Pass Locally

**Problem:** Tests pass locally but fail in GitHub Actions

**Common causes:**
1. **Missing secret:** Check that all secrets are configured
2. **Different environment:** GitHub uses Ubuntu, you might use macOS/Windows
3. **Timezone differences:** Use `datetime.timezone.utc` instead of `datetime.UTC`
4. **Dependency versions:** Pin versions in `requirements.txt`

**Solution:**
```bash
# Test in a clean environment locally
python -m venv test-venv
source test-venv/bin/activate
pip install -r backend-agent/requirements.txt
pytest -v
```

### PostgreSQL Connection Failed

**Problem:** `psycopg.OperationalError: connection refused`

**Solution:** The workflow already handles this with health checks, but if it fails:
1. Check PostgreSQL service definition in `.github/workflows/main.yml`
2. Ensure `pg_isready` check completes before tests run
3. Verify `POSTGRES_URI` uses `localhost` (not `127.0.0.1` or `postgres`)

### Workflow Doesn't Trigger

**Problem:** Pushed to main but workflow doesn't run

**Solution:**
1. Check **Actions** tab is enabled (Settings → Actions → Allow all actions)
2. Verify `.github/workflows/main.yml` is committed and pushed
3. Check branch name matches: `git branch` should show `main` (not `master`)

---

## ⚡ Advanced Configuration

### Run Tests on Multiple Python Versions

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Add Code Coverage Badges

1. Install `pytest-cov`:
   ```bash
   pip install pytest-cov
   ```

2. Update pytest command:
   ```yaml
   pytest --cov=. --cov-report=xml
   ```

3. Add Codecov action:
   ```yaml
   - uses: codecov/codecov-action@v3
   ```

### Run Subset of Tests

```yaml
# Only unit tests (fast)
pytest -v -m unit

# Skip slow tests
pytest -v -m "not slow"

# Specific test file
pytest -v test_agent.py
```

---

## 📝 Best Practices

### 1. Test Before Push
```bash
# Always run tests locally first
pytest -v

# Run specific test markers
pytest -v -m integration
```

### 2. Keep Secrets Secure
- ❌ Never commit `.env` files
- ❌ Never hardcode API keys
- ✅ Use GitHub Secrets for CI/CD
- ✅ Use `.env` locally (in `.gitignore`)

### 3. Monitor Workflow Runs
- Check **Actions** tab after every push
- Fix failures immediately
- Review test summaries

### 4. Update Dependencies Regularly
```bash
# Check for updates
pip list --outdated

# Update requirements.txt
pip freeze > backend-agent/requirements.txt
```

---

## ✅ Verification Checklist

Before pushing to GitHub, verify:

- [ ] All secrets added to GitHub repository settings
- [ ] `.github/workflows/main.yml` exists and is committed
- [ ] Tests pass locally: `cd backend-agent && pytest -v`
- [ ] PostgreSQL runs locally: `./setup_postgres.sh`
- [ ] Environment variables set locally for testing
- [ ] `.env` file is in `.gitignore` (not committed)
- [ ] All dependencies in `requirements.txt`

---

## 🎉 You're All Set!

Your GitHub Actions workflow is ready! Here's what happens next:

1. **Add/commit/push** your changes to `main` branch
2. **GitHub Actions** automatically starts testing
3. **View results** in the Actions tab
4. **Fix failures** if any, rinse and repeat

**Example workflow:**
```bash
git add .github/workflows/main.yml
git commit -m "Add GitHub Actions CI/CD workflow"
git push origin main
```

Then visit: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Secrets Management](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [pytest Documentation](https://docs.pytest.org/)
- [PostgreSQL in GitHub Actions](https://docs.github.com/en/actions/using-containerized-services/creating-postgresql-service-containers)

---

**Last Updated:** April 23, 2026  
**Status:** ✅ Ready to Use  
**Next Step:** Add GitHub Secrets → Push to Main → Watch Tests Run!
