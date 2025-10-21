"""
Statistical Evidence Extraction Script

This module provides deterministic regex-based extraction of statistical evidence
from medical and scientific text.

Usage:
    python extract.py <text>
    python extract.py --file <filename>
"""

import re
import sys
import json
from typing import Dict, List, Any, Optional


def extract_statistics(text: str) -> Dict[str, Any]:
    """
    Extract statistical evidence from text using regex patterns.

    This function is 100% deterministic and extracts the following statistics:
    - Hazard ratios (HR)
    - Odds ratios (OR)
    - Risk ratios (RR)
    - P-values
    - Confidence intervals (CI)
    - Sample sizes (n, N)
    - Percentages

    Args:
        text: Input text containing statistical information

    Returns:
        Dictionary containing extracted statistics with the following structure:
        {
            "hazard_ratios": [{"value": float, "context": str, "position": int}],
            "odds_ratios": [{"value": float, "context": str, "position": int}],
            "risk_ratios": [{"value": float, "context": str, "position": int}],
            "p_values": [{"value": float, "context": str, "position": int}],
            "confidence_intervals": [{"lower": float, "upper": float, "context": str, "position": int}],
            "sample_sizes": [{"value": int, "context": str, "position": int}],
            "percentages": [{"value": float, "context": str, "position": int}],
            "summary": {
                "total_statistics": int,
                "has_significance": bool,
                "has_effect_sizes": bool
            }
        }
    """

    results = {
        "hazard_ratios": [],
        "odds_ratios": [],
        "risk_ratios": [],
        "p_values": [],
        "confidence_intervals": [],
        "sample_sizes": [],
        "percentages": []
    }

    # Extract Hazard Ratios (HR)
    hr_patterns = [
        r'\bHR[\s:=]+(\d+\.?\d*)',
        r'\bhazard\s+ratio[\s:=]+(\d+\.?\d*)',
        r'\bhazard\s+ratio\s+was\s+(\d+\.?\d*)',
        r'\bHR\s*\((\d+\.?\d*)\)',
    ]
    for pattern in hr_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            results["hazard_ratios"].append({
                "value": float(match.group(1)),
                "context": context,
                "position": match.start()
            })

    # Extract Odds Ratios (OR)
    or_patterns = [
        r'\bOR[\s:=]+(\d+\.?\d*)',
        r'\bodds\s+ratio[\s:=]+(\d+\.?\d*)',
        r'\bodds\s+ratio\s+was\s+(\d+\.?\d*)',
        r'\bOR\s*\((\d+\.?\d*)\)',
    ]
    for pattern in or_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            results["odds_ratios"].append({
                "value": float(match.group(1)),
                "context": context,
                "position": match.start()
            })

    # Extract Risk Ratios (RR)
    rr_patterns = [
        r'\bRR[\s:=]+(\d+\.?\d*)',
        r'\brisk\s+ratio[\s:=]+(\d+\.?\d*)',
        r'\brisk\s+ratio\s+was\s+(\d+\.?\d*)',
        r'\bRR\s*\((\d+\.?\d*)\)',
        r'\brelative\s+risk[\s:=]+(\d+\.?\d*)',
        r'\brelative\s+risk\s+was\s+(\d+\.?\d*)',
    ]
    for pattern in rr_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            results["risk_ratios"].append({
                "value": float(match.group(1)),
                "context": context,
                "position": match.start()
            })

    # Extract P-values
    p_patterns = [
        r'\bp[\s<>=]+(\d+\.?\d*)',
        r'\bp-value[\s:=]+(\d+\.?\d*)',
        r'\bp\s*=\s*(\d+\.?\d*)',
        r'\bp\s*<\s*(\d+\.?\d*)',
        r'\(p\s*=\s*(\d+\.?\d*)\)',
        r'\(p\s*<\s*(\d+\.?\d*)\)',
    ]
    for pattern in p_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            p_val = float(match.group(1))
            results["p_values"].append({
                "value": p_val,
                "context": context,
                "position": match.start()
            })

    # Extract Confidence Intervals (CI)
    ci_patterns = [
        r'95%?\s*CI[\s:=]*\(?(\d+\.?\d*)[-–—](\d+\.?\d*)\)?',
        r'CI[\s:=]+(\d+\.?\d*)[-–—](\d+\.?\d*)',
    ]
    for pattern in ci_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            # Check if this looks like a CI (reasonable range)
            lower = float(match.group(1))
            upper = float(match.group(2))
            if lower < upper:  # Basic sanity check
                results["confidence_intervals"].append({
                    "lower": lower,
                    "upper": upper,
                    "context": context,
                    "position": match.start()
                })

    # Extract Sample Sizes
    n_patterns = [
        r'\bn[\s=]+(\d+)',
        r'\bN[\s=]+(\d+)',
        r'\bn\s*=\s*(\d+)',
        r'\bN\s*=\s*(\d+)',
        r'\(n\s*=\s*(\d+)\)',
        r'\(N\s*=\s*(\d+)\)',
        r'\bsample\s+size[\s:=]+(\d+)',
    ]
    for pattern in n_patterns:
        for match in re.finditer(pattern, text):
            context = _extract_context(text, match.start(), match.end())
            results["sample_sizes"].append({
                "value": int(match.group(1)),
                "context": context,
                "position": match.start()
            })

    # Extract Percentages
    pct_patterns = [
        r'(\d+\.?\d*)%',
        r'(\d+\.?\d*)\s*percent',
    ]
    for pattern in pct_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            results["percentages"].append({
                "value": float(match.group(1)),
                "context": context,
                "position": match.start()
            })

    # Remove duplicates (same value at same position)
    results = _deduplicate_results(results)

    # Add summary
    total_stats = sum(len(v) for v in results.values())
    has_significance = len(results["p_values"]) > 0
    has_effect_sizes = (len(results["hazard_ratios"]) > 0 or
                        len(results["odds_ratios"]) > 0 or
                        len(results["risk_ratios"]) > 0)

    results["summary"] = {
        "total_statistics": total_stats,
        "has_significance": has_significance,
        "has_effect_sizes": has_effect_sizes
    }

    return results


def _extract_context(text: str, start: int, end: int, window: int = 50) -> str:
    """
    Extract surrounding context for a match.

    Args:
        text: Full text
        start: Start position of match
        end: End position of match
        window: Number of characters to include on each side

    Returns:
        Context string with the match highlighted
    """
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    context = text[context_start:context_end].strip()

    # Replace newlines with spaces for cleaner output
    context = re.sub(r'\s+', ' ', context)

    return context


def _deduplicate_results(results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Remove duplicate extractions (same value at overlapping positions).

    This only removes true duplicates - multiple patterns matching the same text.
    It keeps legitimate multiple instances of the same value in different positions.

    Args:
        results: Dictionary of extracted statistics

    Returns:
        Deduplicated results
    """
    for key in results.keys():
        if key == "summary":
            continue

        deduplicated = []

        # Sort by position first to process in order
        sorted_items = sorted(results[key], key=lambda x: x["position"])

        for item in sorted_items:
            # Check if this overlaps with a previous extraction (within 15 characters)
            # Only mark as duplicate if BOTH value matches AND positions overlap
            is_duplicate = False
            for prev_item in deduplicated:
                if "value" in item and "value" in prev_item:
                    # Same value AND overlapping position (within 15 chars) = duplicate from different pattern
                    if (abs(item["value"] - prev_item["value"]) < 0.001 and
                        abs(item["position"] - prev_item["position"]) < 15):
                        is_duplicate = True
                        break
                elif "lower" in item and "lower" in prev_item:
                    # Same CI AND overlapping position (within 15 chars) = duplicate
                    if (abs(item["lower"] - prev_item["lower"]) < 0.001 and
                        abs(item["upper"] - prev_item["upper"]) < 0.001 and
                        abs(item["position"] - prev_item["position"]) < 15):
                        is_duplicate = True
                        break

            if not is_duplicate:
                deduplicated.append(item)

        results[key] = deduplicated

    return results


def main():
    """Command-line interface for statistical extraction."""
    if len(sys.argv) < 2:
        print("Usage: python extract.py <text>")
        print("       python extract.py --file <filename>")
        sys.exit(1)

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Error: Please provide a filename")
            sys.exit(1)
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = ' '.join(sys.argv[1:])

    results = extract_statistics(text)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
