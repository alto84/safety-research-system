# Troubleshooting Guide

Common issues and solutions for the Safety Research System.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [API and Authentication](#api-and-authentication)
- [Database Issues](#database-issues)
- [LLM Integration](#llm-integration)
- [Agent Errors](#agent-errors)
- [Performance Issues](#performance-issues)
- [Testing Issues](#testing-issues)
- [Deployment Issues](#deployment-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms**:
```
ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies.
```

**Solutions**:
1. Use a fresh virtual environment:
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Update pip and setuptools:
```bash
pip install --upgrade pip setuptools wheel
```

3. Install dependencies one by one to identify conflict:
```bash
pip install anthropic
pip install requests
# ... etc
```

---

### Issue: Import errors after installation

**Symptoms**:
```python
ModuleNotFoundError: No module named 'agents'
```

**Solutions**:
1. Install in editable mode:
```bash
pip install -e .
```

2. Add project root to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/safety-research-system"
```

3. Run from project root directory

---

## API and Authentication

### Issue: "401 Unauthorized" error

**Symptoms**:
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid or missing API key"
  }
}
```

**Solutions**:
1. Check API key is set in environment:
```bash
echo $ANTHROPIC_API_KEY  # Should not be empty
```

2. Verify API key format:
```bash
# Claude keys start with "sk-ant-"
# OpenAI keys start with "sk-"
```

3. Check `.env` file exists and is loaded:
```bash
cat .env | grep API_KEY
```

4. Test API key directly:
```python
import anthropic
client = anthropic.Anthropic(api_key="your-key")
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
print(response)
```

---

### Issue: Rate limit exceeded

**Symptoms**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds."
  }
}
```

**Solutions**:
1. Add exponential backoff:
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        return wrapper
    return decorator
```

2. Reduce concurrent requests
3. Use reasoning cache to avoid duplicate LLM calls
4. Upgrade API plan for higher rate limits

---

## Database Issues

### Issue: Database connection error

**Symptoms**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions**:
1. Check database is running:
```bash
# PostgreSQL
sudo systemctl status postgresql

# Docker
docker ps | grep postgres
```

2. Verify connection string:
```bash
# Format: postgresql://user:password@host:port/database
echo $DATABASE_URL
```

3. Test connection:
```bash
psql -U postgres -h localhost -d safety_research
```

4. Check firewall rules allow database port (5432)

---

### Issue: Migration fails

**Symptoms**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Solutions**:
1. Check migration history:
```bash
python manage.py db history
```

2. Reset to known good state:
```bash
python manage.py db downgrade base
python manage.py db upgrade
```

3. Recreate database (CAUTION - data loss):
```bash
dropdb safety_research
createdb safety_research
python manage.py db upgrade
```

---

## LLM Integration

### Issue: Thought pipe execution fails

**Symptoms**:
```
Exception: LLM response validation failed
```

**Solutions**:
1. Check LLM response format:
```python
# Add logging to see raw response
logger.debug(f"Raw LLM response: {response}")
```

2. Verify prompt template is valid:
```python
# Test prompt formatting
context = {"task": "test"}
formatted = prompt.format(**context)
print(formatted)
```

3. Increase max_tokens if response truncated:
```python
response = llm_client.generate(
    prompt=prompt,
    max_tokens=4000  # Increase from default
)
```

4. Disable intelligent features temporarily:
```python
# In .env
ENABLE_INTELLIGENT_ROUTING=false
ENABLE_INTELLIGENT_RESOLUTION=false
```

---

### Issue: High LLM costs

**Symptoms**:
API bill is unexpectedly high

**Solutions**:
1. Enable reasoning cache:
```python
# Check cache hit rate
stats = reasoning_cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")

# Target: >70% hit rate
```

2. Reduce LLM usage:
```python
# Disable intelligent features for non-critical tasks
ENABLE_INTELLIGENT_COMPRESSION=false  # Use legacy compression
```

3. Monitor LLM calls:
```python
# Add logging
logger.info(f"LLM call: {prompt_name}, tokens: {token_count}, cost: ${cost}")
```

4. Use cheaper models for simple tasks:
```python
# Use Claude Haiku for simple prompts
model = "claude-3-haiku-20240307"
```

---

## Agent Errors

### Issue: Worker agent execution fails

**Symptoms**:
```
TaskExecutionError: Worker agent failed to execute task
```

**Solutions**:
1. Check agent logs:
```bash
grep "ERROR" logs/app.log | grep -i "literature_agent"
```

2. Test agent in isolation:
```python
from agents.workers.literature_agent import LiteratureAgent

agent = LiteratureAgent()
output = agent.execute({
    "query": "test query",
    "context": {}
})
print(output)
```

3. Verify input data format:
```python
# Check required fields
required = ["query", "context"]
for field in required:
    assert field in input_data, f"Missing {field}"
```

4. Check external API availability:
```python
# Test PubMed connection
import requests
response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cancer")
print(response.status_code)
```

---

### Issue: Audit validation fails repeatedly

**Symptoms**:
```
All tasks fail audit validation, even with corrections
```

**Solutions**:
1. Check audit criteria:
```python
# Review validation criteria
auditor = LiteratureAuditor()
print(auditor.validation_criteria)
```

2. Test audit in isolation:
```python
result = auditor.validate(
    task_input={"query": "test"},
    task_output=sample_output
)
print(result["issues"])
```

3. Temporarily relax validation:
```python
# In audit checklist, change severity
# From: severity: "critical"
# To:   severity: "warning"
```

4. Check for systematic issues:
```python
# Analyze common failure patterns
issues = [i["category"] for i in audit_result.issues]
from collections import Counter
print(Counter(issues))
```

---

### Issue: Fabrication detection false positives

**Symptoms**:
Real sources flagged as fabricated

**Solutions**:
1. Check PMID format:
```python
# PMIDs must be 1-8 digits, non-sequential
# Valid: 38238097
# Invalid: 12345678 (sequential)
```

2. Verify URL accessibility:
```bash
curl -I https://pubmed.ncbi.nlm.nih.gov/38238097/
# Should return 200 OK
```

3. Check source format:
```python
source = {
    "title": "Actual study title",  # Not "Example Study"
    "authors": "Smith J, Jones K",  # Not "Smith et al."
    "pmid": "38238097",  # Not sequential
    "url": "https://pubmed.ncbi.nlm.nih.gov/38238097/"
}
```

4. Review detection patterns:
```python
# See agents/auditors/literature_auditor.py
# Patterns for fake PMIDs, titles, authors
```

---

## Performance Issues

### Issue: Slow case processing

**Symptoms**:
Cases take >30 minutes to complete

**Solutions**:
1. Check task execution times:
```python
# Add timing
import time
start = time.time()
output = worker.execute(input_data)
duration = time.time() - start
logger.info(f"Task took {duration:.1f}s")
```

2. Enable parallel execution:
```python
# In config
MAX_CONCURRENT_TASKS = 10  # Increase from 1
```

3. Profile code:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
orchestrator.process_case(case)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

4. Check database query performance:
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries >1s

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

### Issue: High memory usage

**Symptoms**:
System runs out of memory

**Solutions**:
1. Enable context compression:
```python
ENABLE_INTELLIGENT_COMPRESSION = true
```

2. Reduce worker pool size:
```python
MAX_CONCURRENT_TASKS = 5  # Reduce from 20
```

3. Monitor memory:
```python
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
logger.info(f"Memory usage: {memory_mb:.1f} MB")
```

4. Clear caches periodically:
```python
# Clear reasoning cache
reasoning_cache.clear()

# Clear compression cache
context_compressor.compression_stats.clear()
```

---

## Testing Issues

### Issue: Tests fail with "fixture not found"

**Symptoms**:
```
pytest.fixtures.FixtureNotFoundError: fixture 'task_executor' not found
```

**Solutions**:
1. Check `conftest.py` exists:
```bash
ls tests/conftest.py
```

2. Add fixture to conftest.py:
```python
import pytest
from core.task_executor import TaskExecutor

@pytest.fixture
def task_executor():
    return TaskExecutor()
```

3. Import fixture properly:
```python
def test_something(task_executor):  # No need to import
    assert task_executor is not None
```

---

### Issue: Tests pass locally but fail in CI

**Symptoms**:
GitHub Actions tests fail, local tests pass

**Solutions**:
1. Check environment variables:
```yaml
# .github/workflows/test.yml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
```

2. Use test-specific configuration:
```python
# conftest.py
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    os.environ["ENABLE_INTELLIGENT_ROUTING"] = "false"
    # Disable LLM calls in tests
```

3. Mock external APIs:
```python
@pytest.fixture
def mock_llm(monkeypatch):
    def mock_generate(*args, **kwargs):
        return {"result": "mocked response"}

    monkeypatch.setattr("core.llm_integration.llm_client.generate", mock_generate)
```

---

## Deployment Issues

### Issue: Docker container fails to start

**Symptoms**:
```
docker: Error response from daemon: container exited with code 1
```

**Solutions**:
1. Check container logs:
```bash
docker logs <container-id>
```

2. Run interactively for debugging:
```bash
docker run -it --entrypoint /bin/bash your-image
```

3. Check environment variables:
```bash
docker exec <container-id> env | grep API_KEY
```

4. Verify file permissions:
```bash
# Ensure non-root user can access files
chown -R appuser:appuser /app
```

---

### Issue: Kubernetes pod crash loop

**Symptoms**:
```
kubectl get pods
NAME                    READY   STATUS             RESTARTS
safety-research-api     0/1     CrashLoopBackOff   5
```

**Solutions**:
1. Check pod logs:
```bash
kubectl logs safety-research-api
```

2. Describe pod for events:
```bash
kubectl describe pod safety-research-api
```

3. Check resource limits:
```yaml
resources:
  requests:
    memory: "2Gi"  # Increase if OOMKilled
    cpu: "1000m"
```

4. Verify secrets exist:
```bash
kubectl get secrets
kubectl describe secret safety-research-secrets
```

---

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Search GitHub issues
3. Review logs for error messages
4. Try reproducing in minimal environment

### How to Ask for Help

Include:
- Error message (full stack trace)
- Steps to reproduce
- Environment (OS, Python version, dependencies)
- Configuration (redact secrets)
- What you've already tried

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and discussions
- **Email**: support@safety-research-system.com
- **Slack**: Community Slack (request invite)

### Reporting Bugs

Use the bug report template:
```markdown
**Bug Description**
Clear description

**Steps to Reproduce**
1. Step 1
2. Step 2

**Expected vs Actual**
What should happen vs what happens

**Environment**
- OS: Ubuntu 22.04
- Python: 3.9.7
- Version: 1.0.0

**Logs**
```
Error logs here
```
```

---

## Diagnostic Commands

### System Health Check

```bash
# Check all components
python -m safety_research_system.diagnostics

# Or manually:
# 1. Database
psql -U postgres -c "SELECT 1"

# 2. Redis
redis-cli ping

# 3. LLM API
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'

# 4. Application
curl http://localhost:8000/health
```

### Log Analysis

```bash
# Recent errors
tail -100 logs/app.log | grep ERROR

# Count errors by type
grep ERROR logs/app.log | cut -d: -f3 | sort | uniq -c | sort -rn

# Task failures
grep "Task.*failed" logs/app.log

# Audit failures
grep "Audit.*failed" logs/app.log
```

---

**Last Updated**: November 1, 2025
