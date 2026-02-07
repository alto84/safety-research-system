# Iteration 3 Accessibility Validation Report

**Validator:** WCAG 2.1 AA Compliance Review
**Date:** 2026-02-07
**File Under Review:** `src/api/static/index.html`
**Standard:** WCAG 2.1 Level A and Level AA
**Reference:** WAI-ARIA Authoring Practices 1.2

---

## Summary

Iteration 3 made meaningful progress on accessibility. Of the eight targeted fixes, six are implemented correctly. Two have implementation issues that constitute remaining WCAG violations. Additionally, the review identified four new accessibility issues introduced or carried forward in the Iteration 3 codebase.

| Verdict | Count |
|---------|-------|
| PASS    | 6     |
| FAIL    | 2     |
| New Issues Found | 4 |

---

## Fix-by-Fix Verification

### Fix 1: `role="alert"` and `aria-live="assertive"` on Danger Alert Containers

**Result: PASS**

**Location:** `renderAlertsHtml()` function (line 2093-2100)

**Implementation:**
```html
<div role="alert" aria-live="assertive" aria-atomic="false">
  <!-- danger alerts rendered here -->
</div>
```

**Analysis:**
- Danger alerts are correctly wrapped in a container with `role="alert"` and `aria-live="assertive"`. This ensures screen readers announce critical clinical alerts immediately.
- Non-danger alerts (warning, info, success) are rendered outside the live region, which is correct -- only urgent content should use `assertive`.
- `aria-atomic="false"` is explicitly set, meaning only changed nodes within the region are announced rather than the entire container. This is appropriate because multiple danger alerts can be present, and re-announcing all of them on every update would be disruptive.

**WCAG Conformance:** Satisfies 4.1.3 Status Messages (Level AA).

**Minor Note:** When content is dynamically replaced via `innerHTML`, the live region is destroyed and recreated. Most modern screen readers handle this correctly, but the most robust pattern would be to have a persistent live region in the DOM and inject content into it. This is a best-practice recommendation, not a conformance failure.

---

### Fix 2: WAI-ARIA Tabs Pattern

**Result: PASS**

**Location:** Task navigation (lines 482-494, 797-820)

**Implementation:**
```html
<nav class="task-nav" aria-label="Task workflow">
  <div role="tablist" aria-label="Clinical workflow tabs">
    <button role="tab" aria-selected="true" tabindex="0">Overview</button>
    <button role="tab" aria-selected="false" tabindex="-1">Pre-Infusion</button>
    ...
  </div>
</nav>
```

**Keyboard handler (lines 810-820):**
- ArrowRight/ArrowLeft: moves focus to next/previous tab (wrapping)
- Home: moves focus to first tab
- End: moves focus to last tab
- `activateTab()` correctly updates `aria-selected`, `tabindex`, class, and calls `focus()`

**Analysis:**
- `role="tablist"` container with descriptive `aria-label` -- correct.
- Each tab button has `role="tab"` -- correct.
- Only the active tab has `tabindex="0"`; inactive tabs have `tabindex="-1"` -- correct roving tabindex pattern.
- `aria-selected` is toggled between `"true"` and `"false"` correctly in `activateTab()` (line 800-803).
- Arrow keys, Home, and End are all handled with `preventDefault()` -- correct.
- Activation follows focus (immediate activation model) -- acceptable per WAI-ARIA Authoring Practices.

**Missing but non-blocking:** The `role="tabpanel"` on the content area (line 528) lacks an explicit `aria-labelledby` pointing to the active tab's `id`. The tabs themselves have no `id` attributes, and the tabpanel has no `aria-labelledby`. This is a best-practice gap but does not constitute a Level A or AA failure because the tabpanel is identifiable by its role and the `aria-label` on the tablist provides context.

**WCAG Conformance:** Satisfies 2.1.1 Keyboard (Level A), 4.1.2 Name, Role, Value (Level A).

---

### Fix 3: Patient Cards with `role="option"`, `tabindex="0"`, Keyboard Activation

**Result: FAIL**

**Location:** `renderPatientList()` (lines 697-711)

**Implementation:**
```html
<div id="patientList" role="listbox" aria-label="Demo Patients">
  <div class="patient-card" role="option" aria-selected="false" tabindex="0"
       aria-label="Patient Name, 62M, high risk"
       onclick="selectPatient(0)"
       onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectPatient(0)}">
  </div>
</div>
```

**Analysis:**
- `role="listbox"` with `aria-label` on the container -- correct.
- `role="option"` on each patient card -- correct.
- `aria-selected` toggled based on active state -- correct.
- `tabindex="0"` on all options -- **VIOLATION**.
- Enter and Space key activation -- correct.

**Violation: Incorrect Roving Tabindex**

Per WAI-ARIA Authoring Practices for Listbox, all options should NOT have `tabindex="0"`. The correct pattern is roving tabindex: only the currently selected (or first) option should have `tabindex="0"`, and all others should have `tabindex="-1"`. This means a keyboard user currently has to Tab through every single patient card to move past the listbox, rather than pressing Tab once to enter the listbox and using arrow keys to navigate within it.

Furthermore, the listbox is missing arrow key navigation (Up/Down). WAI-ARIA Authoring Practices require that a listbox widget support:
- Down Arrow: move focus to next option
- Up Arrow: move focus to previous option
- Home: move focus to first option
- End: move focus to last option

Currently, the only keyboard interaction is Enter/Space to select. There is no ArrowUp/ArrowDown handling.

**WCAG Violations:**
- **2.1.1 Keyboard (Level A):** The listbox widget does not support the expected keyboard interaction pattern. Users who rely on screen readers will encounter a `role="listbox"` and expect arrow key navigation, which is not provided.
- **4.1.2 Name, Role, Value (Level A):** The role implies a keyboard contract that is not fulfilled.

**Severity:** Moderate. The cards are still operable via Enter/Space and are focusable, so the content is not inaccessible. But the interaction model is non-standard for the declared role.

---

### Fix 4: Skip Navigation Link

**Result: PASS**

**Location:** Line 460, CSS lines 73-74

**Implementation:**
```html
<a href="#contentArea" class="skip-link">Skip to main content</a>
```

```css
.skip-link {
  position: absolute; top: -100px; left: 8px;
  background: var(--primary); color: #fff;
  padding: 8px 16px; z-index: 999;
  border-radius: var(--radius); font-size: 14px;
  text-decoration: none;
}
.skip-link:focus { top: 8px; }
```

**Analysis:**
- The link is the first focusable element in the DOM (appears before the header) -- correct.
- It is visually hidden off-screen and becomes visible on focus -- correct.
- The target `#contentArea` (line 528) exists as the `<main>` element -- correct.
- Contrast: white text on `--primary` (#2563eb) yields a contrast ratio of approximately 4.56:1, which passes the AA threshold of 4.5:1 for normal text (14px is below 18px, so the large text exception does not apply; however, the text is bold equivalent at 14px, which does not meet the 14pt bold large text threshold either). The ratio of 4.56:1 narrowly passes AA.
- The skip link is hidden in print CSS (`display: none !important`) -- correct, not needed in print.

**WCAG Conformance:** Satisfies 2.4.1 Bypass Blocks (Level A).

---

### Fix 5: Focus-Visible Indicators

**Result: PASS**

**Location:** Line 70

**Implementation:**
```css
*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
```

**Analysis:**
- Uses `:focus-visible` (not `:focus`), which correctly shows outlines only for keyboard navigation, not mouse clicks -- correct and user-friendly.
- `outline: 2px solid var(--primary)` where `--primary` is `#2563eb` (blue). Against the light theme background (`#ffffff`), the contrast ratio is approximately 4.56:1. Against dark theme background (`#0f1117`), the ratio is approximately 3.53:1.
- `outline-offset: 2px` ensures the outline does not overlap the element content -- good practice.
- The universal selector `*` ensures all focusable elements receive the indicator -- correct.

**Potential Issue:** The `.form-input:focus` rule (line 270) uses `outline: none` and replaces it with a `box-shadow` ring. Since `.form-input:focus` targets `:focus` (not `:focus-visible`), and the universal rule targets `:focus-visible`, there is a specificity interaction. When a form input receives keyboard focus, both `:focus` and `:focus-visible` will match. The `*:focus-visible` has lower specificity than `.form-input:focus`, so the `outline: none` from `.form-input:focus` will win, and the input will only show the box-shadow ring. The box-shadow ring (`0 0 0 3px var(--primary-light)`) uses `--primary-light` which is `#dbeafe` in light mode -- this has very low contrast against a white background (ratio approximately 1.16:1). However, combined with the border-color change to `var(--primary)`, there is a visible focus indication. This is borderline but likely passes because the border-color change itself provides sufficient indication.

**WCAG Conformance:** Satisfies 2.4.7 Focus Visible (Level AA).

---

### Fix 6: Risk Icons Beyond Color-Only Communication

**Result: PASS**

**Location:** `getRiskIcon()` function (lines 2102-2109), used in patient cards (line 708), risk meter labels (lines 1017-1019), score cards (line 1037)

**Implementation:**
```javascript
function getRiskIcon(level) {
  if (!level) return '';
  const l = level.toLowerCase();
  if (l === 'high') return '&#9888;';    // warning sign triangle
  if (l === 'moderate') return '&#9650;'; // upward triangle
  if (l === 'low') return '&#10003;';     // checkmark
  return '';
}
```

**Analysis:**
- Risk levels are no longer communicated by color alone. Each level has a distinct icon shape: checkmark (low), triangle (moderate), warning sign (high).
- The `risk-critical` CSS class also includes `font-weight: 700` and a pulsing animation as additional non-color indicators.
- On sidebar patient cards (line 708): `${getRiskIcon(risk)} ${(risk || 'unknown').toUpperCase()}` -- icon + uppercase text label.
- On score cards (line 1037-1038): icon + numeric score + uppercase risk label.
- The `aria-label` on patient cards (line 703) includes the risk level in text form.

**WCAG Conformance:** Satisfies 1.4.1 Use of Color (Level A).

**Minor Note:** The `critical` level is not handled in `getRiskIcon()` -- it returns empty string. The critical badge does have other visual differentiators (dark background, bold text, pulse animation, and the text "CRITICAL"), so this is not a conformance issue. However, adding a distinct icon for critical would improve consistency.

---

### Fix 7: Dark Theme Contrast Improvements

**Result: PASS (with caveats)**

**Location:** Lines 63-67

**Implementation:**
```css
[data-theme="dark"] .risk-low { color: #34d399; }
[data-theme="dark"] .risk-moderate { color: #fb923c; }
[data-theme="dark"] .risk-high { color: #f87171; }
[data-theme="dark"] .risk-critical { background: #7f1d1d; color: #fecaca; }
```

**Analysis (contrast ratios against dark surface `#1a1d27`):**
- `.risk-low`: `#34d399` on `#1a1d27` = approximately 7.7:1 -- **PASSES AA** (4.5:1 required for small text).
- `.risk-moderate`: `#fb923c` on `#1a1d27` = approximately 5.8:1 -- **PASSES AA**.
- `.risk-high`: `#f87171` on `#1a1d27` = approximately 5.0:1 -- **PASSES AA**.
- `.risk-critical`: `#fecaca` on `#7f1d1d` = approximately 6.2:1 -- **PASSES AA**.

**Dark theme text colors:**
- `--text: #e4e4f0` on `--bg: #0f1117` = approximately 13.8:1 -- passes.
- `--text-secondary: #9a9ab8` on `--bg: #0f1117` = approximately 5.8:1 -- passes.
- `--text-secondary: #9a9ab8` on `--surface: #1a1d27` = approximately 4.8:1 -- passes.

**WCAG Conformance:** Satisfies 1.4.3 Contrast (Minimum) (Level AA).

**Caveat:** The risk badge colors in the default (light) theme were not explicitly adjusted in Iteration 3. Checking light theme defaults:
- `.risk-low`: `#047857` on `#d1fae5` = approximately 4.7:1 -- narrowly passes AA.
- `.risk-moderate`: `#9a3412` on `#ffedd5` = approximately 5.1:1 -- passes.
- `.risk-high`: `#b91c1c` on `#fee2e2` = approximately 5.0:1 -- passes.

All light theme risk badge combinations pass AA minimum contrast.

---

### Fix 8: Print-Safe Risk Indicators

**Result: PASS**

**Location:** Lines 372-378

**Implementation:**
```css
@media print {
  .risk-low::before { content: "[LOW] "; font-weight: 700; }
  .risk-moderate::before { content: "[MOD] "; font-weight: 700; }
  .risk-high::before { content: "[HIGH] "; font-weight: 700; }
  .risk-critical::before { content: "[CRIT] "; font-weight: 700; }
  .pc-risk { background: #fff !important; color: #000 !important; border: 2px solid #000; }
  .alert { border: 2px solid #000 !important; }
}
```

**Analysis:**
- `::before` pseudo-elements inject text labels for risk levels, ensuring printed output does not rely on color.
- Risk badges are forced to black text on white background with a solid black border -- universally readable in grayscale.
- Alerts get solid black borders for visibility without color.
- The sidebar, navigation, and buttons are hidden in print -- correct, they are interactive elements not needed in print.

**WCAG Conformance:** Satisfies 1.4.1 Use of Color (Level A) in print context. Note: WCAG technically applies to web content as rendered, and print stylesheets are not formally scoped by WCAG 2.1. However, this is strong accessibility practice.

---

## Remaining WCAG Violations

### Violation 1: Listbox Missing Arrow Key Navigation (Fix 3 Failure)

**WCAG SC:** 2.1.1 Keyboard (Level A), 4.1.2 Name, Role, Value (Level A)
**Severity:** Moderate
**Location:** `renderPatientList()`, lines 697-711

**Description:** The patient list declares `role="listbox"` but does not implement the expected keyboard interaction model. Arrow key navigation (Up/Down) is not supported. All options have `tabindex="0"` instead of using roving tabindex.

**Recommendation:** Implement roving tabindex pattern: set `tabindex="0"` only on the active/first option, `tabindex="-1"` on all others. Add `keydown` handler for ArrowUp, ArrowDown, Home, End keys on the listbox or its options.

---

### Violation 2: CRS Grade Boxes Use `role="radio"` Without `radiogroup`

**WCAG SC:** 4.1.2 Name, Role, Value (Level A)
**Severity:** Moderate
**Location:** `renderCRS()`, line 1264

**Description:** The CRS grade selector boxes use `role="radio"` but are not wrapped in a `role="radiogroup"` container. The WAI-ARIA specification requires that elements with `role="radio"` be owned by (contained within) an element with `role="radiogroup"`. Without the group container, assistive technology cannot properly convey the relationship between the radio options or communicate how many options exist in the set.

Additionally:
- The radio buttons lack `aria-checked` attribute. `role="radio"` requires `aria-checked="true"` or `"false"` to communicate state. The current implementation uses a CSS class `.selected` for visual state but provides no ARIA state.
- There is no keyboard interaction for the radio group (no ArrowUp/ArrowDown/ArrowLeft/ArrowRight to cycle between options).
- `tabindex="0"` is set on all radio buttons -- should use roving tabindex (only the checked/first has `tabindex="0"`).

**Recommendation:** Wrap the grade boxes in a `div` with `role="radiogroup"` and `aria-label="CRS Grade Selection"`. Add `aria-checked` state management. Implement arrow key navigation per the WAI-ARIA radio group pattern.

---

## New Issues Identified

### New Issue 1: Form Inputs Missing Programmatic Labels

**WCAG SC:** 1.3.1 Info and Relationships (Level A), 4.1.2 Name, Role, Value (Level A)
**Severity:** High
**Location:** Clinical Visit form (lines 1807-1896), ICE score form (lines 1477-1518), Pre-Infusion form (lines 1131-1152)

**Description:** Form inputs throughout the application use visual labels (`.form-label` divs) that are not programmatically associated with their corresponding inputs. The labels use `<div class="form-label">` instead of `<label for="...">`. While some inputs have `id` attributes, no `<label>` elements reference them.

Examples:
- `<div class="form-label">Temperature<span class="unit">C</span></div>` followed by `<input id="visit_temperature" ...>` -- no `for` attribute linkage.
- The lab value inputs in the Clinical Visit form are generated dynamically with `id="visit_${key}"` but their labels are `<div>` elements.
- ICE score selects (`#iceOrientation`, `#iceNaming`, etc.) have `<div class="form-label">` labels with no programmatic association.

Screen readers will not announce the label text when the user focuses these inputs. The user will hear only "edit text" or "combobox" without context.

**Impact:** A screen reader user filling out the Clinical Visit form will not know which lab value each input corresponds to.

**Recommendation:** Replace `<div class="form-label">` with `<label class="form-label" for="inputId">` throughout all form groups, or use `aria-labelledby` on the inputs referencing the label div's `id`.

---

### New Issue 2: Checkbox Lists Missing Accessible Labels

**WCAG SC:** 1.3.1 Info and Relationships (Level A)
**Severity:** Low-Moderate
**Location:** Pre-Infusion Checklist (lines 1196-1203), Day 1 Checklist (lines 1402-1408), Discharge Criteria (lines 1751-1758)

**Description:** The checkbox items use `<label>` elements wrapping both the `<input type="checkbox">` and the text content, which is correct for implicit labeling. However, the checkboxes in the discharge criteria (lines 1752-1757) are pre-checked based on clinical logic (`${c.met ? 'checked' : ''}`) and there is no indication to screen readers that these represent system-assessed criteria versus user-checkable items.

This is a minor concern. The `<label>` wrapping pattern is technically correct for WCAG. The larger issue is that none of these checklist sections have a group label. There is no `<fieldset>`/`<legend>` or `role="group"` with `aria-label` to provide context for what the group of checkboxes represents.

**Recommendation:** Wrap each checklist group in a `<fieldset>` with a `<legend>` (e.g., "Pre-Infusion Checklist", "Day 1 Monitoring Checklist", "Discharge Readiness Criteria").

---

### New Issue 3: Status Dot Conveys Connection State by Color Alone

**WCAG SC:** 1.4.1 Use of Color (Level A)
**Severity:** Low
**Location:** Lines 102-103, 470-472, function `checkApiHealth()` (lines 604-617)

**Description:** The API connection status indicator (`.status-dot`) uses only a colored dot (green for connected, red for disconnected). The adjacent text (`#apiStatusText`) does provide a text alternative ("Connected - X models" or "Disconnected"), which mitigates the color-only issue for screen readers.

However, the status dot itself is a purely decorative `<span>` with no `aria-hidden="true"` attribute. If a screen reader encounters it, it may attempt to read it as empty content or announce the element. Adding `aria-hidden="true"` to the dot would be appropriate since the text label conveys the same information.

Additionally, the `.status-dot` has a CSS `pulse` animation that runs infinitely. While this is subtle (opacity oscillation), WCAG 2.3.1 Three Flashes or Below Threshold (Level A) should be considered. The animation only alternates opacity between 1 and 0.5, which does not constitute a "flash" per WCAG definition (requires >10% shift in relative luminance at >3 Hz). The animation runs at 0.5 Hz (2s period), so this is compliant.

**Recommendation:** Add `aria-hidden="true"` to the `.status-dot` span, and consider providing a `prefers-reduced-motion` media query to disable the pulse animation for users who have requested reduced motion.

---

### New Issue 4: Missing `prefers-reduced-motion` Accommodations

**WCAG SC:** 2.3.3 Animation from Interactions (Level AAA, advisory for AA)
**Severity:** Low (advisory, not a Level AA failure)
**Location:** Various animations throughout

**Description:** The page includes multiple CSS animations:
- `.status-dot` pulse animation (line 103) -- infinite
- `.risk-critical` pulse animation (line 180) -- infinite
- `.loading-spinner` spin animation (line 394) -- infinite
- Various `transition` properties on hover/focus states

None of these respect the `prefers-reduced-motion` media query. While WCAG 2.1 AA does not strictly require `prefers-reduced-motion` support (2.3.3 is Level AAA), it is considered best practice and is increasingly expected. The infinite animations (especially the critical risk pulse) could be distracting or nauseating for users with vestibular disorders.

**Recommendation:** Add:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Conformance Summary

### WCAG 2.1 Level A

| Success Criterion | Status | Notes |
|---|---|---|
| 1.1.1 Non-text Content | PASS | SVG logo has no alt but is decorative alongside text; risk icons are supplementary to text labels |
| 1.3.1 Info and Relationships | **FAIL** | Form inputs lack programmatic label associations (New Issue 1) |
| 1.3.2 Meaningful Sequence | PASS | DOM order matches visual order |
| 1.3.3 Sensory Characteristics | PASS | Instructions do not rely solely on shape/color |
| 1.4.1 Use of Color | PASS | Risk icons, text labels, and print prefixes supplement color |
| 2.1.1 Keyboard | **FAIL** | Listbox missing arrow key navigation (Violation 1); CRS radio group missing keyboard support (Violation 2) |
| 2.1.2 No Keyboard Trap | PASS | No traps detected; all interactive elements allow Tab to move away |
| 2.4.1 Bypass Blocks | PASS | Skip navigation link present and functional |
| 2.4.2 Page Titled | PASS | Title is descriptive: "Cell Therapy Safety Platform - Clinical Dashboard" |
| 2.4.3 Focus Order | PASS | Focus order follows logical DOM sequence |
| 2.4.4 Link Purpose | PASS | Links have descriptive text or context |
| 3.1.1 Language of Page | PASS | `<html lang="en">` present |
| 4.1.1 Parsing | PASS | No duplicate IDs detected in static markup (dynamic IDs are unique per rendering) |
| 4.1.2 Name, Role, Value | **FAIL** | CRS grade radio buttons missing radiogroup and aria-checked (Violation 2); listbox interaction contract not fulfilled (Violation 1) |

### WCAG 2.1 Level AA

| Success Criterion | Status | Notes |
|---|---|---|
| 1.4.3 Contrast (Minimum) | PASS | Both light and dark themes pass 4.5:1 for text, 3:1 for large text |
| 1.4.4 Resize Text | PASS | Layout uses CSS Grid, relative units; content reflows at 200% zoom |
| 1.4.11 Non-text Contrast | PASS | Focus indicators are 2px solid at ~4.56:1 contrast; form input borders visible |
| 2.4.7 Focus Visible | PASS | Global `*:focus-visible` rule with 2px solid outline |
| 4.1.3 Status Messages | PASS | Danger alerts use `role="alert"` with `aria-live="assertive"` |

---

## Priority Remediation Recommendations

1. **[High] Fix form label associations** -- Replace `<div class="form-label">` with `<label>` elements using `for` attributes, or add `aria-labelledby` to inputs. This affects all form views (Clinical Visit, Pre-Infusion, ICANS, CRS).

2. **[Moderate] Fix listbox keyboard navigation** -- Implement roving tabindex and ArrowUp/ArrowDown/Home/End key handlers on the patient list.

3. **[Moderate] Fix CRS grade radio group** -- Wrap in `role="radiogroup"`, add `aria-checked` state, implement arrow key navigation, apply roving tabindex.

4. **[Low] Add `prefers-reduced-motion`** -- Respect user motion preferences for all animations and transitions.

5. **[Low] Add `aria-hidden="true"` to decorative elements** -- Status dot, loading spinners, and emoji icons that duplicate adjacent text content.
