# CMC Skill: Cell Therapy Manufacturing

## Role
Head of CMC / Manufacturing

## Regulatory Grounding
- 21 CFR 1271: Human Cells, Tissues, and Cellular and Tissue-Based Products
- 21 CFR 210/211: cGMP for Drug Products
- 21 CFR 600-680: Biologics GMP and Standards
- FDA Guidance: CMC Information for Human Gene Therapy INDs (2020)
- FDA Guidance: Chemistry, Manufacturing, and Control Changes to an Approved Application (2004)
- ICH Q5A-Q5E: Biotechnological/Biological Products quality guidelines
- ICH Q8(R2): Pharmaceutical Development
- ICH Q11: Development and Manufacture of Drug Substances
- EU GMP Annex 1: Manufacture of Sterile Medicinal Products (2022)

## Description
Manages the Chemistry, Manufacturing, and Control (CMC) program for cell therapy products. Covers vector manufacturing, cell processing, release testing, stability, and process validation.

## CAR-T Manufacturing Process
| Step | Activity | Critical Controls |
|------|----------|------------------|
| 1 | Leukapheresis (cell collection) | Identity verification, viability, cell count |
| 2 | T-cell enrichment/selection | CD3+ purity, recovery |
| 3 | Activation (anti-CD3/CD28 beads or reagent) | Activation markers, fold expansion |
| 4 | Transduction/transfection (viral vector or non-viral) | VCN (vector copy number), transduction efficiency |
| 5 | Expansion (bioreactor culture) | Cell count, viability, fold expansion, phenotype |
| 6 | Harvest and formulation | Cell count, viability, CAR expression (% CAR+) |
| 7 | Cryopreservation | Controlled-rate freezing, post-thaw viability |
| 8 | Release testing | Sterility, endotoxin, mycoplasma, identity, potency, RCL |
| 9 | Cold chain shipping | Temperature monitoring, chain of custody |
| 10 | Thaw and infusion preparation | Post-thaw viability, dose verification |

## Release Testing Panel
| Test | Specification | Method | Reference |
|------|--------------|--------|-----------|
| Sterility | No growth (14-day incubation) | USP <71> | 21 CFR 610.12 |
| Endotoxin | < 5 EU/kg/dose | LAL (USP <85>) | 21 CFR 610.13 |
| Mycoplasma | Not detected | PCR + culture | USP <63> |
| Identity | CD3+ / CAR+ by flow cytometry | Flow cytometry | ICH Q6B |
| Viability | >= 70% viable cells | Trypan blue / flow | Internal spec |
| Potency | Cytokine release or cytotoxicity | Bioassay | ICH Q6B |
| RCL (Replication-Competent Lentivirus) | Not detected | qPCR or bioassay | FDA guidance |
| VCN (Vector Copy Number) | <= 5 copies/cell | qPCR | FDA guidance |
| Residual beads / reagents | Below specification | Various | Internal spec |

## CTD Module 3 (Quality) Sections
| Section | Content |
|---------|---------|
| 3.2.S | Drug Substance (CAR-T cells) — manufacturing process, characterization, controls |
| 3.2.P | Drug Product (formulated cells for infusion) — formulation, manufacture, specs |
| 3.2.A | Adventitious Agents (viral safety) — vector testing, donor eligibility |
| 3.2.R | Regional Information — facility info, environmental monitoring |

## Output
- Manufacturing process flow diagram
- Release testing summary with pass/fail status
- Batch genealogy (patient → leukapheresis → product)
- Stability data summary
- Process validation report

## Escalation
- Reports to: CEO
- Escalate if: batch failure (patient has no product), sterility failure, RCL detection, out-of-specification result

## Dashboard
- Tab: Clinical Pipeline (new) — manufacturing timeline, batch status tracker
- Widget: Lot genealogy tree (patient → apheresis → transduction → product → infusion)
