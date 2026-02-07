# Iteration 3 -- Clinical Safety Officer Final Review

**Reviewer:** Dr. Angela Frost, MD, PhD -- Clinical Safety Officer
**Date:** 2026-02-07
**Scope:** Final pre-pilot safety verification of Cell Therapy Safety Platform dashboard
**Files Reviewed:**
- `src/api/static/index.html` (2305 lines)
- `src/api/static/demo_cases.js` (~1800 lines, 8 demo cases)
**Purpose:** Confirm that 10 identified safety fixes from prior review rounds are correctly implemented, identify any remaining P0 patient safety issues before pilot use.

---

## Part 1: Verification of Prior Safety Fixes

### Fix 1 -- MAP Calculation and MAP<65 Alert

- [x] **Implemented:** Yes. Lines 1067-1069 in the Overview lab table compute MAP as `(systolic_bp + 2 * diastolic_bp) / 3`, displayed in the "Derived Vitals" section. Lines 2158-2161 in `generateAlerts()` fire a danger-level alert when MAP < 65.
- [x] **Correct:** The formula `(SBP + 2*DBP) / 3` is the standard clinical MAP approximation. Threshold of 65 mmHg is the accepted critical threshold for organ perfusion (Surviving Sepsis Campaign).
- **Edge cases:**
  - If `systolic_bp` or `diastolic_bp` is missing/null, the outer `if (vitals.systolic_bp && vitals.diastolic_bp)` guard on line 2158 correctly prevents the calculation. No division-by-zero risk.
  - MAP display on line 1069 uses `.toFixed(0)`, alert message on line 2161 also uses `.toFixed(0)`. Consistent.
  - **Minor concern:** The MAP display section (lines 1067-1081) is only rendered inside the Overview view. The CRS view, Day 1 view, and Clinical Visit results do NOT display derived MAP. A clinician in the CRS Monitor tab would not see this value. **Severity: P1.**

**VERDICT: PASS -- correctly implemented.**

---

### Fix 2 -- Shock Index Calculation and Alerts (SI>0.9 Warning, SI>1.2 Danger)

- [x] **Implemented:** Yes. Lines 1070 and 2163-2168 compute SI as `heart_rate / systolic_bp`. Warning fires at SI > 0.9, danger at SI > 1.2.
- [x] **Correct:** Shock Index = HR / SBP is the standard formula. SI > 0.9 as early warning and SI > 1.2 as danger are clinically appropriate thresholds (Allgower & Burri classification).
- **Edge cases:**
  - Guard on line 2163 checks `vitals.heart_rate` before dividing: `const si = vitals.heart_rate ? vitals.heart_rate / vitals.systolic_bp : null`. If HR is 0 (cardiac arrest), SI would be 0 and no alert fires -- but in that scenario the patient is in arrest and this is not the relevant concern. Acceptable.
  - Display in the lab table (line 1072) uses separate styling: `si > 1.2` gets `cell-high`, `si > 0.9` gets `cell-low`. Consistent with alert tiers.
  - SI display and alerts are only in Overview. Same P1 concern as MAP regarding other tabs.

**VERDICT: PASS -- correctly implemented.**

---

### Fix 3 -- ICANS-Without-CRS Alert (Dexamethasone Guidance)

- [x] **Implemented:** Yes. Lines 2178-2181 in `generateAlerts()` check `clinical.icans_grade > 0 && (!clinical.crs_grade || clinical.crs_grade === 0)` and fire a danger-level alert.
- [x] **Correct:** The alert message explicitly states: "Dexamethasone is first-line for isolated ICANS. Tocilizumab has limited CNS penetration and is NOT recommended as initial therapy for isolated ICANS." This is correct per ASTCT consensus guidelines and is a critical clinical distinction.
- **Edge cases:**
  - The condition `!clinical.crs_grade || clinical.crs_grade === 0` correctly handles both undefined and zero. If `crs_grade` is explicitly `0` (CRS resolved) while `icans_grade > 0`, the alert fires. This is the correct clinical scenario (ICANS often peaks as CRS resolves).
  - Demo Case 5 (Sarah Thompson, Day 7) has `icans_grade: 3, crs_grade: 0` -- this should correctly trigger the alert.
  - **Edge case concern:** If `clinical` is undefined entirely, `tp.clinical || {}` on line 2178 produces an empty object, so `icans_grade` would be `undefined`, and `undefined > 0` is `false`. Alert does not fire. This is correct behavior (no ICANS data = no alert).

**VERDICT: PASS -- correctly implemented.**

---

### Fix 4 -- HScore >= 169 Alert

- [x] **Implemented:** Yes. Lines 2171-2176 in `generateAlerts()` search `pred.individual_scores` for the HScore model and fire a danger alert when `hscore.score >= 169`.
- [x] **Correct:** The 169 threshold corresponds to >93% probability of HLH per Fardet et al. 2014. The alert message correctly references this probability and recommends pulse methylprednisolone and hematology consultation.
- **Edge cases:**
  - If the API fails to return an HScore (model skipped, network error), `pred.individual_scores.find(...)` returns `undefined`, and `undefined.score` would throw. However, the `if (hscore && hscore.score >= 169)` guard on line 2173 prevents this. Safe.
  - Demo Case 4, Day 5: HScore 212 -- should trigger. Day 4: HScore 158 -- should not trigger (correctly under 169). Day 7 (ICU Day 2): HScore 195 -- should trigger.
  - The HLH view (lines 1590-1601) also visually flags HScore >= 169 with "HIGH PROBABILITY HLH (>93%)" in a red badge. Consistent.

**VERDICT: PASS -- correctly implemented.**

---

### Fix 5 -- "Critical" Risk Level No Longer Renders as Blue UNKNOWN

- [x] **Implemented:** Yes. The `riskClass()` function (lines 642-650) explicitly maps `'critical'` to `'risk-critical'` on line 645, before the catch-all `return 'risk-unknown'` on line 649.
- [x] **Correct:** The CSS class `.risk-critical` (line 179) renders with `background: #450a0a; color: #fecaca; font-weight: 700;` and has a pulsing red animation. This is visually distinct and alarming. Dark theme override on line 67 also correctly styles it: `background: #7f1d1d; color: #fecaca`.
- **Edge cases:**
  - The `riskClass` function normalizes to lowercase on line 644 (`const l = level.toLowerCase()`), so "Critical", "CRITICAL", or "critical" all match correctly.
  - `riskBorderClass()` on line 655 maps `'critical'` to `'risk-high-border'` (same as high). This is acceptable since there is no separate `risk-critical-border` class.
  - Demo Case 4 (Robert Kim), Day 5 has `expected_risk: "critical"` -- this would be rendered with the patient sidebar list. However, the `risk` variable in `renderPatientList()` on line 700 reads from `p.timepoints[tpIdx]?.expected_risk`. Since the risk badge is based on the *currently selected* timepoint's `expected_risk`, it will only show "CRITICAL" when that specific timepoint is active. The API prediction `risk_level` could also return "critical" -- this is separately handled by `riskClass(pred.risk_level)` in the score cards and composite display.

**VERDICT: PASS -- correctly implemented.**

---

### Fix 6 -- ALT Normal Range Changed to 40 U/L (Was 33)

- [x] **Implemented:** Yes. Line 566 in `NORMAL_RANGES` defines `alt: { low: 0, high: 40, unit: 'U/L', name: 'ALT' }`.
- [x] **Correct:** 40 U/L is the standard upper limit of normal for ALT used by most clinical laboratories. The previous value of 33 U/L would have generated false-positive "HIGH" flags.
- **Edge cases:**
  - The ALT > 200 alert (line 2154) messages "ALT > 5x ULN" and references ULN of 40: `5 * 40 = 200`. This is internally consistent.
  - The `demo_cases.js` header comment on line 16 states `ALT: 7-56 U/L`. This is inconsistent with the dashboard's normal range of 0-40. The comment in demo_cases.js uses a broader range. **This is a documentation inconsistency but does not affect patient safety since the dashboard code uses the correct 40 U/L threshold.** The comment range of 7-56 appears to reference a different lab's reference range. **Severity: P2.**

**VERDICT: PASS -- correctly implemented. Minor documentation inconsistency in demo_cases.js.**

---

### Fix 7 -- ICE Score Displayed From Patient Data at Top of ICANS View

- [x] **Implemented:** Yes. Lines 1437-1468 in `renderICANS()` display a prominent ICE score card at the top of the ICANS view. The score is read from `tp.clinical?.ice_score` (line 1438). It shows the numeric score, color-coded (green >= 7, yellow >= 3, red < 3), the ICANS grade, and delta from previous timepoint.
- [x] **Correct:** The ICE score display includes:
  - Current score as `X/10` in large monospace font
  - Color coding matching ICANS grade thresholds
  - Delta showing direction of change from prior timepoint (lines 1443-1449)
  - Fallback message if no ICE score is recorded
- **Edge cases:**
  - If `ice_score` is 0, `hasIce` on line 1440 would be `false` (since `0 != null` is `true`, but `0` is falsy in `const hasIce = iceScore != null`). Wait -- `iceScore != null` with `!=` (loose equality) means `0 != null` evaluates to `true`. So `hasIce = true` when ICE is 0. This is correct. An ICE score of 0 is clinically meaningful (Grade 4 ICANS) and should be displayed.
  - The delta calculation on line 1446 `prevIce !== iceScore` correctly handles same-value case (no delta shown).

**VERDICT: PASS -- correctly implemented.**

---

### Fix 8 -- Tocilizumab Weight-Based Dose Shown in CRS Management Protocols

- [x] **Implemented:** Yes. Lines 1308 and 1311 in `renderCRS()` calculate and display the weight-based dose:
  - Grade 2: `Tocilizumab 8mg/kg IV (max 800mg) [${Math.min(currentPatient.weight_kg * 8, 800).toFixed(0)}mg for ${currentPatient.weight_kg}kg]`
  - Grade 3: Same calculation inline.
- [x] **Correct:** 8 mg/kg with a maximum of 800 mg is the FDA-approved dosing for tocilizumab in CRS. The `Math.min(..., 800)` correctly caps the dose.
- **Edge cases:**
  - If `currentPatient?.weight_kg` is undefined or null, the conditional `${currentPatient?.weight_kg ? ... : ''}` prevents display. The generic "Tocilizumab 8mg/kg IV" text still shows. Safe fallback.
  - For demo Case 2 (James Williams, 92 kg): `92 * 8 = 736 mg`, correctly under the 800 mg cap.
  - For a hypothetical 120 kg patient: `120 * 8 = 960`, capped to 800. Correct.
  - **Concern:** Grade 4 management (line 1313-1314) does NOT show weight-based dosing. It says "Tocilizumab + High-dose methylprednisolone 1g IV." The tocilizumab dose is not specified at Grade 4. This is a minor inconsistency. **Severity: P2.**
  - **Concern:** The dose is shown only in the CRS Monitor tab. The Overview tab alerts for high CRS do not include dosing. This is acceptable since dosing is protocol-specific and belongs in the management tab.

**VERDICT: PASS -- correctly implemented for Grades 2-3. Grade 4 lacks specific dose display (P2).**

---

### Fix 9 -- Comprehensive FDA/CDS Disclaimer

- [x] **Implemented:** Yes. Lines 535-537 contain a footer disclaimer: "This software is NOT an FDA-cleared or approved medical device. Not intended to diagnose, treat, cure, or prevent any disease. All clinical decisions must be made by qualified healthcare providers exercising independent clinical judgment. Scoring algorithms are deterministic calculations from published formulas (EASIX, HScore, CAR-HEMATOTOX, Teachey, Hay). The composite risk index is NOT a validated clinical prediction."
- [x] **Correct:** The disclaimer correctly:
  - States non-FDA-cleared status
  - Explicitly names the scoring algorithms used
  - Distinguishes deterministic scores from the composite risk index
  - Requires independent clinical judgment
  - Links to version details with algorithm citations
- **Edge cases:**
  - The disclaimer is a persistent footer in the main content area, visible on all task views. Good.
  - It is hidden during print (`@media print` hides `.btn` but the disclaimer div does not have a class that would be hidden). Actually, looking at print styles lines 358-381, the disclaimer footer is inside `.content-area` which is not hidden. So it WILL appear in printed output. This is desirable for legal purposes.
  - **Concern:** The disclaimer uses `alert()` for version details (onclick handler line 536). A modal or separate page would be more professional for a clinical tool. **Severity: P2 (cosmetic/professional).**

**VERDICT: PASS -- correctly implemented.**

---

### Fix 10 -- Risk Icons (Not Just Color) on Sidebar Badges

- [x] **Implemented:** Yes. Line 708 in `renderPatientList()` renders `${getRiskIcon(risk)} ${(risk || 'unknown').toUpperCase()}`. The `getRiskIcon()` function (lines 2102-2109) returns:
  - `'high'` -> warning sign (&#9888;)
  - `'moderate'` -> triangle (&#9650;)
  - `'low'` -> checkmark (&#10003;)
- [x] **Correct:** Icons provide a non-color-dependent visual cue for risk level, improving accessibility for color-blind users. The risk badge on score cards (line 1037) also includes `getRiskIcon(s.risk_level)`. Risk meter labels (line 1018) also include icons.
- **Edge cases:**
  - `getRiskIcon('critical')` returns `''` (empty string) because there is no case for `'critical'` in the function. The function handles `'high'`, `'moderate'`, and `'low'` only. **This means a "CRITICAL" risk level gets NO icon.** This is a safety gap. **Severity: P1.**
  - `getRiskIcon(null)` or `getRiskIcon(undefined)` returns `''` due to the guard on line 2103. Safe for null inputs.
  - Dark theme and print overrides for `.risk-critical` exist (lines 67, 376), so color styling is present, but the missing icon is a concern for accessibility.

**VERDICT: PARTIAL PASS -- icons present for low/moderate/high, but MISSING for "critical" risk level.**

---

## Part 2: Remaining Safety Issues

### P0 -- CRITICAL (Must Fix Before Pilot)

#### P0-1: `generateAlerts()` is NOT called on ICANS, HLH, CRS, Day1, Hematox, or Discharge views

The `generateAlerts()` function is comprehensive and contains all the critical safety logic (MAP alert, SI alert, HScore alert, ICANS-without-CRS alert, hypotension, hypoxia, etc.). However, it is ONLY invoked in two places:

1. `renderOverview()` -- line 1002: `const alerts = generateAlerts(tp, pred);`
2. `runManualPrediction()` -- line 1943: `const alerts = generateAlertsFromPrediction(pred, labs, vitals);`

The following views do **NOT** call `generateAlerts()` and therefore do **NOT** display any alerts:
- `renderCRS()` -- has hardcoded fever alert only (lines 1273-1278), but NO MAP, SI, HScore, ICANS, or other alerts
- `renderICANS()` -- NO alerts at all
- `renderHLH()` -- has its own inline ferritin/fibrinogen check (lines 1573-1581), but NOT the full alert set
- `renderDay1()` -- has its own inline fever check only
- `renderHematox()` -- NO alerts
- `renderDischarge()` -- NO alerts

**Impact:** A clinician viewing the CRS tab for a patient with MAP < 65 and SI > 1.2 would see NO alert. A clinician on the ICANS tab for a patient with HScore >= 169 would see NO HScore alert. The safety alerts are siloed to the Overview tab only.

**Recommendation:** All task views that display patient data must call `generateAlerts()` and render the alerts banner at the top of the view.

---

#### P0-2: `generateAlerts()` does not check for `pred.risk_level === 'critical'`

Line 2121 checks: `if (pred.risk_level === 'high')`. There is no check for `pred.risk_level === 'critical'`. If the API returns a "critical" risk level (as demo case 4 day 5 has `expected_risk: "critical"`), the HIGH RISK alert would NOT fire.

**Impact:** The most severe risk classification produces no risk-level alert in the overview.

**Recommendation:** Change the condition to `if (pred.risk_level === 'high' || pred.risk_level === 'critical')` or use a set: `if (['high', 'critical'].includes(pred.risk_level))`.

---

#### P0-3: No SpO2 display or oxygen requirement in vital signs derived section

The "Derived Vitals" section (lines 1067-1081) shows MAP, Shock Index, and O2 requirement string. However, the actual SpO2 numeric value is not displayed in any lab table or vitals section in the Overview. SpO2 is only used for alerting (line 2148: `spo2 < 94`). SpO2 is not in `NORMAL_RANGES` and therefore does not appear in the lab value table.

For a cell therapy dashboard, SpO2 is a critical vital sign that must be visible at a glance, not just alerting in the background.

**Impact:** Clinician may miss a SpO2 of 90% if it is only surfaced as an alert (which itself only shows in Overview).

**Recommendation:** Add SpO2 to the derived vitals display, or add it to a separate vital signs display panel visible across all task views.

---

#### P0-4: `generateAlertsFromPrediction()` wrapper loses clinical data for ICANS-without-CRS check

Line 2186-2188:
```javascript
function generateAlertsFromPrediction(pred, labs, vitals) {
  return generateAlerts({ labs, vitals }, pred);
}
```

This constructs a synthetic timepoint with only `labs` and `vitals`. It does NOT pass `clinical` data (which includes `icans_grade` and `crs_grade`). Inside `generateAlerts()`, line 2178 reads `const clinical = tp.clinical || {};`, which will be `{}` since no `.clinical` property was passed.

**Impact:** The ICANS-without-CRS alert (Fix 3) can NEVER fire from the Clinical Visit manual entry view. A clinician manually entering data for a patient with ICANS Grade 3 and CRS Grade 0 would receive no alert about dexamethasone being first-line.

**Recommendation:** Pass clinical data through `generateAlertsFromPrediction()`, or add clinical input fields to the Clinical Visit form.

---

### P1 -- HIGH (Should Fix Before Pilot)

#### P1-1: `getRiskIcon('critical')` returns empty string -- no icon for most severe risk level

As noted in Fix 10 verification. The `getRiskIcon` function (lines 2102-2109) has no case for `'critical'`. This means sidebar badges, score cards, and risk meter labels for critical-risk patients display no icon, undermining the accessibility improvement that icons were intended to provide.

**Recommendation:** Add `if (l === 'critical') return '&#9760;';` (skull/crossbones) or `'&#9888;&#9888;'` (double warning) or another distinct icon.

---

#### P1-2: MAP and Shock Index only visible in Overview tab

As noted in Fix 1 and Fix 2 verification. The derived vitals section showing MAP, SI, and O2 is only rendered in `renderOverview()` (lines 1067-1081). The CRS Monitor view, which is arguably where clinicians most need hemodynamic assessment, does not display these values.

**Recommendation:** Extract the derived vitals display into a reusable function and render it in CRS, Day 1, and Overview views at minimum.

---

#### P1-3: Discharge readiness uses risk_level instead of CRS grade for discharge criterion

Line 1728: `{ name: 'CRS resolved or Grade <= 1', met: (pred?.risk_level || 'low') !== 'high' }`.

This checks the composite `risk_level` (which aggregates EASIX, HScore, CAR-HEMATOTOX, etc.) instead of the actual CRS grade (`tp.clinical?.crs_grade`). A patient could have a "high" composite risk from HScore or CAR-HEMATOTOX while having CRS Grade 0 (resolved), and the discharge criterion would incorrectly show as NOT met.

**Impact:** May delay discharge decisions or cause confusion. The criterion text says "CRS resolved or Grade <= 1" but the logic checks something entirely different.

**Recommendation:** Change to `met: (tp.clinical?.crs_grade ?? 0) <= 1`.

---

#### P1-4: No heart rate or blood pressure displayed in vital sign summaries for non-overview views

The CRS view shows trend charts for CRP, Ferritin, LDH, and Fibrinogen (lines 1323-1340) but does NOT include heart rate or blood pressure trends. For CRS grading (which depends on hypotension and vasopressor requirement), HR and BP trends are essential.

---

#### P1-5: Demo case ALT reference range inconsistency

The `demo_cases.js` header comment (line 16) states `ALT: 7-56 U/L`, but the dashboard uses `0-40 U/L`. While not a runtime error, if someone uses the demo_cases.js documentation as a reference for normal ranges, they would use the wrong threshold.

---

### P2 -- MODERATE (Should Fix Before General Availability)

#### P2-1: Discharge criterion for ICANS uses hardcoded `true`

Line 1729: `{ name: 'ICANS resolved or Grade <= 1', met: true }`. This is always `true` regardless of the patient's actual ICANS grade. A patient with active Grade 3 ICANS would show this criterion as met.

**Recommendation:** Change to `met: (tp.clinical?.icans_grade ?? 0) <= 1`.

---

#### P2-2: Discharge criterion for vasopressors and O2 always hardcoded `true`

Lines 1726-1727: `{ name: 'No vasopressor requirement', met: true }` and `{ name: 'No supplemental O2 requirement', met: true }`. These should check `tp.clinical?.oxygen_requirement` at minimum (O2 is available in demo data).

---

#### P2-3: Grade 4 CRS management does not show weight-based tocilizumab dose

As noted in Fix 8. Line 1313-1314 for Grade 4 management shows generic "Tocilizumab" without the weight-based calculation that is shown for Grades 2-3.

---

#### P2-4: Version details shown via `alert()` dialog

Line 536 uses `alert(...)` to show software version and algorithm citations. This is not appropriate for a clinical tool -- should be a proper modal or info panel.

---

#### P2-5: No validation of ICE score calculator inputs

The `calculateICE()` function (lines 2042-2060) parses `parseInt()` on select values. While selects have predefined options (unlikely to produce NaN), the function does not validate the total or handle edge cases where DOM elements might be missing.

---

#### P2-6: Checklist state not tied to task view in persistence

The `checklistKey` function (line 2242) includes `currentTask` in the key, but the actual checkboxes rendered in views (e.g., lines 1197-1202 in Pre-Infusion) do not use `data-checklist-idx` attributes or call `onChecklistChange()`. The persistence mechanism is defined but not wired to the rendered checkboxes. Checklist state is ephemeral.

---

## Part 3: Summary

### Verification Results

| # | Fix Description | Status | Notes |
|---|----------------|--------|-------|
| 1 | MAP calculation and MAP<65 alert | PASS | Correct formula, correct threshold, but only in Overview |
| 2 | Shock Index alerts (SI>0.9, SI>1.2) | PASS | Correct formula, correct thresholds, but only in Overview |
| 3 | ICANS-without-CRS alert (dexamethasone) | PASS | Correct condition and guidance |
| 4 | HScore >= 169 alert | PASS | Correct threshold, correct recommendation |
| 5 | "Critical" no longer renders as blue UNKNOWN | PASS | Correct CSS class mapping |
| 6 | ALT normal range = 40 U/L | PASS | Correct threshold; minor doc inconsistency in demo_cases.js |
| 7 | ICE score displayed at top of ICANS view | PASS | Score, grade, delta all shown |
| 8 | Tocilizumab weight-based dose in CRS protocols | PASS | Correct for Grade 2-3; missing from Grade 4 |
| 9 | Comprehensive FDA/CDS disclaimer | PASS | Present, persistent, legally appropriate |
| 10 | Risk icons on sidebar badges | PARTIAL | Icons present for low/moderate/high, MISSING for critical |

**9 of 10 fixes fully verified. 1 partial (missing critical-level icon).**

### Remaining Issue Counts

| Severity | Count | Summary |
|----------|-------|---------|
| P0 | 4 | Alerts siloed to Overview; no critical-level alert; SpO2 not displayed; ICANS alert broken in Clinical Visit |
| P1 | 5 | Missing critical icon; MAP/SI only in Overview; discharge logic wrong; no HR/BP trends in CRS; ALT doc mismatch |
| P2 | 6 | Discharge hardcoded criteria; Grade 4 dose; alert() dialog; ICE validation; checklist persistence |

### Recommendation

**NOT READY for clinical pilot in current state.**

The 4 P0 issues represent genuine patient safety risks:

1. Safety alerts that only appear on one tab create a fragmented safety picture. Clinicians navigating to the CRS or ICANS tabs -- the exact views where they need alerts most -- will see none of the critical hemodynamic or HScore alerts.

2. The "critical" risk level gap in `generateAlerts()` means the most dangerous patients produce FEWER alerts than "high" risk patients. This is a severity inversion.

3. SpO2 is a primary vital sign for CRS grading (hypoxia determines Grade 2 vs. Grade 3). It must be visible, not just used for background alerting.

4. The ICANS-without-CRS alert -- one of the most important clinical safety features -- is structurally broken in the Clinical Visit manual entry workflow.

**Minimum required before pilot:** Fix all 4 P0 issues and the P1-1 critical icon issue. The remaining P1 and P2 issues should be addressed before any expansion beyond a tightly supervised pilot.

---

*Reviewed by: Dr. Angela Frost, MD, PhD*
*Clinical Safety Officer*
*2026-02-07*
