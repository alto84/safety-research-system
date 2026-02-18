# CAR-T Cell Therapy Safety Monitoring & Pharmacovigilance: Innovation Research Brief

**Date:** 2026-02-17
**Scope:** Latest innovations in CAR-T safety monitoring, pharmacovigilance tools, regulatory updates, datasets, and AI/ML approaches applicable to the Safety Research System.

---

## 1. Latest CAR-T Safety Publications & Signals (2025-2026)

### 1.1 Secondary Malignancy -- The Defining Safety Signal

The most significant safety signal in recent CAR-T pharmacovigilance is the emergence of T-cell malignancies (including CAR-positive lymphomas) following BCMA-directed and CD19-directed autologous CAR-T therapy.

**Key findings:**
- By April 2024, 38 cases of T-cell malignancy after CAR-T therapy were reported in patients aged 29-80 years. In 19 patients where tumor samples were tested for the CAR transgene, it was detected in 7 cases. Most T-cell malignancies were diagnosed within 12 months of treatment (22/33; 67%). The reporting rate is approximately 1 case per 1,000 patients treated.
- An FAERS analysis found second primary malignancies occurred in 4.3% (536/12,394) of adverse event reports in CAR-T patients.
- The Paul-Ehrlich-Institut published a landmark analysis arguing that these findings challenge current pharmacovigilance concepts, particularly around causality assessment -- molecular testing for vector integration is often lacking.
- The FDA now requires lifelong monitoring for secondary malignancies in all CAR-T recipients.

**Sources:**
- [FDA Boxed Warning Requirement for T-Cell Malignancies](https://www.fda.gov/vaccines-blood-biologics/safety-availability-biologics/fda-requires-boxed-warning-t-cell-malignancies-following-treatment-bcma-directed-or-cd19-directed)
- [FDA Safety Communication -- Serious Risk of T-Cell Malignancy](https://www.fda.gov/safety/medical-product-safety-information/bcma-directed-or-cd19-directed-autologous-chimeric-antigen-receptor-car-t-cell-immunotherapies-fda)
- [Second Primary Malignancies After Commercial CAR-T: FAERS Analysis (Blood/ASH)](https://ashpublications.org/blood/article/143/20/2099/515310/Second-primary-malignancies-after-commercial-CAR-T)
- [CAR-T Secondary Malignancies Challenge Pharmacovigilance Concepts (EMBO Mol Med / PEI)](https://link.springer.com/article/10.1038/s44321-024-00183-2)
- [PEI Press Release: CAR T-Cell Therapies Pharmacovigilance Challenges](https://www.pei.de/EN/newsroom/press-releases/year/2025/01-car-t-cell-therapies-pharmacovigilance-challenges.html)
- [EMA Evaluation of 38 Suspected Cases of Secondary T-Cell Malignancy](https://www.nature.com/articles/s41434-025-00586-x)
- [PEI: CAR T-Cell Therapy and Secondary Tumour Development](https://www.pei.de/EN/newsroom/hp-news/2025/251222-bulletin-article-car-t-cell-therapy.html)

**Implementation relevance:** The safety research system should model the secondary malignancy signal as a primary use case. Build detection pipelines that can identify disproportionate reporting of secondary cancers across CAR-T products using FAERS data. The causality assessment challenge (CAR transgene detection) is an opportunity for structured data capture modeling.

### 1.2 Product-Specific Safety Signals from FAERS

A comprehensive FAERS analysis of BCMA-directed CAR-T therapies (cilta-cel and ide-cel) revealed distinct safety profiles:

**Ide-cel (Abecma) signals:** Parkinsonism, sarcoidosis, ventricular arrhythmias, cardiac arrest, confusion, disorientation, seizures, balance disturbances, tremors.

**Cilta-cel (Carvykti) signals:** Cranial nerve palsies, Parkinson's disease/parkinsonism, Guillain-Barre syndrome, intracranial hemorrhage, cerebrovascular accidents, Haemophilus and cytomegalovirus infections.

A global population-based study identified 266 adverse events as safety signals, including 59 high-fatality events (pulmonary hemorrhage, lactic acidosis, etc.).

**Sources:**
- [Neurotoxicity and Rare AEs in BCMA-Directed CAR-T: FAERS Data (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S2666636724008030)
- [Prognostic Implications of AEs Associated with CAR-T (eClinicalMedicine/Lancet)](https://www.thelancet.com/journals/eclinm/article/PIIS2589-5370(25)00557-7/fulltext)
- [Second Primary Malignancies Post CAR-T: FAERS and VigiBase (eClinicalMedicine)](https://www.thelancet.com/journals/eclinm/article/PIIS2589-5370(24)00263-3/fulltext)
- [Post-Marketing Surveillance of CAR-T: FAERS Analysis (Drug Safety/Springer)](https://link.springer.com/article/10.1007/s40264-022-01194-z)

**Implementation relevance:** Replicate the disproportionality analysis methodology for CAR-T products. The product-specific signal differentiation (cilta-cel vs. ide-cel) demonstrates the value of comparative safety analytics that the system should support.

### 1.3 Evolving Pharmacovigilance Frameworks for CGTs

A comprehensive 2025 review in Drug Safety articulates the unique pharmacovigilance challenges for cell and gene therapies, including: risk-adaptive digitally-enabled pharmacovigilance models, AI-based signal detection, seamless pediatric-to-adult follow-up requirements, and attention to atypical presentations missed by clinical trial safety capture.

**Sources:**
- [Pharmacovigilance in Cell and Gene Therapy: Evolving Challenges (Drug Safety)](https://link.springer.com/article/10.1007/s40264-025-01596-9)
- [Pharmacovigilance in Cell and Gene Therapy (PubMed)](https://pubmed.ncbi.nlm.nih.gov/40783602/)
- [CAR-T Therapy in 2025: Approvals, Advances, Risk-Monitoring (Precision Medicine Online)](https://www.precisionmedicineonline.com/precision-oncology/car-t-therapy-2025-new-approvals-vivo-advances-and-risk-monitoring-rollbacks)

**Implementation relevance:** The safety research system should incorporate the risk-adaptive monitoring framework. This means building configurable risk tiers and monitoring intensity levels that can be adjusted as real-world evidence accumulates.

---

## 2. Open-Source Pharmacovigilance Tools

### 2.1 DiAna (R Package) -- FAERS Disproportionality Analysis

The most mature and actively maintained open-source tool for FAERS pharmacovigilance analysis. DiAna provides automated FAERS data import, cleaning, case retrieval, descriptive analysis, and disproportionality analysis. Includes a standardized drug name dictionary mapping free-text to active ingredients and ATC codes.

- **GitHub:** https://github.com/fusarolimichele/DiAna_package
- **Docs:** https://fusarolimichele.github.io/DiAna_package/
- **Data repository (OSF):** https://osf.io/zqu89/
- **Key paper:** [Enhancing Transparency in Defining Studied Drugs: DiAna Dictionary (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10874306/)

**Integration potential: HIGH.** The DiAna dictionary for drug name standardization and its disproportionality analysis methods (ROR, PRR, BCPNN, MGPS) could be adapted into Python equivalents for the safety research system. The cleaned FAERS data on OSF is immediately usable.

### 2.2 MDDC (R and Python) -- Multi-Item Adverse Event Identification

A recently published (2025) package for identifying adverse events in pharmacovigilance data using modified detecting deviating cells (MDDC) algorithms. Available in both R and Python.

- **Paper:** [MDDC: An R and Python Package for AE Identification (Scientific Reports)](https://www.nature.com/articles/s41598-025-00635-w)
- **arXiv:** https://arxiv.org/html/2410.01168v1

**Integration potential: HIGH.** Already has a Python implementation. The multi-item approach detects adverse event clusters rather than individual drug-event pairs, which is particularly relevant for CAR-T therapies that present with complex multi-system toxicity patterns.

### 2.3 FAERS_PHARMACOVIGILANCE_ANALYSIS (Python/Jupyter)

A Jupyter notebook implementing pharmacovigilance signal detection on FAERS data, calculating ROR, PRR, RRR, and Haldane's Odds Ratio with 95% CIs. Includes VigiMatch-style deduplication.

- **GitHub:** https://github.com/DSimoens/FAERS_PHARMACOVIGILANCE_ANALYSIS

**Integration potential: MEDIUM.** Good reference implementation for signal detection metrics. The VigiMatch deduplication logic is valuable. However, it is a notebook rather than a library, so would need refactoring.

### 2.4 faers (R Package)

R interface for FAERS providing data download, parsing, and analysis pipeline.

- **GitHub:** https://github.com/Yunuuuu/faers (also listed as https://github.com/WangLabCSU/faers)

**Integration potential: LOW-MEDIUM.** R-only, but the data parsing logic could inform Python implementations.

### 2.5 OpenVigil

Web-based open tools for FAERS data mining and signal detection.

- **Website:** https://openvigil.sourceforge.net/

**Integration potential: LOW.** Web-based tool rather than a library. Useful as a reference/validation endpoint.

### 2.6 openFDA (Official FDA API and Tools)

The FDA's own open-source API and data pipeline for FAERS data access.

- **API:** https://open.fda.gov/
- **GitHub:** https://github.com/FDA/openfda
- **FAERS data:** https://open.fda.gov/data/faers/
- **Downloads:** https://open.fda.gov/data/downloads/

**Integration potential: HIGH.** The openFDA API should be the primary data source for the safety research system. Supports real-time queries and bulk data downloads in JSON format.

### 2.7 OpenPVSignal Knowledge Graph

A FAIR-compliant data model for representing pharmacovigilance signal reports in a computationally exploitable format. Converts WHO-UMC signals into a knowledge graph.

- **Paper:** [OpenPVSignal Knowledge Graph (Drug Safety/Springer)](https://link.springer.com/article/10.1007/s40264-024-01503-8)

**Integration potential: MEDIUM-HIGH.** The FAIR data model and knowledge graph approach aligns well with the safety research system's knowledge graph design. Could serve as the reference architecture for signal representation.

---

## 3. Regulatory Updates (2025-2026)

### 3.1 FDA Eliminates REMS for All Approved CAR-T Therapies (June 2025)

On June 26, 2025, the FDA eliminated Risk Evaluation and Mitigation Strategies (REMS) for all seven approved BCMA- and CD19-directed autologous CAR-T therapies. The agency determined that REMS is no longer necessary given the hematology/oncology community's established experience managing CRS and neurologic toxicities. This removes the requirement for hospital/clinic certification and on-site tocilizumab access.

**Affected products:** Kymriah, Yescarta, Tecartus, Breyanzi, Abecma, Carvykti, Aucatzyl.

**Sources:**
- [FDA Eliminates REMS for Approved CAR-T Therapies (AABB)](https://www.aabb.org/news-resources/news/article/2025/06/30/fda-eliminates-rems-for-approved-car-t-cell-therapies)
- [FDA Removes REMS Programs for All CAR-T Therapies (OncLive)](https://www.onclive.com/view/fda-removes-rems-programs-for-all-currently-approved-cd19--and-bcma-directed-car-t-cell-therapies-in-hematologic-malignancies)
- [FDA Expands Access to CAR-T by Eliminating REMS (AJMC)](https://www.ajmc.com/view/fda-expands-access-to-approved-car-t-cell-therapies-by-eliminating-rems)
- [Impact of FDA Eliminating REMS (BioPharm International)](https://www.biopharminternational.com/view/biopharm-industry-impacts-of-fda-eliminating-rems-for-car-t-therapies)
- [FDA's REMS Elimination Explained (WCG)](https://www.wcgclinical.com/insights/fdas-elimination-of-rems-for-car-t-cell-therapies/)

**Implementation relevance:** The REMS elimination shifts monitoring burden from pre-treatment certification to post-treatment surveillance. The safety research system should model this shift and track whether AE reporting patterns change post-REMS-elimination (a natural experiment in pharmacovigilance policy).

### 3.2 FDA Boxed Warning for T-Cell Malignancies (January 2024, ongoing)

The FDA mandated class-wide boxed warnings on all approved CAR-T therapies for the risk of secondary T-cell malignancies. This applies to all six BCMA- and CD19-directed products. Patients must be monitored lifelong.

**Source:**
- [FDA Requires Boxed Warning for T-Cell Malignancies](https://www.fda.gov/vaccines-blood-biologics/safety-availability-biologics/fda-requires-boxed-warning-t-cell-malignancies-following-treatment-bcma-directed-or-cd19-directed)

### 3.3 FDA Draft Guidance: Postapproval Methods for CGT Products (September 2025)

FDA/CBER issued draft guidance on postapproval monitoring for cell and gene therapy products. Key points:
- Emphasizes real-world data (RWD) sources for post-market safety and efficacy tracking.
- Addresses 15-year long-term follow-up requirements for gene therapy products.
- Describes benefits and limitations of different data collection methods.
- Comments were due November/December 2025.

**Sources:**
- [FDA Draft Guidance: Postapproval Methods for CGT Products](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/postapproval-methods-capture-safety-and-efficacy-data-cell-and-gene-therapy-products)
- [Draft Guidance PDF](https://www.fda.gov/media/188891/download)
- [Federal Register Notice](https://www.federalregister.gov/documents/2025/09/25/2025-18650/postapproval-methods-to-capture-safety-and-efficacy-data-for-cell-and-gene-therapy-products-draft)
- [Analysis: Strengthening Postapproval Monitoring (FDA Law Blog)](https://www.thefdalawblog.com/2025/10/strengthening-postapproval-monitoring-fdas-draft-guidance-on-cell-gene-therapy-products/)
- [Ropes & Gray Analysis of FDA's CGT Draft Guidances](https://www.ropesgray.com/en/insights/alerts/2025/11/rare-disease-focus-fdas-trio-of-cell-and-gene-therapy-draft-guidances-highlight-expedited-programs)

### 3.4 FDA New Superiority Standard for CAR-T Approvals (December 2025)

CBER leadership published a JAMA Perspective in December 2025 outlining that future CAR-T approvals will generally require randomized controlled trials demonstrating superiority over standard of care, rather than single-arm trials. This represents a major shift from the current approval pathway used for all seven existing approvals.

**Sources:**
- [FDA Outlines New Superiority Standard for CAR-T (Applied Clinical Trials)](https://www.appliedclinicaltrialsonline.com/view/fda-outlines-new-superiority-standard-future-car-t-approvals)
- [FDA Leaders Outline New Regulatory Framework for CAR-T (AABB)](https://www.aabb.org/news-resources/news/article/2025/12/12/fda-leaders-outline-new-regulatory-framework-for-oncologic-car-t-cell-therapy-approvals)
- [FDA to Tighten Approval Requirements for CAR-T (RAPS)](https://www.raps.org/news-and-articles/news-articles/2025/12/fda-to-tighten-approval-requirements-for-car-t-cel)

### 3.5 EMA ATMP Guideline Effective July 2025

The EMA guideline on quality, non-clinical, and clinical requirements for investigational ATMPs in clinical trials came into effect on July 1, 2025, after six years of development.

**Source:**
- [EMA ATMP Guideline Takes Effect (Cell & Gene)](https://www.cellandgene.com/doc/ema-guideline-on-clinical-stage-atmps-comes-into-effect-on-the-verge-of-convergence-0001)

### 3.6 CBER 2026 Guidance Agenda

The FDA released its 2026 CBER guidance agenda, which includes finalization of the "Postapproval Methods to Capture Safety and Efficacy Data for Cell and Gene Therapy Products" guidance.

**Source:**
- [FDA Releases 2026 CBER Guidance Agenda (AABB)](https://www.aabb.org/news-resources/news/article/2026/01/12/regulatory-update--fda-releases-2026-cber-guidance-agenda)

**Implementation relevance:** The system should incorporate the FDA's postapproval monitoring framework as a reference model. The emphasis on RWD sources validates the FAERS-based approach. The new superiority standard will generate more comparative safety data in future trials, which the system should be prepared to ingest.

---

## 4. Datasets and Data Sources

### 4.1 FAERS (FDA Adverse Event Reporting System)

The primary pharmacovigilance database. Available via:
- **openFDA API:** https://open.fda.gov/data/faers/ (real-time JSON queries)
- **Quarterly Data Extracts:** https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html (bulk CSV/ASCII downloads)
- **openFDA Downloads:** https://open.fda.gov/data/downloads/ (bulk JSON)
- **openFDA GitHub:** https://github.com/FDA/openfda (API source code and data pipeline)

**R tools for automated download:**
- `faersquarterlydata` R package: https://luisgarcez11.r-universe.dev/faersquarterlydata

### 4.2 DiAna Cleaned FAERS Data (OSF)

Pre-cleaned, deduplicated FAERS data maintained by the DiAna project. Available for direct download.
- **OSF repository:** https://osf.io/zqu89/

**Integration relevance: HIGH.** Using pre-cleaned data eliminates the substantial data wrangling overhead of raw FAERS files.

### 4.3 AEOLUS (Curated FAERS Dataset)

A curated and standardized adverse drug event resource built on FAERS data, designed to accelerate drug safety research. Maps drug names to RxNorm and outcomes to SNOMED-CT.
- **Paper:** [AEOLUS: Curated ADE Resource (Scientific Data/Nature)](https://www.nature.com/articles/sdata201626)

### 4.4 VigiBase (WHO Global ICSR Database)

The WHO Uppsala Monitoring Centre's global database of individual case safety reports. Used in several recent CAR-T safety studies alongside FAERS for cross-validation.
- Referenced in: [Second Primary Malignancies: FAERS and VigiBase (eClinicalMedicine)](https://www.thelancet.com/journals/eclinm/article/PIIS2589-5370(24)00263-3/fulltext)

**Note:** VigiBase access requires WHO-UMC membership/agreement, so it is less immediately available than FAERS.

### 4.5 ClinicalTrials.gov

FDA has over 2,500 active INDs for CGTs and approximately 1,300 active INDs for gene therapies. ClinicalTrials.gov provides structured trial data including safety endpoints.
- **API:** https://www.clinicaltrials.gov/
- **CAR-T specific trial landscape:** [CAR-T Clinical Trials: Global Progress (Frontiers)](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2025.1583116/full)

### 4.6 FAERS Essentials Guide (2025)

A comprehensive guide published in 2025 on understanding, applying, and interpreting FAERS data, covering methodological best practices.
- **Paper:** [FAERS Essentials Guide (Clinical Pharmacology & Therapeutics)](https://ascpt.onlinelibrary.wiley.com/doi/10.1002/cpt.3701?af=R)
- **PMC:** https://pmc.ncbi.nlm.nih.gov/articles/PMC12393772/

---

## 5. AI/ML in Pharmacovigilance

### 5.1 LLMs for Automated FAERS Querying

A 2025 study demonstrated using GPT-4 with retrieval-augmented generation (RAG) to convert natural language queries into SQL queries against pharmacovigilance databases. Key results:
- With database schema alone: 8.3% pass rate.
- With business context documents added: 85.4% pass rate on low/medium complexity queries (only 5/48 failures).
- The "business context document" approach distills pharmacovigilance domain knowledge into plain language to guide the LLM.

**Sources:**
- [Automating PV Evidence Generation: LLMs for Context-Aware SQL (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11806702/)
- [arXiv preprint](https://arxiv.org/pdf/2406.10690)

**Implementation relevance: HIGH.** This is directly implementable. Build a natural language query interface over the safety research system's data using RAG with domain-specific pharmacovigilance context documents. This would dramatically lower the barrier for safety scientists to explore FAERS data.

### 5.2 LLMs for Adverse Drug Event Extraction from Clinical Text

Multiple 2025 publications demonstrate transformer-based models (BERT, GPT series) for:
- Entity recognition: identifying drug names, adverse effect terms, patient characteristics.
- Relation extraction: linking drugs to adverse events in unstructured text.
- Case narrative parsing: auto-populating database fields from doctor's narratives.

**Sources:**
- [Large Language Models for Adverse Drug Events: Clinical Perspective (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347610/)
- [NLP and ML for ADE Detection in EHR: Scoping Review (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11903561/)
- [Generative AI and LLMs in Mitigating Medication-Related Harm (npj Digital Medicine)](https://www.nature.com/articles/s41746-025-01565-7)
- [AI in Pharmacovigilance: Advancing Drug Safety Monitoring (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12317250/)

**Implementation relevance: HIGH.** Build NLP pipelines for extracting structured adverse event data from unstructured case narratives in FAERS. Use fine-tuned models for CAR-T-specific entity recognition (CRS grading, ICANS scoring, etc.).

### 5.3 Agentic LLM for Pharmacovigilance Automation

Tech Mahindra has developed "PV Agentic LLM" -- an AI-powered solution for automating adverse event intake, processing, and analysis. It handles unstructured safety data and improves regulatory compliance.

**Source:**
- [PV Agentic LLM (Tech Mahindra)](https://www.techmahindra.com/industries/healthcare-life-sciences/pharmacovigilance-agentic-llm/)

**Implementation relevance: MEDIUM.** Commercial product, but the agentic architecture pattern (LLM agents that can autonomously process, classify, and route safety reports) is worth replicating in open-source form.

### 5.4 Graph Neural Networks for ADR Prediction

**PreciseADR (2025, Advanced Science):** Uses heterogeneous graph neural networks to predict patient-level adverse drug reactions by integrating relationships between patients, diseases, drugs, and ADRs. Enables tailored, patient-specific early ADR detection.

**Drug-Disease Graph:** A novel GNN-based framework using healthcare claims data to construct drug-disease interaction graphs for ADR signal detection. GNNs learn node representations indicative of drug-disease relationships and predict ADR signals.

**Subgraph Analysis:** GNN-based subgraph analysis identifies localized patterns in drug-event networks to predict previously unknown adverse drug events.

**Sources:**
- [PreciseADR: Heterogeneous GNN for ADR Prediction (Advanced Science/Wiley)](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202404671)
- [Drug-Disease Graph: GNN for ADR Signal Detection (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7206286/)
- [GNN-Based Subgraph Analysis for Predicting ADEs (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S0010482524013672)
- [GNN for Predicting Side Effects and New Indications (Springer)](https://link.springer.com/chapter/10.1007/978-3-031-83097-6_9)
- [GNN for Drug-Drug Interaction Prediction (MDPI)](https://www.mdpi.com/2673-4591/107/1/42)

**Implementation relevance: HIGH.** The safety research system already has a knowledge graph architecture. Adding GNN layers for predictive signal detection is a natural extension. The PreciseADR heterogeneous graph approach (patients, diseases, drugs, ADRs as different node types) aligns well with the existing knowledge graph design.

### 5.5 Knowledge Graphs in Pharmacovigilance

A scoping review of 47 peer-reviewed articles found knowledge graphs used for detecting/predicting single-drug adverse reactions and drug-drug interactions. A step-by-step implementation guide has been published covering: use case definition, data type selection, data sourcing, KG construction, KG embedding, and deriving actionable insights.

**Sources:**
- [Knowledge Graphs in Pharmacovigilance: Scoping Review (Clinical Therapeutics)](https://www.clinicaltherapeutics.com/article/S0149-2918(24)00144-9/fulltext)
- [Knowledge Graphs in Pharmacovigilance: Step-By-Step Guide (Clinical Therapeutics)](https://www.clinicaltherapeutics.com/article/S0149-2918(24)00071-7/fulltext)
- [OpenPVSignal Knowledge Graph (Drug Safety)](https://link.springer.com/article/10.1007/s40264-024-01503-8)

**Implementation relevance: HIGH.** The step-by-step guide and the OpenPVSignal FAIR data model should inform the safety research system's knowledge graph evolution. KG embeddings for predictive signal detection are a concrete next step.

---

## 6. Implementation Priorities for the Safety Research System

Based on this research, the following are prioritized by feasibility and impact:

### Tier 1: Immediate (can start now)

| Priority | Action | Source |
|----------|--------|--------|
| 1 | **Integrate openFDA API** for automated FAERS data ingestion | openFDA |
| 2 | **Port DiAna's disproportionality metrics** (ROR, PRR, BCPNN, MGPS) to Python | DiAna package |
| 3 | **Build CAR-T secondary malignancy detection pipeline** as primary use case | FAERS + ASH Blood paper |
| 4 | **Adopt MDDC Python package** for multi-item AE cluster detection | MDDC (already Python) |
| 5 | **Integrate DiAna's cleaned FAERS data** from OSF for rapid prototyping | OSF repository |

### Tier 2: Near-term (1-3 months)

| Priority | Action | Source |
|----------|--------|--------|
| 6 | **Build NL-to-SQL query interface** using RAG + business context docs over FAERS | LLM SQL generation paper |
| 7 | **NLP pipeline for case narrative extraction** (drug, AE, temporality) | LLM ADE extraction papers |
| 8 | **Track REMS elimination impact** -- compare AE reporting rates pre/post June 2025 | FDA REMS elimination |
| 9 | **Adopt OpenPVSignal data model** for FAIR-compliant signal representation in KG | OpenPVSignal KG |
| 10 | **Implement comparative safety analytics** across CAR-T products (cilta-cel vs ide-cel) | FAERS neurotoxicity study |

### Tier 3: Medium-term (3-6 months)

| Priority | Action | Source |
|----------|--------|--------|
| 11 | **Add GNN layers to knowledge graph** for predictive signal detection | PreciseADR, Drug-Disease Graph |
| 12 | **Build agentic PV workflow** -- autonomous AE intake, classification, routing | PV Agentic LLM concept |
| 13 | **Model FDA postapproval monitoring framework** per draft guidance | CBER draft guidance |
| 14 | **Incorporate ClinicalTrials.gov data** for trial-to-postmarket signal continuity | ClinicalTrials.gov API |
| 15 | **KG embeddings** for latent signal discovery using TransE/DistMult/ComplEx | KG step-by-step guide |

---

## 7. Key Takeaways

1. **The CAR-T safety landscape is at an inflection point.** REMS elimination, boxed warnings for secondary malignancies, and the new superiority standard for approvals are reshaping the regulatory environment. The safety research system should position itself to analyze the consequences of these changes.

2. **FAERS is the richest public data source** and should be the primary data backbone. The DiAna project's cleaned data and the openFDA API provide two complementary access paths.

3. **LLM-powered pharmacovigilance is production-ready.** Natural language to SQL (85% accuracy with context), case narrative extraction, and agentic report processing are all demonstrated in published research.

4. **Graph-based approaches are the frontier.** GNNs for patient-level ADR prediction and knowledge graph embeddings for latent signal discovery represent the cutting edge. The safety research system's existing KG architecture positions it well to adopt these methods.

5. **The secondary malignancy signal** is the most important CAR-T safety story of 2024-2025 and should be the system's flagship demonstration use case.

---

*This research brief was compiled on 2026-02-17. All URLs were verified at time of writing.*
