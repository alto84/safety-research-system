#!/usr/bin/env python3
"""
Evidence Level Classification

This module provides deterministic classification of research evidence
based on the GRADE (Grading of Recommendations Assessment, Development
and Evaluation) methodology and USPSTF evidence hierarchy.

Evidence Levels:
- I: Systematic reviews and meta-analyses
- II-1: Individual RCTs (Randomized Controlled Trials)
- II-2: Cohort studies
- II-3: Case-control studies
- III: Descriptive studies (case series, case reports, expert opinion)
"""

import re
from typing import Dict, Any, Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for keyword matching.

    Args:
        text: Input text to normalize

    Returns:
        Lowercase text with extra whitespace removed
    """
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())


def classify_evidence_level(source: Dict[str, Any]) -> str:
    """
    Classify evidence level based on study characteristics.

    This function uses a hierarchical decision tree based on GRADE methodology:
    1. Check for systematic review/meta-analysis (Level I)
    2. Check for RCT (Level II-1)
    3. Check for cohort study (Level II-2)
    4. Check for case-control study (Level II-3)
    5. Default to descriptive study (Level III)

    Args:
        source: Dictionary containing source information with keys:
            - study_type (str): Type of study (optional)
            - study_design (str): Design of study (optional)
            - title (str): Title of the study (optional)
            - abstract (str): Abstract of the study (optional)
            - quality_indicators (dict): Quality assessment (optional)

    Returns:
        Evidence level as string: "I", "II-1", "II-2", "II-3", or "III"

    Examples:
        >>> classify_evidence_level({"study_type": "systematic review"})
        'I'
        >>> classify_evidence_level({"study_type": "randomized controlled trial"})
        'II-1'
        >>> classify_evidence_level({"study_design": "cohort"})
        'II-2'
    """
    # Extract and normalize relevant fields
    study_type = normalize_text(source.get("study_type", ""))
    study_design = normalize_text(source.get("study_design", ""))
    title = normalize_text(source.get("title", ""))
    abstract = normalize_text(source.get("abstract", ""))

    # Combine all text fields for comprehensive keyword matching
    combined_text = f"{study_type} {study_design} {title} {abstract}"

    # Level I: Systematic reviews and meta-analyses
    level_i_keywords = [
        "systematic review",
        "meta-analysis",
        "meta analysis",
        "meta-analyses",
        "cochrane review",
        "systematic literature review",
        "umbrella review"
    ]

    for keyword in level_i_keywords:
        if keyword in combined_text:
            return "I"

    # Level II-1: Individual RCTs
    level_ii1_keywords = [
        "randomized controlled trial",
        "randomised controlled trial",
        "rct",
        "randomized trial",
        "randomised trial",
        "random allocation",
        "random assignment",
        "double-blind",
        "double blind",
        "placebo-controlled"
    ]

    for keyword in level_ii1_keywords:
        if keyword in combined_text:
            return "II-1"

    # Special check for "randomized" or "randomised" in title/design
    # (common indicator of RCT even without full phrase)
    if "randomized" in study_type or "randomised" in study_type:
        return "II-1"
    if "randomized" in study_design or "randomised" in study_design:
        return "II-1"

    # Level II-2: Cohort studies
    level_ii2_keywords = [
        "cohort study",
        "cohort",
        "prospective study",
        "prospective",
        "longitudinal study",
        "longitudinal",
        "follow-up study",
        "follow up study",
        "observational cohort"
    ]

    for keyword in level_ii2_keywords:
        if keyword in combined_text:
            return "II-2"

    # Level II-3: Case-control studies
    level_ii3_keywords = [
        "case-control",
        "case control",
        "case-control study",
        "case control study"
    ]

    for keyword in level_ii3_keywords:
        if keyword in combined_text:
            return "II-3"

    # Level III: Descriptive studies (default)
    # This includes case series, case reports, expert opinion, narrative reviews, etc.
    return "III"


def get_level_description(level: str) -> Dict[str, str]:
    """
    Get human-readable description of an evidence level.

    Args:
        level: Evidence level ("I", "II-1", "II-2", "II-3", or "III")

    Returns:
        Dictionary with 'name' and 'description' keys

    Examples:
        >>> desc = get_level_description("I")
        >>> desc['name']
        'Systematic reviews and meta-analyses'
    """
    descriptions = {
        "I": {
            "name": "Systematic reviews and meta-analyses",
            "description": "Evidence from systematic reviews of RCTs"
        },
        "II-1": {
            "name": "Individual RCTs",
            "description": "Evidence from well-designed RCTs"
        },
        "II-2": {
            "name": "Cohort studies",
            "description": "Evidence from well-designed cohort studies"
        },
        "II-3": {
            "name": "Case-control studies",
            "description": "Evidence from case-control studies"
        },
        "III": {
            "name": "Descriptive studies",
            "description": "Expert opinion, case series, case reports"
        }
    }

    return descriptions.get(level, {
        "name": "Unknown",
        "description": "Evidence level not recognized"
    })


def classify_with_details(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify evidence level and return detailed information.

    Args:
        source: Dictionary containing source information

    Returns:
        Dictionary containing:
            - level: Evidence level code ("I", "II-1", etc.)
            - name: Human-readable name
            - description: Description of the evidence level
            - source_info: Original source information

    Examples:
        >>> result = classify_with_details({"study_type": "systematic review"})
        >>> result['level']
        'I'
        >>> result['name']
        'Systematic reviews and meta-analyses'
    """
    level = classify_evidence_level(source)
    description = get_level_description(level)

    return {
        "level": level,
        "name": description["name"],
        "description": description["description"],
        "source_info": source
    }


if __name__ == "__main__":
    # Example usage and testing
    examples = [
        {
            "study_type": "systematic review",
            "title": "A systematic review of AI safety research"
        },
        {
            "study_type": "randomized controlled trial",
            "title": "Effects of intervention X on outcome Y"
        },
        {
            "study_design": "cohort",
            "title": "Long-term follow-up of patients"
        },
        {
            "study_type": "case-control study",
            "title": "Risk factors for disease Z"
        },
        {
            "study_type": "case series",
            "title": "Description of 10 cases"
        }
    ]

    print("Evidence Level Classification Examples:")
    print("=" * 60)

    for example in examples:
        result = classify_with_details(example)
        print(f"\nSource: {example}")
        print(f"Level: {result['level']}")
        print(f"Name: {result['name']}")
        print(f"Description: {result['description']}")
