# Process Validation Summary -- Phase I CAR-T Cell Therapy Program

> **SIMULATED** -- This document is a simulated deliverable for the pharma company simulation.
> It does not represent any real company, product, or regulatory status.

**Document ID:** CMC-PV-001
**Version:** 1.0
**Effective Date:** 2026-02-09
**Prepared by:** Head of CMC / Manufacturing (Simulated)
**Review Cycle:** Quarterly

---

## Purpose

This document summarizes the current process validation status for the autologous anti-CD19 CAR-T cell therapy product. Process validation follows the FDA lifecycle approach (2011 Guidance: Process Validation -- General Principles and Practices) and is aligned with ICH Q8(R2) (Pharmaceutical Development) and ICH Q11 (Development and Manufacture of Drug Substances). For autologous cell therapy products at Phase I, formal process validation is not required; however, process characterization and understanding are expected to support product quality and patient safety.

---

## Validation Lifecycle Stage

| Stage | FDA Guidance Term | Current Status | Description |
|-------|------------------|----------------|-------------|
| **Stage 1** | Process Design | **In Progress** | Process characterization studies ongoing. CPPs and CQAs identified based on development data, platform knowledge, and Phase I clinical manufacturing experience (8 batches). Design space definition not yet complete. |
| **Stage 2** | Process Qualification (PPQ) | **Not Started** | Formal PPQ (consecutive successful batches at commercial scale) planned for late-stage clinical development (Phase II/III). Phase I uses clinical-scale process with enhanced in-process monitoring. |
| **Stage 3** | Continued Process Verification | **Not Applicable (Phase I)** | Will be implemented post-PPQ when commercial manufacturing is established. Phase I batch data is being collected and trended to support future CPV. |

**Current Phase Summary:** The program is in Stage 1 (Process Design). Manufacturing uses a defined clinical-scale process with documented controls. Each batch provides additional process knowledge. Formal process qualification (Stage 2) will be conducted at the to-be-determined commercial scale, likely during Phase II/III in support of the BLA.

---

## Critical Quality Attributes (CQAs)

CQAs are defined per ICH Q8(R2) as physical, chemical, biological, or microbiological properties that should be within an appropriate limit, range, or distribution to ensure the desired product quality.

| CQA | Target / Specification | Rationale | Assessment Method | Criticality Justification |
|-----|----------------------|-----------|-------------------|--------------------------|
| **Viability** | >= 70% viable cells | Directly impacts dose accuracy and in vivo function. Non-viable cells contribute to cytokine burden without therapeutic benefit. | Trypan blue exclusion (automated counter) / Flow cytometry (7-AAD) | High -- Below-spec viability linked to batch failure (BR-2026-004) and potential for reduced efficacy and increased toxicity. |
| **CAR Expression (% CAR+)** | >= 15% CAR+ of viable cells | Primary identity and potency-related attribute. CAR+ percentage determines the active component of the dose. | Flow cytometry (anti-FMC63 idiotype antibody) | High -- Directly determines therapeutic dose. Below-spec CAR expression would result in subtherapeutic dosing. |
| **T-cell Purity (% CD3+)** | >= 90% CD3+ | Ensures product is predominantly T cells. Non-T cell contaminants (monocytes, B cells) may reduce potency or contribute to adverse events. | Flow cytometry (anti-CD3) | High -- Regulatory expectation for identity. Low purity could indicate process failure at enrichment step. |
| **Potency** | >= 500 pg/mL IFN-gamma per 1 x 10^5 CAR+ cells (co-culture bioassay) | Functional measure of CAR-T cell cytotoxic activity against target antigen. Correlates with clinical response in published literature. | IFN-gamma ELISA (24h co-culture with CD19+ target cells) | High -- Only functional potency measure. Required by FDA for lot release per ICH Q6B. |
| **Sterility** | No growth (14-day) | Patient safety -- product is infused intravenously. Microbial contamination is a critical safety risk. | USP <71> (direct inoculation, 14-day incubation) | Critical -- Sterility failure would preclude product release and pose direct patient harm. |
| **Endotoxin** | < 5.0 EU/kg/dose | Patient safety -- endotoxin causes pyrogenic response. Specification based on 21 CFR 610.13 and USP <85>. | LAL kinetic turbidimetric assay (USP <85>) | Critical -- Endotoxin above threshold causes fever, hypotension, potentially life-threatening in immunocompromised patients. |
| **Mycoplasma** | Not detected | Patient safety -- mycoplasma contamination can be latent and immunosuppressive. | qPCR (rapid release) + culture (confirmatory, 21-day) per USP <63> | Critical -- Mycoplasma is a common cell culture contaminant. Undetected infection poses chronic patient risk. |
| **VCN** | <= 5.0 copies/transduced cell | Safety -- high VCN increases risk of insertional mutagenesis and genotoxicity per FDA gene therapy guidance. | qPCR (vector-specific primers, normalized to albumin housekeeping gene) | High -- Directly related to long-term safety (insertional oncogenesis risk). FDA-specified threshold. |
| **RCL** | Not detected | Safety -- replication-competent lentivirus would pose risk of uncontrolled viral infection and insertional mutagenesis. | qPCR for VSV-G envelope gene; bioassay (if triggered) per FDA guidance | Critical -- Regulatory requirement. RCL detection would halt the program. |
| **Residual Beads** | < 100 beads per 3 x 10^6 cells | Safety -- residual activation beads could cause adverse immune reactions if infused. | Manual microscopic count | Medium -- Specification based on vendor recommendation and published safety data for anti-CD3/CD28 beads. |

---

## Critical Process Parameters (CPPs)

CPPs are defined per ICH Q8(R2) as process parameters whose variability has an impact on a CQA and therefore should be monitored or controlled to ensure the process produces the desired quality.

| Process Step | CPP | Operating Range | CQA(s) Impacted | Control Strategy | Current Knowledge Level |
|-------------|-----|----------------|-----------------|-----------------|------------------------|
| **Step 1: Leukapheresis Receipt** | Incoming TNC count | >= 5.0 x 10^9 (proposed) | Viability, Total cell yield, CAR+ % | Acceptance criteria at incoming inspection. Below-spec material triggers re-collection assessment. | Moderate -- BR-2026-004 failure linked to low incoming TNC (3.8 x 10^9). Proposed acceptance criterion based on 8 batch data points. |
| **Step 1: Leukapheresis Receipt** | Incoming viability | >= 80% (proposed) | Viability, Fold expansion | Acceptance criteria at incoming inspection. | Moderate -- Correlation observed between incoming viability and final product viability (r = 0.87, n=7). |
| **Step 2: T-cell Enrichment** | CD3+ selection purity | >= 85% CD3+ post-selection | CD3+ purity (CQA) | In-process flow cytometry check. Enrichment repeated if < 85%. | High -- Well-established platform step. Consistent performance across 8 batches (mean: 89.6%). |
| **Step 3: Activation** | Bead-to-cell ratio | 3:1 (anti-CD3/CD28 beads : T cells) | Activation markers, Fold expansion, Potency | Controlled per batch record. Bead count verified by automated counter before addition. | High -- Platform-standard ratio. Deviation study (development) showed < 2:1 results in suboptimal activation. |
| **Step 4: Transduction** | MOI (Multiplicity of Infection) | MOI 5 (target); range 3-7 | VCN, CAR+ %, Transduction efficiency | Vector volume calculated per cell count. Vector titer verified per lot COA. | Moderate -- MOI directly impacts VCN. Higher MOI increases CAR+ % but also VCN. Current MOI 5 achieves VCN 1.4-3.1 (within spec of <= 5.0). Dose-response characterization ongoing. |
| **Step 4: Transduction** | Transduction duration | 18-24 hours | VCN, CAR+ % | Timed per batch record. Operator records start and end times. | Moderate -- Development data shows < 16h reduces transduction efficiency by ~30%. > 28h does not significantly improve efficiency but may increase VCN. |
| **Step 5: Expansion** | Culture duration | 9 days (target); range 7-12 days | Viability, Total cell count, Fold expansion, CAR+ % | Monitored by daily cell counts (Day 3, 5, 7, 9). Harvest triggered when target cell number reached or at Day 12 (whichever first). | Moderate -- Optimal harvest window under characterization. Shorter expansion may yield insufficient cells; longer expansion risks T-cell exhaustion and viability decline. |
| **Step 5: Expansion** | Culture temperature | 37.0C +/- 0.5C | Viability, Fold expansion, Potency | Incubator monitored continuously (alarm at +/- 1.0C). Calibrated quarterly. | High -- Standard cell culture parameter. Well-controlled. |
| **Step 5: Expansion** | CO2 concentration | 5.0% +/- 0.5% | pH, Viability, Fold expansion | Incubator monitored continuously. CO2 analyzer calibrated monthly. | High -- Standard cell culture parameter. Well-controlled. |
| **Step 6: Harvest** | Bead removal efficiency | < 100 beads per 3 x 10^6 cells | Residual beads (CQA) | Magnetic separation per SOP. Post-removal bead count performed. | High -- Consistent performance. All batches well below specification. |
| **Step 7: Cryopreservation** | Controlled-rate freezing profile | -1C/min from 4C to -40C; -10C/min from -40C to -100C; transfer to LN2 | Post-thaw viability, Viability (CQA) | Controlled-rate freezer programmed per validated profile. Temperature probe in representative bag. Freezing curve reviewed by QA. | Moderate -- Freezer OQ documentation in progress (see audit finding F-2026-001-03). Profile based on CryoStor CS10 vendor recommendation and published literature. |
| **Step 7: Cryopreservation** | DMSO concentration | 10% (CryoStor CS10 formulation) | Post-thaw viability | Pre-formulated cryopreservation medium used (CryoStor CS10). Lot-controlled. | High -- Vendor-formulated. No in-house preparation. |

---

## Process Characterization Studies (Ongoing)

| Study ID | Title | Objective | Status | Expected Completion |
|----------|-------|-----------|--------|-------------------|
| PC-001 | MOI Optimization | Characterize the relationship between MOI (range: 1-10) and VCN/CAR+ expression using small-scale model | **In Progress** | Q2 2026 |
| PC-002 | Expansion Duration Optimization | Evaluate impact of harvest day (Day 7, 9, 11) on viability, fold expansion, phenotype (exhaustion markers: PD-1, LAG-3, TIM-3), and potency | **In Progress** | Q2 2026 |
| PC-003 | Incoming Material Quality Impact | Retrospective analysis of leukapheresis material attributes (TNC, viability, CD3%, prior therapy lines) on batch success/failure | **Planned** | Q3 2026 (requires >= 12 batch data points) |
| PC-004 | Cryopreservation Robustness | Evaluate impact of controlled-rate freezer profile deviations (+/- 0.5C/min) on post-thaw viability and potency | **Planned** | Q3 2026 |
| PC-005 | Hold Time Studies | Establish maximum allowable hold times at ambient and 2-8C for in-process intermediates (post-enrichment, pre-transduction, post-harvest/pre-cryo) | **Planned** | Q3 2026 |
| PC-006 | Post-Thaw Stability | Time-course study of product quality attributes (viability, potency, CAR+ %) post-thaw at 2-8C (0, 2, 4, 8, 12, 24, 48, 72, 96 hours) to support clinical infusion window | **In Progress** | Q1 2026 (preliminary data available; supports 96-hour hold -- referenced in CAPA-2026-004) |

---

## Process Performance Qualification (PPQ) -- Future Plan

| Element | Plan |
|---------|------|
| **Timing** | PPQ will be conducted during late-stage clinical development (Phase II/III), at commercial-scale manufacturing. Not required for Phase I (per FDA 2008 Phase 1 CGMP guidance). |
| **Scale** | PPQ will be performed at the to-be-determined commercial manufacturing scale. Current clinical scale may differ from commercial scale (e.g., if manufacturing is transferred to a CDMO). |
| **Number of PPQ Lots** | Minimum 3 consecutive successful lots meeting all CQA specifications. Number may be increased based on process variability observed during Phase I/II. Autologous products present unique challenges as each batch has different starting material (patient-specific). |
| **Acceptance Criteria** | All CQAs within approved specifications. All CPPs within established operating ranges. Process yields consistent with development and clinical experience. |
| **Protocol** | PPQ protocol to be drafted during Phase II, informed by process characterization studies (PC-001 through PC-006) and Phase I/II clinical manufacturing data. |
| **Report** | PPQ report to be included in BLA submission (CTD Module 3.2.S.2.5 and 3.2.P.3.5). |

---

## Validation Master Plan Outline

The Validation Master Plan (VMP) defines the overall validation strategy for the CAR-T cell therapy manufacturing process. The full VMP (document CMC-VMP-001) is in development. Key sections are outlined below.

| VMP Section | Content | Status |
|-------------|---------|--------|
| **1. Scope and Objectives** | Covers drug substance (CAR-T cells) and drug product (formulated, cryopreserved product). Validation lifecycle approach per FDA 2011 guidance. | Drafted |
| **2. Organizational Responsibilities** | CMC leads validation execution. QA approves protocols and reports. QC provides analytical support. | Drafted |
| **3. Facility and Equipment Qualification** | IQ/OQ/PQ for all GMP manufacturing equipment (isolators, incubators, controlled-rate freezer, automated cell counter, flow cytometer, centrifuges). Facility qualification including HVAC, cleanroom classification, environmental monitoring. | In Progress -- 5 of 7 instruments qualified. Cleanroom qualified (ISO 7 background, ISO 5 at point of work). |
| **4. Analytical Method Qualification** | Qualification (Phase I) or validation (Phase III/BLA) of all release testing methods. Includes USP compendial methods (sterility, endotoxin, mycoplasma) and non-compendial methods (flow cytometry, potency bioassay, VCN qPCR). | In Progress -- Compendial methods verified per USP. Non-compendial methods qualified for Phase I use (accuracy, precision, specificity demonstrated). Full validation planned for Phase III. |
| **5. Process Characterization** | Studies PC-001 through PC-006 (see table above). Define design space, proven acceptable ranges (PARs), and normal operating ranges (NORs) for all CPPs. | In Progress |
| **6. Process Performance Qualification** | PPQ protocol for minimum 3 consecutive lots at commercial scale. Sampling plan, acceptance criteria, and statistical analysis plan. | Not Started (planned for Phase II/III) |
| **7. Cleaning Validation** | Cleaning validation for manufacturing isolator suite, shared equipment, and reusable components. Acceptance criteria based on carryover limits (product, cleaning agent, endotoxin, bioburden). | Not Started (planned Q3 2026) |
| **8. Computer System Validation (CSV)** | Validation of GxP computerized systems per 21 CFR Part 11: LIMS, EDC, environmental monitoring system, equipment data systems (flow cytometer, qPCR). Risk-based approach per GAMP 5. | In Progress -- Risk assessments completed for 3 of 6 systems. Full CSV planned for Phase II. |
| **9. Shipping Qualification** | Qualification of cryoshipment process for all clinical shipping lanes. Includes dry shipper performance qualification, temperature monitoring, and worst-case transit time studies. | In Progress -- Primary lane (to Site 001) qualified. Sites 002 and 003 pending (see CAPA-2026-001). |
| **10. Continued Process Verification (CPV)** | Post-PPQ monitoring program. Statistical process control charts for CPPs and CQAs. Trending, out-of-trend (OOT) detection, and annual product quality review (APQR). | Not Started (post-PPQ) |
| **11. Revalidation Triggers** | Defined conditions requiring revalidation: process changes (major), scale changes, site transfers, equipment changes, raw material changes (e.g., new vector lot, new activation reagent). Managed through change control system. | Drafted |

---

## Regulatory References

| Reference | Application |
|-----------|-------------|
| ICH Q8(R2) | Pharmaceutical Development -- design space, CQAs, process understanding |
| ICH Q11 | Development and Manufacture of Drug Substances (Biological) -- process validation lifecycle |
| ICH Q9(R1) | Quality Risk Management -- risk-based approach to CPP/CQA identification |
| ICH Q6B | Specifications for Biotechnological/Biological Products -- release testing rationale |
| FDA (2011) | Process Validation: General Principles and Practices -- Stage 1/2/3 lifecycle |
| FDA (2008) | CGMP for Phase 1 Investigational Drugs -- Phase I-appropriate validation expectations |
| FDA (2020) | CMC Information for Human Gene Therapy INDs -- cell therapy-specific CMC expectations |
| 21 CFR 211.100 | Written procedures for production and process control |
| 21 CFR 211.110 | Sampling and testing of in-process materials and drug products |
| EU GMP Annex 1 (2022) | Manufacture of Sterile Medicinal Products -- cleanroom and aseptic process requirements |

---

## Document History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-02-09 | Head of CMC (Simulated) | Initial process validation summary |

---

*This summary is reviewed quarterly and updated as process characterization studies are completed and validation activities progress. Next review: Q2 2026.*
