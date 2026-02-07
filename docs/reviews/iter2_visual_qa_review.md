# Iteration 2 - Visual QA Review

**Reviewer:** Senior QA Engineer (Visual & UX)
**Date:** 2026-02-07
**Build:** Iteration 2 - Full clinical dashboard with 8 demo patients, 9 task tabs, 7 scoring models
**Screenshots reviewed:** `dashboard-iter2-clean.png` (Overview tab, Maria Chen, LOW risk), `dashboard-iter2.png` (with Chrome dialog overlay)
**Source file:** `src/api/static/index.html` (2154 lines), `src/api/static/demo_cases.js` (2427 lines)

---

## Executive Summary

The Iteration 2 dashboard is a significant advancement over the Iteration 1 prototype. The layout is professional, the information density is appropriate for clinical use, and the dark/light theme system is well-implemented. The 7-model scoring card grid, lab values table, trend sparklines, and anticipated tests panel all render correctly in the clean screenshot.

However, the review identified **4 Critical**, **7 Major**, **10 Minor**, and **6 Cosmetic** issues requiring attention before clinical pilot deployment.

---

## 1. Visual Hierarchy

### FINDING-01: Risk level badge placement is good but composite risk text is undersized
- **Severity:** Major
- **Location:** Composite Risk Assessment card, center text area
- **Observation:** The composite risk level ("LOW") is displayed at `font-size: 24px` in the center of the card (line 962). While the green "LOW" badge in the card header at the top-right is immediately visible, the central text competes with the model agreement summary on the same line. The most critical information -- the overall risk level -- should dominate the visual space.
- **Suggestion:** Increase the central composite label to 32-36px and give it its own line separate from the model agreement count. Consider adding a background tint to the entire card that reflects risk level (e.g., faint green for LOW, faint red for HIGH).

### FINDING-02: Score card grid renders 7th card ("Teachey Cytokine 3var") as "Not Evaluated" with reduced opacity
- **Severity:** Minor
- **Observation:** In the screenshot, the 7th score card is visually distinct (dashed border, 50% opacity, smaller "Not Evaluated" text at `font-size: 16px` per line 986). This is correctly differentiated from the 6 evaluated models. However, the card is partially cut off at the right edge of the viewport, requiring horizontal awareness.
- **Suggestion:** The `minmax(200px, 1fr)` grid sizing (line 213) works well for 6 cards but creates a partial 7th card. Consider either: (a) reducing `minmax` to `180px` to fit all 7, or (b) wrapping the 7th card onto a second row explicitly. On a 1920px display minus 320px sidebar, the available content area is ~1576px. Seven cards at 200px minimum need ~1400px + gaps, which should fit but is tight.

## 2. Layout Issues

### FINDING-03: Risk meter indicator bar has a positioning issue at low risk values
- **Severity:** Major
- **Location:** `.risk-meter-indicator` (line 326-330), rendered at line 955
- **Observation:** The risk meter indicator position is calculated as `left: ${Math.min(pred.composite_score * 100, 98)}%`. For the LOW risk patient (composite score 7.5), this places the indicator at 7.5% from the left -- visible in the screenshot as a thin dark bar near the left edge of the gradient bar. At this position, the 4px-wide indicator is very small and easy to miss against the green gradient background.
- **Suggestion:** Consider making the indicator wider (8-10px) or adding a contrasting marker (white triangle/diamond above the bar) for better visibility at all positions. Also consider adding a numeric label above/below the indicator.

### FINDING-04: Lab values table and Anticipated Tests panel use a 1fr 1fr grid that may not allocate space well
- **Severity:** Minor
- **Location:** Line 992: `grid-template-columns: 1fr 1fr`
- **Observation:** In the screenshot, the Lab Values table takes up roughly 60% of useful visual content (11 rows of data) while the Anticipated Tests panel is shorter (6 items). The equal 1fr/1fr split means the Anticipated Tests panel has significant empty whitespace below its content. This is not broken but is visually unbalanced.
- **Suggestion:** Either let the cards size independently with `align-items: start` on the grid container, or use a responsive approach where Anticipated Tests appears below Labs on narrower viewports.

### FINDING-05: Patient sidebar scrolling -- no visual scroll indicator
- **Severity:** Minor
- **Location:** `.patient-sidebar` (line 136-141)
- **Observation:** The sidebar has `overflow-y: auto` and `max-height: calc(100vh - 100px)`. With 8 demo patients, at least 2 patients (Linda Park, Michael Santos) are partially or fully below the fold. Michael Santos is barely visible at the bottom. There is no scroll indicator, shadow, or fade-to-transparent effect to signal more content exists below.
- **Suggestion:** Add a bottom fade gradient or subtle shadow to indicate scrollable content, e.g., a pseudo-element with `linear-gradient(transparent, var(--surface))`.

### FINDING-06: Content area also has max-height scrolling constraint
- **Severity:** Major
- **Location:** `.content-area` (line 168-172)
- **Observation:** `max-height: calc(100vh - 100px)` means the content area scrolls independently from the page. This creates a dual-scroll situation where both the sidebar and content area are individually scrollable. The Lab & Vital Trends section at the bottom of the Overview is partially cut off in the screenshot -- the sparkline charts for CRP, Ferritin, LDH, and ANC are only partially visible. Users may not realize there is more content below.
- **Suggestion:** Consider whether dual independent scrolling is the right UX pattern. For clinical use, a single-scroll page might be more intuitive. Alternatively, add a clear "scroll for more" indicator or make the content area taller.

## 3. Typography

### FINDING-07: Citation text in score cards is extremely small
- **Severity:** Major
- **Location:** `.score-citation` at `font-size: 10px` (line 227), rendered at line 979
- **Observation:** In the screenshot, the citation text below each score card (e.g., "Pennisi et al. Blood Adv 2021;5(17):3481-3489; Korell et al. J Cancer Res Clin Oncol 2022") is at 10px with italic styling. On a standard clinical workstation monitor at 1920x1080, this text is nearly illegible. Some citations are also being truncated within the card width.
- **Suggestion:** Increase to 11px minimum. Consider showing citations on hover/expand rather than always visible, to reduce visual clutter while keeping them accessible.

### FINDING-08: Monospace font for score values renders well
- **Severity:** N/A (Positive observation)
- **Location:** `.score-value` at `font-size: 28px; font-family: var(--mono)` (line 225)
- **Observation:** The JetBrains Mono font renders score values crisply. The checkmark icon + numeric score pattern (e.g., "checkmark 1.21") is immediately readable. Good choice.

### FINDING-09: Patient card metadata text truncation with ellipsis
- **Severity:** Minor
- **Location:** `.pc-meta` (line 157), rendered at line 662
- **Observation:** The patient diagnosis is truncated with `substring(0, 40)` followed by "..." in JavaScript (line 662). This hard truncation means some patients show oddly cut text like "DLBCL (ABC/non-GCB subtype), double-hit..." vs "Relapsed/refractory multiple myeloma, Ig...". The truncation point is not word-boundary-aware.
- **Suggestion:** Use CSS `text-overflow: ellipsis` with `overflow: hidden; white-space: nowrap` instead of JavaScript substring, OR increase the character limit to 50+ to capture the full diagnosis type before truncating.

## 4. Color System

### FINDING-10: Color palette is consistent and well-applied
- **Severity:** N/A (Positive observation)
- **Observation:** The CSS variable system (lines 8-61) defines a coherent palette with appropriate semantic colors. Risk-level colors (green/success for LOW, orange/moderate, red/danger for HIGH) are applied consistently across score cards, risk badges, patient list badges, and alert banners. The `risk-low-border` class (line 228) correctly applies a left-border accent on score cards.

### FINDING-11: Hemoglobin row in Lab Values table is highlighted as abnormal (yellow/orange text) but should not be
- **Severity:** Critical
- **Location:** Lab values table, `labValueDisplay()` function (line 639-648), `NORMAL_RANGES.hemoglobin` (line 533)
- **Observation:** In the screenshot, "Hemoglobin" shows value "12.1" with highlighted/colored text (yellow-orange, `cell-low` class). The normal range defined is `low: 12.0, high: 17.5` (line 533). Since 12.1 > 12.0, this should display as normal, not abnormal. However, Maria Chen is a 62-year-old female, and the value 12.1 is within the female normal range (12-16 g/dL per the demo_cases.js header comment). The issue is that the screenshot clearly shows the value in a highlighted/warning color, suggesting the comparison logic may have a floating-point edge case or the range boundaries are not being compared with `>=` correctly.
- **INVESTIGATION:** Looking at line 644: `if (value > r.high) cls = 'cell-high'; else if (value < r.low) cls = 'cell-low';`. Since 12.1 is NOT < 12.0, this should render without highlighting. The screenshot shows it in a different color, which might be the amber/orange `cell-low` class. **Re-examining the screenshot more carefully**: the "12.1" text appears in a green/teal color, not orange -- this actually might be the default `var(--text)` or could be a rendering artifact. Needs verification in browser.
- **Suggestion:** Test with values at exact boundaries (12.0, 12.00001) to verify floating-point comparison correctness. Consider using `<=` and `>=` with epsilon tolerance.

### FINDING-12: "Not Evaluated" card uses inline opacity:0.5 rather than a CSS class
- **Severity:** Minor
- **Location:** Line 984: `style="opacity:0.5; border-style:dashed;"`
- **Observation:** The "Not Evaluated" state for skipped models uses inline styles rather than a defined CSS class. This works but is inconsistent with the rest of the design system which uses classes like `.risk-low`, `.risk-high`, etc.
- **Suggestion:** Define a `.score-card-skipped` class with the opacity and dashed border properties for consistency and maintainability.

## 5. Score Card Design

### FINDING-13: All 6 evaluated score cards show "0.00" for HScore, CAR-HEMATOTOX, and Hay Binary Classifier
- **Severity:** Critical
- **Location:** Score card grid in Overview
- **Observation:** The HScore, CAR-HEMATOTOX, and Hay Binary Classifier all display "0.00" with "LOW" risk. While these may be legitimate API return values for Maria Chen's baseline labs, displaying "0.00" for a clinical score is potentially confusing. Clinicians may wonder if the API failed or returned a default value. The HScore in particular should rarely be exactly 0 -- even a healthy patient typically scores some points on the temperature and ferritin components.
- **Suggestion:** If the API genuinely returns 0.00, add contextual help text explaining why (e.g., "All components below threshold"). If these are default/error values, this is a backend bug that needs investigation. Consider adding a visual cue (information icon) explaining what 0.00 means for each scoring model.

### FINDING-14: Score cards do not show the checkmark icon for "Not Evaluated" card
- **Severity:** N/A (Positive observation)
- **Location:** Line 977 vs line 986
- **Observation:** The `getRiskIcon()` function (line 1977-1984) correctly returns a checkmark for LOW, triangle for MODERATE, and warning sign for HIGH. The "Not Evaluated" card does not call this function and shows no icon. This is correct differentiation.

## 6. Lab Values Table

### FINDING-15: Lab values table is scannable but missing some abnormal value highlighting
- **Severity:** Major
- **Location:** Lab values table in Overview
- **Observation:** In the screenshot, all lab values for Maria Chen at baseline appear in normal range. The table correctly shows "--" dashes in the Trend column (because this is timepoint 1 of 4, so there is no prior data point to compare against). However, the trend column shows dashes with no tooltip or explanation of what "--" means. A clinician scanning quickly might interpret "--" as "data not available" rather than "no prior data for comparison."
- **Suggestion:** Replace "--" trend indicators at timepoint 1 with "Baseline" or a specific "N/A (first measurement)" indicator.

### FINDING-16: ALT normal range shows "0-33 U/L" but Maria Chen's value of 18 U/L
- **Severity:** Major
- **Location:** `NORMAL_RANGES.alt` at line 537: `{ low: 0, high: 33, unit: 'U/L', name: 'ALT' }`
- **Observation:** The ALT normal range defined in code is 0-33 U/L, but the demo_cases.js header comment says ALT normal is "7-56 U/L". The code uses a different (narrower) upper limit than the reference comment. This means values between 33-56 U/L would be flagged as HIGH in the dashboard when they are actually normal. For example, James Williams (DEMO-002) has ALT 45 at baseline, which the dashboard would flag as abnormal when it is within the standard reference range.
- **Suggestion:** Reconcile the `NORMAL_RANGES` values with the reference ranges documented in `demo_cases.js`. ALT upper limit should likely be 56, not 33.

### FINDING-17: Labs not in NORMAL_RANGES are silently omitted from the table
- **Severity:** Minor
- **Location:** Line 999-1002, the overview lab table rendering
- **Observation:** The lab table iterates over `tp.labs` entries and only renders rows where `NORMAL_RANGES[k]` exists. Labs like `il6`, `d_dimer`, `total_bilirubin`, and `albumin` are present in the demo case data but have no entry in `NORMAL_RANGES` (lines 526-538). These values are silently dropped from the overview table. IL-6 is a critical CRS marker and should be visible.
- **Suggestion:** Add `il6`, `d_dimer`, `total_bilirubin`, and `albumin` to `NORMAL_RANGES` so they appear in the lab table. These are clinically significant values for CAR-T monitoring.

## 7. Trend Sparklines

### FINDING-18: Sparklines at baseline timepoint show single dots instead of lines
- **Severity:** Minor
- **Location:** `buildSparklineSVG()` function (line 830-879), trend grid at bottom of Overview
- **Observation:** In the screenshot, the CRP sparkline shows a single green dot at value 5, and Ferritin shows a single dot at 250. This is technically correct (one data point = one dot, no line to draw) but the visual representation is minimal and potentially confusing. The normal range band (faint green rectangle) is visible but hard to see at the small chart size.
- **Suggestion:** For single-data-point sparklines, consider adding a label or larger visual indicator since a lone dot is easy to miss. Alternatively, show a "Need 2+ timepoints for trend" message.

### FINDING-19: Sparkline SVG viewBox size is appropriate
- **Severity:** N/A (Positive observation)
- **Location:** SVG dimensions at `W=200, H=50` (line 831), container `height: 50px` (line 422)
- **Observation:** The sparklines are sized well for trend visualization. The green normal-range band, dashed boundary lines, and color-coded dots (green normal, red abnormal) are all implemented. The axis labels (min/max values at font-size 7) are very small but provide useful scale reference.

### FINDING-20: Trend grid partially cut off at bottom of viewport
- **Severity:** Major
- **Location:** Lab & Vital Trends card at bottom of Overview
- **Observation:** In the screenshot, the trend grid shows CRP and Ferritin in the top row, and LDH and ANC are partially visible at the very bottom edge. Users must scroll the content area to see the full trend grid. The "Timepoints 1-1 of 4" indicator in the card header is helpful but the card itself should ideally be fully visible or have a clear "scroll to see more" indicator.
- **Suggestion:** Consider moving the trend charts into a collapsible/expandable section, or placing them earlier in the page hierarchy if they are clinically important. Alternatively, reduce the overall page content density so trends are above the fold.

## 8. Demo Patient Sidebar

### FINDING-21: 320px sidebar width is adequate but tight
- **Severity:** Minor
- **Location:** `.main-layout` grid: `grid-template-columns: 320px 1fr` (line 130)
- **Observation:** At 320px, patient names, ages, truncated diagnoses, and product names are readable. The sidebar contains three sections: Demo Patients (scrollable list), Current Patient (detail), and Timepoint (timeline). However, only the patient list is visible in the screenshot -- the Current Patient info and Timepoint selector require scrolling past the 8 patient cards. This means the timeline navigation (crucial for switching between baseline, day 1, day 3, day 7) is hidden below the fold in the sidebar.
- **Suggestion:** Consider collapsing the patient list after selection (show only the active patient card at the top, with an expand/collapse toggle) to bring the Current Patient info and Timepoint selector into view. The timepoint selector is critical for navigating the clinical timeline and should be immediately visible.

### FINDING-22: Active patient card styling is clear
- **Severity:** N/A (Positive observation)
- **Location:** `.patient-card.active` (line 155)
- **Observation:** The active patient card (Maria Chen) has a blue border, blue-tinted background, and a subtle double-border effect (`box-shadow: 0 0 0 1px var(--primary)`). This is clearly distinguishable from non-selected cards.

### FINDING-23: Robert Kim shows "MODERATE" risk badge -- color is correct orange
- **Severity:** N/A (Positive observation)
- **Observation:** Among the visible patients in the sidebar, Robert Kim (Tisagenlecleucel / tisa-cel) displays a "MODERATE" orange badge, while all others show "LOW" green. The moderate risk color (orange, `--moderate: #ea580c`) is clearly different from the low risk green, providing good visual differentiation.

## 9. Anticipated Tests Panel

### FINDING-24: Anticipated Tests panel layout is clean and functional
- **Severity:** N/A (Positive observation)
- **Location:** Right panel in the 2-column grid below the score cards
- **Observation:** The test list shows 6 items with color-coded left borders (red for stat, orange for urgent, green for routine). Frequency labels ("Daily", "q4h", "q8-12h", "Weekly") are right-aligned. The hierarchy is clear: CBC and CMP at top as stat, CRP as urgent, then routine items below.

### FINDING-25: Anticipated tests panel does not update dynamically based on lab values
- **Severity:** Minor
- **Location:** `getAnticipatedTests()` function (lines 2043-2078)
- **Observation:** The function checks for fever (`temperature >= 38.0`), high fever (`>= 38.9`), high ferritin (`> 5000`), and low ANC (`< 0.5`) to conditionally add tests. For Maria Chen at baseline, none of these conditions are met, so only the standard tests appear. This is correct behavior, but there is no visual indication to the user that the list is dynamic and would change with different clinical states.
- **Suggestion:** Add a subtle note like "Tests adjusted based on current clinical status" below the list, or highlight items that were conditionally added (e.g., with a "NEW" badge when switching timepoints).

## 10. Cross-Component Consistency

### FINDING-26: Card styles are consistent
- **Severity:** N/A (Positive observation)
- **Observation:** All cards use `border-radius: var(--radius-lg)` (12px), consistent `box-shadow: var(--shadow)`, 1px border, and consistent header/body padding patterns. The Composite Risk Assessment, score grid, Lab Values, Anticipated Tests, and Trend Charts cards all share the same visual language.

### FINDING-27: Button styles are consistent but "Print" button is visually de-emphasized
- **Severity:** Cosmetic
- **Location:** Header right section (line 450)
- **Observation:** The "Print" button uses `btn btn-secondary btn-sm` styling, making it small and low-contrast in the header. The "Theme" button next to it is a custom `theme-toggle` class with different styling. These two adjacent buttons have inconsistent visual weight and style.
- **Suggestion:** Either unify both as `btn btn-secondary btn-sm` or give them both the same visual treatment.

### FINDING-28: Tab navigation icons render as emoji -- cross-platform consistency concern
- **Severity:** Minor
- **Location:** Task navigation buttons (lines 456-464)
- **Observation:** The tab navigation uses HTML entity/emoji characters for icons (chart icon, clipboard, stopwatch, thermometer, brain, warning, blood drop, house, doctor). These render differently across operating systems and browsers. In the screenshot (Chrome on Windows), they render as standard emoji, which is acceptable but not pixel-perfect. On older systems or certain browsers, these may render as tofu or missing glyphs.
- **Suggestion:** Consider using SVG icons or an icon font (e.g., the SVG approach already used for the logo) for consistent cross-platform rendering. This is a lower-priority concern if the target deployment is a known browser environment.

## 11. Missing Visual Elements

### FINDING-29: No loading skeleton or shimmer state visible
- **Severity:** Minor
- **Location:** Content area loading states
- **Observation:** The code defines a `.loading-spinner` class (line 366-371) and uses it for the initial patient list loading state (line 475). However, when switching patients or timepoints, the `loadTimepoint()` function (line 720) calls `renderTaskContent()` after the API response. During the API call, there is no intermediate loading state shown -- the old content persists until the new content replaces it. If the API is slow, this could cause confusion.
- **Suggestion:** Add a brief loading skeleton or spinner overlay during API predictions, especially for the score cards and risk assessment which depend on API data.

### FINDING-30: Print header is hidden in normal view (correct)
- **Severity:** N/A (Positive observation)
- **Location:** `.print-header { display: none; }` (line 341)
- **Observation:** The print header element exists in the DOM (line 500-503) but is correctly hidden in normal view and only shown in print media. This is the correct pattern.

### FINDING-31: No favicon defined
- **Severity:** Cosmetic
- **Location:** `<head>` section (lines 3-6)
- **Observation:** No `<link rel="icon">` is defined. The browser will request `/favicon.ico` which will 404 on the Flask server and show a generic tab icon.
- **Suggestion:** Add a simple SVG favicon using the existing checkmark-in-circle logo design.

## 12. Print View

### FINDING-32: Print CSS hides sidebar but does not restructure score cards
- **Severity:** Major
- **Location:** `@media print` rules (lines 342-357)
- **Observation:** The print CSS hides the header, task nav, sidebar, buttons, and theme toggle. It also removes `max-height` constraints on the content area and applies `break-inside: avoid` on cards. However, the score card grid (`grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))`) will attempt to fit as many cards as possible on the print page width. On A4 paper at standard margins, this may result in 3-4 cards per row instead of the on-screen 6-7, creating a very different visual layout.
- **Suggestion:** Add print-specific score grid styling, e.g., `@media print { .score-grid { grid-template-columns: repeat(3, 1fr); } }` to ensure consistent layout. Also add the patient name and timepoint to the printed output prominently (the print-header div does this but verify it includes risk level).

### FINDING-33: Print view does not include page numbers or header/footer
- **Severity:** Cosmetic
- **Location:** `@page { margin: 1cm; }` (line 356)
- **Observation:** The `@page` rule only sets margins. It does not define running headers/footers with patient name or page numbers. For a clinical document that might be printed and placed in a patient chart, page identification is important.
- **Suggestion:** While CSS `@page` header/footer support is limited, consider adding a visible print-only footer with "Page X of Y" using CSS counters or JavaScript `window.onbeforeprint`.

## 13. Accessibility

### FINDING-34: CRS grade boxes have role="radio" but no ARIA group
- **Severity:** Critical
- **Location:** Line 1187: `role="radio" tabindex="0" aria-label="CRS ${info.label}"`
- **Observation:** The CRS grade selection boxes have `role="radio"` and `tabindex="0"` for keyboard accessibility, but they are not wrapped in a `role="radiogroup"` container. This violates ARIA requirements for radio groups. Screen readers will not properly announce the group context. Additionally, arrow key navigation is not implemented -- only click/Enter would work.
- **Suggestion:** Wrap the `.crs-grade-strip` in a `role="radiogroup"` element with an `aria-label`. Implement arrow key navigation between options. Add `aria-checked="true/false"` state management.

### FINDING-35: Form inputs in Clinical Visit tab lack associated labels
- **Severity:** Critical
- **Location:** Clinical Visit form inputs (lines 1697-1784)
- **Observation:** Form inputs use `<div class="form-label">` elements which are visually positioned as labels but are not `<label>` elements linked to their inputs via `for`/`id` attributes. This means screen readers cannot associate the label text with the form control. The Pre-Infusion checklist items (line 1121) do use `<label>` wrappers, showing inconsistent accessibility patterns.
- **Suggestion:** Convert all `.form-label` divs to `<label for="inputId">` elements, or wrap each input in its label. This is especially important for a clinical tool that may need to meet healthcare accessibility standards (Section 508, WCAG 2.1 AA).

### FINDING-36: Color-only indication of abnormal values
- **Severity:** Minor
- **Location:** Lab value flagging (line 317: `.cell-high` red, line 318: `.cell-low` orange)
- **Observation:** Abnormal lab values are indicated only by color change (red for high, orange for low). There is no secondary indicator (icon, text label, bold weight) for users with color vision deficiencies. The Pre-Infusion view's `renderLabRow()` function (line 1149-1166) does add a text "HIGH"/"LOW"/"Normal" flag column, but the Overview table does not.
- **Suggestion:** Add a text indicator or icon alongside the color change in the Overview lab table, matching the Pre-Infusion view's approach.

## 14. Data Integrity Concerns

### FINDING-37: Patient risk badge in sidebar shows risk from last timepoint, not current timepoint
- **Severity:** Critical (data display correctness)
- **Location:** Line 664: `riskClass(p.timepoints[p.timepoints.length-1].expected_risk)`
- **Observation:** The patient card in the sidebar always shows the risk level from the LAST timepoint in the patient's data, not the currently selected timepoint. For a patient who starts LOW risk at baseline and escalates to HIGH risk at Day 5 (like James Williams), the sidebar badge will always show "LOW" (their Day 7 recovery risk) regardless of which timepoint is being viewed. This is misleading and could cause a clinician to dismiss a patient as low-risk when they are viewing a high-risk timepoint.
- **Suggestion:** Either: (a) show the risk level for the currently selected timepoint (requires re-rendering the sidebar on timepoint change), (b) show the WORST risk level across all timepoints with a warning indicator, or (c) clearly label the badge as "Latest risk" to avoid confusion.

## 15. Functional Concerns Visible in Visual Review

### FINDING-38: Trend direction arrows show flat ("--") for all labs at first timepoint
- **Severity:** Cosmetic
- **Location:** Trend column in Lab Values table
- **Observation:** At the first timepoint, all trend badges render as "--" (horizontal line, stable) because there is no prior data point. This is technically correct (from `getTrendDirection()` which returns 'stable' for < 2 values) but visually looks like every value is "stable" rather than "first measurement."
- **Suggestion:** Return a distinct visual (e.g., empty or "NEW") for single-data-point situations rather than the stable indicator.

### FINDING-39: Clock display in header works correctly
- **Severity:** N/A (Positive observation)
- **Location:** Header right, `clockDisplay` span
- **Observation:** The clock shows "12:58:25" in the clean screenshot, confirming the `updateClock()` function (line 2120-2123) is running correctly with 24-hour format. The monospace font ensures the clock does not shift layout as digits change.

## 16. Responsive Design

### FINDING-40: Responsive breakpoint at 1024px collapses sidebar
- **Severity:** Cosmetic
- **Location:** `@media (max-width: 1024px)` (lines 360-363)
- **Observation:** Below 1024px, the layout switches to single column with the patient sidebar limited to 200px height. This is a reasonable breakpoint but may not have been tested -- the screenshot shows a wide viewport. The sidebar at 200px height would only show ~2 patient cards before scrolling, which may be insufficient.
- **Suggestion:** Test at tablet widths (768px-1024px). Consider a collapsible sidebar drawer pattern for mobile/tablet use. 200px sidebar height may need to be increased to 250-300px to show meaningful content.

### FINDING-41: Trend grid has a separate responsive breakpoint
- **Severity:** Cosmetic
- **Location:** `@media (max-width: 900px) { .trend-grid { grid-template-columns: 1fr; } }` (line 428)
- **Observation:** The trend grid switches to single column at 900px, which is different from the main layout breakpoint at 1024px. This means there is a window between 900-1024px where the sidebar is collapsed but the trend grid is still 2-column. This should work but creates a slightly unusual intermediate layout.

---

## Summary Table

| # | Severity | Component | Issue |
|---|----------|-----------|-------|
| 01 | Major | Composite Risk | Central risk label too small, competes with surrounding text |
| 02 | Minor | Score Grid | 7th card may be partially cut off on some viewports |
| 03 | Major | Risk Meter | Indicator hard to see at low risk values (thin bar on green) |
| 04 | Minor | Layout | Lab table vs Anticipated Tests unbalanced whitespace |
| 05 | Minor | Sidebar | No scroll indicator for hidden patients below fold |
| 06 | Major | Content Area | Dual-scroll pattern may hide important content |
| 07 | Major | Score Cards | Citation text at 10px is nearly illegible |
| 09 | Minor | Sidebar | Diagnosis truncation not word-boundary-aware |
| 11 | **Critical** | Lab Table | Hemoglobin highlighting potential float comparison edge case -- verify |
| 12 | Minor | Score Cards | "Not Evaluated" uses inline styles instead of CSS class |
| 13 | **Critical** | Score Cards | Multiple scores at 0.00 may indicate backend issue or need contextual explanation |
| 15 | Major | Lab Table | Trend "--" at first timepoint ambiguous (stable vs no prior data) |
| 16 | Major | Lab Table | ALT normal range (0-33) conflicts with reference standard (7-56) |
| 17 | Minor | Lab Table | il6, d_dimer, bilirubin, albumin silently omitted from table |
| 18 | Minor | Sparklines | Single-dot sparklines provide minimal visual information |
| 20 | Major | Trends | Trend chart card partially below viewport fold |
| 21 | Minor | Sidebar | Timepoint selector hidden below patient list in sidebar |
| 25 | Minor | Tests Panel | No indication that test list is dynamically generated |
| 27 | Cosmetic | Header | Print and Theme buttons have inconsistent styling |
| 28 | Minor | Tab Nav | Emoji icons may render inconsistently cross-platform |
| 29 | Minor | Loading | No loading skeleton during API calls |
| 31 | Cosmetic | Header | Missing favicon |
| 32 | Major | Print | Score card grid layout may reflow unpredictably on paper |
| 33 | Cosmetic | Print | No page numbers or running headers in print output |
| 34 | **Critical** | Accessibility | CRS grade radio buttons lack ARIA radiogroup |
| 35 | **Critical** | Accessibility | Form inputs not associated with labels via for/id |
| 36 | Minor | Accessibility | Color-only abnormal value indication (no text flag in Overview) |
| 37 | **Critical** (data) | Sidebar | Risk badge shows last timepoint risk, not current selection |
| 38 | Cosmetic | Lab Table | Trend arrows show "stable" for first-ever measurement |
| 40 | Cosmetic | Responsive | Sidebar at 200px height in mobile may be too short |
| 41 | Cosmetic | Responsive | Mismatched responsive breakpoints (900px vs 1024px) |

**Total: 4 Critical, 7 Major, 10 Minor, 6 Cosmetic**

---

## Priority Recommendations

### Must Fix Before Clinical Pilot (Critical + High-Priority Major)
1. **FINDING-37**: Fix sidebar risk badge to reflect current timepoint, not always the last one
2. **FINDING-35**: Add proper `<label>` associations for all form inputs
3. **FINDING-34**: Add `role="radiogroup"` and proper ARIA to CRS grade selector
4. **FINDING-13**: Investigate 0.00 scores for HScore/CAR-HEMATOTOX -- verify backend correctness or add explanatory context
5. **FINDING-16**: Fix ALT normal range to match clinical reference standard
6. **FINDING-07**: Increase citation font size to 11px minimum
7. **FINDING-06**: Address dual-scroll UX -- ensure trend charts and lower content are discoverable

### Should Fix Soon (Remaining Major)
8. **FINDING-01**: Increase composite risk level visual prominence
9. **FINDING-03**: Improve risk meter indicator visibility
10. **FINDING-15**: Distinguish "first measurement" from "stable trend" in lab table
11. **FINDING-20**: Ensure trend charts are accessible without deep scrolling
12. **FINDING-32**: Add print-specific score grid layout

### Nice to Have (Minor + Cosmetic)
13. Add missing lab values (IL-6, D-dimer, bilirubin, albumin) to display
14. Add sidebar scroll indicators
15. Add loading skeletons during API calls
16. Add favicon
17. Consider SVG icons for cross-platform consistency in tab navigation
