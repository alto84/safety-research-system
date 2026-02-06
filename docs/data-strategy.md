# PSP Data Strategy

**Document Classification:** AstraZeneca Confidential - Internal Use Only
**Version:** 1.0 | **Date:** 2026-02-06
**Owner:** Data Science & AI / Safety Sciences

---

## 1. Data Source Inventory

### 1.1 Internal Clinical Data

| Source | Format | Update Frequency | Integration Method |
|--------|--------|------------------|--------------------|
| Clinical trial databases (RAVE, Inform) | CDISC SDTM/ADaM | Near real-time (EDC sync) | API / bulk extract |
| Central lab systems | HL7 v2 / FHIR R4 | Daily | HL7 interface engine |
| Local lab results | HL7 v2 / CSV | Variable | Batch ingestion with QC |
| Cytokine panel data (Luminex/MSD) | Proprietary CSV | Per-visit | Batch ETL |
| Flow cytometry (CAR-T expansion) | FCS 3.1 | Per-visit | Custom parser |
| Manufacturing batch records (CoA) | PDF / structured XML | Per-lot | NLP extraction + manual QC |
| Vital signs / telemetry | HL7 / FHIR Observation | Continuous (inpatient) | Streaming pipeline |
| Concomitant medications | SDTM CM domain | Per-visit | Standard CDISC ETL |

### 1.2 Genomics and Molecular Data

| Source | Format | Volume | Integration Method |
|--------|--------|--------|--------------------|
| Germline WES/WGS | VCF / BAM / CRAM | ~100 GB per patient | Cloud genomics pipeline (AWS HealthOmics) |
| Tumor genomics (panel / WES) | VCF / MAF | ~5 GB per patient | Standard variant pipeline |
| Single-cell RNA-seq (correlative) | H5AD / 10x format | ~50 GB per study | Specialized bioinformatics pipeline |
| TCR/BCR repertoire sequencing | AIRR format | ~1 GB per patient | Immunarch pipeline |
| HLA typing | HLA nomenclature (IMGT) | Structured | Direct mapping |

### 1.3 Imaging Data

| Source | Format | Use Case |
|--------|--------|----------|
| MRI (neuroimaging for ICANS) | DICOM | ICANS spatial correlation |
| CT / PET-CT (tumor burden) | DICOM | Baseline risk stratification |
| Echocardiography | DICOM / structured reports | Cardiac risk assessment |

### 1.4 External Data

| Source | Access Method | Latency | Value |
|--------|--------------|---------|-------|
| FAERS (FDA Adverse Event Reporting) | openFDA API | Quarterly | Population-level signal detection |
| EudraVigilance | EMA data access | Quarterly | EU pharmacovigilance signals |
| Published literature (PubMed, PMC) | PubMed API / NLP | Weekly scan | Emerging safety signals, mechanistic context |
| ClinicalTrials.gov | API | Weekly | Competitor safety signals, trial design context |
| CIBMTR registry | Data use agreement | Annual | Long-term CGT outcomes |

---

## 2. Data Architecture

### 2.1 Layered Data Lake

```
Bronze Layer (Raw)
  - Unmodified source data in native formats
  - Full audit trail, immutable
  - Retention: per protocol + 15 years (ICH E6)

Silver Layer (Standardized)
  - CDISC SDTM mapping for clinical data
  - OMOP CDM for observational / EHR data
  - GA4GH standards for genomics
  - DICOM metadata extraction for imaging
  - Pseudonymized at this layer

Gold Layer (Feature Store)
  - Analysis-ready feature tables
  - Patient-timepoint grain
  - Versioned feature definitions
  - Linked to model training pipelines
```

### 2.2 Integration Standards

- **Clinical data:** CDISC SDTM v3.4 / ADaM v1.3
- **Lab data:** HL7 FHIR R4 (Observation, DiagnosticReport resources)
- **Genomics:** GA4GH VRS, Phenopackets, htsget
- **Imaging:** DICOM + DICOMweb for retrieval
- **Terminology:** MedDRA (AEs), WHO Drug Dictionary (medications), SNOMED CT (diagnoses), LOINC (labs), HGNC (genes)

---

## 3. Feature Engineering

### 3.1 Baseline Features (Pre-Treatment)

| Feature Group | Examples | Rationale |
|--------------|----------|-----------|
| Demographics | Age, sex, BMI, race/ethnicity | Known CRS/ICANS risk modifiers |
| Disease characteristics | Tumor burden (SPD/MTV), disease stage, prior lines of therapy, refractory status | High tumor burden = high CRS risk |
| Organ function | Creatinine, ALT/AST, bilirubin, LVEF, ferritin, CRP | Baseline organ reserve affects toxicity tolerance |
| Hematologic | ALC, ANC, platelet count, LDH, fibrinogen | Pre-infusion immune/inflammatory state |
| Genomic | HLA alleles, cytokine gene polymorphisms (IL6, TNF), germline PGx variants | Genetic predisposition to immune hyperactivation |
| Manufacturing | CAR transduction efficiency, T-cell expansion fold, product phenotype (CD4:CD8 ratio), vector copy number | Product quality drives in vivo expansion kinetics |
| Prior treatment | Bridging therapy type, lymphodepletion regimen, steroid exposure | Conditioning affects immune reconstitution |

### 3.2 Longitudinal Features (Post-Treatment Time Series)

| Feature Group | Temporal Resolution | Engineering Approach |
|--------------|--------------------|--------------------|
| Cytokine kinetics (IL-6, IFN-gamma, IL-1beta, IL-10, TNF-alpha) | q6-12h (CRS window) | Slope, AUC, peak velocity, time-to-peak |
| CAR-T expansion (qPCR / flow) | Daily | Expansion rate, doubling time, peak-to-trough ratio |
| Vital signs (temp, HR, MAP, SpO2) | Continuous / q4h | Rolling statistics, variability indices, threshold crossings |
| Laboratory values (ferritin, CRP, fibrinogen, d-dimer) | Daily | Rate of change, deviation from baseline, trajectory classification |
| Neurological assessments (ICE score, CARTOX-10) | q8-12h | Score trajectory, decline velocity |
| Organ function markers | Daily | Multi-organ dysfunction score (composite) |

**Time series encoding methods:**
- Recurrent features (LSTM/GRU hidden states)
- Temporal convolutional features
- Clinically-derived summary statistics (interpretable)
- Irregularly-sampled time series handling (mTAND / GRU-D)

### 3.3 Graph-Derived Features

| Graph Type | Nodes | Edges | Features Derived |
|-----------|-------|-------|-----------------|
| Cytokine interaction network | Cytokines, receptors | Known signaling relationships | Centrality scores, pathway activation signatures |
| Patient similarity graph | Patients | Feature-space similarity | Community membership, nearest-neighbor risk scores |
| Biological knowledge graph | Genes, proteins, pathways, AEs | Curated biological relationships | Mechanistic pathway scores, novel risk factor discovery |

---

## 4. Privacy and Compliance

### 4.1 Pseudonymization

- Patient identifiers removed at Bronze-to-Silver transition.
- Pseudonymization key held by independent Data Trustee (not accessible to modeling teams).
- Re-identification permitted only for patient safety (SAE follow-up) with DPO and Medical Monitor approval.
- Compliant with GDPR Article 89 (scientific research), HIPAA Safe Harbor, and ICH E6(R3).

### 4.2 Differential Privacy

- Applied to aggregate statistics, model outputs shared externally, and any cross-trial analytics.
- Privacy budget (epsilon) managed per data release with formal accounting.
- Noise injection calibrated to maintain clinical utility (target: <2% degradation in AUROC at epsilon = 1.0).

### 4.3 Data Minimization

- Feature selection pipeline formally documents the necessity of each data element.
- Genomic data access restricted to pre-specified variant panels (no exploratory genome-wide access without IRB/ethics amendment).
- Imaging data retained as extracted features, not raw DICOM, in Gold layer unless explicitly required.
- Temporal data retention aligned with protocol-specific data retention schedules.

### 4.4 Cross-Border Data Transfer

- Primary processing within AZ-managed AWS regions (EU: eu-west-1, US: us-east-1).
- No patient-level data transferred to AI model provider endpoints. All LLM interactions use de-identified, aggregated, or synthetic data.
- Standard Contractual Clauses (SCCs) in place for any EU-to-US data flows.
- China data (if applicable) processed in-region per PIPL requirements.

---

## 5. Data Quality Framework

### 5.1 Automated Validation Rules

| Check | Layer | Action on Failure |
|-------|-------|-------------------|
| Schema validation (data types, required fields) | Bronze ingestion | Reject record, alert data engineer |
| Referential integrity (patient IDs, visit sequences) | Silver | Quarantine, manual review |
| Clinical plausibility (lab ranges, vital sign bounds) | Silver | Flag for medical review |
| Temporal consistency (visit dates, event sequences) | Silver | Flag for data management |
| Completeness thresholds (per feature, per study) | Gold | Imputation pipeline or exclusion |
| Distribution drift (feature distributions vs. training data) | Gold | Alert model monitoring team |

### 5.2 Data Profiling

- Automated profiling on every ingestion batch: completeness, cardinality, distribution statistics, outlier detection.
- Monthly data quality scorecards per study and per data source.
- Quarterly data quality review with Clinical Operations and Biostatistics.

### 5.3 Continuous Monitoring

- Real-time dashboards tracking data freshness, completeness, and anomaly rates.
- Automated alerts for: missing expected data deliveries, sudden distribution shifts, schema changes in upstream systems.
- Data lineage tracking from source to feature to model prediction (end-to-end provenance).

---

## 6. Data Governance

### 6.1 Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| Data Product Owner (Safety Sciences) | Defines data requirements, validates clinical relevance |
| Data Steward (Data Management) | Enforces standards, manages metadata catalog |
| Data Engineer (DS&AI Engineering) | Builds and maintains pipelines, ensures SLAs |
| Data Protection Officer | Approves privacy impact assessments, manages consent |
| Information Security | Encryption, access control, vulnerability management |

### 6.2 Access Control

- Role-based access control (RBAC) with principle of least privilege.
- Patient-level data: Safety Scientists, Biostatisticians, Medical Monitors (with study-specific access).
- Aggregated/feature-level data: Data Scientists, ML Engineers.
- Model outputs only: Clinical Operations, Regulatory Affairs.
- All access logged and auditable (21 CFR Part 11 compliant).

### 6.3 Metadata Catalog

- Centralized catalog (AWS Glue Data Catalog or equivalent) documenting every dataset, field, lineage, and access policy.
- Feature definitions versioned and linked to model versions.
- Searchable by study, data type, therapeutic area, and compliance status.
