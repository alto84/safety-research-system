# PV Skill: Safety Signal Detection

## Role
Head of Patient Safety / Pharmacovigilance

## Regulatory Grounding
- ICH E2E: Pharmacovigilance Planning
- CIOMS VIII: Signal Detection
- FDA Guidance: Good Pharmacovigilance Practices and Pharmacoepidemiologic Assessment (2005)
- EU GVP Module IX: Signal Management
- 21 CFR 312.32: IND Safety Reporting

## Description
Performs systematic review of safety data to identify new or changed safety signals. Uses quantitative disproportionality analysis (PRR, ROR, EBGM) and qualitative clinical review to evaluate potential signals.

## Input
- FAERS data (spontaneous reports by product)
- Clinical trial AE data (controlled, with denominators)
- Published literature case reports
- Reference Safety Information (RSI) / Company Core Safety Information (CCSI)
- Known class effects for cell therapy products

## Process
1. **Data Mining**: Run disproportionality analysis on FAERS data (PRR > 2.0, chi-squared > 4.0, N >= 3)
2. **Clinical Review**: Assess biological plausibility, temporal relationship, dose-response
3. **Signal Validation**: Cross-reference with clinical trial data, literature, mechanism of action
4. **Signal Prioritization**: Classify as validated signal, refuted signal, or ongoing evaluation
5. **Impact Assessment**: Determine if signal changes benefit-risk profile
6. **Action Recommendation**: Propose label update, DHPC, protocol amendment, study halt

## Output
Signal assessment report with:
- Signal description and source
- Disproportionality metrics (PRR, ROR, EBGM with 95% CI)
- Clinical assessment (causality, severity, outcome)
- Recommendation (routine monitoring / enhanced monitoring / urgent action)

## Expedited Reporting Rules (21 CFR 312.32)
- **7-day report**: Fatal or life-threatening unexpected SUSAR
- **15-day report**: All other unexpected SUSARs
- **Annual DSUR**: Comprehensive annual safety review (ICH E2F)

## Escalation
- Reports to: CMO
- Escalate if: new unexpected SUSAR, signal suggesting increased mortality, any event requiring study hold

## Dashboard
- Tab: Signal Detection (existing) — already has FAERS comparison and triangulation
- Tab: PV Dashboard (new) — signal tracking, ICSR timeline, expedited report status
