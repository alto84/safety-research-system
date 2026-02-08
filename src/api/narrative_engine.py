"""
Template-based narrative generation engine for clinical safety narratives.

Generates structured clinical narratives from patient risk data, knowledge graph
pathways, mechanism chains, and population-level context. Uses deterministic
template/rules-based generation with a clear interface for future Claude API
integration.

The ``generate_narrative()`` and ``generate_briefing()`` functions are the
primary entry points. When Claude API integration is enabled, the
``_generate_with_claude()`` path will be used instead of templates.

Architecture note:
    This module deliberately separates data gathering (``_gather_*`` helpers)
    from text generation (``_render_*`` helpers) so that swapping in an LLM
    for the rendering step requires no changes to data gathering logic.
"""

from __future__ import annotations

import logging
from typing import Any

from src.data.knowledge.mechanisms import (
    MECHANISM_REGISTRY,
    MechanismChain,
    TherapyModality,
    get_mechanisms_for_therapy,
)
from src.data.knowledge.pathways import (
    PATHWAY_REGISTRY,
    get_pathways_for_ae,
    get_intervention_points_for_ae,
)
from src.data.knowledge.references import REFERENCES, get_reference
from src.data.knowledge.molecular_targets import (
    MOLECULAR_TARGET_REGISTRY,
    get_druggable_targets,
)
from data.sle_cart_studies import get_sle_baseline_risk

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AE category mapping (string -> enum-compatible values)
# ---------------------------------------------------------------------------

_AE_DISPLAY_MAP: dict[str, str] = {
    "CRS": "Cytokine Release Syndrome",
    "ICANS": "ICANS",
    "HLH": "HLH/MAS",
    "HLH/MAS": "HLH/MAS",
    "B_CELL_APLASIA": "B-Cell Aplasia",
}

_THERAPY_MODALITY_MAP: dict[str, str] = {
    "CAR-T (CD19)": "CAR-T (CD19)",
    "CAR-T (BCMA)": "CAR-T (BCMA)",
    "TCR-T": "TCR-T",
    "CAR-NK": "CAR-NK",
    "TIL": "TIL",
    "Gene Therapy (AAV)": "Gene Therapy (AAV)",
    "Gene Therapy (lentiviral)": "Gene Therapy (lentiviral)",
}


# ---------------------------------------------------------------------------
# Data gathering helpers
# ---------------------------------------------------------------------------

def _gather_mechanisms_for_therapy(therapy_type: str) -> list[MechanismChain]:
    """Return all mechanism chains relevant to the given therapy type."""
    results = []
    for mech in MECHANISM_REGISTRY.values():
        if mech.therapy_modality.value == therapy_type:
            results.append(mech)
    return results


def _gather_relevant_references(mechanism_chains: list[MechanismChain]) -> list[str]:
    """Collect unique PubMed IDs from mechanism chains and their pathway references."""
    refs: set[str] = set()
    for mech in mechanism_chains:
        refs.update(mech.key_references)
        for step in mech.steps:
            for intervention in step.interventions:
                # Some interventions reference PMIDs indirectly via target registry
                pass
    # Also add pathway references
    for pw in PATHWAY_REGISTRY.values():
        refs.update(pw.key_references)
        for step in pw.steps:
            refs.update(step.references)
    return sorted(refs)


def _gather_intervention_points(ae_types: list[str]) -> list[dict[str, Any]]:
    """Gather druggable intervention points for the given AE types."""
    interventions = []
    for ae in ae_types:
        steps = get_intervention_points_for_ae(ae)
        for step in steps:
            agents = list(step.intervention_agents)
            interventions.append({
                "ae_type": ae,
                "pathway_step": f"{step.source} -> {step.target}",
                "agents": agents,
                "mechanism": step.mechanism,
                "temporal_window": step.temporal_window.value,
            })
    return interventions


def _gather_timing_expectations(mechanism_chains: list[MechanismChain]) -> dict[str, str]:
    """Extract typical AE onset timing from mechanism chains."""
    timing: dict[str, str] = {}
    for mech in mechanism_chains:
        ae_name = mech.ae_category.value
        if mech.typical_onset:
            timing[ae_name] = mech.typical_onset
    return timing


def _gather_population_context() -> dict[str, Any]:
    """Gather population-level baseline risk data."""
    try:
        baseline = get_sle_baseline_risk()
        return {
            "n_patients": 47,
            "indication": "SLE",
            "crs_grade3_plus_pct": baseline.get("crs_grade3_plus", {}).get("estimate", "N/A"),
            "icans_grade3_plus_pct": baseline.get("icans_grade3_plus", {}).get("estimate", "N/A"),
            "icahs_pct": baseline.get("icahs", {}).get("estimate", "N/A"),
        }
    except Exception as exc:
        logger.warning("Failed to gather population context: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Text rendering helpers (template-based; replaceable with Claude API)
# ---------------------------------------------------------------------------

def _render_executive_summary(
    patient_id: str,
    therapy_type: str,
    ae_types: list[str],
    risk_scores: dict[str, Any] | None,
    lab_values: dict[str, float] | None,
    mechanism_chains: list[MechanismChain],
    population_ctx: dict[str, Any],
) -> str:
    """Render an executive summary paragraph."""
    # Determine risk level from scores if provided
    risk_level = "unknown"
    composite_score = None
    if risk_scores:
        risk_level = risk_scores.get("risk_level", "unknown")
        composite_score = risk_scores.get("composite_score")

    ae_list = ", ".join(_AE_DISPLAY_MAP.get(ae, ae) for ae in ae_types)

    lines = []
    lines.append(
        f"Patient {patient_id} is receiving {therapy_type} therapy. "
        f"This assessment evaluates risk for the following adverse events: {ae_list}."
    )

    if composite_score is not None:
        lines.append(
            f" The composite risk index is {composite_score:.2f} "
            f"(risk level: {risk_level.upper()}), based on ensemble biomarker scoring "
            f"using validated clinical models."
        )

    # Population context
    if population_ctx:
        n = population_ctx.get("n_patients", "N/A")
        crs_rate = population_ctx.get("crs_grade3_plus_pct", "N/A")
        icans_rate = population_ctx.get("icans_grade3_plus_pct", "N/A")
        lines.append(
            f" In the pooled SLE CAR-T dataset (n={n}), the baseline Grade 3+ CRS rate "
            f"is {crs_rate}% and Grade 3+ ICANS rate is {icans_rate}%."
        )

    # Lab value highlights
    if lab_values:
        abnormals = []
        if lab_values.get("crp", 0) > 10:
            abnormals.append(f"CRP {lab_values['crp']:.1f} mg/L (elevated)")
        if lab_values.get("ferritin", 0) > 300:
            abnormals.append(f"ferritin {lab_values['ferritin']:.0f} ng/mL (elevated)")
        if lab_values.get("ldh", 0) > 280:
            abnormals.append(f"LDH {lab_values['ldh']:.0f} U/L (elevated)")
        if lab_values.get("platelets", 999) < 150:
            abnormals.append(f"platelets {lab_values['platelets']:.0f} x10^9/L (low)")
        if abnormals:
            lines.append(
                f" Notable laboratory findings include: {'; '.join(abnormals)}."
            )

    # Timing expectations
    timing = _gather_timing_expectations(mechanism_chains)
    if timing:
        timing_parts = [f"{ae}: {onset}" for ae, onset in timing.items()]
        lines.append(
            f" Expected AE onset windows: {'; '.join(timing_parts)}."
        )

    return "".join(lines)


def _render_risk_narrative(
    risk_scores: dict[str, Any] | None,
    lab_values: dict[str, float] | None,
    mechanism_chains: list[MechanismChain],
) -> str:
    """Render a detailed risk score interpretation narrative."""
    lines = []

    if not risk_scores:
        lines.append(
            "No risk scores were provided for this narrative. To generate a detailed "
            "risk interpretation, run the /api/v1/predict endpoint first and include "
            "the scores in the narrative request."
        )
        return "\n".join(lines)

    risk_level = risk_scores.get("risk_level", "unknown")
    composite = risk_scores.get("composite_score")
    models_run = risk_scores.get("models_run", 0)
    data_completeness = risk_scores.get("data_completeness")

    lines.append(f"Risk Assessment Summary:")
    if composite is not None:
        lines.append(
            f"The ensemble scoring system produced a composite risk index of "
            f"{composite:.3f} (scale 0-1), classifying this patient as "
            f"{risk_level.upper()} risk. This composite is derived from a "
            f"confidence-weighted aggregation of {models_run} validated biomarker "
            f"scoring models."
        )

    if data_completeness is not None:
        completeness_pct = data_completeness * 100
        if completeness_pct < 50:
            lines.append(
                f"Data completeness is {completeness_pct:.0f}%, which is below "
                f"the recommended 50% threshold. The risk estimate should be "
                f"interpreted with caution as several scoring models could not "
                f"be computed due to missing inputs."
            )
        else:
            lines.append(
                f"Data completeness is {completeness_pct:.0f}%, providing "
                f"adequate input coverage for reliable risk stratification."
            )

    # Individual score interpretation
    individual_scores = risk_scores.get("individual_scores", [])
    if individual_scores:
        lines.append("\nIndividual Model Scores:")
        for score in individual_scores:
            model_name = score.get("model_name", "Unknown")
            score_val = score.get("score")
            score_risk = score.get("risk_level", "unknown")
            citation = score.get("citation", "")

            if score_val is not None:
                lines.append(
                    f"- {model_name}: {score_val:.3f} ({score_risk.upper()}). "
                    f"{_interpret_score(model_name, score_val, score_risk)}"
                    f"{f' [{citation}]' if citation else ''}"
                )

    # Contributing factors
    factors = risk_scores.get("contributing_factors", [])
    if factors:
        lines.append(
            f"\nKey contributing factors: {'; '.join(factors)}."
        )

    return "\n".join(lines)


def _interpret_score(model_name: str, score: float, risk_level: str) -> str:
    """Generate a brief clinical interpretation for a specific model score."""
    name_lower = model_name.lower()

    if "easix" in name_lower:
        if risk_level in ("high", "critical"):
            return (
                "Elevated EASIX reflects endothelial dysfunction, "
                "associated with increased CRS severity and vascular leak risk."
            )
        return "EASIX within acceptable range, suggesting preserved endothelial function."

    if "hscore" in name_lower:
        if score > 169:
            return (
                "HScore exceeds 169, the threshold with >93% sensitivity for "
                "hemophagocytic lymphohistiocytosis (HLH). Close monitoring for "
                "HLH/MAS is warranted."
            )
        return "HScore below the HLH diagnostic threshold."

    if "car" in name_lower and "hematotox" in name_lower:
        if risk_level in ("high", "critical"):
            return (
                "Elevated CAR-HEMATOTOX score indicates high risk for prolonged "
                "cytopenia post-infusion, requiring extended hematologic monitoring."
            )
        return "CAR-HEMATOTOX within low-risk range for hematologic toxicity."

    if "teachey" in name_lower:
        if risk_level in ("high", "critical"):
            return "Cytokine model predicts elevated CRS risk based on measured cytokine levels."
        return "Cytokine levels consistent with low-moderate CRS risk."

    if "hay" in name_lower:
        if risk_level in ("high", "critical"):
            return "Binary classifier indicates high probability of severe CRS."
        return "Binary classifier does not predict severe CRS."

    return ""


def _render_mechanistic_context(
    therapy_type: str,
    ae_types: list[str],
    mechanism_chains: list[MechanismChain],
) -> str:
    """Render mechanistic biology context from the knowledge graph."""
    lines = []

    if not mechanism_chains:
        lines.append(
            f"No mechanism chains are currently defined for {therapy_type} "
            f"in the knowledge graph. The knowledge base covers CAR-T CD19, "
            f"TCR-T, CAR-NK, and gene therapy modalities."
        )
        return "\n".join(lines)

    lines.append(f"Mechanistic Context for {therapy_type}:")

    for mech in mechanism_chains:
        ae_name = mech.ae_category.value
        if not any(
            ae_name == _AE_DISPLAY_MAP.get(at, at)
            for at in ae_types
        ) and not any(at.upper() in ae_name.upper() for at in ae_types):
            continue

        lines.append(f"\n{mech.name}:")
        lines.append(mech.description)

        if mech.typical_onset:
            lines.append(f"Typical onset: {mech.typical_onset}.")
        if mech.typical_duration:
            lines.append(f"Typical duration: {mech.typical_duration}.")
        if mech.incidence_range:
            lines.append(f"Published incidence: {mech.incidence_range}.")

        # Key steps with intervention points
        intervention_steps = [s for s in mech.steps if s.is_intervention_point]
        if intervention_steps:
            lines.append("Intervention points:")
            for step in intervention_steps:
                agents = ", ".join(step.interventions) if step.interventions else "none defined"
                lines.append(
                    f"  - Step {step.step_number} ({step.entity}): "
                    f"{step.action}. Available interventions: {agents}."
                )

        # Branching points
        branching_steps = [s for s in mech.steps if s.is_branching_point]
        if branching_steps:
            lines.append("Branching points (disease trajectory diverges):")
            for step in branching_steps:
                branches = ", ".join(step.branches) if step.branches else "not specified"
                lines.append(
                    f"  - Step {step.step_number} ({step.entity}): "
                    f"Possible outcomes: {branches}."
                )

        if mech.risk_factors:
            lines.append(f"Risk factors: {'; '.join(mech.risk_factors[:5])}.")

        if mech.key_references:
            refs_formatted = []
            for ref_id in mech.key_references:
                ref = get_reference(ref_id)
                if ref:
                    refs_formatted.append(
                        f"{ref.first_author} et al., {ref.journal} {ref.year} ({ref.pmid})"
                    )
                else:
                    refs_formatted.append(ref_id)
            lines.append(f"Key references: {'; '.join(refs_formatted)}.")

    # Druggable targets summary
    druggable = get_druggable_targets()
    if druggable:
        lines.append(f"\nDruggable Targets ({len(druggable)} identified):")
        for target in druggable[:5]:
            modulator_names = [m.name for m in target.modulators]
            lines.append(
                f"  - {target.name} ({target.gene_symbol}): "
                f"Modulators: {', '.join(modulator_names)}. "
                f"{target.clinical_relevance}"
            )

    return "\n".join(lines)


def _render_monitoring_recommendations(
    ae_types: list[str],
    risk_level: str,
    mechanism_chains: list[MechanismChain],
) -> str:
    """Render monitoring recommendations based on risk profile and AE timing."""
    lines = []
    lines.append("Recommended Monitoring Strategy:")

    # Timing-based monitoring
    timing = _gather_timing_expectations(mechanism_chains)

    if risk_level in ("high", "critical"):
        lines.append(
            "Given the elevated risk classification, an intensified monitoring "
            "protocol is recommended:"
        )
        lines.append("- Continuous vital sign monitoring during the acute phase (D0-D7)")
        lines.append("- CRS grading per ASTCT consensus criteria every 4-6 hours")
        lines.append("- Daily CRP, ferritin, and IL-6 levels")
        lines.append("- ICE assessment every 8-12 hours for ICANS surveillance")
        lines.append("- CBC with differential daily during acute phase")
        lines.append("- Tocilizumab and dexamethasone should be available at bedside")
    elif risk_level in ("moderate",):
        lines.append(
            "Standard monitoring with enhanced frequency is recommended:"
        )
        lines.append("- Vital signs every 4 hours during acute phase (D0-D7)")
        lines.append("- CRS grading per ASTCT consensus criteria every 6-8 hours")
        lines.append("- CRP and ferritin every 48 hours; daily if symptoms develop")
        lines.append("- ICE assessment daily for ICANS surveillance")
        lines.append("- CBC with differential every other day")
    else:
        lines.append(
            "Standard monitoring protocol is appropriate:"
        )
        lines.append("- Vital signs every 6-8 hours during acute phase (D0-D7)")
        lines.append("- CRS grading per ASTCT consensus criteria every 8-12 hours")
        lines.append("- CRP and ferritin at baseline and on days 3, 7, 14")
        lines.append("- ICE assessment daily during inpatient stay")
        lines.append("- CBC with differential twice weekly")

    # AE-specific timing
    if timing:
        lines.append("\nExpected AE onset windows for this therapy:")
        for ae, onset in timing.items():
            lines.append(f"- {ae}: {onset}")

    # Long-term follow-up
    lines.append("\nLong-term monitoring:")
    lines.append("- B-cell counts (CD19+) monthly for 6 months, then quarterly")
    lines.append("- Immunoglobulin levels monthly; IVIG replacement if IgG < 400 mg/dL")
    lines.append("- Secondary malignancy screening per FDA long-term follow-up guidelines")
    lines.append("- SLE disease activity assessment (SLEDAI-2K) quarterly")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main generation functions (public API)
# ---------------------------------------------------------------------------

def generate_narrative(
    patient_id: str,
    therapy_type: str = "CAR-T (CD19)",
    ae_types: list[str] | None = None,
    include_mechanisms: bool = True,
    include_monitoring: bool = True,
    risk_scores: dict[str, Any] | None = None,
    lab_values: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Generate a structured clinical narrative for a patient.

    This is the primary entry point for narrative generation. Currently uses
    template-based rules. The interface is designed so that Claude API
    integration can replace the ``_render_*`` functions without changing
    the data gathering logic.

    Args:
        patient_id: Patient identifier.
        therapy_type: Therapy modality string.
        ae_types: Adverse event types to include. Defaults to ["CRS", "ICANS"].
        include_mechanisms: Whether to include mechanistic pathway context.
        include_monitoring: Whether to include monitoring recommendations.
        risk_scores: Pre-computed risk scores from /api/v1/predict.
        lab_values: Current laboratory values.

    Returns:
        Dict with keys: executive_summary, risk_narrative, mechanistic_context,
        recommended_monitoring, references, sections.
    """
    if ae_types is None:
        ae_types = ["CRS", "ICANS"]

    # --- Phase 1: Data gathering ---
    mechanism_chains = _gather_mechanisms_for_therapy(therapy_type)
    all_references = _gather_relevant_references(mechanism_chains)
    population_ctx = _gather_population_context()

    # Determine risk level from scores
    risk_level = "unknown"
    if risk_scores:
        risk_level = risk_scores.get("risk_level", "unknown")

    # --- Phase 2: Text rendering (template-based; future: Claude API) ---
    executive_summary = _render_executive_summary(
        patient_id=patient_id,
        therapy_type=therapy_type,
        ae_types=ae_types,
        risk_scores=risk_scores,
        lab_values=lab_values,
        mechanism_chains=mechanism_chains,
        population_ctx=population_ctx,
    )

    risk_narrative = _render_risk_narrative(
        risk_scores=risk_scores,
        lab_values=lab_values,
        mechanism_chains=mechanism_chains,
    )

    mechanistic_context = ""
    if include_mechanisms:
        mechanistic_context = _render_mechanistic_context(
            therapy_type=therapy_type,
            ae_types=ae_types,
            mechanism_chains=mechanism_chains,
        )

    recommended_monitoring = ""
    if include_monitoring:
        recommended_monitoring = _render_monitoring_recommendations(
            ae_types=ae_types,
            risk_level=risk_level,
            mechanism_chains=mechanism_chains,
        )

    # Build additional sections
    sections = []
    if population_ctx:
        sections.append({
            "title": "Population Context",
            "content": (
                f"Based on pooled data from {population_ctx.get('n_patients', 'N/A')} "
                f"SLE patients treated with CAR-T therapy, the baseline Grade 3+ CRS "
                f"rate is {population_ctx.get('crs_grade3_plus_pct', 'N/A')}% and "
                f"Grade 3+ ICANS rate is {population_ctx.get('icans_grade3_plus_pct', 'N/A')}%. "
                f"Evidence grade: Low (small sample, early-phase trials)."
            ),
            "references": [],
        })

    return {
        "executive_summary": executive_summary,
        "risk_narrative": risk_narrative,
        "mechanistic_context": mechanistic_context,
        "recommended_monitoring": recommended_monitoring,
        "references": all_references,
        "sections": sections,
    }


def generate_briefing(
    patient_id: str,
    therapy_type: str = "CAR-T (CD19)",
    risk_scores: dict[str, Any] | None = None,
    lab_values: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Generate a comprehensive clinical briefing for a patient.

    Produces a structured briefing document with multiple sections covering
    risk assessment, mechanistic context, intervention opportunities, timing
    expectations, and monitoring recommendations.

    Args:
        patient_id: Patient identifier.
        therapy_type: Therapy modality string.
        risk_scores: Pre-computed risk scores from /api/v1/predict.
        lab_values: Current laboratory values.

    Returns:
        Dict suitable for constructing a ClinicalBriefing response.
    """
    ae_types = ["CRS", "ICANS"]

    # Gather data
    mechanism_chains = _gather_mechanisms_for_therapy(therapy_type)
    all_references = _gather_relevant_references(mechanism_chains)
    population_ctx = _gather_population_context()
    intervention_points = _gather_intervention_points(ae_types)
    timing = _gather_timing_expectations(mechanism_chains)

    risk_level = "unknown"
    composite_score = None
    if risk_scores:
        risk_level = risk_scores.get("risk_level", "unknown")
        composite_score = risk_scores.get("composite_score")

    # Build sections
    sections = []

    # 1. Risk Assessment Summary
    risk_narrative = _render_risk_narrative(risk_scores, lab_values, mechanism_chains)
    sections.append({
        "heading": "Risk Assessment",
        "body": risk_narrative,
        "data_points": {
            "composite_score": composite_score,
            "risk_level": risk_level,
            "models_run": risk_scores.get("models_run") if risk_scores else None,
        },
        "references": [],
    })

    # 2. Population Context
    if population_ctx:
        sections.append({
            "heading": "Population-Level Context",
            "body": (
                f"In the pooled SLE CAR-T dataset (n={population_ctx.get('n_patients', 'N/A')}), "
                f"the baseline Grade 3+ CRS rate is {population_ctx.get('crs_grade3_plus_pct', 'N/A')}% "
                f"and Grade 3+ ICANS rate is {population_ctx.get('icans_grade3_plus_pct', 'N/A')}%. "
                f"This patient's individual risk should be interpreted in the context of these "
                f"population-level estimates, which carry wide credible intervals due to the "
                f"limited sample size."
            ),
            "data_points": population_ctx,
            "references": [],
        })

    # 3. Mechanistic Context
    mech_text = _render_mechanistic_context(therapy_type, ae_types, mechanism_chains)
    sections.append({
        "heading": "Mechanistic Biology",
        "body": mech_text,
        "data_points": {},
        "references": [ref for ref in all_references if ref.startswith("PMID:")],
    })

    # 4. Intervention Opportunities
    if intervention_points:
        interv_lines = ["Identified pharmacological intervention points:"]
        for ip in intervention_points:
            agents_str = ", ".join(ip["agents"]) if ip["agents"] else "none"
            interv_lines.append(
                f"- {ip['ae_type']}: {ip['pathway_step']} "
                f"(window: {ip['temporal_window']}). Agents: {agents_str}."
            )
        sections.append({
            "heading": "Intervention Opportunities",
            "body": "\n".join(interv_lines),
            "data_points": {},
            "references": [],
        })

    # 5. Monitoring Recommendations
    monitoring = _render_monitoring_recommendations(
        ae_types, risk_level, mechanism_chains,
    )
    sections.append({
        "heading": "Monitoring Recommendations",
        "body": monitoring,
        "data_points": {},
        "references": [],
    })

    # 6. Laboratory Interpretation
    if lab_values:
        lab_lines = ["Current Laboratory Values:"]
        for name, val in sorted(lab_values.items()):
            lab_lines.append(f"- {name}: {val}")
        sections.append({
            "heading": "Laboratory Values",
            "body": "\n".join(lab_lines),
            "data_points": lab_values,
            "references": [],
        })

    return {
        "patient_id": patient_id,
        "therapy_type": therapy_type,
        "briefing_title": f"Clinical Safety Briefing: Patient {patient_id} ({therapy_type})",
        "risk_level": risk_level,
        "composite_score": composite_score,
        "sections": sections,
        "intervention_points": intervention_points,
        "timing_expectations": timing,
        "key_references": all_references,
    }
