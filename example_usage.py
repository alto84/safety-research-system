"""
Example usage of the safety research system.

This script demonstrates the complete workflow:
1. Create a safety case
2. Initialize the system components
3. Process the case through the orchestrator
4. Review the final report
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models.case import Case, CaseStatus, CasePriority
from models.task import TaskType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor
from agents.orchestrator import Orchestrator
from agents.workers.literature_agent import LiteratureAgent
from agents.workers.statistics_agent import StatisticsAgent
from agents.auditors.literature_auditor import LiteratureAuditor
from agents.auditors.statistics_auditor import StatisticsAuditor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_system():
    """
    Initialize all system components.

    Returns:
        Tuple of (task_executor, audit_engine, resolution_engine, context_compressor, orchestrator)
    """
    logger.info("Initializing safety research system...")

    # Create task executor
    task_executor = TaskExecutor()

    # Create and register worker agents
    lit_worker = LiteratureAgent()
    stats_worker = StatisticsAgent()
    task_executor.register_worker(TaskType.LITERATURE_REVIEW, lit_worker)
    task_executor.register_worker(TaskType.STATISTICAL_ANALYSIS, stats_worker)

    # Create audit engine
    audit_engine = AuditEngine()

    # Create and register auditor agents
    lit_auditor = LiteratureAuditor()
    stats_auditor = StatisticsAuditor()
    audit_engine.register_auditor(TaskType.LITERATURE_REVIEW, lit_auditor)
    audit_engine.register_auditor(TaskType.STATISTICAL_ANALYSIS, stats_auditor)

    # Create resolution engine
    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine,
        max_retries=2
    )

    # Create context compressor
    context_compressor = ContextCompressor(max_summary_length=500)

    # Create orchestrator
    orchestrator = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor
    )

    logger.info("System initialization complete")
    return task_executor, audit_engine, resolution_engine, context_compressor, orchestrator


def create_example_case():
    """
    Create an example safety case.

    Returns:
        Case object
    """
    case = Case(
        title="Adverse Event Assessment: Drug X and Hepatotoxicity",
        description=(
            "Evaluate potential causal relationship between Drug X and "
            "observed hepatotoxicity events in clinical trial CT-2024-001"
        ),
        question=(
            "Is there a causal relationship between Drug X administration "
            "and hepatotoxicity observed in Phase 3 clinical trial?"
        ),
        submitter="Dr. Jane Smith",
        assigned_sme="Dr. John Doe",
        priority=CasePriority.HIGH,
        context={
            "drug_name": "Drug X",
            "adverse_event": "Hepatotoxicity",
            "trial_id": "CT-2024-001",
            "trial_phase": "Phase 3",
            "patient_population": "Adults with condition Y",
            "has_clinical_data": True,
            "event_count": 12,
            "total_patients": 500,
        },
        data_sources=[
            "pubmed",
            "clinical_trials_db",
            "internal_safety_database",
            "preclinical_studies",
        ],
    )

    logger.info(f"Created case: {case.title}")
    return case


def print_report(report: dict):
    """
    Print final report in a readable format.

    Args:
        report: Final report dictionary
    """
    print("\n" + "="*80)
    print("FINAL SAFETY RESEARCH REPORT")
    print("="*80)

    print(f"\nCase ID: {report['case_id']}")
    print(f"Title: {report['title']}")
    print(f"\nQuestion: {report['question']}")

    print(f"\n{'Executive Summary':-^80}")
    print(report['executive_summary'])

    print(f"\n{'Overall Assessment':-^80}")
    print(report['overall_assessment'])

    print(f"\n{'Confidence Level':-^80}")
    print(report['confidence_level'])

    print(f"\n{'Recommendations':-^80}")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")

    print(f"\n{'Limitations':-^80}")
    for i, lim in enumerate(report['limitations'], 1):
        print(f"{i}. {lim}")

    print(f"\n{'Metadata':-^80}")
    for key, value in report['metadata'].items():
        print(f"{key}: {value}")

    print("\n" + "="*80)


def main():
    """Main execution function."""
    try:
        # Step 1: Setup system
        task_executor, audit_engine, resolution_engine, context_compressor, orchestrator = setup_system()

        # Step 2: Create a safety case
        case = create_example_case()

        # Step 3: Process the case
        logger.info(f"Processing case {case.case_id}...")
        report = orchestrator.process_case(case)

        # Step 4: Display results
        print_report(report)

        # Step 5: Show compression statistics
        print(f"\n{'Compression Statistics':-^80}")
        print(f"Average compression ratio: {context_compressor.get_average_compression_ratio():.1f}%")

        logger.info("Example completed successfully!")

    except Exception as e:
        logger.error(f"Error in example execution: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
