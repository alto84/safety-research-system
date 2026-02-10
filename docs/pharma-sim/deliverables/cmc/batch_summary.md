# Manufacturing Batch Summary -- Phase I CAR-T Cell Therapy Program

> **SIMULATED** -- This document is a simulated deliverable for the pharma company simulation.
> It does not represent any real company, product, or regulatory status.

**Document ID:** CMC-BATCH-001
**Version:** 1.0
**Effective Date:** 2026-02-09
**Prepared by:** Head of CMC / Manufacturing (Simulated)
**Review Cycle:** After each batch disposition

---

## Purpose

This document provides a summary of all manufacturing batches produced under the Phase I clinical protocol for the autologous anti-CD19 CAR-T cell therapy product. Each batch corresponds to a single patient (autologous, vein-to-vein model). Release testing is performed in accordance with approved specifications per the IND and applicable compendial methods. Manufacturing is conducted under GMP conditions appropriate for Phase I investigational products per FDA Guidance: CGMP for Phase 1 Investigational Drugs (2008) and 21 CFR 1271 Subpart D.

---

## Product Description

| Attribute | Detail |
|-----------|--------|
| Product Name | Anti-CD19 CAR-T Cells (autologous) |
| Drug Substance | Genetically modified autologous T cells expressing anti-CD19 chimeric antigen receptor |
| Vector | Self-inactivating lentiviral vector (3rd generation) |
| Formulation | Cryopreserved in CryoStor CS10 (10% DMSO) |
| Container Closure | Cryobag (50 mL or 250 mL), overwrapped, stored in vapor-phase LN2 cassette |
| Dose | Target: 1 x 10^6 CAR+ viable T cells/kg (Dose Level 1) to 5 x 10^6 CAR+ viable T cells/kg (Dose Level 2) |
| Storage | Vapor-phase liquid nitrogen (<= -150C) |

---

## Batch Summary Table

| Batch ID | Patient ID | Dose Level | Leukapheresis Date | Mfg Start | Harvest Date | Release Date | Status | Disposition |
|----------|-----------|-----------|-------------------|-----------|-------------|-------------|--------|-------------|
| BR-2025-001 | PT-001 | DL1 | 2025-09-02 | 2025-09-03 | 2025-09-12 | 2025-09-19 | **Released** | Infused 2025-09-22 |
| BR-2025-002 | PT-002 | DL1 | 2025-09-23 | 2025-09-24 | 2025-10-03 | 2025-10-10 | **Released** | Infused 2025-10-14 |
| BR-2025-003 | PT-003 | DL1 | 2025-10-14 | 2025-10-15 | 2025-10-24 | 2025-10-31 | **Released** | Infused 2025-11-04 |
| BR-2026-001 | PT-004 | DL2 | 2025-11-18 | 2025-11-19 | 2025-11-28 | 2025-12-05 | **Released** | Infused 2025-12-10 |
| BR-2026-002 | PT-005 | DL2 | 2025-12-09 | 2025-12-10 | 2025-12-19 | 2025-12-27 | **Released** | Infused 2026-01-03 |
| BR-2026-003 | PT-006 | DL2 | 2026-01-06 | 2026-01-07 | 2026-01-16 | -- | **On Hold** | Pending OOS investigation (CAPA-2026-005). Endotoxin OOS result under Phase 2 investigation. Retest results within specification. |
| BR-2026-004 | PT-007 | DL2 | 2026-01-20 | 2026-01-21 | 2026-01-30 | -- | **Failed** | Viability at harvest: 58% (specification: >= 70%). Batch failed release criteria. Root cause: incoming leukapheresis material had low viability (62%) and low total nucleated cell count. Patient re-scheduled for second leukapheresis. |
| BR-2026-005 | PT-008 | DL2 | 2026-02-03 | 2026-02-04 | -- | -- | **In Process** | Currently in expansion phase (Day 7 of culture). Interim viability: 92%. On track for harvest 2026-02-13. |

---

## Release Testing Results Summary

Release testing performed per IND specifications. Methods referenced below.

### Released Batches

| Test | Method / Reference | Specification | BR-2025-001 | BR-2025-002 | BR-2025-003 | BR-2026-001 | BR-2026-002 |
|------|-------------------|---------------|-------------|-------------|-------------|-------------|-------------|
| **Sterility** | USP <71> (14-day incubation, direct inoculation); 21 CFR 610.12 | No growth at 14 days | Pass (no growth) | Pass (no growth) | Pass (no growth) | Pass (no growth) | Pass (no growth) |
| **Endotoxin** | LAL kinetic turbidimetric, USP <85>; 21 CFR 610.13 | < 5.0 EU/kg/dose | 1.8 EU/kg | 2.1 EU/kg | 1.5 EU/kg | 2.4 EU/kg | 1.9 EU/kg |
| **Mycoplasma** | qPCR (PhEur 2.6.7 / USP <63>); culture (21-day) initiated in parallel | Not detected (qPCR); No growth (culture) | Not detected | Not detected | Not detected | Not detected | Not detected |
| **Identity (CD3+)** | Flow cytometry (anti-CD3-FITC); ICH Q6B | >= 90% CD3+ | 96.2% | 94.8% | 95.5% | 97.1% | 93.9% |
| **Identity (CAR+)** | Flow cytometry (anti-FMC63 idiotype-PE); ICH Q6B | >= 15% CAR+ of viable cells | 32.4% | 28.1% | 35.7% | 41.2% | 37.8% |
| **Viability** | Trypan blue exclusion (automated cell counter) | >= 70% viable cells | 89.3% | 85.6% | 91.2% | 87.4% | 83.1% |
| **Potency** | IFN-gamma ELISA (co-culture with CD19+ target cells, 24h) | >= 500 pg/mL IFN-gamma per 1 x 10^5 CAR+ cells | 2,340 pg/mL | 1,890 pg/mL | 3,150 pg/mL | 2,780 pg/mL | 2,210 pg/mL |
| **VCN** | qPCR (vector-specific primers / albumin normalization) | <= 5.0 copies/transduced cell | 2.3 | 1.8 | 2.7 | 3.1 | 2.5 |
| **RCL** | qPCR for VSV-G (vector envelope) per FDA gene therapy guidance | Not detected | Not detected | Not detected | Not detected | Not detected | Not detected |
| **Dose** | Cell count x CAR+ % x viability; dose per patient weight | DL1: 1 x 10^6 CAR+ viable/kg (+/- 20%); DL2: 5 x 10^6 CAR+ viable/kg (+/- 20%) | 1.02 x 10^6/kg | 0.97 x 10^6/kg | 1.08 x 10^6/kg | 4.85 x 10^6/kg | 5.12 x 10^6/kg |

### Batches Not Released

| Test | BR-2026-003 (On Hold) | BR-2026-004 (Failed) |
|------|----------------------|---------------------|
| **Sterility** | Pass (no growth) | Pass (no growth) |
| **Endotoxin** | **Initial: 6.2 EU/kg (OOS)**; Retest: 2.1, 2.3 EU/kg. Under investigation (CAPA-2026-005). | 1.7 EU/kg |
| **Mycoplasma** | Not detected | Not detected |
| **Identity (CD3+)** | 95.3% | 88.7% |
| **Identity (CAR+)** | 39.5% | 22.3% |
| **Viability** | 86.7% | **58.2% (FAIL -- spec >= 70%)** |
| **Potency** | 2,560 pg/mL | 680 pg/mL (low but within spec) |
| **VCN** | 2.9 | 1.4 |
| **RCL** | Not detected | Not detected |
| **Dose** | Pending disposition | N/A -- batch failed |

---

## Batch Yield and Process Performance Summary

| Batch ID | Apheresis TNC (x 10^9) | Apheresis Viability | Post-Enrichment CD3+ | Transduction Efficiency | Fold Expansion (Day 9) | Harvest Total Viable Cells (x 10^9) | Harvest Viability |
|----------|------------------------|--------------------|--------------------|------------------------|----------------------|-------------------------------------|-------------------|
| BR-2025-001 | 8.2 | 95% | 91.3% | 34.2% | 42x | 3.8 | 89.3% |
| BR-2025-002 | 6.9 | 93% | 89.7% | 30.5% | 38x | 2.9 | 85.6% |
| BR-2025-003 | 9.1 | 96% | 93.1% | 37.8% | 51x | 5.2 | 91.2% |
| BR-2026-001 | 7.5 | 94% | 90.8% | 43.6% | 47x | 4.1 | 87.4% |
| BR-2026-002 | 8.8 | 92% | 88.4% | 40.1% | 44x | 3.6 | 83.1% |
| BR-2026-003 | 7.2 | 91% | 87.9% | 41.7% | 45x | 3.4 | 86.7% |
| BR-2026-004 | **3.8** | **62%** | 79.2% | 24.1% | 18x | **0.8** | **58.2%** |
| BR-2026-005 | 7.9 | 94% | 91.5% | -- (pending) | -- (in process) | -- (in process) | -- (in process) |

---

## Key Observations and Trends

1. **Batch Success Rate:** 5 of 7 completed batches released (71%). One on hold pending OOS investigation; one failed viability specification.

2. **BR-2026-004 Failure Analysis:** Root cause attributed to poor starting material quality. Leukapheresis product had low TNC (3.8 x 10^9 vs. average 7.8 x 10^9) and low viability (62% vs. average 93%). Patient had received 4 prior lines of therapy. Corrective action: implement incoming material acceptance criteria for leukapheresis product (minimum TNC >= 5.0 x 10^9, viability >= 80%). Patients failing incoming criteria will be re-assessed for second collection or protocol-defined alternatives.

3. **BR-2026-003 OOS Investigation:** Endotoxin OOS under investigation per CAPA-2026-005. Retest results are within specification. If Phase 2 investigation confirms assignable laboratory cause, batch may be released per SOP-QC-015.

4. **Process Consistency:** For the 5 released batches, key parameters show acceptable consistency:
   - Transduction efficiency: 28.1% -- 43.6% (mean: 37.2%)
   - Fold expansion: 38x -- 51x (mean: 44.4x)
   - Harvest viability: 83.1% -- 91.2% (mean: 87.3%)
   - CAR+ expression: 28.1% -- 41.2% (mean: 35.0%)

5. **Dose Level Escalation:** Dose Level 1 (3 patients) and Dose Level 2 (2 patients infused, 1 on hold) both met target dose specifications within the allowed +/- 20% range.

---

## Regulatory References

| Reference | Application |
|-----------|-------------|
| 21 CFR 1271 | Human cells, tissues, and cellular and tissue-based products -- donor eligibility, GTP, manufacturing |
| 21 CFR 210/211 | cGMP for drug products -- batch record requirements, release testing |
| 21 CFR 600/610 | Biologics standards -- sterility (610.12), endotoxin (610.13) |
| USP <71> | Sterility testing |
| USP <85> | Bacterial endotoxin testing |
| USP <63> | Mycoplasma testing |
| ICH Q6B | Specifications for biotechnological/biological products |
| FDA (2020) | CMC Information for Human Gene Therapy INDs |
| FDA (2008) | CGMP for Phase 1 Investigational Drugs |

---

## Document History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-02-09 | Head of CMC (Simulated) | Initial batch summary covering 8 batches (5 released, 1 on hold, 1 failed, 1 in process) |

---

*This summary is updated after each batch disposition and reviewed during monthly manufacturing and quality review meetings.*
