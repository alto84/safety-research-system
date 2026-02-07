# Iteration 2 Synthesis: Prioritized Task List for Iteration 3

**Date:** 2026-02-07
**Source Reviews (6 reviewers):**
1. **EM Physician** -- Dr. Marcus Rivera, MD, FACEP (26 findings: 4 P0, 7 P1, 9 P2, 6 P3)
2. **Clinical Informaticist** -- Dr. Priya Chakraborty, MD, MS-CI (28 findings across 8 categories)
3. **Cell Therapy Coordinator** -- Karen Liu, BSN, RN, OCN, BMTCN (15 priority recommendations plus workflow gaps)
4. **Regulatory Affairs** -- Thomas Eriksson, MPH, RAC (20+ findings: 5 Critical, 7 Major, 8 Moderate)
5. **Accessibility Consultant** -- Maya Washington, CPACC (38 findings: 8 Critical, 14 Major, 9 Minor, 7 Advisory)
6. **Visual QA Engineer** -- Senior QA (27 findings: 4 Critical, 7 Major, 10 Minor, 6 Cosmetic)

---

## 1. Executive Summary

### Total Findings
Across all 6 reviews, approximately **164 discrete findings** were documented.

### Breakdown by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical / P0** | 24 | Patient safety risks, WCAG Level A failures, data correctness errors, regulatory blockers |
| **High / P1** | 38 | Critical workflow gaps, WCAG AA failures, compliance requirements, major usability barriers |
| **Medium / P2** | 52 | Important clinical improvements, moderate UX issues, interoperability gaps |
| **Low / P3** | 50 | Polish items, nice-to-have features, cosmetic issues, advisory accessibility notes |

### What Iteration 2 Fixed (from Iteration 1 Synthesis)
The following Iteration 1 issues were confirmed resolved by the Iteration 2 reviewers:
- Vital sign alerts added to `generateAlerts()` (SBP <90, HR >120, SpO2 <94%, RR >24) -- confirmed working
- Respiratory rate added to Clinical Visit form
- CRS grade selector changed to exclusive radio behavior with localStorage persistence
- Composite score relabeled as "weighted score, not a probability" with visible disclaimer
- ALT added to NORMAL_RANGES (though range value disputed -- see below)
- Trend visualization (sparklines) added for key labs and vitals across timepoints
- Skipped models now shown as "Not Evaluated" with dashed border cards
- Colorblind-safe icons added via `getRiskIcon()` function (but only in Overview score cards)
- Patient identification added to print output (print header with name, ID, age/sex, timepoint)
- "AI-powered" label removed, clinical disclaimer added to footer
- Checklist state persisted in localStorage
- Keyboard accessibility partially improved (CRS grade boxes have tabindex/role, buttons used in some places)

### Top 3 Themes Across Multiple Reviewers

**Theme 1: Incomplete ARIA Semantics and Color-Only Risk Communication (5 reviewers)**
The accessibility consultant, visual QA, EM physician, informaticist, and coordinator all identified that risk levels are still communicated primarily through color. The `getRiskIcon()` function exists but is only applied in the Overview score cards -- not in the sidebar badges, timeline dots, risk meter, sparkline dots, or alert banners. The ARIA tab pattern, radio group pattern, and live region announcements are all missing or incomplete. This is both an accessibility compliance failure (WCAG 2.1 Level A and AA) and a patient safety issue.

**Theme 2: Clinical Data Gaps Preventing Accurate CRS/ICANS Grading (4 reviewers)**
The EM physician, informaticist, coordinator, and regulatory reviewer all flagged that the dashboard has the vital signs and lab data needed for CRS grading but does not use them to auto-suggest grades, does not display MAP or oxygen requirements, and does not validate manually selected grades against objective data. The ICE score calculator defaults to 10/10 instead of reflecting patient data, and ICANS grading does not incorporate consciousness level or seizure status. These gaps create opportunities for grading errors that directly affect treatment decisions.

**Theme 3: No Persistent Audit Trail, Event Logging, or REMS Reporting Capability (4 reviewers)**
The informaticist, coordinator, regulatory reviewer, and (implicitly) the EM physician all flagged that CRS/ICANS grading events, tocilizumab administrations, steroid doses, and clinical assessments are either not captured at all or stored only in browser localStorage. There is no server-side persistence, no audit trail, no user identity tracking, and no mechanism to generate REMS reports. This is the single largest barrier to clinical deployment.

---

## 2. Cross-Reviewer Agreement Matrix

### Issues Flagged by 4+ Reviewers (Highest Priority)

| Issue | EM Phys | Informaticist | Coordinator | Regulatory | Accessibility | Visual QA |
|-------|:-------:|:------------:|:-----------:|:----------:|:------------:|:---------:|
| Color-only risk communication needs redundant coding everywhere | X | | X | | X | X |
| CRS grade not auto-suggested / not validated against vitals | X | X | | X | | |
| No persistent audit trail or event logging | | X | X | X | | |
| Alert fatigue -- no acknowledgment, grouping, or prioritization | X | X | X | X | | |
| Composite score methodology questionable / creates automation bias | X | X | | X | | |

### Issues Flagged by 3 Reviewers

| Issue | Reviewers |
|-------|-----------|
| ICE score calculator does not reflect patient data / defaults to 10 | EM Phys, Informaticist, Coordinator |
| O2 requirement and vasopressor status not displayed/tracked | EM Phys, Informaticist, Coordinator |
| Print view strips critical information / not structured for handoff | EM Phys, Coordinator, Visual QA |
| ARIA tab pattern missing on task navigation | Accessibility, Visual QA, Informaticist |
| CRS grade radio buttons lack proper ARIA radiogroup | Accessibility, Visual QA, EM Phys |
| ALT normal range inconsistent (33 vs 56 ULN) | EM Phys, Informaticist, Visual QA |
| No REMS reporting data capture | Coordinator, Regulatory, EM Phys |
| Contrast ratio failures in light and dark themes | Accessibility, Visual QA, Coordinator |

### Issues Flagged by 2 Reviewers

| Issue | Reviewers |
|-------|-----------|
| HScore > 169 should generate a dashboard-level alert | EM Phys, Informaticist |
| MAP calculation missing | EM Phys, Informaticist |
| ICANS without CRS not explicitly flagged | EM Phys, Informaticist |
| Teachey model structurally unreachable (missing schema fields) | Informaticist, Regulatory |
| "Not Evaluated" cards do not specify which inputs are missing | Informaticist, Visual QA |
| Patient sidebar risk badge shows last timepoint, not current | Visual QA, Coordinator |
| Hemoglobin not sex-adjusted | EM Phys, Coordinator |
| No loading state during API calls | Visual QA, Coordinator |
| Checklist state not shared across devices (localStorage only) | Coordinator, Informaticist |
| CORS allows all origins | Informaticist, Regulatory |
| Comprehensive disclaimer inadequate | Regulatory, Informaticist |

### Unique Insights Worth Implementing

| Reviewer | Finding |
|----------|---------|
| **EM Physician** | Biphasic CRS recurrence detection -- when CRS grade goes from >0 to 0 and back to >0, generate a specific "biphasic CRS" alert. ~10-15% of cases show this pattern, and it is often more severe on recurrence. |
| **EM Physician** | Temperature velocity (rate-of-rise in degrees/hour) is more clinically meaningful than simple trend direction. A rise of >0.5C/hour should flag as "rapid escalation." |
| **EM Physician** | "critical" risk level in demo data (Case 4, Day 5) falls through to "unknown" blue badge -- the sickest patient renders as blue/informational. |
| **Coordinator** | Timepoint selector hidden below 8 patient cards in sidebar -- the most critical navigation element (switching between Day 1, Day 3, Day 7) requires scrolling past the entire patient list. |
| **Coordinator** | No concept of "time since last assessment" -- the system cannot flag when a q4h nursing check is overdue. |
| **Visual QA** | Multiple scores displaying "0.00" (HScore, CAR-HEMATOTOX, Hay) for Maria Chen -- clinicians may question whether the API is working correctly; even healthy patients typically score some HScore points. |
| **Accessibility** | SVG sparkline charts have no accessible text (no `<title>`, no `role="img"`, no `aria-label`) -- screen reader users get nothing from the trend visualizations. |
| **Regulatory** | Tecartus (brexucabtagene autoleucel) missing from product selector -- all 6 FDA-approved CAR-T products must be selectable. |

---

## 3. Prioritized Task List for Iteration 3 (20 Items)

### T1: Add `role="alert"` / `aria-live` to Safety Alert Containers
- **Priority:** P0 (patient safety)
- **Flagged by:** Accessibility (Finding 3.1, 3.5), Visual QA (implicit), Informaticist (alert management)
- **Effort:** S (<30 min)
- **Description:** The alert banners generated by `generateAlerts()` contain safety-critical information (HIGH RISK, fever, hypotension, HLH warnings) but are injected via `innerHTML` with no ARIA live region attributes. Screen reader users are never notified when critical alerts appear. Add `role="alert"` and `aria-live="assertive"` to the danger alert container. Add `aria-live="polite"` to informational status areas (patient selection confirmation, ICE score results, API connection status).
- **Acceptance criteria:**
  - The container element for danger-level alerts has `role="alert"` or `aria-live="assertive"` present in the DOM before content is injected
  - The ICE score result container (`#iceResult`) has `aria-live="polite"`
  - The API status text (`#apiStatusText`) has `aria-live="polite"`
  - Tested with NVDA or VoiceOver: selecting a HIGH-risk patient causes the screen reader to announce the danger alerts without manual navigation

---

### T2: Display Current ICE Score from Patient Data at Top of ICANS View
- **Priority:** P0 (patient safety)
- **Flagged by:** EM Physician (P0-3), Informaticist (Section 2.2), Coordinator (Section 4)
- **Effort:** M (1-2 hrs)
- **Description:** The ICANS view's ICE score calculator defaults all dropdowns to maximum values, displaying "10/10 Normal" by default. The patient's actual ICE score from `tp.clinical.ice_score` is available but never displayed prominently. A clinician opening this view at night sees a falsely reassuring 10/10. Add a prominent "Current ICE Score" card at the top of the ICANS view that reads `tp.clinical.ice_score` and `tp.clinical.icans_grade`, displays them in large font (32px+) with color coding (green >= 7, yellow 3-6, red 0-2), and shows the delta from the previous timepoint (e.g., "ICE 5/10, down from 8/10"). Relabel the calculator section as "New Assessment" to distinguish it from stored data.
- **Acceptance criteria:**
  - Top of ICANS view shows patient's current ICE score in large font with ICANS grade
  - Color coding matches severity: green (7-10), yellow/orange (3-6), red (0-2)
  - Delta from prior timepoint displayed when available (e.g., "down from 8")
  - Calculator section header reads "New ICE Assessment" (not just "ICE Score Calculator")
  - Dropdown defaults remain at maximum values (appropriate for a fresh assessment) but the section is visually separated from the stored score

---

### T3: Add ICANS-Without-CRS Alert
- **Priority:** P0 (patient safety)
- **Flagged by:** EM Physician (P0-4), Informaticist (Section 2.2)
- **Effort:** S (<30 min)
- **Description:** When ICANS is present without active CRS (`icans_grade > 0 && crs_grade === 0`), the treatment approach differs fundamentally: dexamethasone is first-line, not tocilizumab (which has poor CNS penetration). The dashboard has no alert for this specific condition. Demo Case 5 (Sarah Thompson) demonstrates this exact scenario. Add a conditional alert in `generateAlerts()` that fires when `icans_grade > 0` and `crs_grade === 0`, with text: "ICANS detected WITHOUT active CRS. Dexamethasone is first-line for isolated ICANS. Tocilizumab has limited CNS penetration and is NOT recommended as initial therapy for isolated ICANS."
- **Acceptance criteria:**
  - Alert fires on any timepoint where `icans_grade > 0` and `crs_grade === 0`
  - Alert renders as `danger` level with explicit treatment guidance text
  - Alert does NOT fire when both CRS and ICANS are present simultaneously
  - Verified against Demo Case 5 (Sarah Thompson) Day 8 and Day 10 timepoints

---

### T4: Calculate and Display MAP; Add MAP-Based Alert
- **Priority:** P0 (patient safety)
- **Flagged by:** EM Physician (P0-2), Informaticist (implicit in CRS grading)
- **Effort:** M (1-2 hrs)
- **Description:** Mean Arterial Pressure (MAP) is the standard ICU hemodynamic metric and is more reliable than SBP alone for detecting CRS-related vasodilation. MAP is trivially calculated as `(SBP + 2*DBP) / 3`. Currently, a patient with BP 92/48 (MAP = 63, below the critical 65 threshold) generates no alert because SBP > 90. Add MAP calculation to the vital signs display in the Overview and CRS views. Add MAP < 65 as a danger alert. Optionally add Shock Index (HR/SBP) with warning at SI > 0.9 and danger at SI > 1.2.
- **Acceptance criteria:**
  - MAP displayed next to BP in the Overview vital signs section and CRS Monitor view
  - MAP calculated as `(systolic + 2 * diastolic) / 3`, rounded to one decimal
  - Alert generated when MAP < 65 (danger level)
  - A patient with BP 92/48 now generates a "MAP 63 -- below critical threshold of 65" danger alert
  - Shock Index displayed as an optional derived metric (HR/SBP) if time permits

---

### T5: Handle "critical" Risk Level in UI
- **Priority:** P0 (patient safety)
- **Flagged by:** EM Physician (P2-9), Visual QA (Finding 37 related)
- **Effort:** S (<30 min)
- **Description:** Demo Case 4 (Robert Kim, Day 5) has `expected_risk: "critical"` which is not handled by the `riskClass()` function (lines 607-614). It falls through to `risk-unknown`, rendering as a blue/info badge -- the most critically ill patient in the case series displays as blue "UNKNOWN." Add a `"critical"` case to `riskClass()` that maps to the most visually alarming styling (pulsing red border, bold uppercase text, distinct from "high"). If a separate critical tier is not desired, map "critical" to "high" instead of "unknown."
- **Acceptance criteria:**
  - `riskClass("critical")` returns a CSS class that renders as visually alarming (at minimum, the same as "high" risk; ideally, more prominent with pulsing animation)
  - Robert Kim (DEMO-004) Day 5 no longer shows a blue "UNKNOWN" badge
  - The risk badge text reads "CRITICAL" or "HIGH" (not "UNKNOWN")
  - Verified across all 8 demo cases that no risk levels fall through to unknown

---

### T6: Extend Risk Icons to All Risk Indicator Locations
- **Priority:** P1 (WCAG 2.1 AA -- 1.4.1 Use of Color)
- **Flagged by:** Accessibility (Finding 1.1, 1.4), Visual QA (Finding 36), Coordinator (Section 8), EM Physician (P3-5)
- **Effort:** M (1-2 hrs)
- **Description:** The `getRiskIcon()` function produces appropriate icons (checkmark for LOW, triangle for MODERATE, warning sign for HIGH) but is only used in the Overview score cards. Risk is still communicated by color alone in: sidebar patient badges, timeline dots, risk meter gradient bar, sparkline dots, alert banners, CRS grade boxes, lab value cells (cell-high/cell-low). Extend the icon system (or add text labels) to every location where color is the sole risk/status differentiator. For the risk meter, add labeled tick marks or text overlay ("Low | Moderate | High" regions). For sparkline abnormal dots, use diamond shapes instead of circles. For the Overview lab table, add "H"/"L" text flags matching the Pre-Infusion view's approach.
- **Acceptance criteria:**
  - Sidebar risk badges include an icon or shape alongside the color (not color alone)
  - Timeline dots have a shape or text label distinguishing risk levels
  - Risk meter gradient bar has text region labels ("Low", "Moderate", "High")
  - Sparkline abnormal values use a distinct shape (diamond or triangle), not just red color
  - Overview lab table cells with abnormal values include "H" or "L" text indicator
  - All changes tested with a grayscale filter to verify information is conveyed without color

---

### T7: Fix Contrast Ratios for Risk Badges and Alert Text
- **Priority:** P1 (WCAG 2.1 AA -- 1.4.3 Contrast Minimum)
- **Flagged by:** Accessibility (Finding 1.2, 1.3), Visual QA (implicit), Coordinator (Section 8)
- **Effort:** S (<30 min)
- **Description:** Multiple color pairings fail the 4.5:1 contrast ratio requirement. Specifically: success badge text (`#059669` on `#d1fae5` = ~3.1:1), warning text (`#d97706` on `#fef3c7` = ~3.0:1), moderate badge (`#ea580c` on `#ffedd5` = ~3.2:1), danger badge (`#dc2626` on `#fee2e2` = ~3.5:1). In dark theme, danger text (`#dc2626` on `#2a1010` = ~3.4:1) and success text (`#059669` on `#081f15` = ~3.9:1) also fail. Fix by darkening foreground colors in light theme (e.g., success `#047857`, danger `#b91c1c`, warning `#b45309`) and using lighter tints in dark theme (e.g., danger `#f87171`, success `#34d399`).
- **Acceptance criteria:**
  - All text-on-background color pairings for risk badges, alert banners, and status indicators achieve 4.5:1 contrast ratio minimum
  - Verified in both light and dark themes
  - No visual regression -- risk badges remain visually distinct and recognizable
  - Tested with a contrast ratio calculator (e.g., WebAIM) for the specific hex values used

---

### T8: Implement WAI-ARIA Tab Pattern on Task Navigation
- **Priority:** P1 (WCAG 2.1 AA -- 4.1.2 Name, Role, Value)
- **Flagged by:** Accessibility (Finding 2.2), Visual QA (Finding 34 related), Informaticist (implicit)
- **Effort:** M (1-2 hrs)
- **Description:** The 9-tab task navigation uses `<button>` elements inside a `<nav>` but lacks the WAI-ARIA Tabs pattern. Add `role="tablist"` on the container, `role="tab"` with `aria-selected` on each button, `role="tabpanel"` with `aria-labelledby` on each content area. Implement Left/Right arrow key navigation between tabs with roving `tabindex` (active tab has `tabindex="0"`, others have `tabindex="-1"`). Add `aria-label="Task workflow"` to the `<nav>` element.
- **Acceptance criteria:**
  - `<nav>` has `aria-label="Task workflow"`
  - Tab container has `role="tablist"`
  - Each tab button has `role="tab"` and `aria-selected="true"/"false"`
  - Active tab has `tabindex="0"`, inactive tabs have `tabindex="-1"`
  - Left/Right arrow keys move focus between tabs and activate them
  - Content areas have `role="tabpanel"` and `aria-labelledby` referencing their tab
  - Tested with NVDA or VoiceOver: announces "tab 3 of 9, CRS Monitor, selected"

---

### T9: Make Patient Cards Keyboard-Accessible
- **Priority:** P1 (WCAG 2.1 A -- 2.1.1 Keyboard)
- **Flagged by:** Accessibility (Finding 2.1), Visual QA (implicit)
- **Effort:** S (<30 min)
- **Description:** Patient cards are `<div>` elements with `onclick` handlers. They have no `tabindex`, no `role`, no keyboard activation. A clinician using keyboard navigation cannot select a patient. Convert patient card container to use `role="listbox"` with each card as `role="option"` and `aria-selected` for the active patient. Add `tabindex="0"` and a `keydown` handler that activates on Enter and Space. Add `aria-label` to each card summarizing the patient (e.g., "Maria Chen, 62F, Low risk").
- **Acceptance criteria:**
  - Patient list container has `role="listbox"` and `aria-label="Demo Patients"`
  - Each patient card has `role="option"`, `tabindex="0"`, and `aria-selected`
  - Pressing Enter or Space on a focused patient card selects that patient
  - Arrow Up/Down navigation between patient cards is supported
  - Each card has an `aria-label` with patient name and risk level
  - A visible focus indicator appears on the focused patient card

---

### T10: Add HScore >= 169 Alert
- **Priority:** P1 (critical clinical workflow)
- **Flagged by:** EM Physician (P1-4), Informaticist (Section 2.3, 2.4)
- **Effort:** S (<30 min)
- **Description:** HScore > 169 has > 93% probability of HLH (Fardet 2014), but the dashboard only alerts on ferritin > 10,000 and fibrinogen < 1.5 individually. HScore can exceed 169 even when these individual thresholds are not met. The computed HScore is available in `pred.individual_scores` but is never used to generate a dashboard-level alert. Add an alert in `generateAlerts()` that checks the HScore from the prediction result. If HScore >= 169, fire a danger alert: "HScore [score] exceeds 169 (>93% HLH probability). Evaluate for IEC-HS. Consider pulse methylprednisolone and hematology consultation."
- **Acceptance criteria:**
  - Alert fires when computed HScore >= 169 (from `pred.individual_scores`)
  - Alert is danger level with specific actionable text
  - Alert fires independently of ferritin and fibrinogen individual alerts
  - Verified against Demo Case 4 (Robert Kim) Day 5 where HScore should be elevated

---

### T11: Fix ALT Normal Range Inconsistency
- **Priority:** P1 (data correctness)
- **Flagged by:** EM Physician (P1-7), Informaticist (implicit), Visual QA (Finding 16)
- **Effort:** S (<30 min)
- **Description:** `NORMAL_RANGES.alt` uses `high: 33` but `demo_cases.js` header states ALT normal is 7-56 U/L. The 5x ULN alert fires at > 165 (5 x 33), but if ULN should be 40-56, the alert threshold is wrong. This creates false-positive ALT flagging in the lab table (any ALT 34-56 shown as abnormal when it is normal) and a potentially incorrect hepatotoxicity alert threshold. Standardize ALT ULN to 40 U/L (common consensus for CAR-T monitoring) and update the 5x ULN alert to > 200. Update the `demo_cases.js` header comment to match.
- **Acceptance criteria:**
  - `NORMAL_RANGES.alt.high` changed to 40 (or clinically appropriate value, consistently applied)
  - The ALT > 5x ULN alert threshold updated to match (5 x new ULN)
  - `demo_cases.js` header reference range comment matches the code
  - James Williams (DEMO-002) baseline ALT 45 no longer flagged as abnormal in the lab table

---

### T12: Add Visible Focus Indicators to All Interactive Elements
- **Priority:** P1 (WCAG 2.1 AA -- 2.4.7 Focus Visible)
- **Flagged by:** Accessibility (Finding 2.3)
- **Effort:** S (<30 min)
- **Description:** Many interactive elements lack visible focus indicators: `.task-btn`, `.timeline-btn`, `.theme-toggle`, `.btn`, `.crs-grade-box`, `.tab-btn`. Some may have `outline: none` without a replacement. Add a universal focus-visible rule: `*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`. Ensure this does not create visual clutter on mouse clicks (use `:focus-visible` not `:focus` so it only applies for keyboard navigation).
- **Acceptance criteria:**
  - All interactive elements show a visible 2px outline when focused via keyboard
  - Focus indicator has sufficient contrast (3:1 minimum against adjacent colors per WCAG 2.4.11)
  - Focus indicator does NOT appear on mouse click (uses `:focus-visible`)
  - Tested by tabbing through the entire page: every clickable element is visually identifiable when focused

---

### T13: Add CRS Grade-to-Management Protocol Linking
- **Priority:** P1 (critical workflow)
- **Flagged by:** EM Physician (P1-2), Informaticist (Section 2.1)
- **Effort:** S (<30 min)
- **Description:** The CRS grade selector function `selectCRSGrade()` queries for `[data-crs-mgmt]` elements to highlight the matching management protocol, but the management algorithm blocks do not have `data-crs-mgmt` attributes. Clicking a CRS grade box selects the grade visually but does not scroll to or highlight the corresponding treatment protocol. Add `data-crs-mgmt="1"`, `data-crs-mgmt="2"`, etc. to each management protocol section. When a grade is selected, add a highlight class to the matching protocol and optionally scroll it into view.
- **Acceptance criteria:**
  - Each CRS management protocol block has a `data-crs-mgmt` attribute matching its grade
  - Clicking "Grade 2" on the grade strip highlights the Grade 2 management protocol
  - Previously highlighted protocol un-highlights when a different grade is selected
  - The matching protocol scrolls into view if it is below the fold

---

### T14: Add Skip Navigation Link
- **Priority:** P1 (WCAG 2.1 A -- 2.4.1 Bypass Blocks)
- **Flagged by:** Accessibility (Finding 8.3)
- **Effort:** S (<30 min)
- **Description:** There is no "Skip to main content" link. Keyboard users must tab through the header, 9-tab navigation bar, and sidebar before reaching the main content area. Add a visually hidden skip link as the first focusable element in the DOM: `<a href="#contentArea" class="skip-link">Skip to main content</a>`. Style it to be visible only when focused.
- **Acceptance criteria:**
  - First focusable element on the page is a skip link
  - Skip link is visually hidden by default but becomes visible on keyboard focus
  - Activating the skip link moves focus to the main content area (`#contentArea` or equivalent)
  - Verified by pressing Tab once after page load: skip link appears

---

### T15: Specify Missing Inputs on "Not Evaluated" Score Cards
- **Priority:** P1 (critical workflow)
- **Flagged by:** Informaticist (Section 4.1), Visual QA (Finding 13), EM Physician (implicit)
- **Effort:** M (1-2 hrs)
- **Description:** When a model is skipped due to missing inputs, the card shows "Not Evaluated" and "Missing required inputs" but does not say WHICH inputs are missing. A clinician cannot determine which lab to order to enable the model. The `models_skipped` list from the API `LayerDetail` gives model names but not the specific missing fields. Either (a) have the backend return the list of missing fields per skipped model and render them on the card (e.g., "Requires: IFN-gamma, sgp130, IL-1RA"), or (b) hardcode the required inputs per model in the frontend and display them. Also replace "Not Evaluated" with more specific language: "Cannot compute -- missing data" with an action-oriented prompt.
- **Acceptance criteria:**
  - Each "Not Evaluated" score card lists the specific missing inputs by name
  - Card text reads "Cannot compute" with a sub-line listing missing fields (e.g., "Missing: IFN-gamma, sgp130")
  - The card uses a distinct visual treatment (gray background, question mark icon) beyond just reduced opacity
  - Verified with Demo Case 1 (Maria Chen) where Teachey model should show its specific missing inputs

---

### T16: Add Comprehensive FDA/CDS Disclaimer
- **Priority:** P1 (regulatory compliance)
- **Flagged by:** Regulatory (DIS-01, DIS-02), Informaticist (Section 6.2)
- **Effort:** S (<30 min)
- **Description:** The current disclaimer ("For clinical decision support only -- not a substitute for clinical judgment") is inadequate. It does not state that the software is not FDA-cleared, not intended to diagnose or treat disease, and has not been validated in a clinical trial. Add a prominent disclaimer banner that appears on page load and is accessible from a persistent footer link. The disclaimer must include: (1) Not an FDA-cleared or approved medical device, (2) Not intended to diagnose, treat, cure, or prevent any disease, (3) All clinical decisions must be made by qualified healthcare providers, (4) Scoring algorithms are deterministic calculations from published formulas, (5) The composite risk score is NOT a validated clinical prediction, (6) Software version and algorithm versions.
- **Acceptance criteria:**
  - A prominent disclaimer is visible at the top of the page or in a modal on first load
  - The disclaimer includes "NOT an FDA-cleared or approved medical device" language
  - The disclaimer includes the software version number
  - A persistent footer link opens the full disclaimer text
  - The disclaimer is included in print output
  - The API `/api/v1/predict` response includes a `disclaimer` field in the JSON

---

### T17: Fix Sidebar Risk Badge to Reflect Current Timepoint
- **Priority:** P1 (data correctness)
- **Flagged by:** Visual QA (Finding 37), Coordinator (implicit)
- **Effort:** S (<30 min)
- **Description:** The patient card in the sidebar always displays the risk level from the LAST timepoint (`p.timepoints[p.timepoints.length-1].expected_risk`), not the currently selected timepoint. For James Williams, who escalates from LOW to HIGH and back, the sidebar always shows his recovery-phase risk regardless of which timepoint is being viewed. This is misleading and could cause a clinician to overlook a high-risk timepoint. Change the sidebar rendering to either (a) show the risk for the currently selected timepoint (re-render sidebar on timepoint change), or (b) show the WORST risk across all timepoints with a "peak" indicator.
- **Acceptance criteria:**
  - Sidebar risk badge updates when a different timepoint is selected for the active patient
  - For James Williams (DEMO-002), selecting Day 3 shows "HIGH" risk in the sidebar (not the Day 7 recovery level)
  - Alternatively, if showing worst-ever risk, the badge is labeled "Peak: HIGH" to avoid confusion
  - All 8 demo patients verified: badge reflects the displayed timepoint's risk

---

### T18: Add Tecartus to Product Selector
- **Priority:** P1 (regulatory completeness)
- **Flagged by:** Regulatory (REG-01)
- **Effort:** S (<30 min)
- **Description:** The Clinical Visit product selector lists 5 of the 6 FDA-approved CAR-T products but is missing Tecartus (brexucabtagene autoleucel), approved for relapsed/refractory MCL and ALL. Add Tecartus to the product dropdown with its generic name and manufacturer (Kite/Gilead). Ensure it is selectable and submitted with the form data.
- **Acceptance criteria:**
  - "Tecartus (brexucabtagene autoleucel)" appears as an option in the product selector dropdown
  - It is selectable and included in form submission data
  - The product list now contains all 6 FDA-approved CAR-T products

---

### T19: Add Print-Safe Risk Indicators and Structured Print Layout
- **Priority:** P2 (important usability)
- **Flagged by:** Accessibility (Finding 7.2), Visual QA (Finding 32, 33), EM Physician (P1-6), Coordinator (Section 2)
- **Effort:** M (1-2 hrs)
- **Description:** The print view has two categories of issues. First, colored risk indicators will be indistinguishable on black-and-white printers (common in clinical settings). Add print-specific CSS that prepends text labels to risk badges (e.g., `[HIGH]`, `[LOW]`) and sets all risk indicators to black text on white background with borders. Second, the score card grid may reflow unpredictably on paper. Add `@media print` rules that set the score grid to 3 columns, expand the print header to include diagnosis, product, day post-infusion, current CRS/ICANS grade, and all current vital signs. Add a footer with the disclaimer text and "Printed by [if available] at [timestamp]."
- **Acceptance criteria:**
  - Risk badges print with text labels `[HIGH]`, `[MODERATE]`, `[LOW]` in black text
  - Score card grid prints as 3 columns consistently on A4/Letter paper
  - Print header includes: patient name, ID, age/sex, diagnosis, CAR-T product, day post-infusion, current CRS grade, ICANS grade
  - Footer includes disclaimer and print timestamp
  - Verified by Print Preview in Chrome: all risk information legible in grayscale

---

### T20: Add Oxygen Requirement Display to CRS View
- **Priority:** P2 (important clinical context)
- **Flagged by:** EM Physician (P1-3), Informaticist (Section 2.1), Coordinator (Section 5)
- **Effort:** M (1-2 hrs)
- **Description:** The demo case data contains `oxygen_requirement` strings (e.g., "Room air", "4L nasal cannula", "High-flow nasal cannula 40L/min 60% FiO2") but this information is never rendered in the dashboard. Oxygen requirement is a core criterion for ASTCT CRS grading (Grade 2: low-flow, Grade 3: high-flow, Grade 4: positive pressure). Display the current oxygen requirement prominently in the CRS Monitor view and the Overview vital signs section, alongside temperature and blood pressure. Use the existing demo data field `tp.clinical.oxygen_requirement`.
- **Acceptance criteria:**
  - Oxygen requirement displayed in the CRS Monitor view next to vital signs
  - Oxygen requirement displayed in the Overview vital signs section
  - The value is pulled from `tp.clinical.oxygen_requirement` when available
  - "Room air" displays in green/normal styling; any supplemental O2 displays in warning styling
  - Verified with Demo Case 2 (James Williams) Day 3 showing "High-flow nasal cannula" prominently

---

## 4. Deferred Items

### Out of Scope for Iteration 3 (Important but Requires Separate Work Stream)

| Item | Source | Reason for Deferral |
|------|--------|-------------------|
| **Persistent audit trail / server-side logging** | Informaticist, Regulatory, Coordinator | Requires backend database architecture, not a frontend iteration task. This is the highest-priority backend work for any clinical deployment path. |
| **User authentication and RBAC** | Informaticist, Regulatory | Requires backend auth infrastructure (OAuth/SAML), session management, and role definitions. Cannot be done in a frontend-only iteration. |
| **CORS restriction to specific origins** | Informaticist, Regulatory | Requires deployment configuration change, not a dashboard code change. Should be addressed when deploying to any non-localhost environment. |
| **REMS reporting module with data export** | Coordinator, Regulatory | Requires new backend endpoints, data persistence, and report generation. Best addressed as a dedicated feature after audit trail is in place. |
| **FHIR R4 / LOINC terminology mapping** | Informaticist | Requires backend API schema changes and a mapping layer. Important for EHR integration but not needed for standalone dashboard use. |
| **Teachey model schema fields (sgp130, il1ra)** | Informaticist, Regulatory | Requires `schemas.py` changes in the backend. The model is structurally unreachable until the Pydantic schema is updated. For now, the "Not Evaluated" card with missing inputs (T15) is the appropriate frontend-side fix. |
| **Server-side checklist persistence** | Coordinator, Informaticist | Requires backend API endpoints for checklist state CRUD operations. localStorage is adequate for single-user demo; multi-user requires server persistence. |
| **HIPAA-compliant data architecture (encryption, access controls)** | Regulatory | Requires infrastructure-level changes (HTTPS enforcement, encrypted storage, audit logging). Not a frontend task. |
| **Multi-patient overview / worklist view** | Coordinator | Large feature (L+) requiring new page layout, sort/filter logic, and a fundamentally different information architecture. Best addressed as a separate iteration or module. |
| **Shift handoff report generator** | Coordinator, EM Physician | Requires new rendering logic, data aggregation across patients, and export capability. Important feature but too large for this iteration's scope. |
| **CRS/ICANS event log with timestamps** | Coordinator, Regulatory | Requires a new data model for event capture (timestamp, user, grade change, intervention). Depends on server-side persistence. |
| **Tocilizumab / steroid dose tracking** | EM Physician, Coordinator | Requires medication administration data model, tracking logic, and dose-counting business rules. Depends on backend persistence. |

### Aspirational / Nice-to-Have

| Item | Source |
|------|--------|
| Biphasic CRS recurrence detection algorithm | EM Physician |
| Temperature velocity (rate-of-rise in degrees/hour) | EM Physician |
| Seizure risk assessment card in ICANS view | EM Physician |
| Product-specific CRS timing expectations display | EM Physician, Coordinator |
| Role-based views (physician / nurse / pharmacist) | Informaticist |
| "Quick Status" single-pane nursing view | Informaticist |
| Auto-calculate ICE score on dropdown change (remove Calculate button) | Accessibility |
| Keyboard shortcuts for tab switching (1-9 keys) | Accessibility |
| Abbreviation glossary with `<abbr>` tags | Accessibility |
| Heading hierarchy (`<h1>`-`<h6>` semantic structure) | Accessibility |
| SVG sparkline accessible text (`role="img"`, `aria-label`) | Accessibility |
| Favicon | Visual QA |
| Loading skeleton/shimmer during API calls | Visual QA |
| Sidebar scroll indicator (fade gradient) | Visual QA, Coordinator |
| Day 28 / Day 100 milestone assessment workflows | Coordinator |
| Mobile-optimized view for rounding | Coordinator |
| Formal risk management file per ISO 14971 | Regulatory |
| Intended Use / Indications for Use statement | Regulatory |

---

## 5. Key Insights

### Surprising Findings

1. **The "critical" risk level rendering as blue "UNKNOWN" was missed in Iteration 1 reviews.** This is a data-display bug that makes the sickest demo patient (Robert Kim, Day 5 -- active IEC-HS) appear as informational/unknown. It was caught by the EM physician who would interact with exactly this kind of patient, not by the QA engineer working from screenshots of less severe cases. This underscores the value of specialty-specific clinical reviewers.

2. **The ICE calculator defaulting to 10/10 is more dangerous than a blank state.** Three reviewers flagged this, but the EM physician's framing was most compelling: at 2am, a covering resident who opens the ICANS tab and sees "10/10 Normal" may be falsely reassured and move on. A blank or "No assessment recorded" state would be safer than a falsely normal default.

3. **Alert fatigue is now a risk precisely because Iteration 1 added vital sign alerts.** The informaticist calculated that a severely ill patient can trigger 8-9 simultaneous alerts. The Iteration 1 fix (adding vital sign alerts) was correct, but without the corresponding alert grouping, acknowledgment, and prioritization infrastructure, the system may now over-alert. This is a classic safety system paradox: more alerts does not equal more safety.

4. **The ALT normal range inconsistency was flagged by 3 reviewers independently**, each approaching it from a different angle (EM physician: clinical accuracy, informaticist: standards compliance, visual QA: visual display correctness). This kind of cross-reviewer convergence on a specific data value is a strong signal that it needs fixing.

### What Is Working Well (Consistent Across Reviewers)

1. **Clinical domain knowledge is excellent.** Every reviewer, including the regulatory specialist, praised the quality of the clinical content, scoring model selections, ASTCT grading implementation, and management algorithms. The EM physician rated the demo cases as "clinically realistic" with accurate lab trajectories. The coordinator gave clinical accuracy a 9/10.

2. **The teaching points system is praised by all clinical reviewers.** The EM physician called it "outstanding," the coordinator found the clinical notes "excellent narrative summaries," and the informaticist noted the demo cases "could serve as an excellent educational tool independent of the scoring platform."

3. **The sparkline trend visualization (added in Iteration 2) is a success.** It was the single highest-impact feature request in Iteration 1, and all Iteration 2 reviewers who commented on it found it well-implemented. The EM physician praised the color coding of abnormal values and normal range bands. The visual QA confirmed correct rendering.

4. **The layered ensemble architecture degrades gracefully.** The informaticist specifically praised partial scoring with confidence adjustment. The regulatory reviewer confirmed that the max-risk aggregation strategy is conservative and appropriate for safety.

5. **Iteration 2 resolved the majority of Iteration 1 critical findings.** Of the 7 critical issues from Iteration 1 (C1-C7), all appear to have been addressed: vital sign alerts added, CAR-HEMATOTOX scoring corrected, composite score relabeled, CRS grade selector fixed, demo case errors corrected, "AI-powered" label removed. This validates the iterative review process.

### Strategic Recommendations for Future Development

1. **Prioritize backend infrastructure over frontend features.** The audit trail, data persistence, and user authentication gaps identified by the informaticist and regulatory reviewer are the gatekeepers for any clinical deployment. No amount of frontend polish will compensate for in-memory data stores and absent audit logging. The next major development investment should be a database-backed persistence layer.

2. **Engage FDA regulatory counsel before significant further development.** The regulatory reviewer's analysis of SaMD classification risk is serious. The composite score and management recommendations may place this tool under FDA jurisdiction. The regulatory strategy determination (pursue clearance vs. restructure for CDS exemption) will fundamentally shape what features can be built and how they must be documented.

3. **Consider splitting the platform into two products.** The coordinator's feedback reveals a fundamental tension: the dashboard is designed as a single-patient deep-dive tool, but coordinators need a multi-patient operational cockpit. These are different products with different information architectures. The current single-patient view is excellent for physician decision-making; the multi-patient worklist would be a separate development effort.

4. **Accessibility remediation should be treated as a parallel work stream, not an afterthought.** The accessibility audit identified 38 findings, with 8 at critical severity. Many of these (ARIA attributes, focus indicators, live regions) are quick fixes that should be addressed alongside feature development, not deferred to a "polish" phase.

---

*Synthesis completed 2026-02-07. This document consolidates 6 independent professional reviews (~164 total findings) into a prioritized 20-task plan for Iteration 3 development. Tasks are ordered by patient safety impact, cross-reviewer agreement, and implementation effort.*
