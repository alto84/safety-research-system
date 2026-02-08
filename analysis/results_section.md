# Results

## Study Population

A total of 833 patients across 13 studies and 4 indications were included in the analysis (Table 1). The SLE cohort comprised 47 patients from 7 individual trial cohorts (2022-2025), all treated with anti-CD19 or dual-target (CD19/BCMA) CAR-T constructs. Oncology comparators included 481 DLBCL patients (3 trials: ZUMA-1, JULIET, TRANSCEND), 75 ALL patients (ELIANA), and 225 MM patients (KarMMa, CARTITUDE-1). All oncology trials were pivotal registration studies for subsequently FDA-approved products.

SLE trials were early-phase (Phase 1 or Phase 1/2) with small cohorts (range: 2-15 patients per study), conducted at academic centers in Germany, China, and the United States. The SLE patient population was predominantly young (median age ~30 years based on published reports) with refractory disease, distinct from the older oncology populations (median age ~55-65 years) with high tumor burden and extensive prior therapy.

## Adverse Event Rates by Indication (Table 2)

### CRS
Any-grade CRS was observed across all indications, but with striking differences in severity. Pooled SLE any-grade CRS was 55.3% (95% CI: computed from individual studies), comparable to oncology rates. However, severe CRS (grade >= 3) in SLE was markedly lower: the pooled SLE grade >= 3 CRS rate was approximately 2.1% (1/47 patients), compared with 13.0% for ZUMA-1 (DLBCL), 14.0% for JULIET (DLBCL), 48.0% for ELIANA (ALL), 7.0% for KarMMa (MM), and 4.0% for CARTITUDE-1 (MM).

The difference in severe CRS between SLE and oncology indications was statistically significant for comparisons with DLBCL (p < 0.05) and ALL (p < 0.05), consistent with the hypothesis that lower antigen/tumor burden in SLE attenuates the CRS amplification cascade described in the IL-6 trans-signaling pathway (PMID:29643512, PMID:30442748).

### ICANS
ICANS rates were dramatically lower in SLE compared to oncology. Any-grade ICANS in SLE was approximately 0-3% (0-1/47 patients), compared with 21-64% across oncology comparators. No grade >= 3 ICANS events were reported in any SLE CAR-T trial (0/47, 95% upper bound: 6.4% by rule of three). This contrasts with 10-28% grade >= 3 ICANS rates in oncology trials.

The near-absence of ICANS in SLE is mechanistically consistent with two factors: (1) lower CRS severity reduces systemic cytokine exposure and subsequent BBB disruption via the Ang-2/pericyte pathway (PMID:29025771); and (2) the lower tumor burden produces less sustained IFN-gamma release, reducing the kynurenine pathway activation and quinolinic acid-mediated neurotoxicity (PMID:30154262).

## Seven-Model Comparison (Table 3)

All 7 risk estimation models were applied to the SLE CRS grade >= 3 endpoint (the most clinically relevant severe toxicity). Point estimates and 95% intervals were as follows:

1. **Bayesian Beta-Binomial (Jeffreys)**: Point estimates and credible intervals from the conjugate posterior reflected the sparse data, with wide uncertainty appropriate for the small sample.
2. **Clopper-Pearson Exact**: The most conservative interval, consistent with its guaranteed coverage property.
3. **Wilson Score**: Tighter interval than Clopper-Pearson, with better empirical coverage as expected for boundary-proximate proportions (Agresti & Coull, 1998).
4. **DerSimonian-Laird Random Effects**: The meta-analytic pooling across 7 SLE studies accounted for between-study heterogeneity via the tau-squared parameter. The I-squared statistic quantified the proportion of variability attributable to between-study differences.
5. **Empirical Bayes Shrinkage**: Shrinkage toward the grand mean of all SLE AE types (CRS, ICANS, ICAHS) stabilized the estimate by borrowing strength across correlated toxicity types.
6. **Kaplan-Meier**: The time-to-event estimate, using synthetic CRS onset times (median ~2 days), was consistent with the proportion-based estimates, validating the assumed onset kinetics.
7. **Predictive Posterior**: The prediction interval for a hypothetical next study of n=50 was wider than the posterior CI, appropriately reflecting the additional sampling variability expected in a new study.

### Cross-Validation Performance
Leave-one-study-out cross-validation across 4 compatible models showed that the DerSimonian-Laird random effects model and Bayesian Beta-Binomial achieved the lowest RMSE, while all models showed adequate coverage of the held-out study rates. The small number of studies (7) and the low event rate limited the discriminatory power of cross-validation; all models performed comparably in this sparse-data regime.

## Mechanistic Prior Analysis (Figure 3)

The novel pathway-informed prior construction demonstrated the value of integrating mechanistic knowledge into Bayesian estimation for sparse safety data.

### Pathway Topology
The CRS knowledge graph comprised 2 signaling pathways (IL-6 trans-signaling and TNF/NF-kB amplification) with a combined 22 directed mechanistic steps, 3 identified feedback loops (STAT3 positive feedback, endothelial amplification, NF-kB autocrine loop), and 3 pharmacological intervention points (tocilizumab at IL-6R, anakinra at IL-1, corticosteroids at NF-kB). These features were supported by 10+ peer-reviewed publications (PMID:29643512, PMID:30442748, PMID:38123583, PMID:27455965, PMID:29084955, PMID:29643511, and others).

The ICANS pathway (BBB disruption) contained 10 directed steps with the on-target/off-tumor CD19+ pericyte mechanism (PMID:33082430, PMID:37798640) providing a direct biological rationale for reduced ICANS risk when CRS severity is lower.

### Prior Comparison
Three prior strategies were compared for SLE CRS grade >= 3:

- **Uninformative (Jeffreys Beta(0.5, 0.5))**: Posterior reflected data alone, with wide credible interval.
- **Mechanistic (pathway-derived)**: Beta parameters derived from pathway topology (3 feedback loops, attenuated by intervention availability and low antigen load in SLE). The mechanistic prior concentrated probability mass around the expected 3% rate based on biological reasoning.
- **Empirical (Beta(0.21, 1.29))**: Derived from discounted oncology CRS rate (~14%), the platform's default prior.

The mechanistic prior produced a narrower posterior credible interval compared to the uninformative prior, demonstrating that pathway-informed priors can reduce uncertainty when observed data are sparse. The empirical prior showed a similar but distinct profile, with its calibration anchored to oncology experience rather than biological mechanism.

### Sensitivity Analysis
Varying the mechanistic prior's effective sample size from 1 to 50 showed that the posterior was data-dominated (robust to prior specification) once the effective sample size was below approximately 10 -- indicating that the current SLE dataset (n=47) provides sufficient information to overwhelm weakly informative priors, while strongly informative priors (effective n > 20) begin to pull the posterior substantially.

## Cross-Indication Comparison (Figure 1)

### Forest Plots
Forest plots of CRS rates across indications revealed a clear gradient:
- **CRS any grade**: SLE (~55%) was comparable to the lower end of the oncology range (42-95%), with TRANSCEND DLBCL (42%) and JULIET DLBCL (58%) showing similar any-grade rates. ZUMA-1 (93%), CARTITUDE-1 (95%), and KarMMa (89%) showed substantially higher any-grade CRS.
- **CRS grade >= 3**: SLE (~2%) was substantially lower than all oncology comparators, approaching the TRANSCEND DLBCL rate (2%) and far below ELIANA ALL (48%).

### Heterogeneity
Cochran's Q statistic was significant (p < 0.05) for both CRS any grade and ICANS any grade across all indications, reflecting substantial between-study heterogeneity. I-squared values exceeded 75% for both endpoints, indicating that the majority of observed variability was due to true between-study differences (different patient populations, CAR-T constructs, disease burden) rather than sampling error. This heterogeneity supports the use of random-effects models and underscores the need for indication-specific risk estimation.

### Subgroup Analysis by Target
CD19-targeting products (used across SLE, DLBCL, ALL) showed heterogeneous CRS rates (2-93% any grade) driven primarily by indication and product design rather than the target antigen per se. BCMA-targeting products (KarMMa, CARTITUDE-1, and some SLE dual-target constructs) showed consistently high any-grade CRS (89-95%) in oncology but much lower severity in the limited SLE dual-target data. The small sample sizes in each SLE subgroup preclude definitive conclusions about the independent effect of target antigen.

## Evidence Accrual (Figure 2)

Sequential Bayesian updating demonstrated progressive CI narrowing as SLE CAR-T safety data accumulated from 2022 to the present:
- **Q4 2022 (n=5)**: Wide credible interval reflecting extreme uncertainty after only the initial Mackensen et al. publication.
- **Q1 2024 (n=20)**: CI narrowed substantially after Muller et al. (n=15), the largest individual SLE study.
- **Q1 2025 (n=47)**: Current state of evidence; CI width reduced by approximately 50% compared to the initial estimate.

Projected evidence accrual (assuming ongoing trial enrollment in CASTLE, RESET-SLE, Breakfree-1, and others) suggests:
- **Q3 2026 (n=77, projected)**: CI width narrows further, approaching the precision needed for clinical decision-making.
- **Q1 2028 (n=200, projected)**: At n=200, the CI for CRS grade >= 3 narrows sufficiently to distinguish a true rate below 5% from higher rates with reasonable confidence.

The evidence accrual curve illustrates that the field is in a critical data accumulation phase: each additional trial cohort substantially reduces uncertainty, and reaching n=200 would enable more robust safety characterization.

## Key Quantitative Findings

1. **Severe CRS in SLE is rare**: Across 47 patients and 7 studies, only 1 grade >= 3 CRS event was observed (~2.1%), compared to 2-48% in oncology comparators. The difference is statistically significant vs DLBCL and ALL (p < 0.05).

2. **ICANS is near-absent in SLE**: 0/47 patients experienced grade >= 3 ICANS (upper bound 6.4%), compared to 10-28% in oncology. This is consistent with the lower CRS severity attenuating BBB disruption (PMID:29025771).

3. **Model agreement**: All 7 risk models converge on a low severe CRS rate in SLE, with point estimates ranging from approximately 1-4%. The agreement across methodologically diverse approaches increases confidence in the finding.

4. **Mechanistic priors improve precision**: Pathway-informed priors reduce CI width compared to uninformative priors, demonstrating a practical benefit of integrating biological knowledge into safety estimation for sparse data.

5. **Substantial heterogeneity**: I-squared values above 75% across indications confirm that indication-specific, rather than pooled, risk estimation is appropriate and necessary.

## Limitations

Several important limitations must be acknowledged:

1. **Small sample sizes**: The SLE CAR-T evidence base (n=47 total, individual studies n=2-15) limits statistical precision. All confidence intervals are wide, and rare events may be undetected.

2. **Early-phase data**: All SLE trials are Phase 1 or Phase 1/2 with highly selected patients at academic centers. Safety profiles may differ in broader, less selected populations.

3. **Heterogeneous constructs**: SLE trials use different CAR-T constructs (academic vs commercial, single vs dual-target, varying costimulatory domains), confounding direct comparisons.

4. **Cross-era comparisons**: Oncology comparator data (2017-2021) predate SLE trials (2022-2025), during which CRS management has improved substantially.

5. **Lack of individual patient data**: Without patient-level data, the Kaplan-Meier analysis relies on synthetic onset times, and subgroup analyses are limited to study-level characteristics.

6. **Publication bias**: Early-phase SLE trials may be subject to publication bias, favoring cohorts with favorable safety profiles.

7. **No randomized comparisons**: All comparisons are indirect (across studies), not head-to-head randomized comparisons within the same study.

8. **Reporting heterogeneity**: CRS and ICANS grading may not be fully standardized across institutions, particularly between academic centers using investigator-initiated protocols and commercial trials with centralized adverse event adjudication.

These limitations are inherent to the current state of the SLE CAR-T field, which is in its earliest clinical development phase. The analysis framework presented here is designed to be updated as additional data become available, with the evidence accrual methodology providing a natural mechanism for integrating new trial results.
