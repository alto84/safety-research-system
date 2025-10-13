# Statistical Analysis Audit Checklist

## Overview
This checklist is used by the Statistics Auditor to validate statistical analysis outputs.

## Anti-Fabrication Checks (CRITICAL)

### Result Fabrication
- [ ] All numerical results backed by actual data
- [ ] Data source documented for every statistic
- [ ] No p-values without raw data access
- [ ] No effect sizes without measurement basis
- [ ] Sample sizes provided and verified

### Banned Claims
- [ ] No "statistically significant" without p-value and context
- [ ] No scores above 80% without external validation
- [ ] No composite metrics without calculation shown
- [ ] No "X times more likely" without baseline data

### Measurement Requirements
- [ ] All statistics derived from measured data (not simulated)
- [ ] Measurement methodology documented
- [ ] Data collection process described
- [ ] Sample characteristics provided

## Completeness Checks

### Required Fields
- [ ] Summary present and substantive
- [ ] Primary result documented
- [ ] Interpretation provided
- [ ] Assumptions listed
- [ ] Limitations documented
- [ ] Methodology described
- [ ] Confidence level stated

### Primary Result Fields
- [ ] Statistical test identified
- [ ] Test statistic provided
- [ ] P-value reported (or justification for absence)
- [ ] Effect size calculated
- [ ] Confidence intervals included

## Methodology Validation

### Test Selection
- [ ] Statistical test appropriate for data type
- [ ] Test matches research question
- [ ] Alternatives considered if applicable
- [ ] Justification for test choice provided

### Methodology Documentation
- [ ] Analysis plan documented
- [ ] Software/tools specified
- [ ] Statistical significance level (α) stated
- [ ] Power analysis included (if prospective)
- [ ] Multiple comparison adjustments noted (if applicable)

### Data Description
- [ ] Sample size reported
- [ ] Sample characteristics described
- [ ] Missing data acknowledged
- [ ] Outliers addressed
- [ ] Data transformations documented

## Assumptions Validation (CRITICAL)

### Assumption Documentation
- [ ] All relevant assumptions listed
- [ ] Minimum 2 assumptions documented
- [ ] Assumptions specific to test used
- [ ] Verification methods described

### Common Assumptions by Test Type

#### T-tests
- [ ] Independence of observations
- [ ] Normality of distribution
- [ ] Homogeneity of variance (if applicable)

#### ANOVA
- [ ] Independence of observations
- [ ] Normality within groups
- [ ] Homogeneity of variance across groups

#### Regression
- [ ] Linearity
- [ ] Independence of errors
- [ ] Homoscedasticity
- [ ] Normality of residuals
- [ ] No multicollinearity (multiple regression)

#### Chi-square
- [ ] Independence of observations
- [ ] Expected frequencies ≥5
- [ ] Adequate sample size

### Assumption Verification
- [ ] Assumptions tested/verified (not just stated)
- [ ] Verification results reported
- [ ] Violations addressed
- [ ] Robustness checks performed if assumptions violated

## Statistical Rigor

### Effect Size Reporting
- [ ] Effect size calculated and reported
- [ ] Effect size measure appropriate
- [ ] Clinical/practical significance discussed
- [ ] Not just statistical significance

### Confidence Intervals
- [ ] Confidence intervals provided for key estimates
- [ ] CI level specified (typically 95%)
- [ ] Interpretation of CIs included
- [ ] CIs consistent with p-values

### Multiple Comparisons
- [ ] Multiple testing acknowledged if applicable
- [ ] Correction applied (Bonferroni, FDR, etc.)
- [ ] Family-wise error rate considered
- [ ] Adjusted p-values reported

## Uncertainty Quantification (REQUIRED)

### Confidence Expression
- [ ] Overall confidence level stated (low/moderate/high)
- [ ] Confidence justified by data quality
- [ ] Uncertainty sources identified
- [ ] Limitations acknowledged

### Limitations
- [ ] At least 3 statistical limitations identified
- [ ] Sample size limitations noted
- [ ] Generalizability discussed
- [ ] Confounding variables acknowledged
- [ ] Missing data impact assessed

### Error Sources
- [ ] Measurement error considered
- [ ] Sampling error quantified
- [ ] Systematic biases identified
- [ ] Random variation acknowledged

## Interpretation Validation

### Result Interpretation
- [ ] Results accurately represent data
- [ ] Clinical significance addressed
- [ ] Context provided
- [ ] Limitations impact interpretation
- [ ] Alternative explanations considered

### Causal Language
- [ ] Appropriate causal language for study design
- [ ] Correlation vs causation distinguished
- [ ] Confounding acknowledged
- [ ] Temporal relationships considered

### Overgeneralization Checks
- [ ] Conclusions match analysis scope
- [ ] Population generalizability addressed
- [ ] No extrapolation beyond data
- [ ] Subgroup analyses appropriate

## Data Quality Checks

### Data Integrity
- [ ] Data source verified
- [ ] Data collection process described
- [ ] Data cleaning steps documented
- [ ] Quality control measures noted

### Missing Data
- [ ] Missing data percentage reported
- [ ] Missing data pattern described
- [ ] Missing data handling method documented
- [ ] Sensitivity analysis for missing data

### Outliers
- [ ] Outlier detection method described
- [ ] Outliers identified and reported
- [ ] Outlier handling justified
- [ ] Sensitivity analysis with/without outliers

## Subgroup Analysis (if applicable)

### Subgroup Definition
- [ ] Subgroups defined a priori
- [ ] Subgroup rationale provided
- [ ] Sample sizes adequate per subgroup
- [ ] Multiple testing adjusted

### Subgroup Results
- [ ] Interaction tests performed
- [ ] Results reported for all subgroups
- [ ] Heterogeneity assessed
- [ ] Overfitting considered

## Regulatory Standards

### Clinical Trials (if applicable)
- [ ] Analysis follows statistical analysis plan
- [ ] ITT analysis included
- [ ] Per-protocol analysis justified
- [ ] Safety analyses comprehensive
- [ ] Multiplicity addressed

### Safety Assessment
- [ ] Adverse event rates calculated
- [ ] Relative risk or odds ratios provided
- [ ] Confidence intervals for safety metrics
- [ ] Dose-response relationships explored

## Issue Severity Classification

### Critical Issues (Must Fix)
- Fabricated statistics without data
- Missing data source documentation
- Assumptions violated and unaddressed
- Inappropriate test for data/question
- No uncertainty quantification
- Causal claims from correlational data

### Warning Issues (Should Fix)
- Incomplete assumption documentation
- Missing confidence intervals
- Effect size not reported
- Insufficient limitations
- Multiple testing not addressed
- Missing sample characteristics

### Info Issues (Nice to Have)
- Additional sensitivity analyses
- More detailed methodology
- Expanded interpretation
- Additional subgroup analyses
- Power calculation for future studies

## Recommended Actions by Issue Type

### If Data Source Not Documented
1. Add data source information
2. Describe data collection
3. Provide sample characteristics
4. Document data quality measures
5. Mark as CRITICAL - retry required

### If Assumptions Not Verified
1. Test each assumption
2. Report verification results
3. Address violations with robust methods
4. Perform sensitivity analyses
5. Mark as CRITICAL - retry required

### If Uncertainty Not Quantified
1. Add confidence intervals
2. State overall confidence level
3. Expand limitations section
4. Discuss error sources
5. Mark as WARNING - retry recommended

### If Results Overinterpreted
1. Align conclusions with analysis scope
2. Remove causal language (if inappropriate)
3. Add qualifying statements
4. Expand limitations
5. Consider alternative explanations

## CLAUDE.md Compliance

All statistical analyses must comply with CLAUDE.md:
- MEASUREMENT REQUIREMENT: All statistics from actual data
- NO COMPOSITE SCORES without calculation basis
- EVIDENCE CHAIN: Provide data sources and methodology
- UNCERTAINTY EXPRESSION: Always include confidence levels
- STATISTICAL RIGOR: Include sample size, CI, methodology
- Truth over optimism
- No fabrication, ever

## Special Considerations

### Bayesian Analyses
- [ ] Prior distributions specified and justified
- [ ] Posterior distributions reported
- [ ] Credible intervals provided
- [ ] Prior sensitivity analysis performed

### Machine Learning Models
- [ ] Train/test split described
- [ ] Cross-validation performed
- [ ] Feature importance reported
- [ ] Overfitting prevention measures
- [ ] Model assumptions verified

### Time Series
- [ ] Stationarity tested
- [ ] Autocorrelation assessed
- [ ] Seasonal patterns addressed
- [ ] Trend analysis appropriate
