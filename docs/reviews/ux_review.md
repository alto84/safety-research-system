# UX Review: Cell Therapy Safety Platform - Clinical Dashboard

**Reviewer:** Alex Rivera, Senior UX Designer (Clinical Decision Support Systems)
**Date:** 2026-02-07
**File Reviewed:** `src/api/static/index.html`
**Scope:** Full dashboard including all 9 task views, patient sidebar, responsive behavior, print, and accessibility

---

## Executive Summary

This is a well-structured clinical dashboard that successfully integrates multiple validated scoring systems (EASIX, HScore, CAR-HEMATOTOX, ICE, Hay Binary Classifier) into a cohesive workflow organized around the CAR-T therapy patient journey. The information architecture follows a logical clinical timeline from pre-infusion through discharge. The design system is clean with a professional aesthetic appropriate for clinical settings.

However, there are significant issues around accessibility, data density on smaller viewports, keyboard navigation, and state management that would need to be addressed before deployment in a clinical environment. The color palette has red/green colorblind accessibility gaps, and the print stylesheet strips too much context. Several interaction patterns do not meet the minimum touch-target and click-target sizes expected in clinical workstation environments where users may be wearing gloves or working under stress.

**Overall Rating:** 6.5/10 for clinical deployment readiness
**Strongest Areas:** Information architecture, visual design system, clinical content accuracy
**Weakest Areas:** Accessibility, responsive behavior below 1024px, state persistence, keyboard navigation

---

## 1. Information Architecture

### What Works

- **Task navigation mirrors clinical workflow.** The 9 tabs (Overview, Pre-Infusion, Day 1 Monitor, CRS Monitor, ICANS, HLH Screen, Hematologic, Discharge, Clinical Visit) follow the actual temporal sequence of CAR-T therapy management. A clinician's mental model maps naturally to this layout.
- **Patient sidebar with timepoint timeline** is an effective pattern. It provides persistent context (who am I looking at, what day) while the main content area changes.
- **Score cards in the Overview** give a good at-a-glance summary before diving into specific monitoring tabs.

### Issues

- **9 tabs is at the upper limit** for horizontal navigation without grouping. On a 15" laptop at 1366x768 (common clinical workstation resolution), these will overflow and require horizontal scrolling. The `scrollbar-width: none` and `::-webkit-scrollbar { display: none }` rules (lines 106-107) hide the scrollbar entirely, making the overflow invisible. Users will not know there are more tabs to the right. This is a critical discoverability problem.
- **No tab grouping or categorization.** Clinical workflows could benefit from grouping: "Assessment" (Overview, Pre-Infusion), "Active Monitoring" (Day 1, CRS, ICANS, HLH), "Recovery" (Hematologic, Discharge), "Ad Hoc" (Clinical Visit). Even subtle visual dividers between groups would help.
- **No breadcrumb or state indicator** showing where the user is in the patient journey. The active tab is highlighted, but there is no indication of which tabs have data, which have alerts, or which have been completed.
- **Clinical Visit tab** is structurally different from the other tabs (manual entry vs. demo-driven). It feels bolted on rather than integrated. The switch between "demo patient mode" and "manual entry mode" should be more explicit.

### Recommendation

Add visual grouping dividers between tab categories. Add overflow indicators (fade gradient or arrow buttons) to the tab navigation. Consider adding badge indicators to tabs when they contain active alerts (e.g., a red dot on "CRS Monitor" when fever is detected).

---

## 2. Visual Hierarchy

### What Works

- **Alert banners at the top of views** immediately draw attention to critical findings. The danger/warning/success/info color coding is semantically correct.
- **Risk level badges** (LOW/MODERATE/HIGH) are well-placed in card headers and patient cards. The combination of background color + text color + uppercase + bold provides strong visual weight.
- **Composite Risk Meter** (gradient bar with indicator) provides an intuitive analog representation of risk level. This is an effective clinical decision support pattern.
- **Score values at 28px with monospace font** stand out clearly as the primary data point in each score card.

### Issues

- **Too many visual weights competing at once.** On the Overview page, the user sees: alert banners, risk meter, score cards, lab table, anticipated tests, and teaching points all at once. There is no clear "read this first" hierarchy beyond the alert banners. In Epic's Storyboard or Cerner's PowerChart, there is always a single dominant summary element.
- **Card headers are not differentiated enough from card bodies.** The 14px/18px padding difference (lines 183-191) is subtle. Card titles at 15px are only 1px larger than body text at 14px. Headers need more visual weight -- consider a slightly different background color or larger title font.
- **Teaching points** have the same visual prominence as actionable clinical data. In a time-pressured clinical environment, educational content should be visually subordinate to actionable information.

### Recommendation

Introduce a clear visual hierarchy: (1) Alerts/Banners at top, (2) Single dominant summary card (composite risk), (3) Actionable detail cards, (4) Reference/educational content collapsed by default. Consider making teaching points collapsible or moving them to a separate "Education" tab.

---

## 3. Data Density

### What Works

- **Score grid** with `grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))` is a good responsive pattern that packs score cards efficiently.
- **Lab value tables** present data in a compact, scannable format. The inclusion of normal ranges inline is clinically useful.
- **Sparkline rows** in the CRS view are an efficient use of space for trend visualization. The combination of label + value + visual bar is a well-established clinical pattern.

### Issues

- **The 2-column layout** (labs table + anticipated tests) at the bottom of Overview uses `grid-template-columns: 1fr 1fr` (line 793). On a 1920x1080 monitor with 320px sidebar, each column gets ~780px. This is fine. But on a 1366x768 monitor, each column gets ~523px, and the 5-column lab table (Test, Value, Normal, Flag, Relevance) becomes cramped in Pre-Infusion view.
- **The patient sidebar at 320px fixed width** (line 130) is generous. On smaller monitors, this eats too much horizontal space. The sidebar-to-content ratio should be more like 260px/1fr on smaller screens.
- **Clinical notes are truncated to 50 characters** in the timeline (line 672: `tp.clinical_note.substring(0, 50)`). This is too aggressive. Clinical context is lost. Consider 80-100 characters or an expandable pattern.
- **CRS Management Algorithm and ICANS Management** present treatment protocols as stacked colored boxes (lines 1022-1035, 1230-1243). These are dense text blocks with no visual structure beyond background color. Bullet points or structured sub-elements would improve scannability.
- **No sparkline trend charts** across timepoints. The sparkline bars show a single point-in-time value as a percentage of range, not a trend. Clinical decision-making relies heavily on trends (is CRP rising or falling?). This is the single biggest data density gap.

### Recommendation

Add true trend visualization (mini line charts) showing lab values across timepoints. Reduce sidebar width to 280px. Consider making the 2-column overview layout stack on narrower viewports at a higher breakpoint than 1024px (try 1280px). Add "expand" controls for truncated clinical notes.

---

## 4. Color System

### What Works

- **CSS custom properties** (lines 8-38) provide a well-organized design token system. The light/dark theme implementation is comprehensive.
- **Semantic color assignments** are clinically intuitive: red for danger/high-risk, orange for moderate, green for success/low-risk, blue for info.
- **The 5-level CRS grading strip** (lines 381-394) uses a distinct color for each grade that aligns with clinical severity expectations.

### Issues

- **Red/green colorblind (deuteranopia/protanopia) safety gap.** The `--danger: #dc2626` (red) and `--success: #059669` (green) are the primary risk indicators. Approximately 8% of males have red-green color vision deficiency. This palette will cause `risk-low` and `risk-high` badges to appear nearly identical to these users. This is a patient safety concern in a clinical CDSS.
  - The risk meter gradient (line 324: `linear-gradient(90deg, var(--success) 0%, #84cc16 25%, var(--warning) 50%, var(--moderate) 75%, var(--danger) 100%)`) becomes an indistinguishable blur for colorblind users.
- **Cell-high (red) and cell-low (orange-yellow)** flags on lab values (lines 317-318) also rely on hue discrimination alone. There are no secondary indicators (icons, patterns, or text labels) to supplement color.
- **Warning (#d97706) vs. moderate (#ea580c)** are very close in hue. On some monitors, especially clinical workstation LCDs with poor color calibration, these may be hard to distinguish.
- **Dark theme** danger-light and warning-light backgrounds (lines 49-52) have very low contrast. `--danger-light: #3f1515` on `--surface: #1a1d27` may not meet WCAG contrast thresholds.

### Recommendation

Add secondary indicators beyond color: icons (checkmark for low, triangle-exclamation for high), text labels (already present in badges -- good), and/or patterns. Use a colorblind-safe palette: consider blue for low-risk instead of green, or use Oklab/OKLCH color space to ensure perceptual distinctiveness. The risk meter should include labeled tick marks, not just a gradient. Test the entire palette through a deuteranopia simulator.

---

## 5. Typography

### What Works

- **Inter + JetBrains Mono** is an excellent combination for clinical dashboards. Inter has strong legibility at small sizes, and JetBrains Mono's distinct character shapes prevent number misreading (critical for lab values).
- **Monospace for all numerical values** (score-value at 28px, lab values, clock) is correct practice for clinical data display.
- **Font hierarchy** uses 4 clear levels: 20px logo, 15px card titles, 14px body, 12-13px labels/meta.

### Issues

- **13px body text in many elements** (task buttons, alerts, table cells, form labels, teaching points, management algorithms) is below the recommended minimum for clinical workstation viewing distances. Clinicians typically view dashboard screens at 50-70cm (arm's length). At 96dpi on a 22" monitor, 13px text subtends roughly 0.17 degrees of visual angle -- below the 0.2-degree threshold recommended for sustained reading.
- **11px text** is used for score-citation, test-freq, unit labels, and score-label (lines 224-227, 243, 303). This is too small for clinical environments, especially under fatigue or low lighting conditions (overnight shifts).
- **Line 143:** `.sidebar-title` uses `font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px`. Uppercase small text with letter spacing is harder to read than title-case at a slightly larger size. This pattern sacrifices legibility for aesthetic compactness.
- **No `font-size` on `<html>` or `<body>`** means the type scale is absolute (px), not relative (rem). This prevents users from scaling text with browser zoom in a predictable way. Clinical accessibility standards recommend rem-based sizing.

### Recommendation

Increase minimum body text to 14px, minimum label text to 12px. Convert all `px` font sizes to `rem` with a 16px base. Replace uppercase section headers with title-case at 13-14px. Ensure all clinical data (lab values, scores, vital signs) are at least 14px monospace. Test readability at arm's length on a 22" 1080p monitor.

---

## 6. Interaction Design

### What Works

- **Checkbox-based checklists** for pre-infusion and day-1 monitoring are clinically appropriate. Checkboxes provide clear binary state.
- **CRS grade strip** with click-to-select is an intuitive pattern for grade selection. The hover transform (`translateY(-2px)`) provides clear affordance.
- **Real-time lab value flagging** on the Clinical Visit form (`oninput="flagVisitInput(this, '${key}')"` at line 1521) gives immediate feedback when values are abnormal. Red/yellow border + background change is a strong pattern.
- **Theme toggle and print button** in the header are accessible and well-placed.

### Issues

- **Click targets are too small in several areas:**
  - Timeline buttons (`.timeline-btn`, line 289): padding is only `2px 0`. These are small text links used to switch between timepoints. On a touchscreen or with motor impairment, these are nearly impossible to hit. WCAG 2.2 minimum target size is 24x24px; recommended is 44x44px.
  - Tab buttons (`.task-btn`, line 108): padding is `12px 20px`, which is adequate for mouse but the 13px font makes the total height only about 40px. Acceptable but tight.
  - `.btn-sm` (line 269): `padding: 4px 10px` with 12px font creates a ~24px tall button. This is the WCAG minimum; clinical environments should target 32px+.
- **No keyboard navigation support.** There are no `tabindex` attributes, no `role` attributes, no `aria-label` attributes on interactive custom elements. The CRS grade boxes, timeline buttons, and patient cards are `<div onclick="...">` elements that are not keyboard-accessible.
- **CRS grade strip allows multiple selections.** The `onclick="this.classList.toggle('selected')"` pattern (line 985) allows selecting multiple grades simultaneously, which is clinically nonsensical -- a patient can only have one CRS grade at a time. This should be radio-button behavior.
- **Checkboxes in checklists are not persisted.** Checking items in the pre-infusion or day-1 checklist, then switching tabs and returning, resets all checkboxes. This is a significant workflow disruption.
- **ICE score calculator** requires clicking a "Calculate" button rather than auto-calculating on select change. Every extra click costs time in a clinical emergency. Auto-calculation with debounce is the expected pattern.
- **No form validation** on the Clinical Visit manual entry. Negative lab values, implausible values (temperature 50C, platelets -100), and missing required fields are all accepted silently.
- **No undo/confirmation on destructive actions.** The "Clear" button on Clinical Visit (`clearVisitForm()` at line 1675) wipes all form data with no confirmation dialog.

### Recommendation

Convert all custom interactive elements (`div[onclick]`) to `<button>` elements with proper ARIA attributes. Increase timeline button click targets to minimum 44x44px. Make CRS grade selection exclusive (radio behavior). Auto-persist checklist state in localStorage per patient/timepoint. Auto-calculate ICE score on input change. Add form validation with clinically plausible ranges. Add confirmation dialog to the Clear button.

---

## 7. Responsive Design

### What Works

- **CSS Grid layout** provides good structural flexibility. The `grid-template-columns: 320px 1fr` pattern (line 130) is appropriate for the sidebar+content layout.
- **1024px breakpoint** (lines 349-352) collapses to single-column. The sidebar gets a `max-height: 200px` which keeps it visible but compact.
- **Score grid** uses `repeat(auto-fit, minmax(200px, 1fr))` which reflows gracefully.
- **Form grid** uses `repeat(auto-fit, minmax(180px, 1fr))` for lab input fields.

### Issues

- **Only one breakpoint at 1024px.** Clinical workstations range from 1366x768 (common Dell clinical monitors) to 2560x1440 (newer workstations) to 3840x2160 (radiology-grade). A single breakpoint cannot serve this range. Key missing breakpoints:
  - 1280px: Where the 9-tab navigation starts to overflow
  - 1440px: Where the 2-column content layouts (labs + tests) become comfortable
  - 1920px+: Where the layout could benefit from a 3-column content area or wider sidebar
- **Sidebar at 200px height when collapsed** (line 351) is too short to show patient information, timepoint selector, AND patient list. The user has to scroll within a 200px container. This is unusable for managing a patient panel.
- **No landscape/portrait consideration** for tablet use. Some clinicians use iPads at bedside.
- **Task navigation overflow** is completely hidden (invisible scrollbar). Below ~1280px width, some tabs become inaccessible unless the user knows to horizontally scroll.
- **The ICE score form** uses `grid-template-columns: repeat(5, 1fr)` (line 1164). On narrow viewports, 5 columns of select dropdowns will be extremely cramped.

### Recommendation

Add breakpoints at 1280px and 1600px. At 1280px, reduce sidebar to 260px and make tab navigation wrap or add overflow indicators. At 1600px+, expand the content area to 3-column layouts. Make the collapsed sidebar expandable (drawer pattern) rather than cramming it into 200px. For the ICE score, switch to 2 or 3 columns below 1024px.

---

## 8. Accessibility (WCAG 2.1 AA)

### Critical Failures

1. **No ARIA landmarks or roles.** The `<header>`, `<nav>`, `<aside>`, and `<main>` elements are used correctly as HTML5 landmarks (good), but custom widgets (CRS grade selector, timeline, patient cards, tab panels) have no ARIA roles, states, or properties.

2. **Interactive `<div>` elements without keyboard access.** Patient cards (`div.patient-card onclick`), CRS grade boxes, and timeline buttons are not focusable and cannot be activated with keyboard. This fails WCAG 2.1.1 (Keyboard) -- a Level A requirement.

3. **Color as sole information carrier.** Lab value flags (cell-high, cell-low) and risk badges use color alone to convey clinical risk level. While text labels like "HIGH" and "LOW" exist in some contexts, the sparkline bars (lines 1041-1060) use only color to indicate severity. This fails WCAG 1.4.1 (Use of Color).

4. **Missing form labels.** Checkboxes in the pre-infusion and day-1 checklists use `<label>` wrapping (good), but many form inputs in the Clinical Visit section lack explicit `<label for="">` associations. Screen readers will announce "edit text" without context.

5. **No skip navigation link.** There is no way to skip past the header and tab navigation to reach the main content area.

6. **No live regions.** When predictions are loaded or alerts appear, there is no `aria-live` region to announce changes to screen reader users. The loading spinner has no `aria-label`.

7. **No focus management on tab switch.** When clicking a task tab, focus stays on the tab button. The content area updates but focus does not move to the new content. Screen reader users will not know the content changed.

### Passes

- HTML5 semantic elements (`header`, `nav`, `aside`, `main`) are used correctly.
- `lang="en"` is set on the `<html>` element.
- Form inputs have visible labels (even if not programmatically associated).
- Color contrast for primary text (--text: #1a1a2e on --bg: #f5f6fa) meets AA requirements (~13:1 ratio).

### Recommendation

This dashboard would fail a WCAG 2.1 AA audit in its current state. Priority fixes: (1) Add `role="tablist"`, `role="tab"`, `role="tabpanel"` to task navigation. (2) Make all interactive elements keyboard-accessible with `tabindex="0"` and `keydown` handlers. (3) Add `aria-live="polite"` to the content area and alert containers. (4) Add a skip-to-content link. (5) Add `aria-label` to all form inputs.

---

## 9. State Management

### What Works

- **Theme preference** is persisted in `localStorage` (line 1795-1796). Good.
- **API health polling** at 30-second intervals (line 1817) keeps the connection status current.
- **Patient selection state** (currentPatient, currentTimepoint, currentTask, lastPrediction) is held in module-level variables. Simple and appropriate for a single-page application.

### Issues

- **No loading states for API calls.** The `runPrediction()` function (line 549) makes an async API call but the UI does not show a loading indicator in the main content area. The only loading indicator is in the Clinical Visit view (`visitResults`). When switching patients or timepoints, the content area renders stale data until the new prediction returns.
- **No error states in main views.** If `runPrediction()` fails (line 700: `lastPrediction = null`), the Overview renders the empty state "Select a Patient" which is misleading -- a patient IS selected, the API just failed. This should show an error state with retry option.
- **Checklist state is not persisted.** Pre-infusion and day-1 checklists reset on any navigation. In a real clinical workflow, a nurse might check items, switch to look at CRS data, then come back. All progress is lost.
- **CRS grade selection is not persisted.** Selected grade resets on re-render.
- **ICE score result is not persisted.** The calculated score disappears on tab switch.
- **No optimistic updates or debouncing** on the Clinical Visit form. Each keystroke in lab value fields triggers `oninput` for flagging but there is no debounce on the "Run Risk Assessment" action.
- **No offline/disconnected mode.** If the API goes down (status shows "Disconnected"), the user can still interact with forms but all submissions will fail silently or show generic errors. There should be a prominent banner and form-level disabled states.
- **Race conditions possible.** Rapid patient switching triggers multiple `runPrediction()` calls. The last to resolve wins (`lastPrediction = await runPrediction(reqData)` at line 698), but there is no cancellation of inflight requests. A slow response from patient A could overwrite a faster response from patient B.

### Recommendation

Add loading spinners to the main content area during API calls. Show explicit error states with retry buttons when predictions fail. Persist checklist/CRS grade/ICE score state in localStorage keyed by patient_id + timepoint. Add AbortController to cancel inflight requests on patient switch. Show a prominent "API Disconnected" banner that disables prediction-dependent actions.

---

## 10. Print Layout

### What Works

- **Print media query exists** (lines 341-346). It correctly hides non-essential UI elements (header, nav, sidebar, buttons, theme toggle).
- **Cards avoid page breaks** (`break-inside: avoid`).
- **Box shadows are removed** and borders simplified for clean print output.

### Issues

- **Patient context is completely lost.** The header and sidebar are hidden, but there is no print-specific header that identifies: patient name, patient ID, date of assessment, current timepoint, or clinician name. A printed page with lab values and risk scores but no patient identifier is a patient safety hazard.
- **Only the current tab content prints.** There is no option to print a comprehensive summary across all tabs. A clinician printing for a paper chart handoff needs the full picture.
- **Color-dependent elements (risk badges, alert banners, sparkline bars) lose meaning in grayscale print.** No print-specific styling converts colors to patterns or text labels.
- **Page margins are not specified.** Clinical printers often use standard letter paper with institutional headers/footers. Without `@page { margin: ... }` rules, content may overlap with institutional print templates.
- **No print date/time stamp.** Printed clinical documents must include generation timestamp for medicolegal documentation.

### Recommendation

Add a print-specific header block with patient name, ID, DOB, date/time of print, clinician, and institution placeholder. Add `@page` rules for margins. Add a "Print Summary" option that compiles all tabs into a single printable report. Replace color-coded elements with text labels and/or patterns for grayscale printing. Add automatic timestamp in print footer.

---

## 11. Comparison with Best Practices

### Epic Flowsheets / Storyboard

Epic's clinical dashboards use a **persistent patient banner** at the top of every screen showing patient name, MRN, DOB, allergies, and code status. This dashboard's sidebar approach is similar in concept but inferior in execution because the patient context collapses to 200px on smaller screens and disappears entirely in print.

Epic also uses **BPA (Best Practice Advisory) firing patterns** where alerts interrupt workflow at decision points rather than being passive banners. This dashboard's alert system is passive -- it shows warnings but does not gate actions. Consider adding a "hard stop" pattern for critical situations (e.g., HLH warning should require acknowledgment before proceeding).

### Cerner PowerChart

PowerChart uses **structured documentation templates** with required fields that gate completion. The pre-infusion and day-1 checklists in this dashboard are similar but lack the "all required items checked before proceeding" workflow enforcement. The checklist is advisory only.

PowerChart also provides **trending views** with mini-charts for each lab parameter over time. This dashboard's sparkline bars show single-point values, not trends. This is the most significant gap versus commercial CDSSs.

### Commercial CDSS Patterns (UpToDate, DynaMed, VisualDx)

Commercial CDSSs typically include **evidence grading indicators** next to recommendations (e.g., "Grade A, Level 1 evidence"). This dashboard includes citations (line 227, `score-citation`) which is good, but does not grade the evidence strength. For clinical adoption, each management recommendation should cite its evidence level.

Commercial CDSSs also provide **differential diagnosis support** rather than just monitoring. The HLH vs. CRS differentiation table (lines 1308-1322) is an excellent example of this pattern that should be replicated for other toxicity differentials (ICANS vs. stroke, infection vs. CRS).

---

## 12. Top 10 Improvements (Prioritized by Clinical Impact)

### 1. CRITICAL -- Add Trend Visualization Across Timepoints
**Impact:** High | **Effort:** Medium

Currently, lab values and vital signs display only the current timepoint. Clinicians make decisions based on trends (rising CRP, falling platelets, worsening fever curve). Add mini sparkline charts showing values across all available timepoints for each patient. This is the single highest-impact improvement for clinical decision-making.

**Implementation:** For each lab parameter, collect values across `currentPatient.timepoints`, render as an SVG polyline in each sparkline row. Add directional arrows (trending up/down/stable) next to current values.

### 2. CRITICAL -- Fix Accessibility for Keyboard and Screen Reader Users
**Impact:** High | **Effort:** Medium

The dashboard fails WCAG 2.1 Level A requirements. All interactive elements (`div[onclick]` for patient cards, CRS grades, timeline items) must be converted to `<button>` elements or receive `role="button"`, `tabindex="0"`, and keyboard event handlers. Add `role="tablist"`/`role="tab"`/`role="tabpanel"` to the task navigation. Add `aria-live` regions for dynamic content updates.

### 3. CRITICAL -- Add Colorblind-Safe Secondary Indicators
**Impact:** High | **Effort:** Low

Add icons alongside color-coded risk levels: a shield/checkmark for low risk, a triangle-exclamation for moderate risk, a circle-X for high risk. Ensure the risk meter has labeled tick marks. Add text labels to all sparkline bars. This addresses the 8% of male clinicians with red-green color vision deficiency.

### 4. HIGH -- Persist Checklist and Assessment State
**Impact:** High | **Effort:** Low

Store checklist checkbox states, CRS grade selection, and ICE score results in `localStorage` keyed by `patientId-timepoint-taskId`. Restore state on re-render. Without this, clinicians lose work on every tab switch, creating frustration and potential data loss.

### 5. HIGH -- Add Patient Banner for Print and Persistent Context
**Impact:** High | **Effort:** Low

Add a persistent patient banner (name, ID, DOB, current risk level, day post-infusion) visible in print output. Add print timestamp and page numbers. This is a patient safety requirement -- printed clinical documents without patient identification are a Joint Commission violation.

### 6. HIGH -- Improve Responsive Behavior for Clinical Workstations
**Impact:** Medium | **Effort:** Medium

Add breakpoints at 1280px and 1600px. At 1280px, make the tab navigation wrap or add overflow scroll indicators (fade edges with arrow buttons). Reduce sidebar width to 280px. Make the collapsed sidebar a slide-out drawer rather than a 200px cramped box. Test on 1366x768 (Dell clinical workstation standard).

### 7. MEDIUM -- Add Loading, Error, and Empty States
**Impact:** Medium | **Effort:** Low

Show a spinner in the content area during API calls. When prediction fails, show an explicit error with patient context ("Prediction failed for Maria Chen, Day 3") and a Retry button. When the API is disconnected, show a prominent banner and disable prediction-dependent UI. Add AbortController to prevent race conditions on rapid patient switching.

### 8. MEDIUM -- Make CRS Grade Selection Exclusive (Radio Behavior)
**Impact:** Medium | **Effort:** Low

Change the CRS grade strip from `classList.toggle('selected')` to exclusive selection. Only one grade should be selectable at a time. Tie the selection to the management algorithm display -- selecting Grade 3 should highlight the Grade 3 management protocol. This transforms the CRS section from a reference into an active clinical tool.

### 9. MEDIUM -- Add Tab Badges for Active Alerts
**Impact:** Medium | **Effort:** Low

When a patient's data triggers alerts relevant to specific tabs (fever triggers CRS, low fibrinogen triggers HLH, low ANC triggers Hematologic), show a colored badge on the corresponding tab. This guides clinicians to the most relevant view without requiring them to check every tab. Pattern: small colored dot or count badge on the tab button, similar to notification badges in messaging apps.

### 10. LOW-MEDIUM -- Auto-Calculate ICE Score and Add Form Validation
**Impact:** Low | **Effort:** Low

Calculate ICE score automatically when any select input changes (remove the "Calculate" button). Add input validation to the Clinical Visit form: temperature 30-45C, heart rate 20-250bpm, platelets 0-1000, etc. Show inline validation messages with clinically plausible ranges. Add a confirmation dialog to the "Clear" button.

---

## Appendix: CSS Architecture Notes

### Strengths
- CSS custom properties provide a clean design token system
- Dark theme is comprehensive with proper contrast adjustments
- No CSS framework dependency -- vanilla CSS is appropriate for a focused clinical tool
- Animations are subtle and purposeful (spinner, pulse, transitions)

### Areas for Improvement
- Consider adopting CSS Container Queries for component-level responsive design
- The inline styles in JavaScript template literals (throughout render functions) should be extracted to CSS classes for maintainability
- Several CSS classes are defined but only used in JS-generated HTML, making them hard to audit
- Consider CSS layers (`@layer`) to manage specificity between base styles, components, and utility overrides
- The `!important` declarations in print styles (lines 342-346) suggest specificity conflicts

### Code Quality Observations
- Single-file architecture (HTML + CSS + JS in one 1833-line file) will become unmaintainable as the dashboard grows. Consider splitting into separate files or a build system.
- Template literal HTML generation (lines 624-631, 757-834, etc.) is error-prone and hard to test. Consider a lightweight templating solution.
- No TypeScript or JSDoc for the JavaScript. Clinical software should have type safety.
- The `NORMAL_RANGES` object and `CRS_GRADES` object are good data-driven design. Consider externalizing all clinical reference data to a separate JSON/JS file for easier clinical validation and updates.

---

*This review was conducted from a UX design perspective focused on clinical decision support usability. It does not constitute a clinical validation or regulatory assessment. All clinical content accuracy should be verified by domain experts.*
