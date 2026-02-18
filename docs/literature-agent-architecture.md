# Literature Review Agent Architecture for Pharmacovigilance

**Version:** 0.1 (Draft) | **Date:** 2026-02-18
**Status:** Architectural Plan | **Owner:** Safety Research Team

---

## 1. Executive Summary

This document describes the architecture for an **agentic literature review system** integrated into the Predictive Safety Platform (PSP). The system replicates the proven pattern of supervisor-orchestrated specialized agents (as demonstrated in IQVIA's Literature AI Platform) using **Claude Agent SDK**, **Model Context Protocol (MCP) servers**, and **Claude Code skills**.

The system automates the five core stages of pharmacovigilance literature review:

| Stage | Agent | Function |
|-------|-------|----------|
| 1. Protocol Generation | Protocol Generator Agent | Refines research question → PICO framework → search strategy |
| 2. Search | Searcher Agent | Deterministic, reproducible search across PubMed, Europe PMC, and other sources |
| 3. Screening | Screener Agent | Screens abstracts/full-text against PICO inclusion/exclusion criteria |
| 4. Extraction | Extractor Agent | Populates structured extraction templates with study data |
| 5. Synthesis | Insights Generator Agent | Produces evidence summaries, signal narratives, and regulatory-ready outputs |

A **Supervisor Agent** orchestrates the pipeline, manages state, enforces human-in-the-loop checkpoints, and maintains the audit trail.

### 1.1 Design Goals

1. **Regulatory compliance** — Meets ICH E2C(R2), GVP Module VI/IX, FDA 21 CFR 314.80, PRISMA 2020
2. **Copyright compliance** — Operates within EU TDM Directive 2019/790, US fair use, publisher API ToS
3. **Reproducibility** — Every search is deterministic, timestamped, and re-executable
4. **Human-in-the-loop** — Mandatory review gates at screening and extraction stages
5. **Audit trail** — Full provenance from question to conclusion, 21 CFR Part 11 compatible
6. **Integration** — Builds on existing PSP infrastructure (FAERS, knowledge graph, narrative engine)

---

## 2. Reference Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                           │
│  PSP Dashboard (Literature Tab) ←→ REST API ←→ WebSocket       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPERVISOR AGENT                              │
│  Claude Agent SDK | State Machine | Audit Logger                │
│  Orchestrates pipeline, enforces gates, manages retries         │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │ Protocol │→│ Searcher │→│ Screener │→│Extractor │→│Synth.│ │
│  │ Generator│ │  Agent   │ │  Agent   │ │  Agent   │ │Agent │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ │
│       │            │            │             │           │     │
│   HUMAN GATE   HUMAN GATE  HUMAN GATE    HUMAN GATE     │     │
│  (approve PICO) (approve   (approve      (approve       │     │
│                  strategy)  inclusions)   extractions)   │     │
└───────┼────────────┼────────────┼─────────────┼──────────┼─────┘
        │            │            │             │          │
        ▼            ▼            ▼             ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP SERVER LAYER                             │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  PubMed MCP │ │Europe PMC   │ │ OpenFDA MCP │               │
│  │  (E-utils)  │ │  MCP Server │ │  (FAERS)    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ClinTrials   │ │ Semantic    │ │ OpenAlex    │               │
│  │.gov MCP     │ │ Scholar MCP │ │  MCP Server │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐                                │
│  │  MeSH MCP   │ │ Unpaywall   │                                │
│  │ (term expand)│ │  MCP Server │                                │
│  └─────────────┘ └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
        │                                                │
        ▼                                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA / PERSISTENCE                          │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ Review DB    │ │ Audit Trail  │ │ Document Store           │ │
│  │ (SQLite/PG)  │ │ (append-only)│ │ (metadata + cached abs.) │ │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐                              │
│  │ PSP Knowledge│ │ ICSR Queue   │                              │
│  │ Graph        │ │ (E2B output) │                              │
│  └──────────────┘ └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Specifications

### 3.1 Supervisor Agent

**Role:** Pipeline orchestrator, state manager, compliance enforcer.

**Implementation:** Claude Agent SDK with tool use, extended thinking enabled.

```python
# Conceptual — Claude Agent SDK supervisor
from anthropic import Agent, tool

supervisor = Agent(
    model="claude-sonnet-4-5-20250929",
    name="literature_review_supervisor",
    instructions="""You orchestrate pharmacovigilance literature reviews.
    You manage a pipeline of specialized agents: Protocol Generator,
    Searcher, Screener, Extractor, and Insights Generator.
    You enforce human review gates between each stage.
    You maintain a complete audit trail of all decisions.""",
    tools=[
        launch_protocol_agent,
        launch_searcher_agent,
        launch_screener_agent,
        launch_extractor_agent,
        launch_insights_agent,
        request_human_review,
        save_audit_event,
        get_review_state,
    ],
)
```

**State Machine:**

```
INITIATED → PROTOCOL_DRAFT → PROTOCOL_APPROVED → SEARCHING →
SEARCH_COMPLETE → SCREENING → SCREENING_REVIEWED →
EXTRACTING → EXTRACTION_REVIEWED → SYNTHESIZING → COMPLETE
```

Each transition requires either agent completion or human approval (at gates).

**Responsibilities:**
- Accept research questions from users or scheduled PV monitoring triggers
- Delegate to specialized agents in sequence
- Present results at human review gates and wait for approval
- Handle errors, retries, and partial failures gracefully
- Log every action, decision, and state transition to the audit trail
- Produce final review package with full provenance

### 3.2 Protocol Generator Agent

**Role:** Transform a research question into a structured PICO framework, search strategy, and extraction template.

**Implementation:** Claude Agent SDK sub-agent with MeSH MCP access.

**Inputs:**
- Free-text research question (e.g., "What is the incidence of CRS grade ≥3 in CD19 CAR-T therapy for DLBCL?")
- Optional: therapeutic area, product name, adverse event of interest, time period

**Outputs:**
```json
{
  "pico": {
    "population": "Adult patients with relapsed/refractory DLBCL",
    "intervention": "CD19-directed CAR-T cell therapy (axicabtagene ciloleucel, tisagenlecleucel, lisocabtagene maraleucel)",
    "comparator": "Standard salvage chemotherapy or historical controls",
    "outcome": "Cytokine release syndrome (CRS) grade ≥3 per ASTCT consensus grading"
  },
  "search_strategy": {
    "pubmed_query": "(\"CD19\" OR \"axicabtagene\" OR \"tisagenlecleucel\" OR \"lisocabtagene\") AND (\"CAR-T\" OR \"chimeric antigen receptor\") AND (\"cytokine release syndrome\" OR \"CRS\") AND (\"diffuse large B-cell lymphoma\" OR \"DLBCL\")",
    "mesh_terms": ["Receptors, Chimeric Antigen", "Cytokine Release Syndrome", "Lymphoma, Large B-Cell, Diffuse"],
    "date_range": "2015-01-01 to 2026-02-18",
    "languages": ["en"],
    "publication_types": ["Clinical Trial", "Randomized Controlled Trial", "Observational Study", "Meta-Analysis", "Systematic Review", "Case Reports"]
  },
  "extraction_template": {
    "fields": [
      "study_id", "first_author", "year", "journal",
      "study_design", "sample_size", "population_description",
      "intervention_details", "comparator_details",
      "crs_any_grade_n", "crs_any_grade_pct",
      "crs_grade3plus_n", "crs_grade3plus_pct",
      "crs_grading_system", "median_onset_days",
      "management_protocol", "tocilizumab_use_pct",
      "icu_admission_pct", "crs_related_mortality",
      "median_followup_months", "evidence_grade", "limitations"
    ]
  },
  "inclusion_criteria": [
    "Reports CRS incidence data for CD19 CAR-T in DLBCL patients",
    "Sample size ≥ 5 patients",
    "Published in peer-reviewed journal",
    "Uses recognized CRS grading system (Lee, ASTCT, Penn)"
  ],
  "exclusion_criteria": [
    "Preclinical or in vitro studies only",
    "Pediatric-only populations (age < 18)",
    "Non-CD19 targets unless comparison arm includes CD19",
    "Conference abstracts without sufficient outcome data",
    "Duplicate publications of same patient cohort"
  ]
}
```

**MeSH Term Expansion:** Uses the MeSH MCP server to:
- Map free-text terms to MeSH descriptors
- Identify entry terms and qualifiers
- Expand with narrower terms where appropriate
- Build Boolean query with MeSH headings + free-text synonyms

**Tools available:**
- `mesh_lookup` — Look up MeSH terms for concepts
- `mesh_tree_expand` — Get narrower terms in MeSH hierarchy
- `validate_search_syntax` — Validate PubMed query syntax
- `get_medline_field_tags` — Get available MEDLINE field codes

### 3.3 Searcher Agent

**Role:** Execute deterministic, reproducible searches across multiple databases and return deduplicated results.

**Implementation:** Claude Agent SDK sub-agent with PubMed MCP, Europe PMC MCP, and ClinicalTrials.gov MCP.

**Critical requirement:** This agent must produce **identical results** when given identical inputs. Every search is recorded with exact query strings, timestamps, database versions, and result counts.

**Inputs:**
- Approved search strategy from Protocol Generator (post human gate)

**Outputs:**
```json
{
  "search_execution": {
    "search_id": "SR-2026-0218-001",
    "executed_at": "2026-02-18T14:30:00Z",
    "databases_searched": [
      {
        "database": "PubMed/MEDLINE",
        "query": "(exact query as executed)",
        "results_count": 847,
        "api_response_id": "pubmed_esearch_xxxxx"
      },
      {
        "database": "Europe PMC",
        "query": "(exact query as executed)",
        "results_count": 912
      },
      {
        "database": "ClinicalTrials.gov",
        "query": "(exact query as executed)",
        "results_count": 45
      }
    ],
    "total_before_dedup": 1804,
    "duplicates_removed": 389,
    "total_unique": 1415
  },
  "records": [
    {
      "pmid": "12345678",
      "doi": "10.1000/example",
      "title": "...",
      "authors": ["..."],
      "journal": "...",
      "year": 2024,
      "abstract": "...",
      "publication_type": ["Clinical Trial"],
      "mesh_terms": ["..."],
      "source_databases": ["PubMed", "Europe PMC"],
      "open_access": true,
      "oa_url": "https://europepmc.org/article/..."
    }
  ]
}
```

**Deduplication strategy:**
1. Match by DOI (exact)
2. Match by PMID (exact)
3. Match by title similarity (≥0.95 Jaccard on normalized title tokens)
4. Flag near-duplicates for human review

**Tools available:**
- `pubmed_search` — Execute PubMed E-utilities ESearch
- `pubmed_fetch` — Fetch records via EFetch (MEDLINE XML)
- `europepmc_search` — Search Europe PMC REST API
- `clinicaltrials_search` — Search ClinicalTrials.gov API
- `semantic_scholar_search` — Supplementary search via Semantic Scholar
- `unpaywall_check` — Check OA availability via Unpaywall
- `deduplicate_records` — DOI/PMID/title-based deduplication

### 3.4 Screener Agent

**Role:** Screen each record against PICO inclusion/exclusion criteria. Present decisions with rationale for human review.

**Implementation:** Claude Agent SDK sub-agent operating on abstract text.

**Two-pass screening:**

1. **Title/Abstract screening (automated with human review):**
   - Agent reads title + abstract for each record
   - Classifies as INCLUDE / EXCLUDE / UNCERTAIN
   - Provides 1-2 sentence rationale for each decision
   - All UNCERTAIN and a random sample (≥10%) of INCLUDE/EXCLUDE go to human reviewer

2. **Full-text screening (human-led, agent-assisted):**
   - For included records, agent identifies full-text availability (OA, PMC, institutional)
   - Agent pre-highlights relevant sections in available full texts
   - Human makes final inclusion decision
   - Agent records decision and rationale

**Outputs per record:**
```json
{
  "pmid": "12345678",
  "screening_phase": "title_abstract",
  "decision": "INCLUDE",
  "confidence": 0.92,
  "rationale": "Reports CRS outcomes in 150 DLBCL patients receiving axi-cel. Includes grade 3+ CRS rates with ASTCT grading.",
  "pico_match": {
    "population": true,
    "intervention": true,
    "comparator": false,
    "outcome": true
  },
  "flags": ["no_comparator_arm"],
  "human_review_required": false,
  "human_decision": null,
  "human_rationale": null
}
```

**Quality control:**
- Inter-rater reliability: Agent decisions compared against human reviewer sample
- Cohen's kappa tracked per review; if κ < 0.8, re-calibrate screening criteria
- All exclusion reasons categorized and counted for PRISMA flow diagram
- Sensitivity analysis: relaxed criteria re-run to check for near-misses

**Tools available:**
- `classify_record` — Screen a record against PICO criteria
- `batch_screen` — Screen multiple records in parallel
- `fetch_fulltext` — Retrieve OA full text via Europe PMC or PMC
- `highlight_sections` — Identify PICO-relevant sections in full text
- `compute_screening_stats` — Calculate agreement metrics

### 3.5 Extractor Agent

**Role:** Extract structured data from included studies into the extraction template defined by the Protocol Generator.

**Implementation:** Claude Agent SDK sub-agent with access to full-text documents.

**Extraction approach:**
1. Read full text (or abstract if full text unavailable)
2. Map study content to each field in the extraction template
3. Extract verbatim quotes with page/section references as evidence
4. Flag fields where data is absent, ambiguous, or requires interpretation
5. Dual extraction: for critical fields (primary outcomes), extract independently twice and flag discrepancies

**Output per study:**
```json
{
  "pmid": "12345678",
  "extraction_id": "EX-2026-0218-001-042",
  "extracted_at": "2026-02-18T15:45:00Z",
  "data": {
    "study_id": "ZUMA-1",
    "first_author": "Neelapu",
    "year": 2017,
    "journal": "N Engl J Med",
    "study_design": "Single-arm, multicenter, phase 1-2",
    "sample_size": 108,
    "crs_any_grade_n": 101,
    "crs_any_grade_pct": 93.0,
    "crs_grade3plus_n": 13,
    "crs_grade3plus_pct": 13.0,
    "crs_grading_system": "Lee 2014 criteria",
    "median_onset_days": 2,
    "tocilizumab_use_pct": 43.0,
    "icu_admission_pct": 27.0,
    "crs_related_mortality": 0
  },
  "evidence": {
    "crs_grade3plus_pct": {
      "quote": "Grade 3 or higher CRS occurred in 13% of patients (13 of 101 evaluable patients)",
      "location": "Results, paragraph 3",
      "confidence": "high"
    }
  },
  "missing_fields": ["median_followup_months"],
  "flags": ["grading_system_is_lee_not_astct_may_need_mapping"],
  "human_review_required": true
}
```

**Tools available:**
- `extract_from_text` — Extract template fields from document text
- `validate_extraction` — Check internal consistency of extracted data
- `map_grading_systems` — Convert between CRS/ICANS grading systems
- `flag_discrepancies` — Compare dual extractions and flag differences

### 3.6 Insights Generator Agent

**Role:** Synthesize extracted data into evidence summaries, signal assessments, and regulatory-ready narratives.

**Implementation:** Claude Agent SDK sub-agent with access to PSP knowledge graph and narrative engine.

**Outputs:**

1. **Quantitative Summary:**
   - Pooled incidence rates (random-effects meta-analysis where appropriate)
   - Forest plots of incidence across studies
   - Heterogeneity assessment (I², Q statistic)
   - Subgroup analyses by product, grading system, patient population

2. **PRISMA Flow Diagram Data:**
   ```
   Records identified: 1415
   ├─ Duplicates removed: 389
   ├─ Title/abstract screened: 1026
   │  └─ Excluded: 726
   ├─ Full-text assessed: 300
   │  └─ Excluded: 180 (reasons: no outcome data 95, wrong population 52, ...)
   └─ Included in synthesis: 120
      ├─ Quantitative synthesis: 85
      └─ Narrative synthesis only: 35
   ```

3. **Signal Assessment (for PV use):**
   - New safety information identified (yes/no, with evidence)
   - Comparison to known product label / IB safety profile
   - Recommended ICSR submissions for individual case reports found in literature
   - Recommended signal evaluation actions per GVP Module IX

4. **Narrative Output:**
   - Executive summary (1 page)
   - Detailed evidence review (structured by outcome)
   - Limitations and evidence gaps
   - Recommendations for further monitoring or study

5. **Regulatory-Ready Outputs:**
   - PBRER Section 5.4 (Published literature) draft
   - DSUR Section 8 (Literature review summary) draft
   - Signal validation worksheet

**Tools available:**
- `compute_pooled_estimate` — Random-effects meta-analysis
- `generate_forest_plot` — SVG forest plot data
- `generate_prisma_flow` — PRISMA 2020 flow diagram data
- `assess_signal` — Evaluate findings against known safety profile
- `generate_narrative` — Clinical narrative via PSP narrative engine
- `draft_pbrer_section` — Format for PBRER Section 5.4
- `query_knowledge_graph` — Access PSP knowledge graph for mechanistic context
- `identify_icsrs` — Flag individual cases requiring ICSR submission

---

## 4. MCP Server Specifications

Each MCP server wraps a public API with standardized tool interfaces, rate limiting, caching, and audit logging.

### 4.1 PubMed MCP Server

**Source:** NCBI E-utilities (https://eutils.ncbi.nlm.nih.gov/entrez/eutils/)

```python
# MCP server tool definitions
tools = [
    {
        "name": "pubmed_search",
        "description": "Search PubMed via ESearch. Returns PMIDs matching query.",
        "parameters": {
            "query": "PubMed search query string with Boolean operators and field tags",
            "max_results": "Maximum results to return (default 1000, max 10000)",
            "date_min": "Minimum publication date (YYYY/MM/DD)",
            "date_max": "Maximum publication date (YYYY/MM/DD)",
            "publication_types": "Filter by publication type"
        }
    },
    {
        "name": "pubmed_fetch",
        "description": "Fetch full MEDLINE records by PMID list.",
        "parameters": {
            "pmids": "List of PMIDs to fetch",
            "format": "Return format: abstract, medline, xml"
        }
    },
    {
        "name": "pubmed_citation_count",
        "description": "Get citation count for a PMID via ELink.",
        "parameters": {"pmid": "PubMed ID"}
    }
]
```

**Compliance controls:**
- Rate limit: 3 requests/second (NCBI policy without API key), 10/sec with API key
- API key stored in environment variable, never in code
- All queries logged with timestamp, query string, result count
- User-Agent header includes tool name and contact email per NCBI policy
- Retries with exponential backoff on 429/500 errors

### 4.2 Europe PMC MCP Server

**Source:** Europe PMC REST API (https://www.ebi.ac.uk/europepmc/webservices/rest)

```python
tools = [
    {
        "name": "europepmc_search",
        "description": "Search Europe PMC. Supports advanced query syntax.",
        "parameters": {
            "query": "Europe PMC query string",
            "result_type": "lite (metadata) or core (full record)",
            "page_size": "Results per page (max 1000)"
        }
    },
    {
        "name": "europepmc_fulltext",
        "description": "Retrieve OA full text in JATS XML or plain text.",
        "parameters": {
            "pmcid": "PubMed Central ID (PMCxxxxxxx)"
        }
    },
    {
        "name": "europepmc_annotations",
        "description": "Get SciLite annotations (entities, concepts) for a paper.",
        "parameters": {
            "source": "Source database (MED, PMC, etc.)",
            "ext_id": "External ID (PMID or PMCID)"
        }
    }
]
```

**Compliance controls:**
- Full-text retrieval limited to OA content (respects publisher opt-outs)
- Europe PMC API is free and open; comply with EBI terms of use
- Cache responses for 24h to reduce redundant requests

### 4.3 OpenFDA/FAERS MCP Server

**Source:** openFDA API (https://api.fda.gov/)

Extends the existing PSP `faers_signal.py` module.

```python
tools = [
    {
        "name": "faers_search",
        "description": "Search FAERS adverse event reports via openFDA.",
        "parameters": {
            "drug_name": "Drug or product name",
            "adverse_event": "MedDRA preferred term",
            "date_range": "Date range for reports"
        }
    },
    {
        "name": "faers_signal_scores",
        "description": "Compute PRR, ROR, and EBGM for a drug-event pair.",
        "parameters": {
            "drug_name": "Drug or product name",
            "adverse_event": "MedDRA preferred term"
        }
    }
]
```

### 4.4 ClinicalTrials.gov MCP Server

**Source:** ClinicalTrials.gov API v2 (https://clinicaltrials.gov/api/v2/)

```python
tools = [
    {
        "name": "ctgov_search",
        "description": "Search clinical trials by condition, intervention, status.",
        "parameters": {
            "condition": "Disease or condition",
            "intervention": "Treatment or drug name",
            "status": "Recruitment status filter",
            "phase": "Trial phase filter"
        }
    },
    {
        "name": "ctgov_study_details",
        "description": "Get full study record by NCT number.",
        "parameters": {"nct_id": "NCT identifier"}
    },
    {
        "name": "ctgov_results",
        "description": "Get posted results for a completed trial.",
        "parameters": {"nct_id": "NCT identifier"}
    }
]
```

### 4.5 MeSH MCP Server

**Source:** NCBI MeSH API + local MeSH XML

```python
tools = [
    {
        "name": "mesh_lookup",
        "description": "Find MeSH descriptor for a concept.",
        "parameters": {"term": "Free-text term to look up"}
    },
    {
        "name": "mesh_tree_expand",
        "description": "Get narrower terms in MeSH hierarchy.",
        "parameters": {
            "descriptor_ui": "MeSH Descriptor Unique ID",
            "depth": "Levels to expand (default 1)"
        }
    },
    {
        "name": "mesh_entry_terms",
        "description": "Get synonyms/entry terms for a MeSH heading.",
        "parameters": {"descriptor_ui": "MeSH Descriptor Unique ID"}
    }
]
```

### 4.6 OpenAlex MCP Server

**Source:** OpenAlex API (https://api.openalex.org/)

Used for bibliometric analysis, citation networks, and identifying related works.

```python
tools = [
    {
        "name": "openalex_search",
        "description": "Search works by concept, author, institution.",
        "parameters": {
            "query": "Search query",
            "filters": "OpenAlex filter expression"
        }
    },
    {
        "name": "openalex_citations",
        "description": "Get citation network for a work.",
        "parameters": {"doi": "DOI of the work"}
    }
]
```

### 4.7 Unpaywall MCP Server

**Source:** Unpaywall API (https://api.unpaywall.org/)

Used to determine open access availability before attempting full-text retrieval.

```python
tools = [
    {
        "name": "check_oa_status",
        "description": "Check if a paper has open access full text.",
        "parameters": {"doi": "DOI to check"}
    }
]
```

---

## 5. Claude Code Skills

Skills provide user-invocable shortcuts for common literature review workflows.

### 5.1 `/lit-review` Skill

**Trigger:** User types `/lit-review` in Claude Code or PSP dashboard chat.

**Behavior:** Launches the full supervisor pipeline.

```markdown
## Skill: lit-review
Launches a pharmacovigilance literature review pipeline.

Usage: /lit-review <research question>
Example: /lit-review What is the incidence of ICANS in BCMA-directed CAR-T therapy?

Steps:
1. Passes question to Protocol Generator Agent
2. Presents PICO + search strategy for user approval
3. Executes search via Searcher Agent
4. Screens results via Screener Agent (with human review gate)
5. Extracts data via Extractor Agent (with human review gate)
6. Generates synthesis via Insights Generator Agent
7. Produces final review package with PRISMA flow diagram
```

### 5.2 `/lit-signal` Skill

**Trigger:** Periodic PV monitoring or manual signal investigation.

```markdown
## Skill: lit-signal
Runs a targeted literature signal detection scan.

Usage: /lit-signal <product> <adverse event> [--since YYYY-MM-DD]
Example: /lit-signal "axicabtagene ciloleucel" "neurotoxicity" --since 2025-01-01

Steps:
1. Auto-generates search strategy for product + AE
2. Searches PubMed for new publications since last scan
3. Cross-references against FAERS signals via OpenFDA MCP
4. Flags new case reports requiring ICSR submission
5. Generates signal assessment summary
```

### 5.3 `/lit-update` Skill

**Trigger:** Periodic update of an existing review.

```markdown
## Skill: lit-update
Updates a previous literature review with newly published studies.

Usage: /lit-update <review-id>
Example: /lit-update SR-2026-0218-001

Steps:
1. Loads previous review protocol and search strategy
2. Re-executes search with date range starting from last search date
3. Screens and extracts only new records
4. Updates synthesis with combined old + new data
5. Generates change summary highlighting new findings
```

---

## 6. Regulatory Compliance Framework

### 6.1 ICH Guidelines Compliance

| Guideline | Requirement | System Implementation |
|-----------|-------------|----------------------|
| **ICH E2C(R2)** — PBRER | Section 5.4 requires systematic literature review for each reporting period | `/lit-update` skill with product-specific saved protocols; outputs draft PBRER Section 5.4 |
| **ICH E2E** — PV Planning | PV plan must include literature monitoring methodology | Protocol Generator produces documented, reproducible search strategies |
| **ICH E2D** — Post-Approval Reporting | Literature-sourced AEs must be reported as ICSRs within 15 days | Screener + Extractor flag individual cases; ICSR queue with E2B(R3) output |
| **ICH E2B(R3)** — ICSR Format | Individual cases from literature must follow E2B(R3) format | Extractor produces structured data mappable to E2B(R3) fields |
| **ICH M1 (MedDRA)** | All AEs coded to MedDRA preferred terms | MeSH→MedDRA mapping in Protocol Generator; all AEs stored as MedDRA PT + LLT |

### 6.2 EMA GVP Compliance

| Module | Requirement | System Implementation |
|--------|-------------|----------------------|
| **GVP Module VI** — Adverse Reaction Management | MAH must monitor published literature for ICSRs; 15-day reporting for serious cases | Automated weekly scans via `/lit-signal`; ICSR triage queue with severity classification |
| **GVP Module VI, VI.B.1** | "Worldwide published scientific and medical literature" must be monitored | Multi-database search (PubMed, Europe PMC) covers global literature |
| **GVP Module VI, VI.B.1.1** | Reference databases must include at minimum MEDLINE | PubMed MCP server provides direct MEDLINE access |
| **GVP Module IX** — Signal Management | Signals from literature must be detected, validated, and assessed | Insights Generator produces signal assessment aligned with IX.C workflow |
| **GVP Module IX, IX.C.2** | Signal validation requires clinical assessment of individual cases | Human review gates ensure clinical scientist reviews all potential signals |

### 6.3 FDA Compliance

| Regulation | Requirement | System Implementation |
|-----------|-------------|----------------------|
| **21 CFR 314.80** | Post-marketing AE reporting including literature reports | Literature-sourced AEs routed to ICSR queue for regulatory submission |
| **21 CFR 314.81** | Annual reports must include published clinical experience | Annual review summaries generated via `/lit-update` |
| **FDA Guidance on PV** | Literature monitoring as part of REMS and PMR commitments | Configurable scheduled searches with product-specific protocols |

### 6.4 PRISMA 2020 Compliance

The system generates PRISMA-compliant documentation at every stage:

- **PRISMA Checklist:** Auto-populated with system-generated data where available
- **PRISMA Flow Diagram:** Generated from screening statistics
- **Search Strategy Reporting:** Full Boolean queries, database versions, date ranges
- **Screening Methodology:** Inclusion/exclusion criteria, inter-rater agreement metrics
- **Data Extraction:** Template-based with source attribution

### 6.5 Audit Trail Requirements (21 CFR Part 11)

Every action in the system is logged:

```json
{
  "audit_event": {
    "event_id": "uuid",
    "timestamp": "ISO-8601",
    "review_id": "SR-2026-0218-001",
    "stage": "screening",
    "actor": "screener_agent_v1.0 | human:user@org.com",
    "action": "screen_record",
    "record_id": "PMID:12345678",
    "decision": "INCLUDE",
    "rationale": "Reports CRS outcomes in CD19 CAR-T DLBCL population",
    "confidence": 0.92,
    "overridden": false,
    "previous_decision": null,
    "system_version": "psp-lit-review-1.0.0"
  }
}
```

**Retention:** All audit records retained for product lifecycle + 15 years per ICH E6.

---

## 7. Copyright and Legal Compliance Framework

### 7.1 Core Principle: Metadata-First, Full-Text-Only-When-Licensed

The system is designed to minimize copyright exposure by operating primarily on **metadata and abstracts** (not copyrightable factual data) and only accessing full text through **licensed or open-access channels**.

### 7.2 Copyright Law by Jurisdiction

| Jurisdiction | Law | Key Provision | System Approach |
|-------------|-----|---------------|-----------------|
| **EU** | Directive 2019/790, Art. 3 | TDM for scientific research by research organizations on lawfully accessed works — mandatory exception, cannot be overridden by contract | Pharmacovigilance qualifies as scientific research. System processes only lawfully accessed content. For non-research-org use, Art. 4 applies (TDM permitted unless publisher opts out). |
| **EU** | Directive 2019/790, Art. 4 | General TDM exception for lawfully accessed works, but rightholders can opt out | System respects `robots.txt` and publisher TDM opt-out flags. Maintains opt-out registry. |
| **UK** | CDPA 1988, §29A | TDM for non-commercial research on lawfully accessed works | PV literature monitoring for safety purposes qualifies. System logs access basis. |
| **US** | 17 USC §107 | Fair use — four-factor test | Extraction of factual data (AE rates, study results) from scientific papers is strongly defensible as fair use. System extracts facts, not creative expression. Outputs are transformative (structured data, not reproduced text). |
| **Japan** | Copyright Act, Art. 30-4 | Computational analysis permitted regardless of purpose | Broad exception covers all TDM. |
| **Canada** | Copyright Act, §29 | Fair dealing for research | PV literature monitoring qualifies as research. |

### 7.3 Data Source Access Rights

| Source | Access Basis | Full-Text Access | Restrictions |
|--------|-------------|------------------|--------------|
| **PubMed/MEDLINE** | Public API, free | Abstracts only (metadata) | Comply with NCBI E-utilities guidelines; include API key and contact email |
| **PubMed Central OA** | Open Access subset | Full text (JATS XML) | Respect individual article licenses (CC-BY, CC-BY-NC, etc.) |
| **Europe PMC** | Public API, free | OA full text via API | EBI terms of use; respect publisher OA provisions |
| **Unpaywall** | Public API, free | OA location URLs only | API use requires email; 100k/day limit |
| **OpenAlex** | Public API, free | Metadata + OA links | No restrictions on metadata; CC0 data |
| **Semantic Scholar** | Public API, tiered | Abstracts + metadata | API key for higher rate limits; respect ToS |
| **ClinicalTrials.gov** | Public domain (US gov) | Full records | No copyright restrictions; US government work |
| **openFDA** | Public domain (US gov) | Full FAERS data | No copyright restrictions; US government work |

### 7.4 What the System Does NOT Do

1. **No bulk downloading of copyrighted full-text articles** — Full text accessed only for OA papers or through institutional subscription APIs
2. **No storage of copyrighted full text** — Process in memory, store only extracted factual data + citation metadata
3. **No reproduction of substantial portions** — Extracted quotes are brief, attributed, for the purpose of evidence documentation
4. **No circumvention of paywalls** — System checks OA status via Unpaywall before attempting full-text retrieval
5. **No training data collection** — System does not collect articles for AI model training

### 7.5 Practical Copyright Workflow

```
For each search result:
1. Retrieve title + abstract from PubMed (public, not copyrightable)
2. Screen based on title + abstract (no copyright issue — facts)
3. If INCLUDED and full text needed:
   a. Check Unpaywall for OA version
   b. If OA: retrieve via Europe PMC / PMC (respect license)
   c. If not OA: extract only from abstract (flag as "abstract-only extraction")
   d. If institutional subscription available: access via institutional API
4. Extracted data = factual information (not copyrightable)
5. Store: citation metadata + extracted facts + brief attributed quotes
6. Do NOT store: full article text, figures, tables in original form
```

### 7.6 Publisher API Compliance

For any future integration with publisher TDM APIs:

| Publisher | TDM API | Requirements |
|-----------|---------|-------------|
| Elsevier | ScienceDirect TDM API | Requires API key + institutional subscription; content for mining only, no redistribution |
| Springer Nature | TDM API via CrossRef | CrossRef TDM click-through license; content for research purposes |
| Wiley | Wiley TDM API | Token-based access; institutional subscription required |
| All publishers | CrossRef Metadata | Free metadata access; no restrictions on bibliographic data |

---

## 8. Data Model and Persistence

### 8.1 Core Entities

```
Review
├── review_id (PK)
├── research_question
├── status (state machine value)
├── created_at, updated_at
├── created_by (user)
├── protocol_version
└── pico, search_strategy, extraction_template (JSON)

SearchExecution
├── search_id (PK)
├── review_id (FK)
├── database
├── query_string
├── executed_at
├── result_count
└── api_response_metadata (JSON)

Record
├── record_id (PK) — internal
├── pmid, doi, pmcid — external IDs
├── title, authors, journal, year
├── abstract
├── publication_type, mesh_terms
├── source_databases (which searches found it)
└── open_access_status, oa_url

ScreeningDecision
├── decision_id (PK)
├── record_id (FK), review_id (FK)
├── phase (title_abstract | full_text)
├── decision (INCLUDE | EXCLUDE | UNCERTAIN)
├── rationale
├── confidence
├── actor (agent | human)
├── human_override (bool)
├── human_rationale
└── created_at

Extraction
├── extraction_id (PK)
├── record_id (FK), review_id (FK)
├── extracted_data (JSON — template fields)
├── evidence (JSON — quotes + locations)
├── missing_fields, flags
├── human_reviewed (bool)
├── human_corrections (JSON)
└── created_at

AuditEvent
├── event_id (PK)
├── review_id (FK)
├── timestamp
├── stage, actor, action
├── details (JSON)
└── system_version
```

### 8.2 Storage Strategy

| Data Type | Storage | Retention |
|-----------|---------|-----------|
| Review protocols & results | SQLite (dev) / PostgreSQL (prod) | Product lifecycle + 15 years |
| Audit trail | Append-only table, no UPDATE/DELETE | Product lifecycle + 15 years |
| Article abstracts | Database (public data) | Duration of review |
| Full-text content | **Not stored** — processed in memory only | N/A |
| Extracted data | Database (factual data, not copyrightable) | Product lifecycle + 15 years |
| PRISMA diagrams & reports | File system (generated artifacts) | Product lifecycle + 15 years |

---

## 9. Integration with Existing PSP

### 9.1 Shared Components

| Existing PSP Module | Integration Point |
|--------------------|--------------------|
| `faers_signal.py` | Insights Generator cross-references literature findings with FAERS signals |
| `src/data/knowledge/` | Knowledge graph provides mechanistic context for signal interpretation |
| `narrative_engine.py` | Insights Generator uses narrative engine for clinical text generation |
| `model_registry.py` | Literature-derived incidence rates feed into Bayesian risk models |
| `cell_therapy_registry.py` | Therapy type taxonomy shared between literature search and risk models |
| `population_routes.py` | New literature review endpoints added to population route group |

### 9.2 New API Endpoints

```
POST   /api/v1/literature/reviews              — Create new literature review
GET    /api/v1/literature/reviews               — List all reviews
GET    /api/v1/literature/reviews/{id}          — Get review details + status
POST   /api/v1/literature/reviews/{id}/approve  — Approve current gate
GET    /api/v1/literature/reviews/{id}/records  — Get search results
GET    /api/v1/literature/reviews/{id}/screening — Get screening results
GET    /api/v1/literature/reviews/{id}/extractions — Get extracted data
GET    /api/v1/literature/reviews/{id}/synthesis — Get synthesis/insights
GET    /api/v1/literature/reviews/{id}/prisma   — Get PRISMA flow diagram
GET    /api/v1/literature/reviews/{id}/audit    — Get audit trail
POST   /api/v1/literature/signals/scan          — Run signal detection scan
GET    /api/v1/literature/signals/queue          — Get ICSR submission queue
```

### 9.3 Dashboard Integration

New **Literature Review** tab in the PSP dashboard (tab 18):

- Review management panel (create, view status, approve gates)
- PRISMA flow diagram visualization (SVG, vanilla JS)
- Screening decisions table with approve/override controls
- Extraction data table with edit capability
- Signal assessment summary
- Audit trail viewer

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

| Task | Deliverable |
|------|------------|
| MCP servers for PubMed, Europe PMC | Working tool interfaces with tests |
| Data model + persistence layer | SQLite schema, repository pattern |
| Audit trail infrastructure | Append-only logging with 21 CFR Part 11 fields |
| Protocol Generator Agent | PICO extraction, MeSH expansion, search strategy generation |
| Basic supervisor with state machine | Sequential pipeline, no parallelism yet |
| `/lit-review` skill (basic) | End-to-end pipeline, CLI-only |

### Phase 2: Core Pipeline (Weeks 5-8)

| Task | Deliverable |
|------|------------|
| Searcher Agent with multi-database search | PubMed + Europe PMC + deduplication |
| Screener Agent with two-pass screening | Title/abstract + full-text screening |
| Human review gate API | Approve/override endpoints |
| Extractor Agent | Template-based extraction with evidence attribution |
| MCP servers for ClinicalTrials.gov, OpenFDA | Additional data sources |
| Quality metrics (Cohen's kappa, coverage) | Screening quality dashboard |

### Phase 3: Synthesis and Compliance (Weeks 9-12)

| Task | Deliverable |
|------|------------|
| Insights Generator Agent | Meta-analysis, PRISMA, signal assessment |
| PBRER/DSUR section generation | Regulatory-ready outputs |
| ICSR queue with E2B(R3) mapping | Literature case processing |
| `/lit-signal` and `/lit-update` skills | PV monitoring workflows |
| Dashboard Literature Review tab | Full UI integration |
| Validation testing against manual reviews | Sensitivity/specificity benchmarking |

### Phase 4: Production Hardening (Weeks 13-16)

| Task | Deliverable |
|------|------------|
| PostgreSQL migration | Production database |
| Scheduled monitoring pipeline | Automated weekly/monthly scans |
| Performance optimization | Parallel screening, caching |
| GAMP 5 validation documentation | IQ/OQ/PQ protocols and reports |
| User acceptance testing | Clinical PV team validation |
| Copyright compliance audit | Legal review of all data access patterns |

---

## 11. Validation Strategy

### 11.1 Benchmarking Against Manual Reviews

To validate the system, run parallel reviews:

1. Select 3-5 completed manual PV literature reviews with known results
2. Run the same research questions through the agent pipeline
3. Compare:
   - **Search sensitivity:** Did the system find all studies the manual review found?
   - **Search precision:** What percentage of system results were relevant?
   - **Screening agreement:** Cohen's kappa between agent and manual screening
   - **Extraction accuracy:** Field-level accuracy vs. manual extraction
   - **Signal detection:** Did the system identify the same signals?

**Acceptance criteria:**
- Search sensitivity ≥ 95% (must not miss relevant studies)
- Screening κ ≥ 0.80 (substantial agreement)
- Extraction accuracy ≥ 90% per field
- Zero missed ICSRs requiring 15-day reporting

### 11.2 Ongoing Performance Monitoring

- Track screening agreement per review (human reviewer sample)
- Track extraction accuracy per review (human QC on random 20%)
- Monitor search result counts for temporal consistency
- Alert on anomalous drops in result counts (potential API issues)

---

## 12. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AI hallucination in extraction (fabricated data) | Medium | High | Dual extraction, human review gate, evidence quotes with source attribution |
| Missed ICSR in literature (regulatory non-compliance) | Low | Critical | High-sensitivity screening threshold, human review of all UNCERTAIN, validation benchmarking |
| Copyright infringement via full-text processing | Low | High | Metadata-first design, OA-only full text, no storage of copyrighted content |
| PubMed API downtime or rate limiting | Medium | Medium | Multi-source search, caching, graceful degradation |
| Search strategy drift (evolving terminology) | Medium | Medium | Periodic protocol review, MeSH update monitoring |
| Model version changes affecting consistency | Low | Medium | Pin model versions, version tracking in audit trail |
| Data loss in audit trail | Low | Critical | Append-only storage, backups, integrity checksums |

---

## 13. Appendix A: Regulatory Reference Index

| Reference | Full Title | Relevance |
|-----------|-----------|-----------|
| ICH E2C(R2) | Periodic Benefit-Risk Evaluation Reports | PBRER literature review requirements |
| ICH E2D | Post-Approval Safety Data Management | Expedited and periodic reporting of literature AEs |
| ICH E2E | Pharmacovigilance Planning | Literature monitoring as PV plan component |
| ICH E2B(R3) | Electronic Transmission of ICSRs | Format for literature-sourced case reports |
| ICH M1 | MedDRA | Adverse event terminology standard |
| EMA GVP Module VI | Management and Reporting of Adverse Reactions | Literature monitoring obligations for MAHs |
| EMA GVP Module IX | Signal Management | Signal detection from literature sources |
| FDA 21 CFR 314.80 | Postmarketing Reporting of AEs | Literature-based AE reporting requirements |
| FDA 21 CFR 314.81 | Other Postmarketing Reports | Annual report literature review requirements |
| PRISMA 2020 | Systematic Reviews Reporting Guideline | Search and reporting methodology standard |
| EU Directive 2019/790 | Copyright in the Digital Single Market | TDM exception for research (Art. 3) and general (Art. 4) |
| 21 CFR Part 11 | Electronic Records; Electronic Signatures | Audit trail and record integrity requirements |
| GAMP 5 (2nd Ed.) | Risk-Based Approach to GxP Computerized Systems | Validation framework for the system |

---

## 14. Appendix B: Comparison with IQVIA Architecture

| IQVIA Component | PSP Equivalent | Key Difference |
|----------------|----------------|----------------|
| IQVIA Scientific Navigator (proprietary) | PubMed + Europe PMC + OpenAlex (public APIs) | Open-source, multi-source; no proprietary database dependency |
| Supervisor Agent | Claude Agent SDK Supervisor | Same pattern; our implementation adds explicit regulatory gates |
| Protocol Generator Agent | Protocol Generator Agent | Equivalent; adds MeSH MCP for automated term expansion |
| Searcher Agent | Searcher Agent | Equivalent; multi-database with deduplication |
| Screener Agent | Screener Agent | Equivalent; adds two-pass screening + quality metrics |
| Extractor Agent | Extractor Agent | Equivalent; adds dual extraction + evidence quotes |
| Insights Generator Agent | Insights Generator Agent | Extended: adds ICSR detection, PBRER/DSUR drafting, PSP knowledge graph integration |
| Proprietary platform | Open-source PSP + Claude Agent SDK | Fully open-source, extensible, auditable |

---

*This document is part of the Predictive Safety Platform. All data sources are public. No proprietary data or personal information is included.*
