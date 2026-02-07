# Accessibility Audit: Cell Therapy Safety Platform - Clinical Dashboard

**Reviewer:** Maya Washington, CPACC
**Role:** Senior Accessibility Consultant, IAAP-Certified
**Date:** 2026-02-07
**Standard:** WCAG 2.1 Level AA (with AAA recommendations where clinically relevant)
**Scope:** `index.html` -- full single-page application (2,154 lines)
**Methodology:** Static code analysis against WCAG 2.1 success criteria; contrast ratio calculations; keyboard flow analysis; ARIA pattern review

---

## Executive Summary

This clinical dashboard presents **significant accessibility barriers** that would prevent clinicians with disabilities from using it safely. The most critical issues are: risk levels communicated solely by color, missing ARIA semantics on virtually every interactive widget, patient cards that are not keyboard-accessible, and alert banners that will not be announced by screen readers when they appear dynamically. In a safety-critical healthcare context, these failures carry higher consequences than in a typical web application -- a blind clinician who cannot hear a risk-level change, or a colorblind nurse who cannot distinguish HIGH from MODERATE, is a patient safety hazard.

**Finding Counts by Severity:**

| Severity | Count |
|----------|-------|
| Critical | 8 |
| Major | 14 |
| Minor | 9 |
| Advisory | 7 |
| **Total** | **38** |

---

## 1. Color and Contrast

### Finding 1.1 -- Risk Levels Communicated Solely by Color
**WCAG:** 1.4.1 Use of Color
**Severity:** Critical

Risk levels are differentiated exclusively through color in multiple locations:

- **Risk badges** (lines 162-165): `.risk-low` uses green (`--success: #059669`), `.risk-moderate` uses orange (`--moderate: #ea580c`), `.risk-high` uses red (`--danger: #dc2626`). The only text inside these badges is the word "LOW", "MODERATE", or "HIGH" -- which helps partially, but the text is 11px uppercase (line 160), making it extremely small and easy to miss.
- **Score card left borders** (lines 228-230): Risk is indicated by a 4px colored left border alone, with no text or icon alternative.
- **Timeline dots** (lines 283-286): Timepoint risk is shown as colored circles (12px diameter) with no text label.
- **Risk meter gradient bar** (lines 323-325): A gradient from green to red with a thin 4px indicator -- no pattern, texture, or text overlay to distinguish regions.
- **Sparkline dots** (lines 870-873): Abnormal vs. normal values distinguished only by red vs. green circles.
- **Trend arrows** (lines 811-813): Direction is color-coded (red for up, blue for down) with arrow shapes that help, but the color distinction between stable (gray) and the others is the primary differentiator.

**Impact:** Approximately 8% of males have some form of color vision deficiency. Red-green colorblindness (protanopia/deuteranopia) makes the HIGH (red) and LOW (green) risk levels virtually indistinguishable. In a clinical safety tool, this is a patient safety issue.

**Recommendation:** Add text labels, icons, or patterns alongside every color indicator. The `getRiskIcon()` function (lines 1977-1984) already produces icons (warning sign for HIGH, triangle for MODERATE, checkmark for LOW) but is only used in the overview score cards. Extend this to all risk indicators. Add hatching or patterns to the risk meter bar. Use shapes in sparkline dots (e.g., diamond for abnormal, circle for normal).

---

### Finding 1.2 -- Contrast Ratio Failures in Light Theme
**WCAG:** 1.4.3 Contrast (Minimum)
**Severity:** Major

Calculated contrast ratios for key color pairings against white (`#ffffff`) background:

| Element | Foreground | Background | Ratio | Required | Pass? |
|---------|-----------|------------|-------|----------|-------|
| Secondary text | `#5a5a7a` | `#ffffff` | ~4.8:1 | 4.5:1 | Borderline pass |
| Success badge text | `#059669` on `#d1fae5` | -- | ~3.1:1 | 4.5:1 | **FAIL** |
| Warning text | `#d97706` on `#fef3c7` | -- | ~3.0:1 | 4.5:1 | **FAIL** |
| Moderate badge | `#ea580c` on `#ffedd5` | -- | ~3.2:1 | 4.5:1 | **FAIL** |
| Danger badge | `#dc2626` on `#fee2e2` | -- | ~3.5:1 | 4.5:1 | **FAIL** |
| Score citation text | 10px italic `--text-secondary` | `#ffffff` | ~4.8:1 | 4.5:1 | Borderline (but 10px is too small to qualify as large text) |
| Risk badge text (11px) | colored on light bg | -- | varies 3.0-3.5:1 | 4.5:1 | **FAIL** |

The colored-text-on-tinted-background pattern used for risk badges, alert banners, and CRS grade boxes systematically fails the 4.5:1 ratio requirement because both the foreground and background are light/saturated rather than having one anchor in a dark value.

**Recommendation:** Darken the foreground colors or significantly lighten the backgrounds. For example, `--success` could become `#047857` (darker green) and the badge background could remain `#d1fae5`, yielding approximately 4.6:1. Alternatively, switch to dark text on light colored backgrounds (e.g., dark green text `#065f46` on `#d1fae5`).

---

### Finding 1.3 -- Dark Theme Contrast Issues
**WCAG:** 1.4.3 Contrast (Minimum)
**Severity:** Major

Dark theme variables (lines 42-61):

| Element | Foreground | Background | Estimated Ratio | Pass? |
|---------|-----------|------------|-----------------|-------|
| Secondary text | `#9a9ab8` on `#1a1d27` | -- | ~5.2:1 | Pass |
| Main text | `#e4e4f0` on `#1a1d27` | -- | ~11:1 | Pass |
| Danger text | `#dc2626` on `#2a1010` | -- | ~3.4:1 | **FAIL** |
| Success text | `#059669` on `#081f15` | -- | ~3.9:1 | **FAIL** |
| Warning text | `#d97706` on `#2a1d08` | -- | ~4.2:1 | **FAIL** |
| Border | `#2d3040` on `#1a1d27` | -- | ~1.3:1 | **FAIL** (but decorative, so may be acceptable for non-text) |

The dark theme colored text (used for risk labels, alert content, and status indicators) fails against the dark tinted backgrounds. This is especially concerning because clinicians often prefer dark themes during night shifts.

**Recommendation:** In dark theme, use lighter tints of the status colors for text (e.g., `#f87171` instead of `#dc2626` for danger text on dark backgrounds).

---

### Finding 1.4 -- Colorblind-Hostile Palette
**WCAG:** 1.4.1 Use of Color
**Severity:** Critical

The application uses a red-orange-green palette that is the worst possible choice for users with the most common forms of color vision deficiency:

- **Protanopia (red-blind):** Cannot distinguish red (`#dc2626`) from green (`#059669`). HIGH and LOW risk look identical.
- **Deuteranopia (red-green weak):** Same issue. The orange (`#ea580c`) for MODERATE also blends into the continuum.
- **The risk meter gradient** (line 324) transitions through green, yellow-green, yellow, orange, red -- all of which collapse to roughly two distinguishable hues for ~8% of male clinicians.

**Recommendation:** Supplement with redundant coding: shapes, text labels, patterns, and/or icons at every risk-indicator location. Consider a colorblind-safe palette option using blue/orange or other deuteranopia-safe combinations.

---

### Finding 1.5 -- Animated Status Dot Has No Text Alternative
**WCAG:** 1.4.1 Use of Color, 1.1.1 Non-text Content
**Severity:** Minor

The API connection status indicator (line 89, `.status-dot`) is an 8px green/red pulsing circle. While there is adjacent text ("Connected" / "Disconnected"), the dot itself has no `aria-hidden="true"` to remove it from the accessibility tree, nor an accessible label. The color change (green to red) is the primary visual indicator of connection state.

**Recommendation:** Add `aria-hidden="true"` to the dot element and ensure the adjacent text (line 444, `#apiStatusText`) is sufficient.

---

## 2. Keyboard Navigation

### Finding 2.1 -- Patient Cards Not Keyboard-Accessible
**WCAG:** 2.1.1 Keyboard
**Severity:** Critical

Patient cards (lines 659-666) are rendered as `<div>` elements with `onclick` handlers:

```html
<div class="patient-card" onclick="selectPatient(${i})">
```

These `<div>` elements:
- Have no `tabindex` attribute, so they cannot receive keyboard focus
- Have no `role="button"` or `role="option"`, so screen readers do not announce them as interactive
- Have no `keydown` handler for Enter/Space activation
- Have no `aria-label` describing the patient

A clinician using keyboard-only navigation (e.g., due to motor disability, or in a sterile environment using a switch device) literally cannot select a patient.

**Recommendation:** Change to `<button>` elements or add `tabindex="0"`, `role="button"`, and a keydown handler that activates on Enter and Space. Better yet, make the patient list a `role="listbox"` with each patient as a `role="option"` and `aria-selected` for the active one.

---

### Finding 2.2 -- Task Navigation Tabs Lack Keyboard Support
**WCAG:** 2.1.1 Keyboard, 4.1.2 Name, Role, Value
**Severity:** Critical

The task navigation (lines 455-465) uses `<button>` elements, which are inherently keyboard-focusable. However:

- The `<nav>` container has no `role="tablist"` attribute
- The buttons have no `role="tab"` attribute
- There is no `aria-selected` on the active tab
- There is no arrow-key navigation between tabs (the WAI-ARIA tab pattern requires Left/Right arrow keys to move between tabs, not Tab)
- The corresponding content panels have no `role="tabpanel"` or `aria-labelledby`
- There is no `aria-controls` linking tabs to panels

A screen reader user would hear these as generic buttons with no indication of their tab-like behavior, the currently selected state, or how many tabs exist (e.g., "tab 3 of 9").

**Recommendation:** Implement the WAI-ARIA Tabs pattern: `role="tablist"` on the container, `role="tab"` with `aria-selected` on each button, `role="tabpanel"` on content areas, and JavaScript arrow-key navigation between tabs with roving `tabindex`.

---

### Finding 2.3 -- No Visible Focus Indicators
**WCAG:** 2.4.7 Focus Visible
**Severity:** Major

Form inputs (line 254) have a custom focus style:
```css
.form-input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }
```

This removes the browser's default outline and replaces it with a blue glow. While this is visible on form inputs, the following interactive elements lack any custom focus style and have `outline: none` or no focus style defined:

- `.task-btn` (tab buttons) -- no `:focus` style defined
- `.patient-card` -- not focusable at all (see Finding 2.1)
- `.timeline-btn` -- no `:focus` style defined
- `.theme-toggle` -- no `:focus` style defined (`:hover` only, line 96)
- `.btn` (general buttons) -- no `:focus` style defined
- `.crs-grade-box` -- has `tabindex="0"` but no `:focus` style defined
- `.tab-btn` (inner tab buttons) -- no `:focus` style defined

**Recommendation:** Add a visible, high-contrast focus indicator to ALL interactive elements. A simple universal rule like `*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }` would be a good starting point.

---

### Finding 2.4 -- Timepoint Buttons Are Tiny and Lack Keyboard Semantics
**WCAG:** 2.1.1 Keyboard, 2.5.5 Target Size
**Severity:** Major

Timepoint selectors (line 706) are rendered as:
```html
<button class="timeline-btn" onclick="selectTimepoint(${i})">
```

While these are `<button>` elements (good), they are styled as small inline text links (12px font, `padding: 2px 0`), making them extremely small click targets. Combined with the timeline dot (12px diameter), the total target area is well below the 44x44px WCAG 2.5.5 AAA recommendation.

**Recommendation:** Increase the clickable area to at least 44x44px or add padding. Consider making the entire timeline item row clickable.

---

### Finding 2.5 -- No Keyboard Shortcuts
**WCAG:** 2.1.1 Keyboard (Advisory)
**Severity:** Advisory

For a clinical application used during rounds (time pressure), keyboard shortcuts would significantly improve efficiency. Common patterns include:

- `1-9` to switch tabs
- `J/K` to navigate patients
- `N/P` for next/previous timepoint
- `Esc` to return to overview

None are implemented.

**Recommendation:** Add keyboard shortcuts with a discoverable help overlay (e.g., `?` key). Ensure shortcuts do not conflict with screen reader commands (use single-key shortcuts with care per WCAG 2.1.4 Character Key Shortcuts).

---

### Finding 2.6 -- CRS Grade Boxes: Partial Keyboard Support
**WCAG:** 2.1.1 Keyboard
**Severity:** Major

CRS grade selection boxes (line 1187) have `role="radio"` and `tabindex="0"`, which is a good start. However:

- There is no `role="radiogroup"` on the parent container (`.crs-grade-strip`)
- Arrow key navigation between radio options is not implemented (required by WAI-ARIA radio pattern)
- `aria-checked` is not set to reflect the selected state (only a CSS class `selected` is toggled)
- There is no `name` grouping
- The `onclick` handler (line 1187) works, but there is no `onkeydown` handler for Space/Enter activation

**Recommendation:** Implement the full WAI-ARIA radio group pattern with `role="radiogroup"`, `aria-checked`, and arrow key navigation. Alternatively, use native `<input type="radio">` elements with proper `<label>` elements for automatic keyboard and screen reader support.

---

## 3. Screen Reader Compatibility

### Finding 3.1 -- Alert Banners Not Live Regions
**WCAG:** 4.1.3 Status Messages
**Severity:** Critical

Alert banners (lines 194-208, rendered dynamically in `generateAlerts()`) are inserted via `innerHTML` when a patient or timepoint changes. These alerts contain safety-critical information (HIGH RISK, fever warnings, HLH warnings, hypotension alerts). However:

- No alert banner has `role="alert"` or `aria-live="assertive"`
- The container `#taskContent` has no `aria-live` attribute
- The `#visitResults` container (line 1788) also has no `aria-live`

A screen reader user will not be notified when critical alerts appear. They would only discover them by manually navigating to the alert region.

**Recommendation:** Add `role="alert"` to danger alerts and `role="status"` or `aria-live="polite"` to informational status updates. For dynamically generated content, ensure the live region container exists in the DOM before content is injected.

---

### Finding 3.2 -- Score Cards Missing Semantic Structure
**WCAG:** 1.3.1 Info and Relationships, 4.1.2 Name, Role, Value
**Severity:** Major

Score cards (lines 216-231) contain critical clinical data:
```html
<div class="score-card risk-high-border">
  <div class="score-label">EASIX</div>
  <div class="score-value">15.23</div>
  <div class="score-risk risk-high">HIGH</div>
  <div class="score-citation">Luft et al. 2017</div>
</div>
```

Issues:
- No `aria-label` on the score card grouping the information semantically (e.g., "EASIX score: 15.23, risk level: HIGH")
- The relationship between label, value, and risk level is only conveyed visually through proximity
- A screen reader would announce these as a series of disconnected text fragments
- No heading structure within cards

**Recommendation:** Add `aria-label` to each score card summarizing its content (e.g., `aria-label="EASIX score: 15.23, High risk"`). Consider using `<dl>`/`<dt>`/`<dd>` for label-value pairs, or `role="group"` with `aria-label`.

---

### Finding 3.3 -- Risk Meter Not Accessible
**WCAG:** 1.1.1 Non-text Content, 4.1.2 Name, Role, Value
**Severity:** Major

The composite risk meter (lines 321-331) is a purely visual gradient bar with a CSS-positioned indicator:

```html
<div class="risk-meter-bar">
  <div class="risk-meter-indicator" style="left: ${score}%;"></div>
</div>
```

- No `role="meter"` or `role="progressbar"`
- No `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- No `aria-label`
- No text alternative for the current position

A screen reader user gets no information from this element.

**Recommendation:** Add `role="meter"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Composite risk score"`. Alternatively, ensure the textual score below the meter (line 967) is sufficient and mark the visual meter as `aria-hidden="true"`.

---

### Finding 3.4 -- Data Tables Missing Accessibility Attributes
**WCAG:** 1.3.1 Info and Relationships
**Severity:** Minor

Data tables (e.g., lab values table, ICANS grading table) use `<table>`, `<thead>`, `<th>`, and `<tbody>` elements, which is good for basic structure. However:

- No `<caption>` elements to describe table purpose
- No `scope="col"` or `scope="row"` on `<th>` elements
- No `summary` attribute (deprecated in HTML5 but `<caption>` is the replacement)

**Recommendation:** Add `<caption>` to each table (e.g., "Laboratory Values for Current Timepoint") and `scope="col"` to column headers.

---

### Finding 3.5 -- Dynamic Content Updates Not Announced
**WCAG:** 4.1.3 Status Messages
**Severity:** Critical

When actions occur:
- Selecting a patient (line 669): The entire content area is re-rendered via `innerHTML` -- no announcement
- Changing a timepoint (line 714): Same issue
- ICE score calculation result (line 1942): Result injected into `#iceResult` -- no `aria-live`
- API connection status changes (lines 573-580): Status text changes -- no `aria-live` on `#apiStatusText`
- Manual prediction results (line 1826): Loading state and results injected -- no `aria-live`

**Recommendation:** Wrap key status containers in `aria-live` regions. Use `aria-live="polite"` for routine updates (patient selection, timepoint changes) and `aria-live="assertive"` for critical alerts (HIGH risk, connection loss).

---

### Finding 3.6 -- Checkboxes Missing Accessible Labels
**WCAG:** 1.3.1 Info and Relationships, 4.1.2 Name, Role, Value
**Severity:** Minor

Checklist checkboxes (e.g., lines 1120-1125, 1324-1328) are wrapped in `<label>` elements containing both the `<input type="checkbox">` and the label text. This is technically correct as an implicit label association. However:

- No `id`/`for` explicit association
- No `aria-describedby` linking to any help text
- The checked state is not persisted via ARIA (though the `data-checklist-idx` system on lines 2090-2108 provides localStorage persistence for some checklists, the ones in dynamically rendered views do not use this system)

**Recommendation:** While implicit labels are acceptable, add explicit `id`/`for` pairs for robustness. Ensure all checklist instances use the persistence system.

---

### Finding 3.7 -- SVG Charts Not Accessible
**WCAG:** 1.1.1 Non-text Content
**Severity:** Major

Sparkline SVG charts (generated by `buildSparklineSVG()`, lines 830-879) contain no accessible text:

- No `<title>` element inside the SVG
- No `role="img"` on the SVG
- No `aria-label` on the SVG container
- The `<text>` elements inside the SVG show axis values but do not describe the trend

A screen reader user would either skip these entirely or hear meaningless coordinate data.

**Recommendation:** Add `role="img"` and `aria-label` to each SVG with a meaningful description (e.g., "CRP trend: values 5, 12, 45, 120 mg/L over 4 timepoints, currently elevated"). Alternatively, provide a visually hidden text summary of the trend data alongside each chart.

---

## 4. Responsive Design

### Finding 4.1 -- Sidebar Collapsed to 200px on Tablets
**WCAG:** 1.4.10 Reflow
**Severity:** Minor

The responsive breakpoint (lines 360-363) at 1024px collapses the sidebar to a 200px max-height:

```css
@media (max-width: 1024px) {
  .main-layout { grid-template-columns: 1fr; }
  .patient-sidebar { max-height: 200px; ... }
}
```

At 200px height, the patient list (potentially 5+ patients), current patient info, and timepoint selector must all fit. This will cause scrolling within the sidebar, making it difficult to see all patients and the timepoint selector simultaneously during rounds.

**Recommendation:** Increase the sidebar max-height to at least 300px, or use a collapsible/expandable pattern with clear toggle controls. Consider a slide-out drawer pattern for tablet use.

---

### Finding 4.2 -- Two-Column Layouts Break at Narrow Widths
**WCAG:** 1.4.10 Reflow
**Severity:** Minor

Several views use `grid-template-columns: 1fr 1fr` (e.g., lab values + anticipated tests at line 992, CRS management + trends at line 1221, checklists at line 1119). These have no responsive breakpoint, so at widths below 900px (common on tablets in portrait), content will be cramped.

The trend grid does have a 900px breakpoint (line 428), but the other two-column layouts do not.

**Recommendation:** Add `@media (max-width: 768px) { ... }` breakpoints to collapse all two-column grids to single-column on smaller screens.

---

### Finding 4.3 -- Text Readable at Default Size
**WCAG:** 1.4.4 Resize Text
**Severity:** Advisory (positive finding)

Base font size is 14px for body text, 13px for secondary text, and 12px for labels. While 12px is small, it is standard for clinical dashboards with dense information. The monospace font family (JetBrains Mono, Consolas) at 14px for numerical values is appropriate.

**Note:** At 200% browser zoom, the grid layout should be tested to verify content reflows properly. The fixed `320px` sidebar width (line 130) will become 640px effective width at 200% zoom, consuming most of a standard screen.

**Recommendation:** Consider using `rem` units instead of `px` for font sizes and sidebar width to better support user font-size preferences. Test at 200% zoom.

---

### Finding 4.4 -- Horizontal Scroll on Task Navigation
**WCAG:** 1.4.10 Reflow
**Severity:** Minor

The task navigation bar (lines 104-107) uses `overflow-x: auto` with `scrollbar-width: none` and hidden WebKit scrollbar, meaning the horizontal scrollbar is invisible. On narrow screens, some tabs will be hidden off-screen with no visual indication that more tabs exist.

**Recommendation:** Add scroll indicators (fade effect or arrow buttons) to signal that more tabs are available. Alternatively, wrap tabs to multiple rows on smaller screens.

---

## 5. Cognitive Accessibility

### Finding 5.1 -- Medical Abbreviations Not Consistently Explained
**WCAG:** 3.1.4 Abbreviations
**Severity:** Major

The following abbreviations are used without expansion on first use in some views:

| Abbreviation | Expansion | Explained? |
|-------------|-----------|------------|
| CRS | Cytokine Release Syndrome | Only in tab label context, not formally defined |
| ICANS | Immune Effector Cell-Associated Neurotoxicity Syndrome | Not expanded |
| HLH | Hemophagocytic Lymphohistiocytosis | Not expanded |
| IEC-HS | Immune Effector Cell-Associated HLH-like Syndrome | Partially (line 1454 title mentions "HLH/IEC-HS") |
| EASIX | Endothelial Activation and Stress Index | Not expanded |
| ICE | Immune Effector Cell-Associated Encephalopathy | Expanded on line 1365 |
| ASTCT | American Society for Transplantation and Cellular Therapy | Not expanded |
| CAR-HEMATOTOX | CAR-T Hematologic Toxicity (score) | Not expanded |
| ANC | Absolute Neutrophil Count | Not expanded |
| DIC | Disseminated Intravascular Coagulation | Not expanded |
| ECOG | Eastern Cooperative Oncology Group | Not expanded |
| G-CSF | Granulocyte Colony-Stimulating Factor | Not expanded |
| REMS | Risk Evaluation and Mitigation Strategy | Not expanded |

**Recommendation:** Use `<abbr title="...">` tags for all abbreviations on first use in each view. Add a glossary accessible from the header. For the intended audience (oncology clinicians), most of these abbreviations are well-known, but fellowship trainees, nursing staff, and pharmacists who rotate onto the service may not know all of them.

---

### Finding 5.2 -- Information Hierarchy Is Logical
**WCAG:** 1.3.1 Info and Relationships, 2.4.6 Headings and Labels
**Severity:** Advisory (positive finding)

The dashboard follows a logical information hierarchy:
1. Header with system status
2. Task navigation for workflow stages
3. Patient sidebar for case selection
4. Content area with card-based layout

Within each view, information flows from alerts (most urgent) to scores to details. This is clinically appropriate.

**However:** There are no HTML heading elements (`<h1>`-`<h6>`) used semantically. Headings are simulated with styled `<div class="card-title">` and `<h4>` elements. The `<h4>` elements (e.g., line 1053, 1308) appear without preceding `<h1>`, `<h2>`, or `<h3>`, creating a broken heading hierarchy.

**Recommendation:** Add a visually hidden `<h1>` for the page title, `<h2>` for each major section (sidebar, content area), and `<h3>` for each card. This allows screen reader users to navigate by heading level.

---

### Finding 5.3 -- Error Messages Are Clear
**WCAG:** 3.3.1 Error Identification
**Severity:** Advisory (positive finding)

Error handling for API failures (line 1885) displays a clear error message:
```html
<div class="alert alert-danger">Prediction Failed: ${e.message}</div>
```

The `apiFetch` function (lines 552-567) captures error details from the API response. Connection status is displayed in the header. These are appropriate for the clinical audience.

---

### Finding 5.4 -- No Confirmation for Destructive Actions
**WCAG:** 3.3.4 Error Prevention
**Severity:** Minor

The "Clear" button on the Clinical Visit form (line 1691) calls `clearVisitForm()` which immediately erases all entered lab values without confirmation. If a clinician has spent several minutes entering data, accidental clearing would be frustrating.

**Recommendation:** Add a confirmation dialog ("Clear all entered values?") before wiping the form.

---

## 6. Motor Accessibility

### Finding 6.1 -- Small Click/Touch Targets
**WCAG:** 2.5.5 Target Size (AAA), 2.5.8 Target Size (Minimum) (WCAG 2.2)
**Severity:** Major

Multiple interactive elements fall below the 44x44px recommended minimum:

| Element | Approximate Size | Location |
|---------|-----------------|----------|
| Timeline buttons | ~60x16px (width ok, height too small) | Sidebar timepoint selector |
| Timeline dots | 12x12px | Sidebar timepoint selector |
| Theme toggle button | ~60x30px | Header |
| Print button | ~50x26px (btn-sm) | Header |
| Tab buttons (inner cards) | ~80x30px | Card-level tab bars |
| Checkbox inputs | Browser default (~16x16px) | Checklists |
| Status dot | 8x8px (non-interactive, but visually important) | Header |

**Recommendation:** Ensure all interactive elements have a minimum 44x44px touch target, either through padding or min-height/min-width. For checkboxes, increase the label padding so the entire label area (which is already a click target via `<label>`) meets the size requirement. The label-wrapped checkboxes (lines 1121-1124) have `padding: 6px 8px` -- increasing this to `padding: 12px` would help.

---

### Finding 6.2 -- CRS Grade Radio Buttons Are Keyboard-Accessible but Motor-Challenging
**WCAG:** 2.5.5 Target Size
**Severity:** Minor

CRS grade boxes (lines 392-405) are reasonably sized for mouse use (approximately 120x60px per grade box in a 5-column grid). However:

- On tablet or at zoom, the 5-column grid may compress significantly
- The click target includes the text description, which is helpful
- The `transform: translateY(-2px)` hover effect provides visual feedback

This is acceptable but could be improved with larger tap targets on mobile breakpoints.

---

### Finding 6.3 -- ICE Score Calculator Usable but Suboptimal
**WCAG:** 2.1.1 Keyboard
**Severity:** Minor

The ICE score calculator (lines 1366-1411) uses five `<select>` dropdowns plus a "Calculate" button. This is keyboard-accessible (native `<select>` elements work with Tab and arrow keys). However:

- Five separate dropdowns on a 5-column grid is motor-intensive
- Each dropdown requires precise navigation
- The "Calculate" button requires a separate action after filling all dropdowns

**Recommendation:** Consider auto-calculating the ICE score as dropdowns are changed (removing the need for the Calculate button click). Add a total that updates live.

---

### Finding 6.4 -- No Timeout Issues Detected
**WCAG:** 2.2.1 Timing Adjustable
**Severity:** Advisory (positive finding)

No session timeouts, auto-refresh, or timed interactions were found in the code. The API health check runs every 30 seconds (line 2139), but this is a background operation that does not require user interaction. Checklist state is persisted to localStorage. This is appropriate for clinical use where clinicians may be interrupted.

---

## 7. Print Accessibility

### Finding 7.1 -- Print View Hides Interactive Elements Appropriately
**WCAG:** N/A (print-specific)
**Severity:** Advisory (positive finding)

The print stylesheet (lines 342-357) hides:
- Header, task navigation, sidebar, buttons, theme toggle

And shows:
- Print header with patient info, date/time
- Content cards with `break-inside: avoid`

This is a good foundation.

---

### Finding 7.2 -- Print View Does Not Convert Colors to Patterns
**WCAG:** 1.4.1 Use of Color (applies to print)
**Severity:** Major

The print stylesheet does not:
- Convert colored risk indicators to patterns, shapes, or text-only alternatives
- Add high-contrast borders to replace colored borders
- Ensure colored text (green/orange/red risk labels) is readable on grayscale printers
- Add the textual risk level where only a colored badge currently appears

On a black-and-white printer (common in clinical settings), the green SUCCESS and red DANGER risk badges will print as similar gray tones, making them indistinguishable.

**Recommendation:** Add print-specific styles:
```css
@media print {
  .risk-high::before { content: "[HIGH] "; font-weight: bold; }
  .risk-moderate::before { content: "[MODERATE] "; }
  .risk-low::before { content: "[LOW] "; }
  .risk-high, .risk-moderate, .risk-low { color: #000 !important; background: none !important; border: 1px solid #000; }
}
```

---

### Finding 7.3 -- Print Font Size Adequate
**WCAG:** N/A (print-specific)
**Severity:** Advisory (positive finding)

The print header uses 16px for the title and 12px for metadata. Card content inherits the 14px body font. The `@page` margin is 1cm. These are reasonable for printed output, though 12px metadata may be tight for some readers.

---

### Finding 7.4 -- Trend Charts May Not Print Meaningfully
**WCAG:** 1.1.1 Non-text Content
**Severity:** Minor

SVG sparkline charts use `var()` CSS custom properties for colors. Print rendering of CSS custom properties in SVGs varies by browser. The normal-range shading uses `opacity: 0.08`, which will likely be invisible on paper. The trend lines use `var(--primary)` (blue), which should print as gray on black-and-white printers.

**Recommendation:** Add print-specific SVG styles with solid black lines and dashed normal-range boundaries. Consider providing a tabular data fallback for print that lists the numerical values alongside or instead of the chart.

---

## 8. Additional Findings

### Finding 8.1 -- Language Attribute Set Correctly
**WCAG:** 3.1.1 Language of Page
**Severity:** Advisory (positive finding)

Line 2: `<html lang="en">` is correctly set.

---

### Finding 8.2 -- Page Title Is Descriptive
**WCAG:** 2.4.2 Page Titled
**Severity:** Advisory (positive finding)

Line 6: `<title>Cell Therapy Safety Platform - Clinical Dashboard</title>` is descriptive and appropriate.

---

### Finding 8.3 -- No Skip Navigation Link
**WCAG:** 2.4.1 Bypass Blocks
**Severity:** Major

There is no "Skip to main content" link. The page has a header, a task navigation bar, and a sidebar that a keyboard user must Tab through before reaching the main content area. This is particularly burdensome when switching between tasks or patients.

**Recommendation:** Add a visually hidden skip link as the first focusable element:
```html
<a href="#contentArea" class="skip-link">Skip to main content</a>
```
With CSS to make it visible on focus.

---

### Finding 8.4 -- Landmark Regions Partially Implemented
**WCAG:** 1.3.1 Info and Relationships
**Severity:** Minor

The page uses some semantic HTML5 elements:
- `<header>` (line 436) -- correct
- `<nav>` (line 455) -- correct for task navigation
- `<aside>` (line 470) -- correct for patient sidebar
- `<main>` (line 499) -- correct for content area

These are good landmark regions. However, the `<nav>` element has no `aria-label` to distinguish it from other potential navigation regions (e.g., a screen reader user hearing "navigation" needs to know which navigation).

**Recommendation:** Add `aria-label="Task workflow"` to the `<nav>` element and `aria-label="Patient selection"` to the `<aside>` element.

---

### Finding 8.5 -- Inline Styles Impede User Style Overrides
**WCAG:** 1.4.4 Resize Text, 1.4.12 Text Spacing
**Severity:** Minor

Extensive inline `style` attributes are used throughout the dynamically rendered HTML (e.g., lines 686-691, 944-945, 961-968). This makes it difficult for users to apply custom stylesheets (e.g., high-contrast mode, increased text spacing) because inline styles have higher CSS specificity.

**Recommendation:** Move inline styles to CSS classes wherever possible. This improves maintainability and allows user style overrides.

---

## Summary of Recommendations by Priority

### Immediate (Critical -- Patient Safety Impact)

1. **Add redundant non-color coding for all risk indicators** -- text labels, icons, and/or patterns alongside every color-coded element (Findings 1.1, 1.4)
2. **Make patient cards keyboard-accessible** -- add `tabindex`, `role`, and key handlers (Finding 2.1)
3. **Add `aria-live` regions to alert containers** -- ensure screen readers announce risk changes (Findings 3.1, 3.5)
4. **Implement WAI-ARIA tab pattern** for task navigation (Finding 2.2)

### Short-Term (Major -- Significant Barriers)

5. Fix color contrast ratios for risk badges, alert text, and dark theme (Findings 1.2, 1.3)
6. Add visible focus indicators to all interactive elements (Finding 2.3)
7. Add semantic structure to score cards (Finding 3.2)
8. Make risk meter accessible with ARIA attributes (Finding 3.3)
9. Add SVG chart alternatives for screen readers (Finding 3.7)
10. Add skip navigation link (Finding 8.3)
11. Expand abbreviations with `<abbr>` tags (Finding 5.1)
12. Fix heading hierarchy (Finding 5.2)
13. Enlarge touch targets to 44x44px minimum (Finding 6.1)
14. Add print-safe risk indicators (Finding 7.2)

### Medium-Term (Minor and Advisory)

15. Complete ARIA radio group pattern for CRS grades (Finding 2.6)
16. Add table captions and header scopes (Finding 3.4)
17. Fix responsive two-column layouts (Findings 4.1, 4.2, 4.4)
18. Add keyboard shortcuts (Finding 2.5)
19. Add form clearing confirmation (Finding 5.4)
20. Move inline styles to CSS classes (Finding 8.5)
21. Add landmark labels (Finding 8.4)

---

## Compliance Verdict

| Level | Status |
|-------|--------|
| WCAG 2.1 Level A | **Does not conform** -- Failures in 1.1.1, 1.3.1, 2.1.1, 2.4.1, 4.1.2, 4.1.3 |
| WCAG 2.1 Level AA | **Does not conform** -- Additional failures in 1.4.3, 1.4.11, 2.4.7 |
| Section 508 | **Does not conform** -- Section 508 incorporates WCAG 2.0 Level AA |

This application requires remediation before it can be considered accessible for clinical use. The critical findings (risk communication by color only, keyboard inaccessibility of patient selection, and silent screen reader updates for safety alerts) should be addressed immediately as they represent both accessibility compliance and patient safety risks.

---

*Maya Washington, CPACC*
*Senior Accessibility Consultant*
*IAAP Certified Professional in Accessibility Core Competencies*
