"""
Skills Composition Example: End-to-End Literature Review Workflow

This example demonstrates how to chain multiple skills together to perform
a complete literature review with validation, classification, and extraction.

Skills used:
1. literature-search - Search PubMed for sources
2. source-authenticity-verification - Validate sources for fabrication
3. evidence-level-classification - Classify evidence hierarchy
4. statistical-evidence-extraction - Extract statistical findings

This shows the power of the skills-based architecture: each skill is
independent, testable, and composable.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import skills directly from scripts
sys.path.insert(0, str(project_root / "skills/literature/literature-search/scripts"))
sys.path.insert(0, str(project_root / "skills/audit/source_authenticity_verification/scripts"))
sys.path.insert(0, str(project_root / "skills/literature/evidence-level-classification/scripts"))
sys.path.insert(0, str(project_root / "skills/statistics/statistical-evidence-extraction/scripts"))

from search import search_pubmed
from verify import verify_source_authenticity
from classify import classify_evidence_level
from extract import extract_statistics


def run_complete_literature_review(query: str, max_results: int = 10):
    """
    Run a complete literature review workflow using composed skills.

    Args:
        query: PubMed search query
        max_results: Maximum number of results to retrieve

    Returns:
        dict: Complete analysis with all skill outputs
    """
    print("=" * 80)
    print("SKILLS COMPOSITION DEMO: Complete Literature Review Workflow")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"Max Results: {max_results}\n")

    # =========================================================================
    # STEP 1: Search PubMed for Literature
    # =========================================================================
    print("STEP 1: Searching PubMed...")
    print("-" * 80)

    try:
        sources = search_pubmed(query, max_results=max_results)
        print(f"✅ Found {len(sources)} sources from PubMed")
        for i, source in enumerate(sources[:3], 1):
            print(f"   {i}. {source.get('title', 'N/A')[:80]}...")
        if len(sources) > 3:
            print(f"   ... and {len(sources) - 3} more")
    except Exception as e:
        print(f"⚠️  Note: PubMed API may be restricted in this environment")
        print(f"   Using mock data for demonstration...")
        # Mock data for demonstration
        sources = [
            {
                'pmid': '31415927',
                'title': 'Antibody-Drug Conjugates in Interstitial Lung Disease: A Systematic Review',
                'authors': ['Johnson A', 'Smith B', 'Lee C'],
                'abstract': 'This systematic review examined ADC-associated ILD. The hazard ratio was 2.45 (95% CI: 1.23-4.87, p<0.001) with n=856 patients.',
                'publication_date': '2023-05-15',
                'study_type': 'systematic review',
                'doi': '10.1234/example',
                'url': 'https://pubmed.ncbi.nlm.nih.gov/31415927/'
            },
            {
                'pmid': '27182818',
                'title': 'Clinical Trial of Novel ADC in NSCLC Patients',
                'authors': ['Garcia M', 'Chen L'],
                'abstract': 'Randomized controlled trial showed OR=1.98 (95% CI: 1.52-2.58, p=0.001). Sample size n=423.',
                'publication_date': '2022-11-20',
                'study_type': 'randomized controlled trial',
                'doi': '10.5678/trial',
                'url': 'https://pubmed.ncbi.nlm.nih.gov/27182818/'
            }
        ]
        print(f"✅ Using {len(sources)} mock sources for demonstration")

    print()

    # =========================================================================
    # STEP 2: Verify Source Authenticity
    # =========================================================================
    print("STEP 2: Verifying source authenticity...")
    print("-" * 80)

    verification = verify_source_authenticity(sources)

    authentic_count = len(verification['authentic_sources'])
    fabricated_count = len(verification['fabricated_sources'])

    print(f"✅ Authentic sources: {authentic_count}")
    print(f"❌ Fabricated sources: {fabricated_count}")

    if verification['issues']:
        print(f"\n   Issues detected:")
        for issue in verification['issues'][:3]:
            print(f"   - {issue['category']}: {issue['description'][:70]}...")

    # Use only authentic sources going forward
    authentic_sources = verification['authentic_sources']
    print(f"\n   Proceeding with {len(authentic_sources)} authenticated sources")
    print()

    # =========================================================================
    # STEP 3: Classify Evidence Levels
    # =========================================================================
    print("STEP 3: Classifying evidence hierarchy...")
    print("-" * 80)

    classified_sources = []
    for source in authentic_sources:
        classification = classify_evidence_level(source)
        source['evidence_level'] = classification['level']
        source['evidence_description'] = classification['description']
        classified_sources.append(source)

    # Count by level
    level_counts = {}
    for source in classified_sources:
        level = source['evidence_level']
        level_counts[level] = level_counts.get(level, 0) + 1

    print("Evidence Level Distribution:")
    for level in sorted(level_counts.keys()):
        count = level_counts[level]
        print(f"   Level {level}: {count} source(s)")

    print()

    # =========================================================================
    # STEP 4: Extract Statistical Evidence
    # =========================================================================
    print("STEP 4: Extracting statistical evidence...")
    print("-" * 80)

    statistics_extracted = []
    total_stats_count = 0

    for source in classified_sources:
        abstract = source.get('abstract', '')
        if abstract:
            stats = extract_statistics(abstract)
            source['statistics'] = stats

            # Count extracted statistics
            stats_count = stats['summary']['total_statistics']
            total_stats_count += stats_count

            if stats_count > 0:
                statistics_extracted.append({
                    'pmid': source['pmid'],
                    'title': source['title'],
                    'statistics': stats
                })

    print(f"✅ Extracted {total_stats_count} statistical values from {len(statistics_extracted)} sources")

    if statistics_extracted:
        print(f"\n   Example from PMID {statistics_extracted[0]['pmid']}:")
        stats = statistics_extracted[0]['statistics']
        if stats.get('hazard_ratios'):
            print(f"   - Hazard Ratio: {stats['hazard_ratios'][0]['value']}")
        if stats.get('confidence_intervals'):
            ci = stats['confidence_intervals'][0]
            print(f"   - 95% CI: {ci['lower']}-{ci['upper']}")
        if stats.get('p_values'):
            print(f"   - P-value: {stats['p_values'][0]['value']}")
        if stats.get('sample_sizes'):
            print(f"   - Sample Size: {stats['sample_sizes'][0]['value']}")

    print()

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)

    summary = {
        'query': query,
        'total_sources_found': len(sources),
        'authentic_sources': authentic_count,
        'fabricated_sources': fabricated_count,
        'evidence_levels': level_counts,
        'statistical_values_extracted': total_stats_count,
        'sources_with_statistics': len(statistics_extracted)
    }

    print(f"\nQuery: {summary['query']}")
    print(f"Sources found: {summary['total_sources_found']}")
    print(f"Authentic: {summary['authentic_sources']}")
    print(f"Fabricated: {summary['fabricated_sources']}")
    print(f"\nEvidence Distribution:")
    for level, count in sorted(summary['evidence_levels'].items()):
        print(f"  Level {level}: {count}")
    print(f"\nStatistical Evidence:")
    print(f"  Total values extracted: {summary['statistical_values_extracted']}")
    print(f"  Sources with statistics: {summary['sources_with_statistics']}")

    print("\n" + "=" * 80)
    print("✅ COMPLETE: All skills executed successfully")
    print("=" * 80)

    return {
        'summary': summary,
        'classified_sources': classified_sources,
        'statistics': statistics_extracted,
        'verification_report': verification
    }


if __name__ == '__main__':
    # Run the complete workflow
    query = "antibody drug conjugate interstitial lung disease"
    result = run_complete_literature_review(query, max_results=10)

    print(f"\n\nResult object contains:")
    print(f"  - summary: Overview of the workflow")
    print(f"  - classified_sources: All sources with evidence levels")
    print(f"  - statistics: Extracted statistical evidence")
    print(f"  - verification_report: Source authenticity details")
    print(f"\n✅ Skills composition demonstration complete!")
