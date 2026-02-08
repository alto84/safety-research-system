# Cell Therapy Adverse Event Database Research Report

**Date:** 2026-02-08
**System:** Safety Research System
**Scope:** Comprehensive assessment of publicly available databases for cell therapy adverse events, with emphasis on CAR-T products

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Database Inventory](#database-inventory)
3. [Prototype Results](#prototype-results)
4. [Data Extraction Approaches](#data-extraction-approaches)
5. [Feasibility Assessment](#feasibility-assessment)
6. [Recommended Next Steps](#recommended-next-steps)
7. [Effort Estimates](#effort-estimates)

---

## 1. Executive Summary

This report documents 12 publicly accessible databases containing cell therapy adverse event data, along with prototype extraction results from two key sources. Our ClinicalTrials.gov extractor successfully retrieved structured AE data from 47 completed CAR-T clinical trials (201 total found, 805 unique serious AE types, 1,243 other AE types). Our FAERS extractor queried all 6 FDA-approved CAR-T products, finding 16,432 total adverse event reports across products with detailed AE profiles, demographic data, and cross-product comparisons.

**Key Findings:**
- FAERS (via openFDA) and ClinicalTrials.gov are immediately actionable with free, well-documented APIs
- CIBMTR and EBMT hold the richest patient-level CAR-T safety data but require formal research collaboration agreements
- EudraVigilance and VigiBase provide international coverage but have limited programmatic access
- Literature mining (PubMed) is feasible via E-utilities and would supplement structured database data
- FDA BLA review documents contain detailed safety data but require NLP-based extraction

---

## 2. Database Inventory

### 2.1 FAERS / openFDA (FDA Adverse Event Reporting System)

| Attribute | Detail |
|-----------|--------|
| **Organization** | FDA |
| **URL** | https://open.fda.gov/apis/drug/event/ |
| **Access Method** | REST API (JSON), quarterly bulk data files (ASCII/XML) |
| **Data Format** | JSON (API), ASCII/XML (bulk download) |
| **Coverage** | All 6 approved CAR-T products (Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti); 27M+ total AE reports |
| **CAR-T Reports Found** | 16,432 total (Yescarta: 6,410; Carvykti: 3,767; Kymriah: 3,591; Tecartus: 1,262; Abecma: 879; Breyanzi: 523) |
| **Cost** | Free, public domain |
| **Rate Limits** | 240 requests/min with API key, 40/min without |
| **Limitations** | Voluntary reporting (underreporting bias), no denominators, duplicate reports possible, reporter quality variable. Reports are by product name, not mechanism -- must search each product separately. |
| **Feasibility** | HIGH -- fully automated, already prototyped successfully |

### 2.2 ClinicalTrials.gov

| Attribute | Detail |
|-----------|--------|
| **Organization** | NIH/NLM |
| **URL** | https://clinicaltrials.gov/data-api/about-api/ |
| **Access Method** | REST API v2 (JSON/CSV), bulk XML download |
| **Data Format** | JSON (API), XML (bulk), structured AE tables |
| **Coverage** | 201 completed CAR-T trials found; 47 with posted results containing structured AE data |
| **AE Data Structure** | Three tables per trial: All-Cause Mortality, Serious AEs, Other AEs -- each with group-level numerator/denominator |
| **Cost** | Free |
| **Rate Limits** | No hard limit documented, polite use expected |
| **Limitations** | Only ~23% of completed trials have posted AE results. AE terms not always MedDRA-standardized. Results lag behind trial completion. |
| **Feasibility** | HIGH -- fully automated, already prototyped successfully |

### 2.3 EudraVigilance (European Medicines Agency)

| Attribute | Detail |
|-----------|--------|
| **Organization** | EMA |
| **URL** | https://www.adrreports.eu/ |
| **Access Method** | Web portal (adrreports.eu) for public access; ICSR download for Marketing Authorization Holders; no public API |
| **Data Format** | Web tables (exportable), ICH E2B(R3) XML for MAH downloads |
| **Coverage** | All EEA-authorized medicines including CAR-T products. Reports from EU/EEA member states. |
| **Cost** | Free for public access; formal agreement required for ICSR-level data |
| **Limitations** | No programmatic API for researchers. Data download is year-by-year manual export. Public data is aggregated (counts), not individual cases. Requires product-by-product manual searches. |
| **Feasibility** | MEDIUM -- web scraping possible but fragile. Formal data access request needed for research-grade data. |

### 2.4 VigiBase (WHO Global ICSR Database)

| Attribute | Detail |
|-----------|--------|
| **Organization** | WHO / Uppsala Monitoring Centre (UMC) |
| **URL** | https://www.vigiaccess.org/ (public), https://who-umc.org/vigibase/ (full) |
| **Access Method** | VigiAccess web portal (public aggregated data); VigiLyze/VigiSearch for authorized WHO Programme members; formal data request for researchers |
| **Data Format** | RDMS (SQL-compatible), ODBC interface, web export |
| **Coverage** | 170+ member countries, largest global ICSR database |
| **Cost** | Free public access (aggregated); formal collaboration required for individual case data |
| **Limitations** | Public portal provides only counts by age, country, drug, reaction -- not case-level data. Full access requires being a WHO Programme for International Drug Monitoring member or submitting a formal research request. |
| **Feasibility** | LOW-MEDIUM -- VigiAccess public data is limited; full data requires institutional collaboration with UMC. |

### 2.5 PubMed / MEDLINE (via E-utilities)

| Attribute | Detail |
|-----------|--------|
| **Organization** | NIH/NLM |
| **URL** | https://eutils.ncbi.nlm.nih.gov/ |
| **Access Method** | REST API (E-utilities: ESearch, EFetch, ELink); NCBI Datasets API |
| **Data Format** | XML, JSON, PubMed XML |
| **Coverage** | 36M+ articles; thousands of CAR-T publications including systematic reviews, case series, clinical trials |
| **Cost** | Free with API key (10 req/sec), 3 req/sec without |
| **Limitations** | Unstructured text requires NLP for AE extraction. Published bias -- positive results overrepresented. Time lag between events and publication. |
| **Feasibility** | MEDIUM-HIGH -- API is well-documented; NLP extraction from abstracts/full text is the main challenge. |

### 2.6 FDA BLA Review Documents (Drugs@FDA)

| Attribute | Detail |
|-----------|--------|
| **Organization** | FDA/CBER |
| **URL** | https://www.accessdata.fda.gov/scripts/cder/daf/ |
| **Access Method** | PDF download from Drugs@FDA; some structured data via DailyMed API |
| **Data Format** | PDF (review documents), XML (DailyMed labels) |
| **Coverage** | All 6 approved CAR-T products -- BLA review packages contain detailed Phase 2/3 safety data with granular AE tables |
| **Cost** | Free |
| **Limitations** | Data is embedded in PDF documents -- requires NLP/OCR extraction. Tables vary in format across products. One-time data (approval snapshot), not updated. |
| **Feasibility** | MEDIUM -- PDF parsing is feasible but requires per-document tuning. High-value one-time data extraction. |

### 2.7 REMS Databases (Risk Evaluation and Mitigation Strategy)

| Attribute | Detail |
|-----------|--------|
| **Organization** | FDA |
| **URL** | https://www.accessdata.fda.gov/scripts/cder/rems/ |
| **Access Method** | REMS@FDA website; individual product REMS sites |
| **Data Format** | PDF documents, web pages |
| **Coverage** | Previously covered all CAR-T products. NOTE: As of July 2025, FDA eliminated REMS for all currently approved CD19/BCMA-directed CAR-T products. |
| **Cost** | Free |
| **Limitations** | REMS programs have been eliminated for CAR-T products. Historical REMS data (certification records, training completion) was not publicly available at case level. Manufacturers still required to conduct 15-year post-marketing observational safety studies. |
| **Feasibility** | LOW -- REMS programs discontinued. Post-marketing study data flows into FAERS. |

### 2.8 CIBMTR (Center for International Blood and Marrow Transplant Research)

| Attribute | Detail |
|-----------|--------|
| **Organization** | CIBMTR (MCW/NMDP) |
| **URL** | https://cibmtr.org/ |
| **Access Method** | Formal research collaboration; de-identified datasets via data request; research proposal submission |
| **Data Format** | SAS/CSV datasets (de-identified); FormsNet data collection system |
| **Coverage** | ~10,347 first CAR-T recipients as of September 2023 (60-70% of US CAR-T therapies); 195 US reporting centers. Captures CRS/ICANS grading, infection data, cytokine levels, and long-term outcomes. |
| **Cost** | Free for approved research collaborations; data use agreement required |
| **Limitations** | Requires formal research proposal and IRB approval. Data access takes months. US-centric (some international sites). Voluntary reporting -- not all centers participate. |
| **Feasibility** | HIGH VALUE but LOW AUTOMATION -- richest CAR-T safety dataset in existence but requires institutional partnership. Cannot be programmatically accessed. |

### 2.9 EBMT (European Society for Blood and Marrow Transplantation)

| Attribute | Detail |
|-----------|--------|
| **Organization** | EBMT |
| **URL** | https://www.ebmt.org/registry/ebmt-registry |
| **Access Method** | Research proposal submission via EBMT Studies page; data retrieval through EBMT data office |
| **Data Format** | Registry database export (format negotiated per study) |
| **Coverage** | 806,518 patients total; 17,220 CAR-T treatments as of January 2026. European centers primarily. Captures effectiveness and safety data on CRS, ICANS, and other AEs of special interest. EMA-qualified registry. |
| **Cost** | Membership/collaboration required |
| **Limitations** | Formal study proposal required. European-focused. Data sharing negotiations ongoing. Not publicly downloadable. |
| **Feasibility** | HIGH VALUE but LOW AUTOMATION -- comparable to CIBMTR for European data. Requires institutional partnership. |

### 2.10 JADER (Japanese Adverse Drug Event Report Database)

| Attribute | Detail |
|-----------|--------|
| **Organization** | PMDA (Pharmaceuticals and Medical Devices Agency, Japan) |
| **URL** | https://www.pmda.go.jp/ |
| **Access Method** | Bulk CSV download from PMDA website |
| **Data Format** | CSV files (quarterly releases) |
| **Coverage** | Japanese market adverse event reports including CAR-T products approved in Japan |
| **Cost** | Free |
| **Limitations** | Japanese language data fields. Smaller volume than FAERS. Japan-specific products and indications. |
| **Feasibility** | MEDIUM -- downloadable but requires Japanese text processing. |

### 2.11 WHO ICTRP (International Clinical Trials Registry Platform)

| Attribute | Detail |
|-----------|--------|
| **Organization** | WHO |
| **URL** | https://trialsearch.who.int/ |
| **Access Method** | Web search portal; bulk XML download available |
| **Data Format** | XML |
| **Coverage** | Aggregates trial registrations from 17 primary registries worldwide including ClinicalTrials.gov, EU-CTR, and others |
| **Cost** | Free |
| **Limitations** | Registry-level metadata only -- does not contain results or AE data. Useful for identifying trials registered outside ClinicalTrials.gov that might have AE data reported elsewhere. |
| **Feasibility** | LOW for AE data directly -- useful as a discovery tool for finding trials in non-US registries. |

### 2.12 Europe PMC / OpenAlex / Semantic Scholar

| Attribute | Detail |
|-----------|--------|
| **Organization** | EMBL-EBI / OurResearch / Allen AI |
| **URLs** | https://europepmc.org/, https://openalex.org/, https://api.semanticscholar.org/ |
| **Access Method** | REST APIs |
| **Data Format** | JSON |
| **Coverage** | Complement PubMed with full-text access (Europe PMC), citation networks, and semantic search capabilities |
| **Cost** | Free |
| **Limitations** | Same NLP challenges as PubMed. Overlapping coverage. |
| **Feasibility** | MEDIUM -- supplementary to PubMed E-utilities. |

---

## 3. Prototype Results

### 3.1 ClinicalTrials.gov Extraction Results

**Script:** `analysis/ct_gov_extractor.py`
**Output:** `analysis/results/ct_gov_ae_data.json` (6.3 MB)
**Runtime:** 20.7 seconds

| Metric | Value |
|--------|-------|
| Total completed CAR-T trials found | 201 |
| Trials with posted results | 47 (23%) |
| Trials with structured AE data | 47 |
| Unique serious AE types | 805 |
| Unique other (non-serious) AE types | 1,243 |
| CRS-related events found | 167 instances across trials |
| ICANS-related events found | 167 instances across trials |

**Top 10 Serious Adverse Events (by total patients affected across all trials):**

| Rank | Adverse Event | Total Affected | Number of Trials |
|------|--------------|----------------|-----------------|
| 1 | Cytokine release syndrome | 362 | 20 |
| 2 | Febrile neutropenia | 359 | 27 |
| 3 | Hypotension | 204 | 28 |
| 4 | Pyrexia | 193 | 21 |
| 5 | Encephalopathy | 172 | 24 |
| 6 | Pneumonia | 136 | 20 |
| 7 | Hypoxia | 97 | 23 |
| 8 | Cytokine Release Syndrome (variant casing) | 96 | 7 |
| 9 | Sepsis | 80 | 22 |
| 10 | Fever | 72 | 14 |

**Notable trials with large AE datasets:**
- NCT02348216 (ZUMA-1, axicabtagene ciloleucel): 181 serious AE types, 210 other AE types, 14 treatment groups
- NCT02601313 (ZUMA-2, brexucabtagene autoleucel): 113 serious, 215 other AE types
- NCT03391466 (ZUMA-7, axi-cel vs SOC): 167 serious, 94 other AE types
- NCT03361748 (KarMMa, ide-cel): 147 serious, 80 other AE types

### 3.2 FAERS Product Comparison Results

**Script:** `analysis/enhanced_faers.py`
**Output:** `analysis/results/faers_product_comparison.json` (99 KB)
**Runtime:** 159.2 seconds

#### Total Reports by Product

| Product | Target | Total FAERS Reports | Approval Date |
|---------|--------|-------------------:|---------------|
| Yescarta (axi-cel) | CD19 | 6,410 | 2017-10-18 |
| Carvykti (cilta-cel) | BCMA | 3,767 | 2022-02-28 |
| Kymriah (tisa-cel) | CD19 | 3,591 | 2017-08-30 |
| Tecartus (brexu-cel) | CD19 | 1,262 | 2020-07-24 |
| Abecma (ide-cel) | BCMA | 879 | 2021-03-26 |
| Breyanzi (liso-cel) | CD19 | 523 | 2021-02-05 |

#### CRS Reporting Rates

| Product | CRS Reports | Rate (% of total reports) |
|---------|------------:|------------------------:|
| Abecma | 537 | 61.1% |
| Tecartus | 668 | 52.9% |
| Yescarta | 3,337 | 52.1% |
| Breyanzi | 237 | 45.3% |
| Kymriah | 1,421 | 39.6% |
| Carvykti | 522 | 13.9% |

#### Neurotoxicity Reporting Rates (combined: neurotoxicity + encephalopathy + ICANS)

| Product | Neurotox Reports | Rate (% of total reports) |
|---------|------------------:|------------------------:|
| Tecartus | 1,064 | 84.3% |
| Yescarta | 4,349 | 67.9% |
| Breyanzi | 292 | 55.8% |
| Abecma | 334 | 38.0% |
| Kymriah | 1,104 | 30.7% |
| Carvykti | 508 | 13.5% |

#### Secondary Malignancy Reporting Rates (T-cell lymphoma + MDS + AML)

| Product | Malignancy Reports | Rate |
|---------|-----------------:|-----:|
| Kymriah | 128 | 3.56% |
| Abecma | 27 | 3.07% |
| Breyanzi | 12 | 2.29% |
| Yescarta | 129 | 2.01% |
| Carvykti | 57 | 1.51% |
| Tecartus | 13 | 1.03% |

#### Mortality Reporting Rates

| Product | Death Reports | Rate |
|---------|--------------:|-----:|
| Tecartus | 142 | 11.25% |
| Yescarta | 664 | 10.36% |
| Kymriah | 276 | 7.69% |
| Abecma | 41 | 4.66% |
| Breyanzi | 21 | 4.02% |
| Carvykti | 137 | 3.64% |

**Key Observations:**
- CD19-targeting products (Yescarta, Tecartus, Kymriah) show higher neurotoxicity rates than BCMA-targeting products (Abecma, Carvykti)
- Carvykti shows notably lower CRS reporting rate (13.9%) despite high total reports, possibly reflecting delayed CRS onset or different reporting patterns
- Secondary malignancy reporting is consistent across products (1-3.5%), though this is an area of active FDA surveillance
- Carvykti shows a unique parkinsonism signal (206 reports, 5.5%) not prominent with other products

---

## 4. Data Extraction Approaches

### 4.1 openFDA API for FAERS Data

**Status: IMPLEMENTED AND WORKING**

Approach:
- Query `patient.drug.medicinalproduct` for each CAR-T brand name
- Use `count` endpoint for top AE terms, demographics, reporting trends
- Use `search` with `AND` operator for specific AE term counts
- Rate limit to 0.15-0.3 second delay between requests

Enhancements possible:
- Add disproportionality analysis (PRR, ROR) comparing CAR-T AE rates to background rates
- Time-series analysis of reporting patterns by quarter
- Drug interaction analysis (concomitant medications)
- Signal detection for emerging safety signals

### 4.2 ClinicalTrials.gov API for Clinical Trial Safety Data

**Status: IMPLEMENTED AND WORKING**

Approach:
- Search API v2 with intervention terms for CAR-T/chimeric antigen receptor
- Filter on `overallStatus=COMPLETED`
- Fetch full study records including `resultsSection.adverseEventsModule`
- Parse three-table AE structure (mortality, serious, other) with group-level counts

Enhancements possible:
- Expand search to ACTIVE/RECRUITING trials for protocol-level AE monitoring plans
- Link trial NCT IDs to published results via PubMed
- Extract outcome measure data alongside AE data
- Build longitudinal view across multiple data cutoffs for same trial

### 4.3 PubMed E-utilities for Literature Mining

**Status: DESIGN PHASE**

Proposed approach:
1. Use ESearch to identify CAR-T AE publications with query like:
   `("CAR-T" OR "chimeric antigen receptor") AND ("adverse event" OR "safety" OR "toxicity" OR "CRS" OR "ICANS")`
2. Use EFetch to retrieve abstracts and available full text
3. Apply NLP extraction for:
   - AE term identification (MedDRA mapping)
   - Incidence rate extraction (regex + NLP for "X% of patients experienced...")
   - Patient population characteristics
   - Grading scale information (CTCAE, Lee CRS grading)
4. Cross-reference with ClinicalTrials.gov NCT IDs

Implementation requirements:
- NLP model for biomedical named entity recognition (BioBERT, PubMedBERT, or ScispaCy)
- MedDRA term dictionary for standardized AE coding
- Regular expression patterns for numeric extraction (rates, counts, confidence intervals)

### 4.4 NLP-Based Extraction from FDA Review Documents

**Status: DESIGN PHASE**

Proposed approach:
1. Download BLA review PDFs from Drugs@FDA for all 6 CAR-T products
2. Extract text with PDF parsing (PyMuPDF/pdfplumber)
3. Identify and extract safety tables from review sections
4. Parse tabular data for AE terms, incidence rates, grading
5. Extract narrative safety findings

Implementation requirements:
- PDF table extraction library (camelot, tabula-py, or pdfplumber)
- Custom table schema mapping per document format
- NLP pipeline for safety narrative analysis

---

## 5. Feasibility Assessment

### Tier 1: Immediately Actionable (Automated, Free API Access)

| Database | Implementation Status | Effort | Data Value |
|----------|----------------------|--------|------------|
| **FAERS/openFDA** | COMPLETE (prototype working) | 1 week to production | HIGH -- 16K+ CAR-T reports |
| **ClinicalTrials.gov** | COMPLETE (prototype working) | 1 week to production | HIGH -- 47 trials with structured AE data |
| **PubMed E-utilities** | API access confirmed | 2-3 weeks (includes NLP) | MEDIUM-HIGH |
| **DailyMed (labels)** | API available | 1 week | MEDIUM (structured label data) |

### Tier 2: Feasible with Moderate Effort

| Database | Access Method | Effort | Data Value |
|----------|--------------|--------|------------|
| **EudraVigilance** | Web scraping or formal access request | 2-4 weeks | MEDIUM-HIGH (European data) |
| **FDA BLA Reviews** | PDF parsing + NLP | 3-4 weeks | HIGH (detailed trial-level data) |
| **JADER** | CSV download + Japanese NLP | 2-3 weeks | LOW-MEDIUM (Japan only) |
| **Semantic Scholar/OpenAlex** | API integration | 1-2 weeks | MEDIUM (supplementary) |

### Tier 3: Requires Institutional Partnership

| Database | Access Method | Effort | Data Value |
|----------|--------------|--------|------------|
| **CIBMTR** | Research proposal + data use agreement | 3-6 months | VERY HIGH (patient-level data) |
| **EBMT** | Research proposal + collaboration | 3-6 months | VERY HIGH (European patient-level data) |
| **VigiBase (full)** | UMC collaboration request | 2-4 months | HIGH (global data) |

---

## 6. Recommended Next Steps

### Phase 1: Production-Quality Data Pipeline (Weeks 1-3)

1. **Harden FAERS extractor** -- Add error handling, incremental updates, deduplication logic, and store results in structured format for ongoing monitoring
2. **Harden ClinicalTrials.gov extractor** -- Add MedDRA term normalization, handle variant AE term spellings, link to product names
3. **Build data harmonization layer** -- Map AE terms across sources to MedDRA preferred terms; normalize product names
4. **Set up scheduled extraction** -- Quarterly FAERS updates, monthly ClinicalTrials.gov scans

### Phase 2: Expand Data Sources (Weeks 4-8)

5. **Implement PubMed literature miner** -- Build NLP pipeline for AE extraction from abstracts; use BioBERT or similar biomedical NLP
6. **Extract FDA BLA review data** -- Download and parse PDFs for all 6 CAR-T products; extract safety tables and narratives
7. **Scrape EudraVigilance public data** -- Build web scraper for adrreports.eu to get European AE counts
8. **Integrate DailyMed label data** -- Extract structured prescribing information AE sections

### Phase 3: Institutional Data Access (Months 3-6)

9. **Submit CIBMTR research proposal** -- Draft protocol for CAR-T safety analysis using CIBMTR registry data
10. **Explore EBMT collaboration** -- Contact EBMT data office for potential research partnership
11. **Request VigiBase access** -- Apply through UMC for research-grade global pharmacovigilance data

### Phase 4: Advanced Analytics (Months 4-8)

12. **Disproportionality analysis** -- Implement PRR, ROR, EBGM calculations for signal detection
13. **Cross-database integration** -- Build unified AE dataset combining all sources with deduplication
14. **Predictive modeling** -- Train models on combined dataset for CRS/ICANS risk prediction
15. **Dashboard** -- Build real-time safety monitoring dashboard with automated signal detection

---

## 7. Effort Estimates

| Task | Estimated Effort | Priority |
|------|-----------------|----------|
| FAERS production pipeline | 1 week | P0 |
| ClinicalTrials.gov production pipeline | 1 week | P0 |
| MedDRA term harmonization layer | 1 week | P0 |
| PubMed literature mining prototype | 2-3 weeks | P1 |
| FDA BLA PDF extraction | 3-4 weeks | P1 |
| EudraVigilance web scraper | 2 weeks | P1 |
| DailyMed label integration | 1 week | P2 |
| Disproportionality analysis module | 2 weeks | P1 |
| CIBMTR proposal preparation | 2-4 weeks | P2 |
| EBMT collaboration initiation | 2-4 weeks | P2 |
| Cross-database integration | 3-4 weeks | P2 |
| Safety monitoring dashboard | 4-6 weeks | P3 |
| **Total estimated effort** | **~6-8 months for full implementation** | |

---

## Appendix: File Inventory

| File | Description | Size |
|------|-------------|------|
| `analysis/ct_gov_extractor.py` | ClinicalTrials.gov extraction script | 10 KB |
| `analysis/enhanced_faers.py` | FAERS product comparison script | 19 KB |
| `analysis/results/ct_gov_ae_data.json` | ClinicalTrials.gov extraction results | 6.3 MB |
| `analysis/results/faers_product_comparison.json` | FAERS product comparison results | 99 KB |
| `analysis/ae_database_research.md` | This research report | -- |
