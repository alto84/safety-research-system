# Data Scientist / Biostatistician Review

**Reviewer:** Dr. Rachel Chen, PhD (Biostatistics & ML Engineering)
**Date:** 2026-02-07
**Scope:** Model transparency, score calibration, normalization methodology, ensemble aggregation, and responsible AI practices across the clinical dashboard, biomarker scoring models, ensemble runner, and API layer.

---

## Executive Summary

The Predictive Safety Platform implements seven published clinical scoring formulas as deterministic calculators and combines them via a layered ensemble. The underlying biomarker models are faithfully implemented from their respective publications, with proper citations and reasonable input validation. However, there are significant concerns about **how results are aggregated and presented** that could mislead clinicians. The composite score is displayed as a percentage but is not a calibrated probability. The ensemble uses confidence-weighted averaging of ad hoc normalizations. The "max risk" aggregation strategy can be dominated by a single outlier model. These issues do not invalidate the tool, but they require clearer communication and several methodological corrections before clinical deployment.

**Overall Assessment:** The individual model implementations are sound. The aggregation and presentation layer needs substantial revision to meet responsible AI standards for clinical decision support.

---

## 1. Model Transparency

### What works well

- Each score card in the UI displays the **model name**, **raw score**, **risk level**, and **citation** (e.g., `index.html:787-789`). This is good practice.
- The HLH view (`index.html:1290-1302`) shows a full **component breakdown table** with per-variable points for HScore. The CAR-HEMATOTOX view does the same (`index.html:1354-1367`). This level of transparency is exemplary.
- The ensemble runner (`ensemble_runner.py:67-68`) exposes `models_run`, `models_skipped`, and `models_failed` lists at the layer level. The API passes these through to the response.
- The UI shows "X/Y models" in the composite score header (`index.html:777`).

### What needs improvement

- **Skipped models are invisible in the Overview.** The UI shows the count ("4/7 models") but does not list *which* models were skipped or *why*. A clinician seeing "4/7 models" has no way to know whether the missing models are irrelevant (e.g., no cytokine panel ordered) or represent a data quality failure. The layer details (`pred.layers`) contain `models_skipped` arrays but these are not rendered anywhere in the current UI.
- **No per-model contributing factor display in the Overview.** Only the HLH and Hematox views show component breakdowns. The Overview's score grid shows only the aggregate score and risk level per model -- not what drove it. For EASIX, the clinician cannot see the LDH, creatinine, and platelet values that produced the number without navigating to the lab table separately.
- **Layer architecture is not communicated.** The ensemble runner has a Layer 0 / Layer 1 architecture, but the UI does not group or label models by layer. A clinician does not know that EASIX and HScore are "always available" models while Teachey requires specialized cytokine assays.

---

## 2. Confidence Communication

### The composite score is misleading

The composite score (`app.py:359-384`) is computed as:

```
composite = sum(normalised_score_i * confidence_i) / sum(confidence_i)
```

This is then displayed as `(pred.composite_score * 100).toFixed(1) + '%'` (`index.html:775`), placed on a color gradient bar labeled "Low Risk" to "High Risk" (`index.html:766-771`).

**Problem:** This looks like a probability (e.g., "34.2%") but it is not one. It is a weighted average of arbitrarily normalized scores. The percentage symbol and the risk meter create a strong visual implication that this is a calibrated probability of an adverse event. A clinician reading "72.3%" will naturally interpret this as "72.3% chance of a serious event," which is not what this number means.

### Confidence values are ad hoc

- EASIX and Modified EASIX set `confidence = 1.0` when there are no warnings, `0.85` otherwise (`biomarker_scores.py:367-368`). This binary drop has no statistical basis.
- HScore computes `confidence = variables_available / total_variables` (`biomarker_scores.py:822`). This treats all 9 variables as equally important, which contradicts the weighted point system (ferritin at 50 points vs. AST at 19 points).
- Teachey model hardcodes `confidence = 0.95` (`biomarker_scores.py:1212`). This is based on the reported AUC of the original study, but AUC is not confidence in an individual prediction.
- Hay classifier uses a mix of fixed values (0.50, 0.65, 0.70, 0.75, 0.90, 0.95) depending on timing and data completeness (`biomarker_scores.py:1362-1417`). These are reasonable heuristics but are presented as if they were calibrated.

**None of these confidence values have been validated against real-world calibration data.** They are being used as weights in the composite score, which means the composite is influenced by arbitrary scale choices.

### No confidence intervals shown

The UI shows point estimates only. There are no error bars, credible intervals, or uncertainty ranges. For a clinical decision support tool, this is a significant omission.

---

## 3. Calibration Display

### The percentage display is inappropriate

As noted above, `(pred.composite_score * 100).toFixed(1) + '%'` (`index.html:775, 1629`) creates a strong implication of probability. The composite score is a 0-1 number derived from a weighted average of normalized values, not a probability.

**Recommendation:** Either:
1. **Remove the percentage display** and show the composite as a unitless score on an arbitrary scale (e.g., "Composite: 0.34 / 1.0"), or
2. **Calibrate the composite** against actual outcome data so it corresponds to a real probability, or
3. **Replace the composite** with a simpler ordinal summary (e.g., "3 of 5 models report HIGH risk").

### Risk level derivation

The overall `risk_level` in the response comes from `_max_risk()` (`ensemble_runner.py:134-138`), which takes the maximum risk across all models. This means a single model reporting HIGH drives the entire assessment to HIGH. The composite score (a weighted average) and the risk level (a max) can be contradictory: a composite of 0.25 (25%, appears low) with a risk_level of "HIGH" because one model triggered high while four others were low.

The UI displays both the percentage and the risk badge side-by-side (`index.html:763, 774-778`), which could be confusing when they disagree.

---

## 4. Validation Status

### Critical distinction not communicated

These are **deterministic formulas from published literature**, not trained ML models. The docstring in `biomarker_scores.py:1-18` states this clearly, and the API description mentions "deterministic biomarker scoring" (`app.py:113-115`). However, the clinical dashboard UI does not communicate this distinction anywhere.

The UI labels include:
- "Composite Risk Assessment" (`index.html:762`)
- "Risk Assessment Result" (`index.html:1618`)
- "AI-powered adverse event prediction" (in the FastAPI description, `app.py:113`)

The phrase "AI-powered" in the API description is misleading -- these are closed-form arithmetic formulas, not AI/ML models. A clinician seeing "AI-powered prediction" may ascribe more authority to the output than warranted.

**Recommendation:** Add a visible disclaimer in the UI such as: "Scores are computed using published clinical formulas, not trained machine learning models. They should be interpreted alongside clinical judgment." Remove "AI-powered" from descriptions.

### Per-model validation data is incomplete

The models report citations but not:
- Original validation cohort size
- External validation status (has the score been validated outside the original study population?)
- AUC or other performance metrics in the UI (these exist in the code comments but are not displayed)
- Known limitations (e.g., EASIX was validated in allo-HCT before being adapted for CAR-T; the Teachey model was derived from a pediatric ALL cohort)

---

## 5. Score Normalization

### `_normalise_score()` review (`app.py:387-410`)

| Model | Normalization | Concern |
|-------|--------------|---------|
| EASIX | `log1p(score) / log1p(50)` | Why 50? EASIX values in the demo cases reach 81.5 (Case 2, Day 3). Any value above 50 maps to >1.0 (clipped to 1.0). The log transform compresses the clinically important high-end range. The choice of 50 as the denominator is not justified by the literature. |
| Modified EASIX | `log1p(score) / log1p(100)` | Same concern with 100 as denominator. |
| HScore | `score / 337` | Linear normalization. This is defensible since HScore is a bounded additive point system. However, the clinical threshold is at 169 (which normalizes to 0.50), and the relationship between HScore and HLH probability is sigmoidal, not linear. |
| CAR-HEMATOTOX | `score / 10` | Linear normalization of a bounded 0-10 score. Defensible but the clinical threshold is at 3 (normalizes to 0.30), not 5 (0.50). |
| Teachey | Identity (already 0-1 probability) | Appropriate. |
| Hay | Identity (0 or 1) | Appropriate for binary. |

**Key issue:** The normalizations are not validated. The log-transform for EASIX means that an EASIX of 10 (the published HIGH threshold) normalizes to `log(11)/log(51) = 0.61`, while an EASIX of 3.2 (LOW threshold) normalizes to `log(4.2)/log(51) = 0.37`. This compresses the meaningful risk gradient into a narrow band. Meanwhile, HScore's linear normalization gives the HLH threshold (169) a value of 0.50. These different normalization curves mean the models contribute unevenly to the composite despite the weighting.

**These normalizations have no clinical or statistical basis.** They are engineering conveniences that happen to map disparate scales to [0, 1]. The weighted average of these arbitrarily normalized values has no interpretable meaning.

---

## 6. Risk Aggregation

### "Max across all models" approach

The ensemble runner uses `_max_risk()` (`ensemble_runner.py:134-138, 233`) for both layer-level and overall risk. This is a conservative strategy: if any model says HIGH, the patient is HIGH.

**Clinical appropriateness:** This is defensible as a screening approach -- you do not want to miss a true high-risk patient. However, it has significant problems:

1. **Single outlier dominance.** If HScore says HIGH (score >= 169) while EASIX, Modified EASIX, and CAR-HEMATOTOX all say LOW, the patient is classified as HIGH. The clinician sees a big red "HIGH" badge but most models disagree. This could cause alert fatigue.

2. **Risk discordance detection exists but is weak.** The ensemble runner generates a warning when HIGH and LOW coexist (`ensemble_runner.py:251-264`), but this warning is buried in `metadata.ensemble_warnings` in the API response. The UI does not render this warning.

3. **No model weighting by clinical context.** Pre-infusion, only EASIX and CAR-HEMATOTOX are meaningful. During active CRS, HScore and cytokine models become relevant. The ensemble treats all models equally regardless of clinical timepoint.

**Recommendation:** Either:
- Display each model's risk independently and let the clinician synthesize, or
- Use a voting/majority approach (e.g., "3 of 5 models report HIGH"), or
- Weight models differently by clinical phase (pre-infusion vs. active CRS vs. recovery).

---

## 7. Demo Case Validation

### Manual verification of Case 1 (DEMO-001), Baseline (Day -5)

**EASIX:** LDH=280, Creatinine=0.8, Platelets=185
- Formula: (280 * 0.8) / 185 = 224 / 185 = **1.21**
- Demo case lists `easix: 0.74` -- **DISCREPANCY**. With the given values, EASIX should be ~1.21, not 0.74.

Wait -- the demo `scores` field appears to be pre-computed reference values in the demo_cases.js file, not values returned by the API. The actual computation happens server-side when `runPrediction()` is called. The `scores` field in demo_cases.js seems to be for reference/documentation only. However, if they are displayed alongside API results or used for validation, the discrepancy matters.

Rechecking: (280 * 0.8) / 185 = 1.2108. The demo says 0.74. This is wrong by approximately 40%. It appears the demo case `scores` values may have been authored independently of the actual model code.

**HScore for Case 1 Baseline:**
- Temperature 36.8: 0 pts (< 38.4)
- Organomegaly 0 (none): 0 pts
- Cytopenias 0: 0 pts (<=1 lineage)
- Ferritin 250: 0 pts (<2000)
- Triglycerides 1.4: 0 pts (<1.5)
- Fibrinogen 3.2: 0 pts (>2.5)
- AST 22: 0 pts (<30)
- Hemophagocytosis false: 0 pts
- Immunosuppression false: 0 pts
- **Total: 0**. Demo says `hscore: 62` -- **DISCREPANCY**. The actual HScore should be 0 with these values, not 62.

**CAR-HEMATOTOX for Case 1 Baseline:**
- ANC 4.2: 0 pts (>1.0)
- Hemoglobin 12.1: 0 pts (>10)
- Platelets 185: 0 pts (>100)
- CRP 5: 0 pts (<10)
- Ferritin 250: 0 pts (<500)
- **Total: 0**. Demo says `car_hematotox: 1` -- **DISCREPANCY**.

**These pre-computed reference scores in the demo cases do not match the formulas.** However, the actual API will compute scores correctly from the lab values. The `scores` field in `demo_cases.js` appears to be illustrative/intended values rather than computed values, and they are not directly rendered in the UI (the UI uses API predictions instead). This is still problematic for documentation and validation purposes -- anyone reading the demo case code would get incorrect expectations.

### Case 2 (DEMO-002), Day 2 verification

**EASIX:** LDH=1180, Creatinine=1.5, Platelets=52
- Formula: (1180 * 1.5) / 52 = 1770 / 52 = **34.04**
- Demo says `easix: 49.6` -- **DISCREPANCY** (34.0 vs 49.6).

**Conclusion:** The `scores` fields in demo_cases.js are consistently inaccurate relative to the actual formulas. They appear to have been hand-crafted to tell a clinical narrative rather than being computed from the lab values. This is acceptable if they are purely illustrative and the API produces the correct values, but it is misleading for validation purposes.

---

## 8. Missing Model Metadata

The UI currently shows per model: name, raw score, risk level (color-coded), and citation text.

**What should also be shown:**

| Metadata | Current Status | Importance |
|----------|---------------|------------|
| Reported AUC / performance | In code comments only (e.g., `biomarker_scores.py:298`) | High -- clinicians need to know discriminative ability |
| Validation cohort size | Not shown | High -- n=549 for CAR-HEMATOTOX vs. n=162 for Teachey |
| External validation status | Not shown | High -- some models only validated in original cohort |
| Population (adult vs. pediatric, disease type) | Not shown | Critical -- Teachey was derived in pediatric ALL |
| Known limitations | Not shown | Critical -- e.g., EASIX originally for allo-HCT GvHD, adapted for CAR-T |
| When NOT to use | Not shown | Critical -- e.g., Hay classifier only valid within 36h of infusion |
| Model type (formula vs. logistic regression vs. rule-based) | Not shown | Moderate -- helps clinicians understand what the number means |
| Score interpretation guide | Not shown | High -- what does EASIX=15 actually mean clinically? |

---

## 9. Top 5 Improvements (Model Transparency & Responsible AI)

### 1. Replace or relabel the composite percentage display

**Severity: Critical**

The composite score displayed as "XX.X%" with a color gradient bar strongly implies a calibrated probability. It is not. Either:
- Remove the composite entirely and show a risk summary grid ("3 HIGH, 1 MODERATE, 1 LOW")
- Relabel it explicitly: "Aggregate Score (not a probability): 0.34 / 1.00"
- Add a visible caveat: "This is a weighted average of normalized scores, not a probability of an adverse event."

### 2. Show skipped/failed models and explain why

**Severity: High**

When a model is skipped due to missing data, the UI should show it in a distinct "not evaluated" state with the specific missing inputs listed. Currently, a model can silently disappear from the score grid. A clinician needs to know: "Teachey Cytokine Model: NOT EVALUATED -- requires IFN-gamma, sgp130, IL-1RA (not ordered)." This is already computed in the ensemble runner but not rendered.

### 3. Add validation metadata per model

**Severity: High**

Each score card should include (on hover or in an expandable section):
- Original cohort: "Validated in N=549 LBCL patients (multicenter)"
- AUC: "Reported AUC 0.80-0.92 for Grade >= 3 CRS"
- Population caveat: "Originally developed for DLBCL; performance in myeloma/ALL not independently validated"
- Temporal applicability: "Use at baseline/pre-infusion" or "Valid within 36h of infusion"

### 4. Add a clear "Not AI / Not ML" disclosure

**Severity: High**

The tool should prominently state that scores are computed from published deterministic formulas, not from trained machine learning models. Remove "AI-powered" from the API description. Add to the dashboard header or a persistent banner: "Scores computed from published clinical formulas. For clinical decision support only -- not a substitute for clinical judgment."

### 5. Validate and correct normalization or remove the composite

**Severity: High**

If the composite score is retained:
- Document and justify each normalization function with clinical rationale
- Ensure the normalization preserves the published risk thresholds at clinically meaningful composite values (e.g., a patient at the HIGH threshold for every model should produce a composite near 1.0, not 0.6)
- Consider replacing ad hoc normalizations with the models' own risk-level ordinals (LOW=0, MODERATE=0.5, HIGH=1.0) to avoid the distortions of arbitrary continuous mapping

If the composite is too difficult to validate, remove it entirely. An ordinal risk summary (count of models at each risk level) is more honest and equally useful.

---

## Additional Observations

### CRP unit handling
The API converts CRP from mg/L to mg/dL by dividing by 10 (`app.py:287-288`) and provides both to the models. This is correct but should be documented in the UI so clinicians know which unit they should enter. The demo cases use mg/L (matching the CAR-HEMATOTOX convention), while Modified EASIX expects mg/dL. The automatic conversion handles this, but a unit mismatch during manual entry could produce a 10x error.

### Risk discordance warning is buried
The ensemble runner detects risk discordance (`ensemble_runner.py:251-264`) and stores it in `ensemble_warnings`, but the UI does not render these warnings. They appear only in `metadata.ensemble_warnings` in the API response. This is a missed opportunity for clinically important information.

### HScore with partial data
HScore allows scoring with as few as 3 of 9 variables (`biomarker_scores.py:808`), producing a "lower bound" score with reduced confidence. This is pragmatic but the UI does not clearly communicate that the HScore is partial. A partial HScore of 85 might look reassuringly low, but with only 3 of 9 variables, the true score could be much higher. The HScore view shows `variables_available` in the metadata but does not present it prominently.

### Teachey coefficient source
The logistic regression coefficients (`biomarker_scores.py:1131-1135`) are described as "approximate published coefficients." If these are approximations rather than exact values from the paper, this should be flagged. Even small coefficient errors can produce meaningfully different probabilities near decision boundaries.

### No temporal model applicability
The ensemble runs all models regardless of clinical timepoint. EASIX is most relevant at baseline/pre-infusion. The Hay classifier is designed for the first 36 hours. Running the Hay classifier on Day 10 data is not clinically meaningful, even though the code handles it (with reduced confidence). The UI should gray out or annotate models that are outside their validated timeframe.

---

## Summary Table

| Concern | Severity | Current State | Recommendation |
|---------|----------|---------------|----------------|
| Composite shown as probability | Critical | "XX.X%" on gradient bar | Remove % or add explicit "not a probability" label |
| No skipped model visibility | High | Silent omission | Show skipped models with reasons |
| No model validation metadata | High | Citations only | Add AUC, cohort size, population, limitations |
| "AI-powered" labeling | High | In API description | Replace with "published clinical formulas" |
| Normalization is ad hoc | High | Log/linear mix, no validation | Validate or replace with ordinal approach |
| Max-risk outlier dominance | Moderate | Single model drives overall risk | Add discordance display; consider voting |
| Demo case scores inaccurate | Moderate | Hand-crafted, not computed | Recompute or remove `scores` field |
| Risk discordance warnings hidden | Moderate | In API metadata, not UI | Render as alert banner |
| Partial HScore not flagged clearly | Moderate | In metadata only | Add prominent "partial score" indicator |
| No temporal model applicability | Moderate | All models run always | Annotate or suppress out-of-window models |

---

*Review prepared using static code analysis only. No patient data was used. All observations are based on source code review of biomarker_scores.py, ensemble_runner.py, app.py, index.html, and demo_cases.js.*
