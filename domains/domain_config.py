"""Multi-domain configuration system for safety research."""
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import json


logger = logging.getLogger(__name__)


class SafetyDomain(Enum):
    """Safety assessment domains."""
    ADC_ILD = "adc_ild"
    CARDIOVASCULAR = "cardiovascular"
    HEPATOTOXICITY = "hepatotoxicity"
    NEPHROTOXICITY = "nephrotoxicity"
    QT_PROLONGATION = "qt_prolongation"
    IMMUNE_RELATED = "immune_related"


class DomainConfig:
    """
    Configuration for a specific safety domain.

    Includes:
    - Required data elements
    - Recommended analyses
    - Risk thresholds
    - Evaluation criteria
    - Domain-specific pathways
    """

    def __init__(
        self,
        domain: SafetyDomain,
        display_name: str,
        description: str,
        required_tasks: List[str],
        optional_tasks: List[str],
        risk_thresholds: Dict[str, float],
        evaluation_criteria: Dict[str, Any],
        domain_specific_data: Dict[str, Any] = None
    ):
        """
        Initialize domain configuration.

        Args:
            domain: Safety domain enum
            display_name: Human-readable domain name
            description: Domain description
            required_tasks: List of required task types
            optional_tasks: List of optional task types
            risk_thresholds: Risk level thresholds
            evaluation_criteria: Domain-specific evaluation criteria
            domain_specific_data: Additional domain-specific data
        """
        self.domain = domain
        self.display_name = display_name
        self.description = description
        self.required_tasks = required_tasks
        self.optional_tasks = optional_tasks
        self.risk_thresholds = risk_thresholds
        self.evaluation_criteria = evaluation_criteria
        self.domain_specific_data = domain_specific_data or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "domain": self.domain.value,
            "display_name": self.display_name,
            "description": self.description,
            "required_tasks": self.required_tasks,
            "optional_tasks": self.optional_tasks,
            "risk_thresholds": self.risk_thresholds,
            "evaluation_criteria": self.evaluation_criteria,
            "domain_specific_data": self.domain_specific_data,
        }


class DomainRegistry:
    """
    Registry for all available safety domain configurations.
    """

    def __init__(self):
        """Initialize domain registry."""
        self.domains: Dict[str, DomainConfig] = {}
        self._load_default_domains()

    def _load_default_domains(self) -> None:
        """Load default domain configurations."""
        # ADC-ILD Domain
        self.register_domain(DomainConfig(
            domain=SafetyDomain.ADC_ILD,
            display_name="ADC-Associated Interstitial Lung Disease",
            description="Assessment of ILD risk with antibody-drug conjugates",
            required_tasks=[
                "literature_review",
                "risk_modeling",
                "mechanistic_inference",
            ],
            optional_tasks=[
                "statistical_analysis",
            ],
            risk_thresholds={
                "low": 0.05,       # <5%
                "moderate": 0.15,  # 5-15%
                "high": 0.25,      # >15%
            },
            evaluation_criteria={
                "key_factors": [
                    "ADC payload type",
                    "Target expression in lung",
                    "Prior pulmonary disease",
                    "Combination therapy",
                ],
                "critical_pathways": [
                    "HER2 signaling",
                    "Inflammatory response",
                    "Pulmonary fibrosis",
                ],
                "assessment_framework": "Bradford Hill criteria + mechanistic analysis",
            },
            domain_specific_data={
                "high_risk_payloads": ["DM1", "DM4", "MMAE"],
                "monitoring_recommendations": "Baseline and periodic CT scans",
                "regulatory_guidance": "FDA Guidance on ADC Development",
            }
        ))

        # Cardiovascular Domain
        self.register_domain(DomainConfig(
            domain=SafetyDomain.CARDIOVASCULAR,
            display_name="Cardiovascular Safety",
            description="Assessment of cardiovascular adverse events",
            required_tasks=[
                "literature_review",
                "risk_modeling",
            ],
            optional_tasks=[
                "statistical_analysis",
                "mechanistic_inference",
            ],
            risk_thresholds={
                "low": 0.02,       # <2%
                "moderate": 0.05,  # 2-5%
                "high": 0.10,      # >10%
            },
            evaluation_criteria={
                "key_factors": [
                    "QT prolongation risk",
                    "Myocardial infarction history",
                    "Heart failure markers",
                    "Arrhythmia risk",
                ],
                "critical_pathways": [
                    "Cardiac ion channels (hERG)",
                    "Myocardial contractility",
                    "Vascular tone regulation",
                ],
                "assessment_framework": "ICH E14/S7B guidelines",
            },
            domain_specific_data={
                "high_risk_classes": [
                    "Tyrosine kinase inhibitors",
                    "Anthracyclines",
                    "Immune checkpoint inhibitors",
                ],
                "monitoring_recommendations": "ECG, troponin, BNP monitoring",
                "regulatory_guidance": "ICH E14 - QT/QTc Interval Prolongation",
            }
        ))

        # Hepatotoxicity Domain
        self.register_domain(DomainConfig(
            domain=SafetyDomain.HEPATOTOXICITY,
            display_name="Drug-Induced Liver Injury (DILI)",
            description="Assessment of hepatotoxicity risk",
            required_tasks=[
                "literature_review",
                "risk_modeling",
                "mechanistic_inference",
            ],
            optional_tasks=[
                "statistical_analysis",
            ],
            risk_thresholds={
                "low": 0.01,       # <1%
                "moderate": 0.05,  # 1-5%
                "high": 0.10,      # >10%
            },
            evaluation_criteria={
                "key_factors": [
                    "Baseline liver function",
                    "Metabolic pathway (CYP involvement)",
                    "Dose and duration",
                    "Alcohol use",
                ],
                "critical_pathways": [
                    "Hepatocyte mitochondrial function",
                    "Bile acid transport",
                    "Oxidative stress response",
                    "Immune-mediated hepatotoxicity",
                ],
                "assessment_framework": "Hy's Law + RUCAM causality assessment",
            },
            domain_specific_data={
                "high_risk_features": [
                    "Daily dose >100mg",
                    "Lipophilicity >3",
                    "Reactive metabolite formation",
                ],
                "monitoring_recommendations": "ALT, AST, bilirubin, alkaline phosphatase",
                "regulatory_guidance": "FDA DILI Guidance",
                "biomarkers": ["ALT", "AST", "Bilirubin", "miR-122"],
            }
        ))

    def register_domain(self, config: DomainConfig) -> None:
        """
        Register a domain configuration.

        Args:
            config: Domain configuration
        """
        self.domains[config.domain.value] = config
        logger.info(f"Registered domain: {config.display_name}")

    def get_domain(self, domain: str) -> Optional[DomainConfig]:
        """
        Get domain configuration.

        Args:
            domain: Domain identifier

        Returns:
            Domain configuration or None if not found
        """
        return self.domains.get(domain)

    def list_domains(self) -> List[str]:
        """
        List all available domains.

        Returns:
            List of domain identifiers
        """
        return list(self.domains.keys())

    def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """
        Get detailed domain information.

        Args:
            domain: Domain identifier

        Returns:
            Domain information dictionary
        """
        config = self.get_domain(domain)
        if not config:
            return {"error": f"Domain '{domain}' not found"}

        return config.to_dict()


class DomainTemplate:
    """
    Template for creating domain-specific cases.
    """

    def __init__(self, domain_config: DomainConfig):
        """
        Initialize domain template.

        Args:
            domain_config: Domain configuration
        """
        self.config = domain_config

    def create_case_template(
        self,
        drug_name: str,
        adverse_event: str,
        additional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a case template for this domain.

        Args:
            drug_name: Drug name
            adverse_event: Adverse event
            additional_context: Additional context

        Returns:
            Case template dictionary
        """
        context = {
            "drug_name": drug_name,
            "adverse_event": adverse_event,
            "domain": self.config.domain.value,
            "assess_risk": True,
            "assess_mechanism": True,
        }

        # Add domain-specific context
        context.update(self.config.domain_specific_data)

        # Add additional context
        if additional_context:
            context.update(additional_context)

        return {
            "title": f"{self.config.display_name} Assessment: {drug_name}",
            "question": f"What is the {adverse_event} risk associated with {drug_name}?",
            "priority": "high",
            "context": context,
            "data_sources": ["pubmed", "clinical_trials"],
            "metadata": {
                "domain": self.config.domain.value,
                "required_tasks": self.config.required_tasks,
                "optional_tasks": self.config.optional_tasks,
                "risk_thresholds": self.config.risk_thresholds,
            },
        }

    def generate_assessment_checklist(self) -> List[str]:
        """
        Generate assessment checklist for this domain.

        Returns:
            List of assessment items
        """
        checklist = [
            f"Domain: {self.config.display_name}",
            "",
            "Required Analyses:",
        ]

        for task in self.config.required_tasks:
            checklist.append(f"  - {task.replace('_', ' ').title()}")

        checklist.append("")
        checklist.append("Key Factors to Consider:")

        for factor in self.config.evaluation_criteria.get("key_factors", []):
            checklist.append(f"  - {factor}")

        checklist.append("")
        checklist.append("Risk Thresholds:")

        for level, threshold in self.config.risk_thresholds.items():
            checklist.append(f"  - {level.capitalize()}: {threshold*100:.1f}%")

        return checklist


def get_domain_template(domain: str) -> Optional[DomainTemplate]:
    """
    Get a domain template.

    Args:
        domain: Domain identifier

    Returns:
        Domain template or None if not found
    """
    registry = DomainRegistry()
    config = registry.get_domain(domain)

    if not config:
        return None

    return DomainTemplate(config)


# Example usage
if __name__ == "__main__":
    # Initialize registry
    registry = DomainRegistry()

    # List available domains
    print("Available domains:")
    for domain in registry.list_domains():
        info = registry.get_domain_info(domain)
        print(f"  - {info['display_name']}: {info['description']}")

    # Get a specific domain template
    template = get_domain_template("cardiovascular")
    if template:
        case = template.create_case_template(
            drug_name="Sunitinib",
            adverse_event="cardiac dysfunction"
        )
        print(f"\nCase template: {case['title']}")

        checklist = template.generate_assessment_checklist()
        print("\nAssessment checklist:")
        for item in checklist:
            print(item)
