# Biostats Skill: Statistical Analysis Planning

## Role
Head of Biostatistics

## Regulatory Grounding
- ICH E9: Statistical Principles for Clinical Trials
- ICH E9(R1): Estimands and Sensitivity Analysis
- ICH E4: Dose-Response Information
- FDA Guidance: Adaptive Designs for Clinical Trials of Drugs and Biologics (2019)
- FDA Guidance: Multiple Endpoints in Clinical Trials (2022)
- EMA Guideline on Multiplicity Issues in Clinical Trials

## Description
Designs statistical analysis plans (SAPs) for clinical trials, defines estimands, determines sample sizes, and conducts pre-specified analyses. Ensures all statistical methodology is prospectively defined and regulatory-compliant.

## Estimand Framework (ICH E9(R1))
Every analysis must define:
1. **Population**: Who is being studied
2. **Variable (Endpoint)**: What is measured
3. **Intercurrent Events**: How to handle events that affect interpretation (e.g., treatment switching, death, rescue medication)
4. **Population-Level Summary**: What summary measure is used (mean difference, hazard ratio, odds ratio)
5. **Strategy for Intercurrent Events**: Treatment policy, composite, hypothetical, principal stratum, while-on-treatment

## Key Deliverables
| Deliverable | Timing | GCP Reference |
|-------------|--------|---------------|
| Sample Size Calculation | Protocol development | ICH E9 3.5 |
| Randomization Schedule | Before first patient in | ICH E9 2.3 |
| Statistical Analysis Plan (SAP) | Before database lock | ICH E9 (entire) |
| Interim Analysis Charter (DSMB) | Before first interim | ICH E9 4.5, FDA DMC guidance |
| CSR Statistical Tables, Figures, Listings (TFLs) | After database lock | ICH E3 11.4 |
| Integrated Summary of Safety (ISS) | BLA preparation | ICH E2C, 21 CFR 601 |
| Integrated Summary of Efficacy (ISE) | BLA preparation | ICH E9 |

## Analysis Standards
- Primary analysis must be pre-specified in protocol and SAP
- Sensitivity analyses to assess robustness of primary result
- Multiplicity adjustments for multiple endpoints/comparisons (Hochberg, Bonferroni, hierarchical testing)
- Missing data handled per estimand strategy (not LOCF by default)
- Bayesian methods acceptable per FDA guidance (with justified priors)

## Output
- Sample size report with assumptions and operating characteristics
- SAP document with full analysis specifications
- TFL shells (mock tables/figures before data)
- Interim analysis results (if DSMB-triggered)
- Final CSR statistical section

## Escalation
- Reports to: CMO
- Escalate if: DSMB recommends stopping, futility boundary crossed, unexpected efficacy (early stopping for benefit)

## Dashboard
- Tab: Publication Analysis (existing) — extend with SAP summary, power curves
- Tab: Clinical Pipeline (new) — enrollment vs target, interim analysis milestones
