# Claude AI Integration Options for the Predictive Safety Platform

**Document Type:** Technical Options Assessment
**Prepared for:** PSP Development Team / Safety Sciences
**Date:** 2026-02-08
**Status:** DRAFT — For Decision

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current System Architecture](#2-current-system-architecture)
3. [Option 1: Claude API Direct Integration](#3-option-1-claude-api-direct-integration)
4. [Option 2: Claude Agent SDK](#4-option-2-claude-agent-sdk)
5. [Option 3: MCP Server Integration](#5-option-3-mcp-server-integration)
6. [Option 4: Embedded Claude in Dashboard](#6-option-4-embedded-claude-in-dashboard)
7. [Option 5: Claude-Powered Report Generation](#7-option-5-claude-powered-report-generation)
8. [Pricing and Cost Estimates](#8-pricing-and-cost-estimates)
9. [Regulatory and Compliance Considerations](#9-regulatory-and-compliance-considerations)
10. [Comparison Matrix](#10-comparison-matrix)
11. [Recommended Implementation Path](#11-recommended-implementation-path)
12. [References](#12-references)

---

## 1. Executive Summary

The Predictive Safety Platform (PSP) currently provides deterministic biomarker scoring, Bayesian risk estimation, FAERS signal detection, and clinical safety plan generation through a FastAPI backend with a 14-tab vanilla JS dashboard. All outputs are numerical or tabular. There is no natural language interpretation, narrative generation, or interactive clinical reasoning capability.

Integrating Claude AI would add three capabilities that the current system cannot provide:

1. **Natural language interpretation** — translating statistical outputs (posterior distributions, credible intervals, disproportionality metrics) into clinical narratives that safety scientists and regulators can immediately act on.
2. **Knowledge synthesis** — combining the platform's quantitative outputs with literature context, regulatory precedent, and mechanistic understanding to produce grounded clinical reasoning.
3. **Interactive clinical decision support** — allowing users to ask questions about a patient's risk profile or a population's safety data and receive contextualized, referenced answers.

This document evaluates five integration approaches. They are not mutually exclusive; the recommended path implements them incrementally, starting with the lowest-risk, highest-value option and building toward a comprehensive AI-augmented safety platform.

**Key Constraints:**
- No patient-identifiable data (PHI/PII) leaves the system. All data is from published literature, public registries, and public APIs.
- Claude outputs are advisory. All clinical decisions remain with the safety scientist.
- The system already includes `anthropic>=0.40.0` in its dependencies (`pyproject.toml`), so the SDK is available.

---

## 2. Current System Architecture

```
+----------------------------------------------------------------------+
|                     CLINICAL DASHBOARD (index.html)                   |
|  14 tabs: Patient Scoring | Population Risk | FAERS | CDP | Summary  |
|  Vanilla JS, SVG charts, fetch() to API                              |
+----------------------------------------------------------------------+
        |                    |                    |
        v                    v                    v
+----------------------------------------------------------------------+
|                    FastAPI Backend (app.py)                           |
|  /api/v1/predict        /api/v1/population/*     /api/v1/signals/*   |
|  /api/v1/scores/*       /api/v1/cdp/*            /api/v1/therapies   |
|  WebSocket /ws/monitor/*                                             |
+----------------------------------------------------------------------+
        |                    |                    |
        v                    v                    v
+------------------+ +------------------+ +-------------------+
| Patient-Level    | | Population-Level | | Knowledge Graph   |
| Models           | | Models           | | & Registry        |
|                  | |                  | |                   |
| EASIX            | | Bayesian Beta-   | | KnowledgeGraph    |
| HScore           | |   Binomial       | | CRS Pathways      |
| CAR-HEMATOTOX    | | Clopper-Pearson  | | AE Taxonomy (21)  |
| Teachey 3-var    | | Wilson Score     | | Therapy Types (12)|
| Hay Classifier   | | DerSimonian-Laird| | Cell Therapy Reg. |
| Ensemble Runner  | | Empirical Bayes  | | Clinical Trials   |
|                  | | Kaplan-Meier     | | SLE Study Data    |
|                  | | Predictive Post. | |                   |
|                  | | Mitigation Model | |                   |
|                  | | FAERS Signal Det.| |                   |
+------------------+ +------------------+ +-------------------+
```

**Key API Endpoints (13+):**
- `POST /api/v1/predict` — Full ensemble patient prediction
- `POST /api/v1/predict/batch` — Batch patient prediction
- `GET /api/v1/scores/{model}` — Individual biomarker scores (EASIX, HScore, CAR-HEMATOTOX)
- `GET /api/v1/population/risk` — Baseline population risk summary
- `POST /api/v1/population/bayesian` — Custom Bayesian posterior
- `POST /api/v1/population/mitigations` — Correlated mitigation analysis
- `GET /api/v1/population/evidence-accrual` — Evidence accrual timeline
- `GET /api/v1/population/trials` — Clinical trial registry
- `GET /api/v1/signals/faers` — FAERS signal detection
- `GET /api/v1/cdp/monitoring-schedule` — Monitoring schedule
- `GET /api/v1/cdp/eligibility-criteria` — Inclusion/exclusion criteria
- `GET /api/v1/cdp/stopping-rules` — Bayesian stopping rules
- `GET /api/v1/cdp/sample-size` — Sample size considerations

---

## 3. Option 1: Claude API Direct Integration

### Overview

Add Claude API calls to the FastAPI backend to generate natural language interpretations alongside numerical outputs. Each existing endpoint gains an optional `?include_narrative=true` parameter that appends a Claude-generated clinical interpretation to the response.

### Architecture

```
+---------------------------+
|    Dashboard (Browser)    |
|  fetch(/api/v1/predict    |
|    ?include_narrative=true)|
+---------------------------+
             |
             v
+---------------------------+     +-------------------+
|    FastAPI Backend         |---->| Anthropic API     |
|                           |     | claude-sonnet-4.5 |
|  1. Run existing model    |     |                   |
|  2. Format result as JSON |     | System prompt:    |
|  3. Call Claude with      |<----| "You are a cell   |
|     structured prompt     |     |  therapy safety   |
|  4. Return combined       |     |  scientist..."    |
|     response              |     +-------------------+
+---------------------------+
```

### Implementation Complexity: **Low**

### Estimated Effort: **2-3 days**

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `anthropic` Python SDK | Already in `pyproject.toml` | Version >=0.40.0 |
| `ANTHROPIC_API_KEY` | Needed | Environment variable or `.env` file |
| Network access | Needed | Outbound HTTPS to `api.anthropic.com` |

### Code Sketch

```python
# src/api/claude_narratives.py
"""Claude-powered narrative generation for PSP API responses."""

from __future__ import annotations

import os
import logging
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None

SYSTEM_PROMPT = """You are a clinical safety scientist specializing in cell therapy
adverse events. You interpret quantitative risk assessment outputs for other safety
scientists and clinical teams.

Rules:
- Be precise. Cite specific numbers from the data provided.
- State uncertainty explicitly. If credible intervals are wide, say so.
- Never recommend specific clinical actions. Frame outputs as "the data suggest..."
- Reference published scoring systems by name and citation when relevant.
- Use ASTCT consensus grading terminology for CRS/ICANS.
- Output 2-4 paragraphs maximum. No bullet lists unless requested.
- If data is insufficient for a conclusion, say so explicitly.
"""


def get_client() -> anthropic.AsyncAnthropic:
    """Lazy-initialize the Anthropic async client."""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Claude narratives require an API key."
            )
        _client = anthropic.AsyncAnthropic(api_key=api_key)
    return _client


async def generate_prediction_narrative(
    prediction_data: dict[str, Any],
    patient_context: dict[str, Any] | None = None,
) -> str:
    """Generate a clinical narrative for a patient prediction result.

    Args:
        prediction_data: The PredictionResponse dict from the ensemble runner.
        patient_context: Optional additional context (therapy type, indication).

    Returns:
        A 2-4 paragraph clinical interpretation of the risk assessment.
    """
    client = get_client()

    user_prompt = f"""Interpret this patient risk assessment for a clinical team:

Patient ID: {prediction_data.get('patient_id', 'Unknown')}
Composite Risk Score: {prediction_data.get('composite_score', 'N/A')} (0-1 scale)
Overall Risk Level: {prediction_data.get('risk_level', 'Unknown')}
Data Completeness: {prediction_data.get('data_completeness', 'N/A')}
Models Run: {prediction_data.get('models_run', 0)}

Individual Model Scores:
{_format_scores(prediction_data.get('individual_scores', []))}

Contributing Factors:
{chr(10).join(prediction_data.get('contributing_factors', ['None identified']))}

Provide a clinical interpretation of these results, including:
1. What the composite score and individual model outputs indicate
2. Which factors are driving the risk assessment
3. What the data completeness means for confidence in this assessment
4. Any caveats about the scoring models used
"""

    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


async def generate_population_narrative(
    population_data: dict[str, Any],
    analysis_type: str = "bayesian_posterior",
) -> str:
    """Generate a narrative for population-level risk estimates."""
    client = get_client()

    prompts = {
        "bayesian_posterior": _build_bayesian_prompt,
        "mitigation_analysis": _build_mitigation_prompt,
        "evidence_accrual": _build_evidence_prompt,
        "faers_signals": _build_faers_prompt,
    }

    builder = prompts.get(analysis_type, _build_generic_prompt)
    user_prompt = builder(population_data)

    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


async def generate_safety_plan_narrative(
    plan_data: dict[str, Any],
    section: str = "monitoring_rationale",
) -> str:
    """Generate narrative sections for clinical safety plans."""
    client = get_client()

    user_prompt = f"""Write the '{section}' section for a clinical safety plan
for {plan_data.get('therapy_type', 'cell therapy')}.

Data provided:
{_format_plan_data(plan_data)}

Write in the style of an IND safety narrative. Use passive voice where
appropriate for regulatory documents. Include specific monitoring parameters
and their clinical rationale.
"""

    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


def _format_scores(scores: list[dict]) -> str:
    """Format individual model scores for the prompt."""
    if not scores:
        return "No individual scores available."
    lines = []
    for s in scores:
        name = s.get("model_name", "Unknown")
        score = s.get("score")
        risk = s.get("risk_level", "unknown")
        conf = s.get("confidence", 0)
        score_str = f"{score:.3f}" if score is not None else "N/A"
        lines.append(f"  - {name}: score={score_str}, risk={risk}, confidence={conf:.0%}")
    return "\n".join(lines)


def _format_plan_data(data: dict) -> str:
    """Format safety plan data for the prompt."""
    import json
    return json.dumps(data, indent=2, default=str)


def _build_bayesian_prompt(data: dict) -> str:
    est = data.get("estimate", {})
    return f"""Interpret this Bayesian posterior estimate for a clinical team:

Adverse Event: {est.get('adverse_event', 'Unknown')}
Prior: Beta({est.get('prior_alpha', '?')}, {est.get('prior_beta', '?')})
Posterior: Beta({est.get('posterior_alpha', '?')}, {est.get('posterior_beta', '?')})
Observed: {est.get('n_events', '?')} events in {est.get('n_patients', '?')} patients
Posterior Mean: {est.get('mean_pct', '?')}%
95% Credible Interval: [{est.get('ci_low_pct', '?')}%, {est.get('ci_high_pct', '?')}%]
CI Width: {est.get('ci_width_pct', '?')} percentage points

Explain what this means clinically, how the prior influenced the estimate,
and what the CI width implies about evidence sufficiency.
"""


def _build_mitigation_prompt(data: dict) -> str:
    return f"""Interpret this mitigation analysis for a clinical team:

Target AE: {data.get('target_ae', 'Unknown')}
Baseline Risk: {data.get('baseline_risk_pct', '?')}%
Mitigated Risk: {data.get('mitigated_risk_pct', '?')}%
Combined Relative Risk: {data.get('combined_rr', '?')}
Naive Multiplicative RR: {data.get('naive_multiplicative_rr', '?')}
Correction Factor: {data.get('correction_factor', '?')}
Mitigations Applied: {', '.join(data.get('mitigations_applied', []))}

Explain what the correction factor means (why correlated mitigations provide
less benefit than naive multiplication suggests), and the clinical implications
of the residual risk.
"""


def _build_evidence_prompt(data: dict) -> str:
    return f"""Interpret this evidence accrual analysis for a clinical team:

Current CRS CI Width: {data.get('current_ci_width_crs_pct', '?')}%
Projected CRS CI Width: {data.get('projected_ci_width_crs_pct', '?')}%
CI Narrowing: {data.get('ci_narrowing_pct', '?')}%
Number of Timeline Points: {len(data.get('timeline', []))}

Explain what the narrowing credible interval means for clinical decision-making,
and how much additional data is needed for regulatory-grade precision.
"""


def _build_faers_prompt(data: dict) -> str:
    signals = data.get("signals", [])
    strong = [s for s in signals if s.get("signal_strength") == "strong"]
    return f"""Interpret these FAERS pharmacovigilance signals for a clinical team:

Products Queried: {', '.join(data.get('products_queried', []))}
Total Reports: {data.get('total_reports', 0)}
Signals Detected: {data.get('signals_detected', 0)}
Strong Signals: {data.get('strong_signals', 0)}

Top signals by EBGM:
{_format_faers_signals(signals[:5])}

Explain what PRR, ROR, and EBGM metrics mean, which signals warrant further
investigation, and the limitations of spontaneous reporting data.
"""


def _format_faers_signals(signals: list[dict]) -> str:
    lines = []
    for s in signals:
        lines.append(
            f"  - {s.get('product', '?')} / {s.get('adverse_event', '?')}: "
            f"PRR={s.get('prr', '?'):.2f}, ROR={s.get('ror', '?'):.2f}, "
            f"EBGM={s.get('ebgm', '?'):.2f}, n={s.get('n_cases', '?')}"
        )
    return "\n".join(lines) if lines else "  No signals to display."


def _build_generic_prompt(data: dict) -> str:
    import json
    return f"""Interpret the following safety data for a clinical team:

{json.dumps(data, indent=2, default=str)}

Provide a clinical interpretation focusing on risk level, uncertainty,
and any factors that warrant attention.
"""
```

**Integration into existing endpoints (example for `/api/v1/predict`):**

```python
# In app.py — modify the predict endpoint

@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(
    request: PatientDataRequest,
    include_narrative: bool = Query(False, description="Include Claude AI narrative"),
) -> PredictionResponse:
    # ... existing prediction logic (unchanged) ...

    response = PredictionResponse(...)

    if include_narrative:
        try:
            from src.api.claude_narratives import generate_prediction_narrative
            narrative = await generate_prediction_narrative(response.model_dump())
            response.metadata["ai_narrative"] = narrative
            response.metadata["ai_model"] = "claude-sonnet-4-5"
            response.metadata["ai_disclaimer"] = (
                "AI-generated interpretation. Not a substitute for clinical judgment."
            )
        except Exception as exc:
            logger.warning("Claude narrative generation failed: %s", exc)
            response.metadata["ai_narrative_error"] = str(exc)

    return response
```

### Pros

- Minimal changes to existing codebase. Narrative is additive, not replacing anything.
- Graceful degradation: if Claude API is unavailable, existing functionality is unaffected.
- Uses Sonnet 4.5 at $3/$15 per MTok — cost-effective for narrative generation.
- Prompt caching can reduce costs significantly for repeated system prompts.
- Structured outputs can enforce response schema if needed.
- The `anthropic` SDK is already a declared dependency.

### Cons

- Adds latency (1-3 seconds per Claude call) to API responses.
- Requires outbound network access and an API key.
- Narratives are not deterministic — same inputs may produce slightly different outputs.
- No conversation memory; each call is independent.
- Clinical validation of generated narratives requires human review protocols.

---

## 4. Option 2: Claude Agent SDK

### Overview

Build autonomous Claude agents that can reason across the PSP's data, run multi-step analyses, and produce comprehensive safety reports without human prompting for each step. The Agent SDK (`claude-agent-sdk` on PyPI) provides the `query()` function that creates an agentic loop with tool access.

### Architecture

```
+-------------------------------------------------------------+
|                    Agent Orchestration Layer                  |
|                                                              |
|  SafetyMonitorAgent      ClinicalAdvisorAgent    ReportAgent |
|  - Polls FAERS weekly    - Answers questions     - Generates |
|  - Detects new signals   - Uses knowledge graph    DSUR/IND  |
|  - Generates alerts      - Cites references        sections  |
|  - Emails safety team    - Interactive chat       - Formats  |
+-------------------------------------------------------------+
         |                       |                    |
         v                       v                    v
+-------------------------------------------------------------+
|              Claude Agent SDK (query loop)                    |
|  Tools: PSP API calls, file read/write, web search           |
|  System prompt: domain-specific safety science context        |
|  Permission mode: per-task configuration                      |
+-------------------------------------------------------------+
         |                       |                    |
         v                       v                    v
+-------------------------------------------------------------+
|                PSP FastAPI Backend (existing)                 |
|  /api/v1/predict   /api/v1/population/*   /api/v1/signals/*  |
+-------------------------------------------------------------+
```

### Implementation Complexity: **High**

### Estimated Effort: **2-3 weeks**

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `claude-agent-sdk` | New dependency | `pip install claude-agent-sdk` |
| `ANTHROPIC_API_KEY` | Needed | Environment variable |
| Claude Code CLI | Needed on host | Agent SDK requires Claude Code installed |
| Task scheduler | Needed for monitoring agent | `cron`, Windows Task Scheduler, or `APScheduler` |
| SMTP / notification | Optional | For alerting on detected signals |

### Code Sketch

```python
# src/agents/safety_monitor.py
"""Autonomous safety monitoring agent using Claude Agent SDK."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions

logger = logging.getLogger(__name__)

SAFETY_MONITOR_PROMPT = """You are the Safety Monitoring Agent for the Predictive
Safety Platform. Your job is to:

1. Query the FAERS signal detection endpoint for all known CAR-T products
2. Compare current signals against the previous report (if available)
3. Identify NEW signals or signals that have STRENGTHENED since last check
4. Generate a concise safety signal report

Use the PSP API at http://localhost:8000 to query data.

Report format:
- Date and time of analysis
- Products queried
- Total signals detected
- New/changed signals since last report
- Risk assessment for each new signal
- Recommended actions (further investigation, literature review, etc.)

Save the report to the reports directory when complete.
"""


async def run_safety_monitor(
    api_base: str = "http://localhost:8000",
    report_dir: str = "./reports/safety_signals",
) -> str:
    """Run the autonomous safety monitoring agent.

    Returns:
        Path to the generated report file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(report_dir) / f"faers_signal_report_{timestamp}.md"

    options = ClaudeAgentOptions(
        system_prompt=SAFETY_MONITOR_PROMPT,
        allowed_tools=["Bash", "Read", "Write", "WebFetch"],
        permission_mode="acceptEdits",
        cwd=str(Path(report_dir).parent),
    )

    prompt = f"""Run a FAERS signal detection analysis now.

API base URL: {api_base}
Previous reports directory: {report_dir}
Output report to: {report_path}

Steps:
1. Fetch current signals: curl {api_base}/api/v1/signals/faers
2. Check for previous reports in {report_dir}
3. Compare and identify changes
4. Write the report to {report_path}
"""

    results = []
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            results.append(message.result)
        logger.info("Agent message: %s", getattr(message, "type", "unknown"))

    return str(report_path)


# src/agents/clinical_advisor.py
"""Interactive clinical advisor agent for answering safety questions."""


async def ask_clinical_advisor(
    question: str,
    patient_data: dict | None = None,
    api_base: str = "http://localhost:8000",
) -> str:
    """Ask the clinical advisor agent a question about safety data.

    Args:
        question: The clinical question to answer.
        patient_data: Optional patient data for context.
        api_base: Base URL for the PSP API.

    Returns:
        The agent's response with references.
    """
    context = ""
    if patient_data:
        context = f"\nCurrent patient context:\n{json.dumps(patient_data, indent=2)}"

    options = ClaudeAgentOptions(
        system_prompt=f"""You are a Clinical Safety Advisor with access to:
- PSP API at {api_base} (Bayesian risk, mitigation analysis, FAERS signals)
- Cell therapy registry with 12 therapy types and 21 AE profiles
- Knowledge graph with biological pathway data
- Published literature on cell therapy safety

When answering questions:
- Query the relevant API endpoints to get current data
- Cite specific numbers, confidence intervals, and evidence grades
- Reference published scoring systems and their citations
- Explicitly state limitations and uncertainty
- Never recommend specific clinical actions; frame as "the data suggest..."
""",
        allowed_tools=["Bash", "Read", "WebFetch", "WebSearch"],
        permission_mode="plan",
    )

    prompt = f"""Answer the following clinical safety question:

{question}
{context}

Use the PSP API at {api_base} to retrieve relevant data. Provide a thorough,
evidence-based response with specific citations.
"""

    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            response_text = message.result
            break

    return response_text


# src/agents/report_generator.py
"""Agent for generating regulatory safety report sections."""


async def generate_dsur_section(
    section: str,
    therapy_type: str = "CAR-T CD19",
    indication: str = "SLE",
    api_base: str = "http://localhost:8000",
) -> str:
    """Generate a DSUR section using the agent.

    Args:
        section: Which DSUR section to generate (e.g., "safety_overview",
                 "signal_detection", "benefit_risk").
        therapy_type: The therapy being assessed.
        indication: Target indication.
        api_base: PSP API base URL.

    Returns:
        The generated DSUR section text.
    """
    options = ClaudeAgentOptions(
        system_prompt=f"""You are a regulatory medical writer generating sections
for a Development Safety Update Report (DSUR) per ICH E2F guidelines.

You have access to the PSP API at {api_base} which provides:
- Population-level AE rates with Bayesian credible intervals
- FAERS post-marketing signal detection
- Mitigation strategy analysis with correlated risk reduction
- Evidence accrual timelines
- Clinical trial registry data

Writing style:
- Formal regulatory language appropriate for health authority submissions
- Passive voice where convention dictates
- Every claim backed by data with specific numbers
- Uncertainty quantified using credible/confidence intervals
- Risk-benefit framing per ICH guidelines
""",
        allowed_tools=["Bash", "Read", "Write", "WebFetch"],
        permission_mode="acceptEdits",
    )

    prompt = f"""Generate the '{section}' section of a DSUR for {therapy_type}
in {indication}.

Retrieve all relevant data from {api_base}/api/v1/population/* and
{api_base}/api/v1/signals/faers endpoints. The section should be
2-4 pages in length and follow ICH E2F structure.
"""

    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            response_text = message.result
            break

    return response_text
```

### Pros

- Agents can perform multi-step reasoning: query data, analyze, compare, report.
- Autonomous monitoring reduces manual safety surveillance burden.
- Agent SDK handles the tool-use loop — no manual orchestration needed.
- Can access multiple data sources (PSP API, web search, file system) in one session.
- Interactive advisor mode enables ad-hoc clinical queries.

### Cons

- Highest implementation complexity. Agent behavior is less predictable than direct API calls.
- Requires Claude Code installed on the host machine — adds infrastructure requirements.
- Cost is higher: agents may make many API calls per task (5-20 tool uses per session).
- Agent SDK is relatively new; API surface may change.
- Output quality depends heavily on prompt engineering and guardrails.
- Autonomous actions need careful human-in-the-loop review before any clinical use.

---

## 5. Option 3: MCP Server Integration

### Overview

Expose the PSP's data and models as an MCP (Model Context Protocol) server, allowing any MCP-compatible client (Claude Desktop, Claude Code, custom agents) to query risk models, access the cell therapy registry, and generate clinical documents from live data.

### Architecture

```
+-------------------------------------------------------------------+
|                     MCP-Compatible Clients                        |
|                                                                   |
|  Claude Desktop    Claude Code    Custom Agent    IDE Extension    |
|  (chat interface)  (CLI)          (Agent SDK)     (VS Code)       |
+-------------------------------------------------------------------+
              |              |              |              |
              v              v              v              v
+-------------------------------------------------------------------+
|                    MCP Protocol (JSON-RPC / stdio)                 |
+-------------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------------+
|                PSP MCP Server (FastMCP)                            |
|                                                                   |
|  Tools:                          Resources:                       |
|  - predict_patient_risk()        - psp://registry/therapies       |
|  - compute_bayesian_posterior()  - psp://registry/ae_taxonomy     |
|  - run_mitigation_analysis()     - psp://models/status            |
|  - detect_faers_signals()        - psp://data/sle_baseline        |
|  - get_monitoring_schedule()     - psp://cdp/eligibility          |
|  - compute_easix()               - psp://cdp/stopping_rules      |
|  - compute_hscore()                                               |
|  - compute_car_hematotox()       Prompts:                         |
|  - get_evidence_accrual()        - safety_assessment              |
|  - generate_safety_narrative()   - signal_interpretation          |
|                                  - dsur_section                   |
+-------------------------------------------------------------------+
              |
              v
+-------------------------------------------------------------------+
|                PSP FastAPI Backend (existing models)               |
+-------------------------------------------------------------------+
```

### Implementation Complexity: **Medium**

### Estimated Effort: **1-2 weeks**

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `fastmcp` | New dependency | `pip install 'fastmcp<3'` (stable v2) or `mcp` SDK |
| PSP server running | Required | MCP server calls PSP API internally |
| MCP client | Required | Claude Desktop, Claude Code, or custom |

### Code Sketch

```python
# src/mcp/psp_server.py
"""MCP Server exposing PSP data and models to Claude and other MCP clients."""

from __future__ import annotations

import httpx
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP(
    name="predictive-safety-platform",
    description=(
        "Cell therapy adverse event risk assessment platform. Provides Bayesian "
        "risk estimation, biomarker scoring, FAERS signal detection, mitigation "
        "analysis, and clinical safety plan generation."
    ),
)

PSP_API_BASE = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Tools — functions Claude can execute
# ---------------------------------------------------------------------------

@mcp.tool()
async def predict_patient_risk(
    patient_id: str,
    ldh: float | None = None,
    creatinine: float | None = None,
    platelets: float | None = None,
    crp: float | None = None,
    ferritin: float | None = None,
    temperature: float | None = None,
    hours_since_infusion: float = 0.0,
) -> dict:
    """Run the full ensemble risk prediction for a patient.

    Computes EASIX, HScore, CAR-HEMATOTOX, and other biomarker scores,
    then produces a composite risk assessment with confidence-weighted
    aggregation. Returns individual model scores, risk level, contributing
    factors, and data completeness.

    Args:
        patient_id: Unique patient identifier.
        ldh: Lactate dehydrogenase in U/L.
        creatinine: Serum creatinine in mg/dL.
        platelets: Platelet count in 10^9/L.
        crp: C-reactive protein in mg/L.
        ferritin: Serum ferritin in ng/mL.
        temperature: Current temperature in Celsius.
        hours_since_infusion: Hours since cell therapy infusion.
    """
    payload = {
        "patient_id": patient_id,
        "labs": {
            "ldh": ldh,
            "creatinine": creatinine,
            "platelets": platelets,
            "crp": crp,
            "ferritin": ferritin,
        },
        "vitals": {"temperature": temperature},
        "product": {"hours_since_infusion": hours_since_infusion},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{PSP_API_BASE}/api/v1/predict", json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def compute_bayesian_posterior(
    adverse_event: str,
    n_events: int,
    n_patients: int,
    use_informative_prior: bool = True,
) -> dict:
    """Compute Bayesian Beta-Binomial posterior for an adverse event rate.

    Uses informative priors derived from discounted oncology CAR-T data.
    Returns posterior mean, 95% credible interval, and prior parameters.

    Args:
        adverse_event: AE type — CRS, ICANS, or ICAHS.
        n_events: Number of observed grade 3+ events.
        n_patients: Total patients observed.
        use_informative_prior: Use informative prior from oncology data.
    """
    payload = {
        "adverse_event": adverse_event,
        "n_events": n_events,
        "n_patients": n_patients,
        "use_informative_prior": use_informative_prior,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PSP_API_BASE}/api/v1/population/bayesian", json=payload
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def run_mitigation_analysis(
    selected_mitigations: list[str],
    target_ae: str = "CRS",
    n_monte_carlo_samples: int = 5000,
) -> dict:
    """Analyze combined risk reduction from multiple mitigation strategies.

    Accounts for mechanistic correlations between interventions using
    copula-based correction. Uses Monte Carlo simulation for uncertainty.

    Args:
        selected_mitigations: List of mitigation IDs (e.g., ["tocilizumab", "corticosteroids"]).
        target_ae: Target adverse event — CRS, ICANS, or ICAHS.
        n_monte_carlo_samples: Number of Monte Carlo samples for uncertainty.
    """
    payload = {
        "selected_mitigations": selected_mitigations,
        "target_ae": target_ae,
        "n_monte_carlo_samples": n_monte_carlo_samples,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PSP_API_BASE}/api/v1/population/mitigations", json=payload
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def detect_faers_signals(
    products: str | None = None,
) -> dict:
    """Query FDA FAERS for post-marketing safety signals on CAR-T products.

    Computes disproportionality metrics: PRR (Proportional Reporting Ratio),
    ROR (Reporting Odds Ratio), and EBGM (Empirical Bayesian Geometric Mean).

    Args:
        products: Comma-separated product names, or None for all CAR-T products.
    """
    params = {}
    if products:
        params["products"] = products

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.get(
            f"{PSP_API_BASE}/api/v1/signals/faers", params=params
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_monitoring_schedule(
    therapy_type: str = "car-t-cd19-sle",
) -> dict:
    """Get the suggested monitoring schedule for a cell therapy clinical plan.

    Returns time-windowed monitoring activities from pre-infusion through
    5-year follow-up, with rationale for each monitoring parameter.

    Args:
        therapy_type: Therapy type identifier.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PSP_API_BASE}/api/v1/cdp/monitoring-schedule",
            params={"therapy_type": therapy_type},
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_stopping_rules(
    therapy_type: str = "car-t-cd19-sle",
) -> dict:
    """Get Bayesian stopping rule boundaries for key adverse events.

    Returns maximum tolerable events at each sample size before enrollment
    should be paused, based on posterior probability thresholds.

    Args:
        therapy_type: Therapy type identifier.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PSP_API_BASE}/api/v1/cdp/stopping-rules",
            params={"therapy_type": therapy_type},
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def list_available_mitigations() -> dict:
    """List all available mitigation strategies with their parameters.

    Returns mitigation IDs, names, mechanisms, target AEs, relative risks,
    confidence intervals, evidence levels, and references.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PSP_API_BASE}/api/v1/population/mitigations/strategies"
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_evidence_accrual() -> dict:
    """Get the sequential Bayesian evidence accrual timeline.

    Shows how credible intervals narrow as SLE CAR-T trial data accumulates,
    with projected future precision at planned enrollment milestones.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PSP_API_BASE}/api/v1/population/evidence-accrual"
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Resources — read-only data Claude can reference
# ---------------------------------------------------------------------------

@mcp.resource("psp://registry/therapies")
async def therapy_registry() -> str:
    """Cell therapy registry with all therapy types and their AE profiles."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PSP_API_BASE}/api/v1/therapies")
        resp.raise_for_status()
        return resp.text


@mcp.resource("psp://population/baseline-risk")
async def baseline_risk() -> str:
    """Population-level baseline risk estimates for SLE CAR-T."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PSP_API_BASE}/api/v1/population/risk")
        resp.raise_for_status()
        return resp.text


@mcp.resource("psp://models/status")
async def model_status() -> str:
    """Status and availability of all scoring models."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{PSP_API_BASE}/api/v1/models/status")
        resp.raise_for_status()
        return resp.text


# ---------------------------------------------------------------------------
# Prompts — reusable prompt templates
# ---------------------------------------------------------------------------

@mcp.prompt()
def safety_assessment_prompt(therapy_type: str, indication: str) -> str:
    """Generate a comprehensive safety assessment prompt."""
    return f"""Perform a comprehensive safety assessment for {therapy_type}
in {indication}. Use the following tools to gather data:

1. Get baseline population risk
2. Run FAERS signal detection
3. Get the evidence accrual timeline
4. Check available mitigations and their combined effect
5. Review monitoring schedule and stopping rules

Synthesize all findings into a structured safety assessment with:
- Executive summary (1 paragraph)
- Risk profile (baseline rates with CIs)
- Post-marketing signals (FAERS)
- Mitigation strategy effectiveness
- Evidence sufficiency assessment
- Recommendations for further data collection
"""


@mcp.prompt()
def signal_interpretation_prompt(product: str) -> str:
    """Generate a prompt for interpreting FAERS signals for a product."""
    return f"""Analyze FAERS signals for {product}. Use detect_faers_signals()
to get the current data. For each signal:

1. Assess clinical significance based on PRR, ROR, and EBGM
2. Compare against known labeled adverse events
3. Identify any novel or unexpected signals
4. Recommend follow-up actions for pharmacovigilance
"""


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
```

**Running the MCP server:**

```bash
# Start the PSP FastAPI server first
python run_server.py &

# Start the MCP server
python -m src.mcp.psp_server

# Or configure in Claude Desktop's config:
# ~/Library/Application Support/Claude/claude_desktop_config.json  (macOS)
# %APPDATA%\Claude\claude_desktop_config.json  (Windows)
```

```json
{
  "mcpServers": {
    "predictive-safety-platform": {
      "command": "python",
      "args": ["-m", "src.mcp.psp_server"],
      "cwd": "C:\\Users\\alto8\\safety-research-system"
    }
  }
}
```

### Pros

- Standard protocol: works with Claude Desktop, Claude Code, and any future MCP client.
- Clean separation of concerns: PSP stays a data/model layer; Claude is the intelligence layer.
- Tools are self-documenting: descriptions and schemas are part of the MCP protocol.
- Resources provide read-only reference data without risk of modification.
- Prompt templates standardize common analysis workflows.
- Can compose with other MCP servers (file system, database, web search) for richer capabilities.
- FastMCP handles all protocol boilerplate — minimal code needed.

### Cons

- Requires running two processes (PSP FastAPI + MCP server) or embedding MCP within FastAPI.
- MCP is primarily designed for local/desktop use; deploying as a remote service requires additional infrastructure (SSE transport, authentication).
- MCP protocol is still evolving; the 2025-11-25 specification added OAuth but the ecosystem is maturing.
- Adds `fastmcp` or `mcp` as a new dependency.
- Users need an MCP-compatible client to benefit.

---

## 6. Option 4: Embedded Claude in Dashboard

### Overview

Add a chat panel directly in the 14-tab clinical dashboard that allows users to ask natural language questions about the current view's data. The chat is context-aware: it knows which tab is active, what data is displayed, and can call PSP APIs on behalf of the user.

### Architecture

```
+----------------------------------------------------------------------+
|                     CLINICAL DASHBOARD (index.html)                   |
|                                                                       |
|  +----------------------------+  +----------------------------------+ |
|  |   Existing 14-Tab Content  |  |     AI Chat Panel (new)          | |
|  |                            |  |                                  | |
|  |  [Patient Scoring]         |  |  "What does this EASIX score     | |
|  |  [Population Risk]         |  |   mean for CRS risk?"           | |
|  |  [Evidence Accrual]        |  |                                  | |
|  |  [Mitigation Explorer]     |  |  AI: "The EASIX score of 12.4   | |
|  |  [FAERS Signals]           |  |   falls in the moderate-risk     | |
|  |  [Executive Summary]       |  |   range (Pennisi et al. 2021).  | |
|  |  [CDP Tabs...]             |  |   Given the current CRP of      | |
|  |                            |  |   45 mg/L and platelets..."     | |
|  |                            |  |                                  | |
|  |                            |  |  [Ask a question...]  [Send]    | |
|  +----------------------------+  +----------------------------------+ |
+----------------------------------------------------------------------+
              |                                    |
              v                                    v
+----------------------------------------------------------------------+
|                    FastAPI Backend                                     |
|                                                                       |
|  Existing endpoints (unchanged)     New: POST /api/v1/chat            |
|                                     - Receives question + context     |
|                                     - Calls Claude API                |
|                                     - Returns structured response     |
+----------------------------------------------------------------------+
```

### Implementation Complexity: **Medium**

### Estimated Effort: **1-2 weeks**

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `anthropic` Python SDK | Already in `pyproject.toml` | Version >=0.40.0 |
| `ANTHROPIC_API_KEY` | Needed | Environment variable |
| Dashboard CSS/JS changes | Required | Chat panel UI in `index.html` |

### Code Sketch

**Backend — Chat Endpoint:**

```python
# Add to app.py or create src/api/chat_routes.py

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request from the dashboard."""
    message: str = Field(..., description="User's question", min_length=1, max_length=2000)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Current dashboard context (active tab, displayed data)",
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Previous messages in this conversation",
        max_length=20,
    )


class ChatResponse(BaseModel):
    """Chat response with AI-generated answer."""
    request_id: str
    timestamp: datetime
    response: str
    model_used: str
    tokens_used: dict[str, int] = Field(default_factory=dict)
    disclaimer: str = "AI-generated interpretation. Not a substitute for clinical judgment."
    suggested_actions: list[str] = Field(default_factory=list)


CHAT_SYSTEM_PROMPT = """You are a clinical safety advisor embedded in the Predictive
Safety Platform dashboard. You help clinical teams interpret cell therapy adverse event
risk data.

You have access to the following data in the user's current session:
{context_description}

Guidelines:
- Answer concisely (2-4 paragraphs max) unless the user asks for detail.
- Always cite specific numbers from the data when available.
- Reference scoring systems by name and publication (e.g., "EASIX, Pennisi et al. 2021").
- Quantify uncertainty: mention credible/confidence interval widths.
- Never make clinical recommendations. Use phrases like "the data suggest" or "this may warrant".
- If the question is outside the scope of the available data, say so.
- Use ASTCT consensus grading terminology for CRS/ICANS.
"""


@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="AI-powered clinical chat",
    description="Ask questions about the current dashboard data.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return an AI response."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Build context description from the active tab data
    context_desc = _build_context_description(request.context)

    # Build system prompt with context
    system = CHAT_SYSTEM_PROMPT.format(context_description=context_desc)

    # Build message history
    messages = []
    for msg in request.conversation_history[-10:]:  # Keep last 10 messages
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": request.message})

    try:
        from src.api.claude_narratives import get_client
        client = get_client()

        response = await client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            system=system,
            messages=messages,
        )

        ai_response = response.content[0].text
        tokens = {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        }
    except Exception as exc:
        logger.exception("Chat failed")
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {exc}")

    return ChatResponse(
        request_id=request_id,
        timestamp=now,
        response=ai_response,
        model_used="claude-sonnet-4-5",
        tokens_used=tokens,
        suggested_actions=_extract_suggested_actions(ai_response),
    )


def _build_context_description(context: dict) -> str:
    """Build a human-readable description of the dashboard context."""
    tab = context.get("active_tab", "unknown")
    descriptions = {
        "patient_scoring": "Patient biomarker scores (EASIX, HScore, CAR-HEMATOTOX)",
        "population_risk": "Population-level Bayesian risk estimates for SLE CAR-T",
        "evidence_accrual": "Evidence accrual timeline with narrowing credible intervals",
        "mitigation_explorer": "Mitigation strategy analysis with correlated risk reduction",
        "faers_signals": "FAERS post-marketing pharmacovigilance signals",
        "executive_summary": "Executive summary of overall safety assessment",
        "cdp_monitoring": "Clinical development plan monitoring schedule",
        "cdp_eligibility": "Suggested inclusion/exclusion criteria",
        "cdp_stopping": "Bayesian stopping rule boundaries",
    }
    desc = descriptions.get(tab, f"Tab: {tab}")

    # Add any data displayed on screen
    data = context.get("displayed_data", {})
    if data:
        import json
        desc += f"\n\nCurrently displayed data:\n{json.dumps(data, indent=2, default=str)[:3000]}"

    return desc


def _extract_suggested_actions(response: str) -> list[str]:
    """Extract any suggested follow-up actions from the AI response."""
    # Simple heuristic: look for phrases that suggest actions
    actions = []
    trigger_phrases = [
        "may warrant",
        "consider",
        "should be evaluated",
        "further investigation",
        "review the",
        "monitor for",
    ]
    for sentence in response.split("."):
        sentence = sentence.strip()
        for phrase in trigger_phrases:
            if phrase in sentence.lower() and len(sentence) < 200:
                actions.append(sentence + ".")
                break
    return actions[:5]
```

**Frontend — Chat Panel (addition to index.html):**

```html
<!-- Add to index.html: Chat toggle button in header -->
<button class="theme-toggle" onclick="toggleChatPanel()" title="AI Safety Advisor">
  AI Advisor
</button>

<!-- Chat panel (collapsible sidebar) -->
<div id="chatPanel" class="chat-panel" style="display:none;">
  <div class="chat-header">
    <span class="chat-title">AI Safety Advisor</span>
    <button onclick="toggleChatPanel()" class="chat-close">&times;</button>
  </div>
  <div class="chat-disclaimer">
    AI-generated. Not a substitute for clinical judgment.
  </div>
  <div id="chatMessages" class="chat-messages"></div>
  <div class="chat-input-area">
    <textarea id="chatInput" placeholder="Ask about the current data..."
              rows="2" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChatMessage()}">
    </textarea>
    <button onclick="sendChatMessage()" class="chat-send">Send</button>
  </div>
</div>

<script>
let chatHistory = [];

function toggleChatPanel() {
  const panel = document.getElementById('chatPanel');
  panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
}

function getCurrentContext() {
  // Gather context from the active tab
  const activeTab = document.querySelector('.tab-btn.active');
  const tabId = activeTab ? activeTab.dataset.tab : 'unknown';

  // Collect any displayed data from the current view
  const displayedData = {};
  // ... gather relevant data from the active tab's DOM or cached API responses

  return { active_tab: tabId, displayed_data: displayedData };
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  // Show user message
  appendChatMessage('user', message);
  input.value = '';

  // Show loading indicator
  const loadingId = appendChatMessage('assistant', 'Analyzing...');

  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        context: getCurrentContext(),
        conversation_history: chatHistory.slice(-10),
      }),
    });

    const data = await response.json();

    // Replace loading message with response
    updateChatMessage(loadingId, data.response);

    // Update history
    chatHistory.push({ role: 'user', content: message });
    chatHistory.push({ role: 'assistant', content: data.response });

  } catch (err) {
    updateChatMessage(loadingId, 'Error: Unable to reach AI advisor. ' + err.message);
  }
}

function appendChatMessage(role, content) {
  const container = document.getElementById('chatMessages');
  const msgDiv = document.createElement('div');
  const msgId = 'msg-' + Date.now();
  msgDiv.id = msgId;
  msgDiv.className = 'chat-msg chat-msg-' + role;
  msgDiv.textContent = content;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  return msgId;
}

function updateChatMessage(id, content) {
  const el = document.getElementById(id);
  if (el) el.textContent = content;
}
</script>
```

### Pros

- Directly accessible in the existing workflow — no context switching for users.
- Context-aware: chat knows what tab and data the user is looking at.
- Conversation history enables follow-up questions.
- Low barrier to adoption: just click the "AI Advisor" button.
- Can suggest next actions based on the AI's analysis.
- Builds on Option 1's narrative engine (reuses `claude_narratives.py`).

### Cons

- Requires both backend (chat endpoint) and frontend (JS/CSS) changes.
- Conversation context can grow large, increasing token costs.
- Latency for chat responses (1-3 seconds) may feel slow for interactive use.
- Chat UI needs careful design to not disrupt the clinical workflow.
- Needs rate limiting per session to control costs.
- Conversation history is in-memory; no persistence across sessions.

---

## 7. Option 5: Claude-Powered Report Generation

### Overview

Automate the generation of regulatory safety documents using Claude API with structured outputs. Produces IND safety narratives, DSUR sections, periodic safety reports, and regulatory submission safety sections from live PSP data.

### Architecture

```
+-------------------------------------------------------------------+
|                    Report Generation Pipeline                      |
|                                                                    |
|  1. Data Collection    2. Section Generation    3. Assembly        |
|                                                                    |
|  PSP API calls         Claude API calls         Document builder   |
|  - Population risk     - Per-section prompts    - Markdown/DOCX    |
|  - FAERS signals       - Structured outputs     - Version control  |
|  - Evidence accrual    - Reference injection    - Review tracking  |
|  - Mitigation data     - Regulatory style       - Audit trail      |
|  - Trial registry                                                  |
+-------------------------------------------------------------------+
         |                       |                       |
         v                       v                       v
+-------------------------------------------------------------------+
|                    Generated Documents                              |
|                                                                    |
|  IND Safety Narrative       DSUR Section              PSR          |
|  - AE summary table        - Safety overview          - Quarterly  |
|  - Signal analysis          - New safety info           safety     |
|  - Benefit-risk             - Signal detection          update     |
|  - Appendices               - Benefit-risk             - Cumul.   |
|                              assessment                  data     |
+-------------------------------------------------------------------+
```

### Implementation Complexity: **Medium**

### Estimated Effort: **1-2 weeks**

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `anthropic` Python SDK | Already in `pyproject.toml` | Version >=0.40.0 |
| `ANTHROPIC_API_KEY` | Needed | Environment variable |
| `python-docx` or `fpdf2` | Optional new dep | For DOCX/PDF export |
| PSP server running | Required | Report pulls live data |

### Code Sketch

```python
# src/reports/safety_report_generator.py
"""Claude-powered regulatory safety report generation."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import anthropic
import httpx

logger = logging.getLogger(__name__)

PSP_API_BASE = os.environ.get("PSP_API_BASE", "http://localhost:8000")


@dataclass
class ReportSection:
    """A single section of a regulatory safety report."""
    title: str
    content: str
    data_sources: list[str] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    generated_at: str = ""
    model_used: str = ""
    tokens_used: int = 0


@dataclass
class SafetyReport:
    """Complete regulatory safety report."""
    title: str
    report_type: str  # "IND_NARRATIVE", "DSUR", "PSR", "REGULATORY_SUBMISSION"
    therapy: str
    indication: str
    generated_at: str
    sections: list[ReportSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# Section-specific prompts with regulatory formatting requirements
SECTION_PROMPTS = {
    "safety_overview": """Write the Safety Overview section of a {report_type} for
{therapy} in {indication}.

Data provided:
{data}

Requirements:
- Follow ICH E2F guidelines for DSUR or ICH M4E for CTD Module 2.7.4
- Begin with a summary statement of the overall safety profile
- Present AE rates as percentages with 95% confidence/credible intervals
- Compare autoimmune vs oncology AE rates where data permits
- Discuss any dose-response relationships observed
- Note the evidence grade and sample size limitations
- Use passive voice per regulatory convention
- Length: 500-800 words
""",

    "signal_detection": """Write the Signal Detection and Evaluation section.

FAERS Signal Data:
{data}

Requirements:
- Define the signal detection methodology (PRR, ROR, EBGM thresholds)
- Present each detected signal with its disproportionality metrics
- Classify signals as "identified risk", "potential risk", or "important missing information"
- For each strong signal, provide clinical assessment of relevance
- Note limitations of spontaneous reporting (Weber effect, stimulated reporting)
- Length: 400-600 words
""",

    "benefit_risk": """Write the Benefit-Risk Assessment section.

Efficacy Context: {therapy} has shown drug-free remission in SLE patients.
Safety Data:
{data}

Requirements:
- Use ICH E2C(R2) framework for benefit-risk evaluation
- Present benefits: remission rates, SLE disease activity improvement
- Present risks: AE rates with credible intervals, mitigated risk estimates
- Discuss the unmet medical need in refractory SLE
- Address the risk management strategy (monitoring, mitigations)
- Conclude with a balanced benefit-risk statement
- Length: 600-1000 words
""",

    "monitoring_plan": """Write the Safety Monitoring Plan section.

Monitoring Schedule Data:
{data}

Requirements:
- Present the monitoring schedule as a structured narrative
- Justify each monitoring parameter based on AE onset timing
- Include specific laboratory thresholds for intervention
- Reference ASTCT consensus grading for CRS/ICANS assessment
- Address long-term monitoring requirements (FDA 15-year guideline for gene therapy)
- Length: 400-700 words
""",
}


class SafetyReportGenerator:
    """Generates regulatory safety reports using Claude API and PSP data."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-5"

    async def generate_report(
        self,
        report_type: str,
        therapy: str = "Anti-CD19 CAR-T",
        indication: str = "Systemic Lupus Erythematosus (SLE)",
        sections: list[str] | None = None,
    ) -> SafetyReport:
        """Generate a complete safety report.

        Args:
            report_type: Type of report (DSUR, IND_NARRATIVE, PSR).
            therapy: Therapy name.
            indication: Target indication.
            sections: Which sections to generate. None = all applicable.

        Returns:
            SafetyReport with all generated sections.
        """
        if sections is None:
            sections = list(SECTION_PROMPTS.keys())

        # Step 1: Collect all data from PSP
        data = await self._collect_report_data()

        # Step 2: Generate each section
        report = SafetyReport(
            title=f"{report_type} — {therapy} in {indication}",
            report_type=report_type,
            therapy=therapy,
            indication=indication,
            generated_at=datetime.utcnow().isoformat(),
        )

        for section_key in sections:
            if section_key not in SECTION_PROMPTS:
                logger.warning("Unknown section: %s", section_key)
                continue

            section = await self._generate_section(
                section_key=section_key,
                report_type=report_type,
                therapy=therapy,
                indication=indication,
                data=data,
            )
            report.sections.append(section)

        report.metadata = {
            "total_sections": len(report.sections),
            "total_tokens": sum(s.tokens_used for s in report.sections),
            "data_timestamp": datetime.utcnow().isoformat(),
            "model": self.model,
            "disclaimer": (
                "AI-generated draft. All content requires review by qualified "
                "safety scientist before regulatory submission."
            ),
        }

        return report

    async def _collect_report_data(self) -> dict[str, Any]:
        """Collect all relevant data from PSP APIs."""
        async with httpx.AsyncClient(timeout=90.0) as client:
            # Parallel data collection
            results = {}

            endpoints = {
                "population_risk": "/api/v1/population/risk",
                "evidence_accrual": "/api/v1/population/evidence-accrual",
                "trials": "/api/v1/population/trials",
                "mitigations": "/api/v1/population/mitigations/strategies",
                "monitoring": "/api/v1/cdp/monitoring-schedule",
                "stopping_rules": "/api/v1/cdp/stopping-rules",
                "eligibility": "/api/v1/cdp/eligibility-criteria",
                "sample_size": "/api/v1/cdp/sample-size",
            }

            for key, endpoint in endpoints.items():
                try:
                    resp = await client.get(f"{PSP_API_BASE}{endpoint}")
                    resp.raise_for_status()
                    results[key] = resp.json()
                except Exception as exc:
                    logger.warning("Failed to fetch %s: %s", key, exc)
                    results[key] = {"error": str(exc)}

            # FAERS may take longer
            try:
                resp = await client.get(f"{PSP_API_BASE}/api/v1/signals/faers")
                resp.raise_for_status()
                results["faers"] = resp.json()
            except Exception as exc:
                logger.warning("FAERS fetch failed: %s", exc)
                results["faers"] = {"error": str(exc)}

            return results

    async def _generate_section(
        self,
        section_key: str,
        report_type: str,
        therapy: str,
        indication: str,
        data: dict[str, Any],
    ) -> ReportSection:
        """Generate a single report section using Claude."""
        prompt_template = SECTION_PROMPTS[section_key]

        # Select relevant data for this section
        relevant_data = self._select_data_for_section(section_key, data)

        user_prompt = prompt_template.format(
            report_type=report_type,
            therapy=therapy,
            indication=indication,
            data=json.dumps(relevant_data, indent=2, default=str)[:8000],
        )

        system_prompt = f"""You are a regulatory medical writer with expertise in
cell therapy safety documentation. You are writing a {report_type} for
{therapy} in {indication}.

Critical rules:
- Every numerical claim must be traceable to the provided data.
- Do not invent or fabricate any data, statistics, or references.
- If data is insufficient for a claim, state "Data not available" explicitly.
- Use 95% credible intervals for Bayesian estimates, 95% CI for frequentist.
- Follow ICH E2F (DSUR) or ICH M4E (CTD) formatting as appropriate.
- Include a "Limitations" paragraph when evidence is sparse.
"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return ReportSection(
            title=section_key.replace("_", " ").title(),
            content=response.content[0].text,
            data_sources=list(relevant_data.keys()),
            generated_at=datetime.utcnow().isoformat(),
            model_used=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
        )

    def _select_data_for_section(
        self, section_key: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Select the relevant subset of data for a given section."""
        section_data_map = {
            "safety_overview": ["population_risk", "evidence_accrual", "trials"],
            "signal_detection": ["faers"],
            "benefit_risk": ["population_risk", "mitigations", "evidence_accrual"],
            "monitoring_plan": ["monitoring", "stopping_rules", "eligibility"],
        }

        keys = section_data_map.get(section_key, list(data.keys()))
        return {k: data[k] for k in keys if k in data}

    def export_markdown(self, report: SafetyReport) -> str:
        """Export the report as a Markdown document."""
        lines = [
            f"# {report.title}",
            "",
            f"**Report Type:** {report.report_type}",
            f"**Therapy:** {report.therapy}",
            f"**Indication:** {report.indication}",
            f"**Generated:** {report.generated_at}",
            "",
            "---",
            "",
            "> **DISCLAIMER:** This document was generated using AI assistance "
            "(Claude, Anthropic). All content requires review and validation by "
            "qualified safety scientists before any regulatory use. AI-generated "
            "content is advisory only.",
            "",
            "---",
            "",
        ]

        for i, section in enumerate(report.sections, 1):
            lines.append(f"## {i}. {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            if section.references:
                lines.append("### References")
                for ref in section.references:
                    lines.append(f"- {ref}")
                lines.append("")
            lines.append("---")
            lines.append("")

        # Appendix: Generation metadata
        lines.append("## Appendix: Generation Metadata")
        lines.append("")
        lines.append(f"- **Model:** {report.metadata.get('model', 'N/A')}")
        lines.append(f"- **Total tokens:** {report.metadata.get('total_tokens', 0):,}")
        lines.append(f"- **Sections generated:** {report.metadata.get('total_sections', 0)}")
        lines.append(f"- **Data timestamp:** {report.metadata.get('data_timestamp', 'N/A')}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# API endpoint for report generation
# ---------------------------------------------------------------------------

# Add to app.py or population_routes.py:

# from src.reports.safety_report_generator import SafetyReportGenerator
#
# @router.post("/api/v1/reports/generate", tags=["Reports"])
# async def generate_safety_report(
#     report_type: str = Query("DSUR", description="Report type"),
#     therapy: str = Query("Anti-CD19 CAR-T"),
#     indication: str = Query("SLE"),
#     sections: list[str] | None = Query(None),
# ) -> dict:
#     generator = SafetyReportGenerator()
#     report = await generator.generate_report(
#         report_type=report_type,
#         therapy=therapy,
#         indication=indication,
#         sections=sections,
#     )
#     return {
#         "report": generator.export_markdown(report),
#         "metadata": report.metadata,
#     }
```

### Pros

- Directly addresses a time-consuming manual task (report writing takes days to weeks).
- Structured prompts ensure regulatory formatting and style compliance.
- Data-driven: every claim traces back to PSP API data (no hallucinated statistics).
- Section-by-section generation allows parallel human review.
- Export to Markdown enables easy conversion to DOCX/PDF.
- Audit trail tracks which model and data were used for each section.
- Batch API (50% discount) can be used for non-urgent report generation.

### Cons

- Generated text requires thorough human review before regulatory use.
- Regulatory language has very specific conventions; prompt tuning is needed.
- Long reports (DSUR can be 50+ pages) require multiple Claude calls and careful assembly.
- References must be verified — Claude may confuse citation details.
- No guarantee of consistency across sections generated in separate calls.
- Version control of generated reports needs a workflow (git, SharePoint, etc.).

---

## 8. Pricing and Cost Estimates

### Claude API Model Pricing (as of February 2026)

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| Claude Haiku 4.5 | $1 / MTok | $5 / MTok | High-volume chat, simple narratives |
| Claude Sonnet 4.5 | $3 / MTok | $15 / MTok | Balanced: report generation, interpretation |
| Claude Opus 4.6 | $5 / MTok | $25 / MTok | Complex reasoning, regulatory analysis |

**Cost Optimizations Available:**
- Prompt caching: 0.1x price on cache hits (10x reduction for repeated system prompts)
- Batch API: 50% discount for non-real-time processing
- Haiku for high-volume, low-complexity tasks (chat, simple summaries)

### Estimated Monthly Costs by Option

Assumptions: 50 predictions/day, 5 chat sessions/day, 2 reports/week, 1 FAERS scan/week.

| Option | Model | Est. Tokens/Month | Est. Cost/Month |
|--------|-------|--------------------|-----------------|
| 1. API Direct (narratives) | Sonnet 4.5 | ~3M input, ~1.5M output | ~$30-35 |
| 2. Agent SDK (monitoring) | Sonnet 4.5 | ~10M input, ~5M output | ~$100-120 |
| 3. MCP Server | Sonnet 4.5 | ~5M input, ~2.5M output | ~$50-55 |
| 4. Dashboard Chat | Haiku 4.5 | ~8M input, ~2M output | ~$18-20 |
| 5. Report Generation | Sonnet 4.5 | ~2M input, ~3M output | ~$50-55 |

**Combined (all options with prompt caching):** Approximately $150-250/month.

The system prompt for the safety scientist context (~500 tokens) will be repeated on every call. With prompt caching (5-minute TTL), this reduces to 0.1x cost on hits, saving approximately 30-40% on input token costs for interactive use cases.

---

## 9. Regulatory and Compliance Considerations

### Classification

Per current FDA guidance and the EU AI Act, this system would likely be classified as:

- **Clinical Decision Support (CDS):** If used to support clinical decisions about patient safety monitoring, the AI component may be subject to FDA medical device regulations (21 CFR Part 820). However, if the system meets all four CDS exemption criteria (not intended to replace clinician judgment, intended to support decision-making, allows clinician to independently review the basis, and the user is a healthcare professional), it may be exempt from device regulation.
- **Non-CDS applications:** Report generation, literature synthesis, and data summarization for non-patient-specific use would not typically trigger medical device classification.

### Best Practices from Literature

Based on current guidance (ESMO ELCAP, Frontiers in AI, npj Digital Medicine):

1. **Human-in-the-loop:** All AI-generated content must be reviewed by a qualified safety scientist before clinical or regulatory use. The system should clearly label AI-generated content.
2. **Validation framework:** Establish a validation protocol for AI-generated narratives against expert-written reference documents. Track concordance metrics.
3. **Audit trail:** Log every AI interaction: input data, prompt used, model version, output, reviewer identity, and approval status.
4. **Data privacy:** The PSP uses only published literature and public data — no PHI/PII concerns. If future versions integrate real patient data, HIPAA BAA with Anthropic would be required.
5. **Reproducibility:** Log the exact model version, temperature setting, and random seed (where applicable) for every generation. Use structured outputs to constrain response format.
6. **Disclaimer labeling:** Every AI-generated output must carry a visible disclaimer. Regulatory submissions using AI-assisted content should disclose this in the methodology section.
7. **Continuous monitoring:** Track AI output quality over time. Establish a feedback loop where safety scientists rate AI outputs, creating a dataset for future evaluation.

### Anthropic Data Policy

Anthropic's current API terms state that data sent via the API is not used for model training. For organizations requiring additional guarantees, enterprise agreements with specific data handling provisions are available.

---

## 10. Comparison Matrix

| Criterion | Option 1: API Direct | Option 2: Agent SDK | Option 3: MCP Server | Option 4: Dashboard Chat | Option 5: Reports |
|-----------|---------------------|--------------------|--------------------|------------------------|--------------------|
| **Complexity** | Low | High | Medium | Medium | Medium |
| **Effort** | 2-3 days | 2-3 weeks | 1-2 weeks | 1-2 weeks | 1-2 weeks |
| **New Dependencies** | None (SDK exists) | claude-agent-sdk, CLI | fastmcp | None (SDK exists) | None (SDK exists) |
| **User Interaction** | None (API param) | Background/CLI | External client | In-dashboard chat | API/CLI trigger |
| **Latency** | +1-3s per call | Minutes per task | +1-3s per tool | +1-3s per message | Minutes per report |
| **Cost/Month** | ~$30-35 | ~$100-120 | ~$50-55 | ~$18-20 | ~$50-55 |
| **Clinical Value** | Medium | High | Medium | High | Very High |
| **Regulatory Risk** | Low | Medium | Low | Medium | Medium |
| **Maintenance** | Low | High | Medium | Medium | Medium |
| **Composability** | Standalone | Needs tools | Composable | Standalone | Standalone |

---

## 11. Recommended Implementation Path

### Phase 1: Foundation (Week 1) — Options 1 + 4

Start with the lowest-risk, highest-value combination:

1. **Implement `claude_narratives.py`** (Option 1) — the narrative generation module that all other options can reuse. Add `?include_narrative=true` to existing endpoints. This is 2-3 days of work with zero risk to existing functionality.

2. **Add the dashboard chat panel** (Option 4) — gives immediate user-facing value. Uses the same narrative module under the hood. Another 3-4 days.

**Deliverable:** Users can toggle AI narratives on any API response and ask questions in the dashboard.

### Phase 2: Reports (Weeks 2-3) — Option 5

3. **Build the report generator** — this addresses the highest-effort manual task. Start with DSUR safety overview and signal detection sections. Validate against existing manually-written reports.

**Deliverable:** One-click generation of draft DSUR sections from live PSP data.

### Phase 3: MCP Server (Week 4) — Option 3

4. **Expose PSP as an MCP server** — this makes the platform available to Claude Desktop and Claude Code users (including the development team itself). It also enables Option 2 agents to use PSP tools natively.

**Deliverable:** Safety scientists can query PSP data conversationally through Claude Desktop.

### Phase 4: Agents (Weeks 5-6) — Option 2

5. **Build the safety monitoring agent** — now that MCP tools exist, the agent can use them. Start with weekly FAERS monitoring and automated signal comparison. Add email notification on new strong signals.

**Deliverable:** Autonomous weekly FAERS monitoring with human-reviewed reports.

### Phase 0 (Prerequisite): Environment Setup

Before any phase:
- Set `ANTHROPIC_API_KEY` in the environment (`.env` file or system environment variable).
- Verify the `anthropic` SDK version is >=0.40.0 (already in `pyproject.toml`).
- Decide on model tier: Sonnet 4.5 recommended for the balance of quality, speed, and cost.
- Establish a review protocol for AI-generated clinical content.

---

## 12. References

### Anthropic Documentation
- [Claude API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Agent SDK Python Reference](https://platform.claude.com/docs/en/agent-sdk/python)
- [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Tool Use Implementation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use)
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)

### MCP (Model Context Protocol)
- [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Reference Servers](https://github.com/modelcontextprotocol/servers)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### Clinical/Regulatory
- [LLM as Clinical Decision Support (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12629785/) — LLM-based CDS augments medication safety across 16 clinical specialties
- [Safe Implementation of LLMs in Healthcare (Frontiers)](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1504805/full) — Practical step-by-step approach
- [Balancing Control, Collaboration, Costs and Security (npj Digital Medicine)](https://www.nature.com/articles/s41746-025-01476-7) — Implementation framework
- [ESMO Guidance on LLMs in Clinical Practice (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0923753425046988) — ELCAP guidelines
- [2025 Expert Consensus on LLM Evaluation in Clinical Scenarios (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2667102625001044) — Retrospective evaluation framework
- [LLMs in Healthcare (PMC Review)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12189880/) — Comprehensive review of applications

### PSP Internal
- `src/api/app.py` — FastAPI application with 13+ endpoints
- `src/api/schemas.py` — Pydantic request/response schemas
- `src/api/population_routes.py` — Population-level API routes
- `src/models/model_registry.py` — 7 statistical models
- `data/cell_therapy_registry.py` — 12 therapy types, 21 AE profiles
- `src/data/graph/knowledge_graph.py` — Biological pathway knowledge graph

---

*Document generated 2026-02-08. Review and approve before proceeding with implementation.*
