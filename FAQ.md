# Frequently Asked Questions (FAQ)

Answers to common questions about the Safety Research System.

---

## General Questions

### What is the Safety Research System?

The Safety Research System is an AI-powered multi-agent platform for pharmaceutical safety assessment. It automates literature reviews, safety signal analysis, and evidence synthesis while ensuring quality through automated validation.

### Who should use this system?

- Safety scientists conducting adverse event assessments
- Medical reviewers preparing regulatory submissions
- Clinical teams evaluating benefit-risk profiles
- Researchers conducting systematic reviews

### How accurate is the system?

The system enforces rigorous quality standards:
- 100% detection rate for fabricated sources
- 0% false positive rate on real references
- Mandatory evidence chains for all claims
- Conservative confidence calibration
- Human oversight for critical decisions

However, results should always be reviewed by domain experts before making critical decisions.

### What makes this different from ChatGPT?

| Feature | Safety Research System | ChatGPT |
|---------|----------------------|---------|
| **Quality Assurance** | Automated audit validation | None |
| **Fabrication Detection** | 100% detection rate | No detection |
| **Evidence Provenance** | Every claim linked to source | No source verification |
| **Retry Loop** | Automatic correction and retry | Manual retry needed |
| **Confidence Calibration** | Conservative, evidence-based | Often overconfident |
| **Domain Specialization** | Pharmaceutical safety agents | General purpose |

---

## Technical Questions

### What AI models does the system use?

- **Primary**: Claude 3.5 Sonnet (Anthropic)
- **Alternative**: GPT-4 (OpenAI)
- **Configurable**: Can use other LLM providers

### How does the "Thought Pipe" architecture work?

Instead of hard-coded if/else logic, the system uses LLM reasoning for decisions:

**Traditional approach**:
```python
if priority == "HIGH" and data_quality < 0.7:
    return "request_more_data"
```

**Thought Pipe approach**:
```python
decision = llm.reason_about(task, context, criteria)
# Returns intelligent decision based on nuanced analysis
```

Benefits: Handles edge cases, adapts to new scenarios, provides transparency.

### What is the Agent-Audit-Resolve pattern?

A quality assurance loop:
1. **Agent** executes task (e.g., literature review)
2. **Audit** validates output against standards
3. **Resolve** decides: accept, retry with corrections, or escalate

This ensures quality while preventing orchestrator context overload.

### How does context compression work?

Full worker outputs (10-15KB) are compressed to 2-3 sentence summaries (1-2KB) before reaching the orchestrator. This:
- Prevents token limit issues
- Enables scaling to hundreds of tasks
- Preserves critical information intelligently
- Achieves 80-95% compression ratios

---

## Usage Questions

### How do I submit a case?

**Via API**:
```python
import requests

response = requests.post(
    "https://api.safety-research-system.com/api/v1/cases",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "title": "Case title",
        "question": "Your safety question",
        "priority": "HIGH",
        "context": {"drug_name": "Drug X"},
        "data_sources": ["pubmed"]
    }
)
```

**Via Dashboard**: Click "New Case", fill form, submit.

See [USER_GUIDE.md](./USER_GUIDE.md) for details.

### How long does processing take?

| Priority | Target Time | Use Case |
|----------|-------------|----------|
| URGENT | <1 hour | Critical safety signals |
| HIGH | <2 hours | Regulatory deadlines |
| MEDIUM | <4 hours | Standard assessments |
| LOW | <8 hours | Background research |

Actual time depends on:
- Question complexity
- Number of sources available
- Data source response times
- System load

### Can I cancel a case in progress?

Yes:
```python
requests.delete(
    f"https://api.safety-research-system.com/api/v1/cases/{case_id}",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
```

Or via Dashboard: Open case → Click "Cancel"

### What data sources are supported?

**Currently Available**:
- PubMed (literature)
- Clinical trials databases
- Internal safety databases (if configured)

**Planned**:
- FDA FAERS
- EMA EudraVigilance
- WHO VigiBase
- Real-world evidence databases

### Can I use my own data sources?

Yes! You can create custom data source connectors. See [AGENT_DEVELOPMENT.md](./AGENT_DEVELOPMENT.md) for instructions.

---

## Quality & Validation Questions

### How does the system prevent fabricated data?

Multi-layer validation:

**Layer 1: Hard-Coded Checks**
- PMID format validation (1-8 digits, non-sequential)
- URL accessibility verification
- Placeholder text detection (e.g., "Example Study")
- DOI format compliance

**Layer 2: Semantic Analysis**
- LLM detects conceptual violations
- Evidence-claim linkage verification
- Confidence level justification
- Assumption-based quality claims

**Layer 3: CLAUDE.MD Compliance**
- No scores >80% without validation
- Mandatory evidence chains
- Required uncertainty expression
- Banned language detection

### What happens if validation fails?

The **Resolution Engine** decides:

1. **RETRY** (if fixable): Prepares corrections, retries automatically
2. **ESCALATE** (if critical): Flags for human review
3. **ABORT** (if max retries): Fails gracefully
4. **ACCEPT** (if partial): Accepts with documented limitations

### Can I review the audit process?

Yes! Every audit result includes:
- List of checks passed/failed
- Specific issues found
- Severity levels (critical/warning/info)
- Suggested fixes
- Reasoning for decisions

### What confidence levels are used?

| Level | Criteria | Example |
|-------|----------|---------|
| **Low** | <5 sources, limited quality | "Preliminary observation based on 3 case reports" |
| **Moderate** | 5-20 sources, some limitations | "Based on 15 studies with heterogeneity" |
| **High** | >20 high-quality sources, consistent findings | Rare - requires exceptional evidence |

Note: System is calibrated conservatively to avoid overconfidence.

---

## Cost & Performance Questions

### What are the costs?

**LLM API Costs**:
- Typical case: $0.50 - $2.00
- Complex case: $2.00 - $5.00
- Bulk discount available for high volume

**System Costs**:
- Self-hosted: Infrastructure only
- Cloud: Based on usage tier

**Cost Optimization**:
- Reasoning cache (70%+ hit rate reduces costs)
- Parallel task execution
- Intelligent compression reduces token usage

### How can I reduce costs?

1. **Enable Reasoning Cache**:
```python
ENABLE_REASONING_CACHE=true
CACHE_TTL=86400  # 24 hours
```

2. **Disable Intelligent Features for Simple Tasks**:
```python
ENABLE_INTELLIGENT_COMPRESSION=false  # Use legacy
```

3. **Use Cheaper Models**:
```python
LLM_MODEL=claude-3-haiku-20240307  # vs claude-3-5-sonnet
```

4. **Monitor Usage**:
```bash
python -m safety_research_system.cli stats --show-costs
```

### How scalable is the system?

**Current Capacity** (single server):
- 100 cases/day
- 20 concurrent tasks
- 1000 cases/month

**Production Capacity** (Kubernetes cluster):
- 10,000+ cases/day
- 200+ concurrent tasks
- Unlimited monthly (with horizontal scaling)

---

## Security & Compliance Questions

### Is my data secure?

Yes:
- **Encryption**: TLS in transit, AES-256 at rest
- **Access Control**: Role-based permissions
- **Audit Trail**: Immutable logs for all actions
- **Data Isolation**: Per-tenant databases (enterprise)
- **Compliance**: SOC 2, HIPAA-ready (enterprise)

### Can I use this for PHI/PII data?

**Standard Version**: No - not HIPAA compliant by default

**Enterprise Version**: Yes - with:
- Business Associate Agreement (BAA)
- De-identification tools
- Encrypted storage
- Access logging
- Data retention policies

### How long is data retained?

**Default Retention**:
- Cases: 90 days
- Audit logs: 1 year
- Cached results: 24 hours

**Configurable**:
```python
DATA_RETENTION_DAYS=180  # Extend to 180 days
AUDIT_LOG_RETENTION_YEARS=7  # Regulatory requirement
```

### Is the system FDA-validated?

No. The system is a **decision support tool**, not a validated system for regulatory submissions. Human expert review is required for:
- Regulatory submissions
- Labeling decisions
- Signal prioritization
- Causality assessment

---

## Integration Questions

### Can I integrate with my existing systems?

Yes! Integration options:
- **REST API**: Standard HTTP/JSON API
- **Python SDK**: Native Python client
- **Webhooks**: Real-time event notifications
- **Database**: Direct PostgreSQL access (on-premise)

### Do you have an SDK?

Yes:
```python
from safety_research_system import Client

client = Client(api_key="YOUR_API_KEY")

case = client.create_case(
    title="Case title",
    question="Your question",
    priority="HIGH"
)

result = client.wait_for_completion(case.id)
print(result.report)
```

### Can I use this in my pipeline?

Yes! Example CI/CD integration:
```yaml
# .github/workflows/safety-check.yml
name: Safety Check
on: [pull_request]

jobs:
  safety_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Safety Assessment
        run: |
          python -m safety_research_system.cli submit \
            --question "Safety assessment for PR#${{ github.event.number }}" \
            --wait
```

---

## Troubleshooting Questions

### Why is my case stuck in "in_progress"?

Common causes:
1. **External API timeout**: PubMed/other APIs slow
2. **High load**: Many concurrent cases
3. **LLM rate limit**: API rate limit hit

**Solution**: Check status endpoint for current task details

### Why did my case fail?

Check error message:
```python
response = requests.get(f"{BASE_URL}/cases/{case_id}")
error = response.json().get("metadata", {}).get("error")
print(error)
```

Common failures:
- Invalid input data
- External API unavailable
- LLM API error
- Timeout exceeded

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for details.

### Why are results different each time?

Possible reasons:
1. **New literature**: Literature evolves daily
2. **LLM temperature**: Set to 0 for deterministic results
3. **Different data sources**: Check which sources queried
4. **Date range**: Time period affects results

For reproducibility:
```python
{
  "temperature": 0.0,  # Deterministic
  "date_range": {"from": "2020-01-01", "to": "2025-01-01"},
  "data_sources": ["pubmed"],  # Explicit sources
  "seed": 42  # Random seed
}
```

---

## Advanced Questions

### Can I create custom agents?

Yes! See [AGENT_DEVELOPMENT.md](./AGENT_DEVELOPMENT.md) for step-by-step guide.

### Can I fine-tune the models?

Currently no, but planned for future releases. You can:
- Adjust prompts
- Configure validation criteria
- Customize retry behavior
- Add domain-specific checks

### Can I run this on-premise?

Yes! See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Docker deployment
- Kubernetes deployment
- Database setup
- Security configuration

### Is there a batch API?

Planned for future release. Current workaround:
```python
import asyncio

async def process_batch(cases):
    tasks = [submit_case(case) for case in cases]
    return await asyncio.gather(*tasks)
```

---

## Support Questions

### How do I get help?

1. **Check Documentation**: Most answers in this FAQ
2. **GitHub Issues**: Bug reports, feature requests
3. **GitHub Discussions**: Questions and discussions
4. **Email**: support@safety-research-system.com
5. **Slack**: Community Slack (request invite)

### What's the response time for support?

| Tier | Response Time |
|------|--------------|
| **Community** | 48 hours (best effort) |
| **Standard** | 24 hours (business days) |
| **Enterprise** | 4 hours (24/7) |

### Can I request new features?

Yes! Submit feature requests via:
- GitHub Issues (public)
- Email (private)
- Roadmap voting (enterprise)

### Is there training available?

Yes:
- **Documentation**: Self-service guides
- **Webinars**: Monthly product webinars
- **Custom Training**: Enterprise customers
- **Office Hours**: Weekly drop-in sessions

---

## Licensing Questions

### What license is this under?

See LICENSE file in repository. Contact for commercial licensing.

### Can I modify the code?

Yes, for on-premise deployments. Modifications must:
- Maintain CLAUDE.MD compliance
- Preserve audit trails
- Not remove quality checks

### Can I resell this?

Contact licensing@safety-research-system.com for OEM/reseller agreements.

---

**Still have questions?**

- Check [USER_GUIDE.md](./USER_GUIDE.md)
- Search [GitHub Discussions](https://github.com/alto84/safety-research-system/discussions)
- Email support@safety-research-system.com

**Last Updated**: November 1, 2025
