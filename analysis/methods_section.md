# Methods

## Study Design and Data Sources

We performed a systematic comparative analysis of adverse event (AE) safety profiles across chimeric antigen receptor T-cell (CAR-T) therapy indications, comparing autoimmune (systemic lupus erythematosus, SLE) with oncology (diffuse large B-cell lymphoma, DLBCL; acute lymphoblastic leukemia, ALL; multiple myeloma, MM) applications. All data were extracted from published peer-reviewed literature, conference abstracts, and public registries (ClinicalTrials.gov). No proprietary or patient-level data were used. This analysis follows the STROBE reporting guidelines for observational studies where applicable.

## Data Extraction

### SLE CAR-T Trials
Individual SLE CAR-T trial data were curated from 7 published studies (2022-2025), comprising 47 total patients across the following cohorts:
- Mackensen et al., Nat Med 2022 (n=5, anti-CD19)
- Muller et al., N Engl J Med 2024 (n=15, anti-CD19)
- CASTLE (Novartis YTB323) interim, ASH 2024 (n=8, anti-CD19)
- BCMA-CD19 compound CAR-T (Jin et al., 2024) (n=7, dual-target)
- CD19/BCMA co-infusion (2024) (n=6, dual-target)
- Cabaletta RESET-SLE Phase 1 interim, ACR 2024 (n=4, anti-CD19)
- BMS Breakfree-1 SLE cohort preliminary, 2025 (n=2, anti-CD19)

### Oncology Comparator Trials
Oncology comparator data were extracted from pivotal registration trials for FDA-approved CAR-T products:
- DLBCL: ZUMA-1 (axi-cel, n=101), JULIET (tisa-cel, n=111), TRANSCEND NHL 001 (liso-cel, n=269)
- ALL: ELIANA (tisa-cel, n=75)
- MM: KarMMa (ide-cel, n=128), CARTITUDE-1 (cilta-cel, n=97)

### Adverse Event Classification
AEs were graded per the ASTCT consensus criteria (Lee et al., Biol Blood Marrow Transplant 2019; PMID:30275568). Primary endpoints were:
- CRS (any grade and grade >= 3)
- ICANS (any grade and grade >= 3)
- ICAHS (immune effector cell-associated hematotoxicity syndrome) rate
- LICATS (late immune cell-associated toxicity syndrome) rate

## Statistical Methods

### Pooled Rate Estimation
For each indication, AE rates were pooled using inverse-variance weighting by sample size. Ninety-five percent confidence intervals were computed using the Clopper-Pearson exact method (guaranteed coverage >= 95%).

### Seven-Model Risk Estimation Framework
The platform's model registry was applied to estimate the true population rate of severe CRS (grade >= 3) in SLE CAR-T recipients. Each model addresses different aspects of the estimation problem:

1. **Bayesian Beta-Binomial** (Jeffreys prior Beta(0.5, 0.5)): Conjugate model suitable for small samples with sequential updating capability. Posterior = Beta(alpha + events, beta + n - events).

2. **Clopper-Pearson Exact**: Conservative frequentist confidence interval based on the exact binomial distribution. Gold standard for regulatory submissions.

3. **Wilson Score Interval**: Improved coverage properties over the Wald interval for small n and proportions near 0 or 1 (Agresti & Coull, Am Stat 1998).

4. **DerSimonian-Laird Random Effects Meta-Analysis**: Pools effect estimates from multiple studies allowing between-study heterogeneity. Uses Freeman-Tukey double arcsine transformation to stabilize the variance.

5. **Empirical Bayes Shrinkage**: Borrows strength across AE types (CRS, ICANS, ICAHS, LICATS) by shrinking each type's estimate toward the grand mean. Method-of-moments estimation of between-type variance.

6. **Kaplan-Meier Cumulative Incidence**: Non-parametric time-to-event estimate using synthetic CRS onset times (log-normal distribution, mean 2 days, based on published SLE CAR-T CRS kinetics). Greenwood's formula for variance.

7. **Bayesian Predictive Posterior**: Predicts the AE rate in a hypothetical next study of n=50 patients, accounting for both parameter uncertainty and sampling variability via the Beta-Binomial predictive distribution.

### Cross-Validation
Leave-one-study-out cross-validation (LOO-CV) was performed for models compatible with multi-study data (Bayesian Beta-Binomial, Clopper-Pearson, Wilson Score, DerSimonian-Laird). At each fold, one SLE study was held out and the remaining studies were used to predict the held-out study's AE rate. Performance was assessed via root mean squared error (RMSE), mean absolute error (MAE), and empirical coverage probability.

### Mechanistic Prior Construction (Novel Contribution)
A pathway-informed Bayesian framework was developed to construct informative priors from the knowledge graph's mechanistic data. For each AE type, we:

1. Extracted pathway topology features: number of signaling steps, feedback loops, amplification edges, intervention points, and high-confidence mechanistic steps (confidence >= 0.85).

2. Derived a base rate expectation from: (a) the number of amplification/feedback mechanisms (more feedback -> higher expected rate), and (b) the intervention-to-step ratio (more targetable steps -> lower expected rate due to available management).

3. Calibrated the prior strength (effective sample size) from the number of supporting PubMed references, capped at n=10 to prevent prior dominance over sparse observed data.

4. Compared three prior strategies: (a) uninformative Jeffreys Beta(0.5, 0.5), (b) mechanistic pathway-derived, and (c) empirical (discounted from oncology rates, Beta(0.21, 1.29) for CRS). The impact of each prior was assessed by posterior CI width and mean.

Pathway-to-prior mappings were as follows:
- **CRS prior**: Derived from IL-6 trans-signaling (PW:IL6_TRANS_SIGNALING) and TNF/NF-kB (PW:TNF_NFKB) pathways. 3 feedback loops, 2+ amplification edges (PMID:29643512, PMID:30442748, PMID:38123583). Base expectation 3% grade >= 3, attenuated by low tumor burden in SLE and 3 intervention points.
- **ICANS prior**: Derived from BBB disruption pathway (PW:BBB_DISRUPTION_ICANS). CD19+ pericyte on-target/off-tumor mechanism (PMID:33082430). Base expectation 2% grade >= 3, attenuated by lower CRS severity in SLE.
- **HLH/MAS prior**: Derived from IFN-gamma/IL-18 feedback loop (PW:HLH_MAS). Base expectation 0.5%, rare in low-tumor-burden settings (PMID:36906275).

### Cross-Indication Comparison
Pairwise comparisons of SLE vs each oncology indication used two-proportion z-tests with pooled standard errors. Heterogeneity across all studies was assessed using Cochran's Q statistic and I-squared (proportion of total variability due to between-study heterogeneity). Subgroup analysis was performed by therapy construct (CD19-targeting vs BCMA-targeting products).

### Evidence Accrual Analysis
Sequential Bayesian updating was performed using the study timeline (Q4 2022 through projected Q1 2028), applying cumulative data to the informative CRS prior (Beta(0.21, 1.29)) at each timepoint. This demonstrates how credible intervals narrow as additional trial data accrue.

### Software and Reproducibility
All analyses were performed using the Predictive Safety Platform (v0.1.0), implemented in Python 3.11+. Statistical computations used SciPy (scipy.stats), NumPy, and custom implementations of the 7-model registry. All code is publicly available at https://github.com/alto84/safety-research-system. The complete analysis is reproducible by running:
```
PYTHONPATH=. python analysis/publication_analysis.py
```

### Reporting and Transparency
- All statistical claims reference the specific model and data source.
- All mechanistic claims reference PubMed IDs from the knowledge graph.
- Only publicly available data were used (no proprietary sources).
- The analysis follows STROBE guidelines for cross-sectional studies where applicable.
- Appropriate caveats about data limitations (small sample sizes, early-phase data, heterogeneous constructs) are noted throughout.
