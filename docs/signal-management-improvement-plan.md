# Signal Management Improvement Plan — Prosinertimib Patient Safety Dashboard

**Date:** 2026-03-06
**Prepared by:** Director, Signal Management (Agent Skill Critique)
**Regulatory basis:** GVP Module IX (Rev 2), CIOMS VIII, FDA Good PV Assessment (2005), ICH E2E

---

## 1. Gaps in Current Signal Detection Methodology

### 1.1 EVDAS Screening Process — Partially Addressed, Needs Formalization

**Current state:** The dashboard (Section 6) shows an EVDAS Review Status card with eRMR counts and compliance rate. This is good. However, the API endpoint (`/api/v1/psd/signals`) does not include EVDAS-specific signal outputs (SDRs — Signals of Disproportionate Reporting). The `detection_methods` list in the API response covers FAERS disproportionality and MGPS but does not separately call out EVDAS SDR review as a detection method.

**Gap:** GVP Module IX.I.3.4 requires MAHs to review EVDAS eRMRs within 30 days and to document the outcome of each SDR review (confirm as signal, dismiss with rationale, or flag for further evaluation). The dashboard shows aggregate compliance metrics but does not expose individual SDR-level tracking.

**Recommendation:**
- Add an EVDAS SDR tracking table to Section 6 showing each SDR received, the drug-event pair, the statistical score, the reviewer's assessment, and the date completed.
- Add `evdas_sdrs` to the `SignalsResponse` API schema with fields: `sdr_id`, `term`, `soc`, `evdas_score`, `review_date`, `outcome` (confirmed / dismissed / under review), `reviewer`.
- Frequency: quarterly full EVDAS query in addition to monthly eRMR review.

### 1.2 BCPNN (IC) Not Implemented in Code

**Current state:** The dashboard correctly lists BCPNN/IC as a detection method with the formula and threshold (IC025 > 0). However, the `faers_signal.py` module only implements PRR, ROR, and EBGM. There is no IC computation in the codebase.

**Gap:** CIOMS VIII recommends using multiple methods in parallel to reduce false negatives. The WHO/UMC BCPNN method is particularly important for products marketed in the EU because EudraVigilance uses IC as its primary disproportionality measure.

**Recommendation:**
- Implement `compute_ic()` in `faers_signal.py` using the Bayesian formulation: IC = log2(P_observed / P_expected) with a Beta(1,1) prior. The lower 95% credibility bound (IC025) is the signal threshold.
- Include IC/IC025 in the `FAERSSignal` dataclass and in signal classification logic.
- Add IC025 to the `SignalItem` Pydantic model in `patient_safety_routes.py`.

### 1.3 Detection Frequency Not Fully Specified

**Current state:** The `detection_methods` in the API response specifies: FAERS monthly, MGPS quarterly, clinical trial biweekly, literature weekly. This is good and exceeds minimum requirements.

**Gap:** The Signal Management Plan (SMP) document is referenced in the `director_signal_management.md` skill (sub-process 7) but does not exist as a versioned artifact. GVP Module IX.I.3 requires a documented SMP specifying detection methods, frequencies, data sources, and thresholds. Without a formal SMP, the detection schedule exists only in code and dashboard display.

**Recommendation:**
- Create a Signal Management Plan document (or represent it as a versioned configuration in the API) specifying: data sources, screening frequency, statistical methods, thresholds, responsible persons, and review schedule.
- The SMP should be version-controlled and updated annually or when material changes occur (per GVP IX.I.3.1).

### 1.4 Signal Detection Thresholds Are Generic, Not Product-Specific

**Current state:** Thresholds are standard literature values (PRR >= 2, chi2 >= 4, N >= 3). These are applied uniformly across all drug-event pairs.

**Gap:** CIOMS VIII and ICH E2E both recommend that detection thresholds be adapted to the product's risk profile. For Prosinertimib, known EGFR class effects (acneiform rash, diarrhea, stomatitis, paronychia) will generate persistent statistical signals at standard thresholds, creating noise that may obscure new safety findings.

**Recommendation:**
- Implement a two-tier threshold scheme:
  - **Standard threshold** (PRR >= 2): Applied to unexpected events (those not in the reference safety information).
  - **Elevated threshold** (PRR >= 3): Applied to known EGFR class effects that are already labeled, to detect meaningful increases above the expected background.
- Document the class-effect exclusion list in the SMP and review it annually.
- Add a `threshold_type` field to the signal tracking log (standard vs. elevated).

---

## 2. Missing Process Steps

### 2.1 PRAC Rapporteur Notification Workflow

**Current state:** The dashboard pipeline shows six stages (Detection, Validation, Analysis, Assessment, Recommendation, Action) but does not include a distinct PRAC notification step. The `head_patient_safety.md` skill mentions PRAC notification, but the dashboard and API do not track it.

**Gap:** GVP Module IX.III requires that validated signals be communicated to the PRAC Rapporteur and EMA within 15 calendar days. This is a regulatory obligation with a hard deadline that must be tracked.

**Recommendation:**
- Add a "Regulatory Notification" stage between Assessment and Recommendation in the pipeline diagram, or add a regulatory notification tracker to each signal item.
- Add fields to `SignalItem`: `prac_notification_date`, `fda_notification_date`, `prac_notification_status` (not required / pending / submitted / acknowledged).
- Add a compliance KPI: "PRAC notification within 15 days of validation — target 100%."

### 2.2 Signal Source Stratification

**Current state:** Each signal has a `source` field (e.g., "FAERS disproportionality + spontaneous cluster", "Clinical trial + spontaneous"), but these are free-text descriptions, not structured categories.

**Gap:** GVP Module IX.I.3.1 lists specific data sources that must be screened: spontaneous reports, clinical trials, published literature, and "other organized data collection systems." The current free-text approach makes it impossible to audit whether all required sources have been systematically screened for each signal.

**Recommendation:**
- Replace the free-text `source` field with a structured `sources` array using an enumerated type: `spontaneous_postmarketing`, `clinical_trial`, `literature`, `regulatory_intelligence`, `evdas`, `registry`, `social_media`.
- Add a signal source coverage matrix to the dashboard showing which sources were screened for each detection run.

### 2.3 Signal Tracking Log (Lifecycle Dates)

**Current state:** The `SignalItem` model includes `detection_date`, `status`, and `next_review`. The `recent_assessments` list in the API provides some historical tracking.

**Gap:** A complete signal tracking log per GVP Module IX should capture the full lifecycle: detection date, validation date, evaluation completion date, SMT decision date, regulatory notification date, label update date, and closure date. The current model captures only the detection date and current status — there is no audit trail of state transitions.

**Recommendation:**
- Add a `lifecycle_dates` object to `SignalItem` with: `detected`, `validated`, `evaluation_complete`, `smt_decision`, `prac_notified`, `fda_notified`, `label_updated`, `closed`.
- Add a `status_history` array to track all state transitions with timestamp, previous status, new status, and decision rationale.
- This enables cycle-time KPI calculation (detection-to-decision) directly from the data.

---

## 3. Recommended Signal Prioritization Framework

### 3.1 Current State

The dashboard assigns priority as High/Medium/Low but the criteria are not documented in the API response or the dashboard. Users cannot determine why SIG-2026-001 is HIGH while SIG-2025-019 is MEDIUM.

### 3.2 Proposed Impact x Likelihood Matrix

**Impact scoring (1-3):**
- **3 (High):** Fatal or life-threatening outcomes, no known mitigation, potential for urgent safety restriction
- **2 (Medium):** Serious but manageable (hospitalization, disability), mitigation available (dose modification, monitoring)
- **1 (Low):** Non-serious, reversible, consistent with known class pharmacology

**Likelihood scoring (1-3):**
- **3 (High):** PRR >= 2 with CI excluding 1, confirmed trend (increasing reporting rate), multiple independent sources
- **2 (Medium):** PRR >= 2 but CI overlaps 1, or single-source signal with plausible mechanism
- **1 (Low):** Sub-threshold statistics (PRR < 2), sparse data (N < 5), or known confounding

**Priority assignment:**
- **HIGH (score 6-9):** Evaluation within 15 calendar days, QPPV notification within 24 hours
- **MEDIUM (score 3-5):** Evaluation within 30 calendar days, standard SMT review
- **LOW (score 1-2):** Evaluation within 60 calendar days, routine monitoring

**Recommendation:** Add `impact_score`, `likelihood_score`, and `priority_rationale` fields to the `SignalItem` model. Display the prioritization matrix in the dashboard Section 6 with each signal plotted on it.

---

## 4. Clinical Trial Signal Detection Specifics

### 4.1 DSMB Interaction

**Current state:** The dashboard Section 10 (Clinical Trials) shows DSMB meeting schedules and SAE/SUSAR counts. However, there is no documented link between the signal detection process in Section 6 and the DSMB review process in Section 10.

**Gap:** ICH E2E requires that the pharmacovigilance plan describe how clinical trial safety data integrates with overall signal detection. The signal management process must define: (a) what data flows to the DSMB, (b) what triggers an ad-hoc DSMB meeting from the signal detection process, and (c) how DSMB recommendations feed back into signal management.

**Recommendation:**
- Add a "DSMB Signal Interaction" card to Section 6 showing: last DSMB meeting date, signals discussed, DSMB recommendations, and next scheduled meeting.
- Define triggers for ad-hoc DSMB meetings: any new HIGH-priority signal from clinical trial data, cumulative SUSAR count exceeding pre-specified threshold, or any signal suggesting increased mortality.
- Add cross-links between Section 6 (Signals) and Section 10 (Clinical Trials) for DSMB-related signals.

### 4.2 Unblinding Rules

**Current state:** Not addressed in the signal detection section. The SIG-2026-001 assessment mentions a cardiac safety review and SRC meeting but does not describe the unblinding decision.

**Gap:** Signal-level unblinding (viewing aggregate treatment arm data) is distinct from individual patient unblinding and requires specific governance. Per ICH E9(R1), aggregate unblinding for safety signal evaluation must be pre-specified in the DSMB charter or protocol.

**Recommendation:**
- Document the unblinding decision framework in the SMP: individual (PV Operations per SOP), aggregate/signal-level (DSMB authorization or Sponsor Safety Committee), study-level (only for study termination decisions).
- When a signal is evaluated using unblinded clinical trial data, record this in the signal tracking log with the authorization reference.

---

## 5. Signal Closure Criteria

### 5.1 Current State

The dashboard shows two closed signals (SIG-2025-008: closed-validated, SIG-2025-022: closed-refuted) with assessment summaries describing the rationale. However, the closure criteria are not formalized — there is no checklist of requirements that must be met before closure.

### 5.2 Recommended Closure Criteria

**For refuted signals (all required):**
1. Clinical evaluation complete with documented refutation rationale
2. Independent expert review confirming refutation (for signals that reached evaluation stage)
3. SMT review and approval of refutation
4. QPPV sign-off
5. Documented in next PBRER Section 16.3

**For validated signals (all required):**
1. Clinical evaluation complete (SAR finalized)
2. SMT decision on regulatory action documented
3. All recommended actions implemented or tracked:
   - Label update submitted (CBE-0 or Type II variation)
   - RMP amendment submitted (if applicable)
   - DHPC distributed (if applicable)
   - Risk minimization measures implemented (if applicable)
4. PRAC notification submitted (if applicable)
5. QPPV sign-off
6. Documented in next PBRER Section 16.3

**Recommendation:** Add a `closure_checklist` object to the `SignalItem` model with boolean fields for each criterion. Display a closure readiness indicator in the dashboard for signals approaching closure.

---

## 6. Cross-Functional Signal Communication

### 6.1 Current State

The dashboard shows the SMT membership (Section 6 pipeline) and the organizational chart (Section 1) identifies the signal management function. However, the communication flow from signal detection to downstream functions is not explicitly mapped.

### 6.2 Recommended Communication Matrix

| Validated Signal Triggers | Recipient Function | Required Action | Timeline |
|---|---|---|---|
| Any validated signal | QPPV | Review and sign-off on signal assessment | Within 5 business days |
| Signal requiring label change | Regulatory Affairs | Prepare variation/supplement submission | Within 30 days of SMT decision |
| Signal affecting ongoing trial B-R | Clinical Development | Protocol amendment assessment | Within 15 business days |
| Signal requiring DHPC | Medical Affairs + Regulatory | Draft DHPC, coordinate distribution | Per GVP XVI timeline |
| Signal with litigation implications | Legal | Litigation hold assessment | Within 10 business days |
| Signal affecting RMP/REMS | Risk Management | RMP amendment / REMS modification assessment | Within 30 days |
| Any new validated signal | Aggregate Reporting | Include in next PBRER/DSUR | At data lock point |

**Recommendation:** Add a "Signal Communication Log" section to the API response tracking which functions have been notified for each validated signal and their response status.

---

## 7. API Schema Enhancements Summary

The following fields should be added to the `SignalItem` Pydantic model in `patient_safety_routes.py`:

```python
# New fields for SignalItem
sources: list[str]  # structured source categories (replaces free-text source)
impact_score: int  # 1-3
likelihood_score: int  # 1-3
priority_rationale: str
ic: Optional[float] = None  # Information Component (BCPNN)
ic_lower: Optional[float] = None  # IC025
lifecycle_dates: dict[str, Optional[str]]  # detection, validation, evaluation, etc.
prac_notification_status: str  # not_required / pending / submitted / acknowledged
fda_notification_status: str
closure_checklist: Optional[dict[str, bool]] = None
```

The following should be added to `SignalsResponse`:

```python
# New fields for SignalsResponse
evdas_sdrs: list[dict]  # EVDAS SDR tracking
signal_management_plan_version: str  # e.g., "SMP v3.0, effective 2026-01-15"
source_coverage_matrix: dict  # which sources screened per detection run
prioritization_matrix: dict  # impact x likelihood definitions
```

---

## 8. Summary of Findings by Regulatory Framework

### GVP Module IX (Rev 2) Compliance
- **Compliant:** Pipeline stages, detection methods, frequency, EVDAS eRMR review, SMT governance
- **Partially compliant:** Signal tracking (missing lifecycle dates), source stratification (free-text not structured), PRAC notification (not tracked in system)
- **Gap:** Signal closure criteria not formalized, SMP not versioned as formal document, EVDAS SDR-level tracking absent

### CIOMS VIII Compliance
- **Compliant:** Multiple disproportionality methods, clinical assessment framework, case-level review
- **Partially compliant:** BCPNN listed but not implemented in code, thresholds not product-specific
- **Gap:** No signal prioritization matrix documented, no false-positive rate tracking

### FDA Good PV Assessment Compliance
- **Compliant:** FAERS screening, EBGM computation, post-marketing surveillance
- **Gap:** FDA notification pathway not tracked per signal, no structured mapping to 21 CFR 314.80/314.81 reporting obligations

### ICH E2E Compliance
- **Compliant:** Signal detection strategy described, detection methods specified
- **Gap:** DSMB interaction with signal detection not formally linked, unblinding governance not documented in signal management context
