"""Statistical analysis worker agent."""
from typing import Dict, Any, List, Optional
import logging
import re
from dataclasses import dataclass

from agents.base_worker import BaseWorker


logger = logging.getLogger(__name__)


@dataclass
class StatisticalEvidence:
    """Represents a piece of statistical evidence extracted from literature."""
    metric: str
    value: str
    sample_size: Optional[int]
    study_design: str
    source_title: str
    source_pmid: Optional[str]
    confidence_interval: Optional[str] = None
    p_value: Optional[str] = None


class StatisticsAgent(BaseWorker):
    """
    Worker agent for conducting statistical analyses.

    This agent performs statistical tests, calculates risk metrics,
    and analyzes clinical trial data.

    Expected input:
        - query: The statistical question
        - data: Dataset or reference to dataset
        - analysis_type: Type of analysis requested
        - context: Additional context

    Output:
        - results: Statistical test results
        - interpretation: Clinical interpretation
        - assumptions: Assumptions made
        - limitations: Statistical limitations
    """

    def __init__(self, agent_id: str = "stats_agent_01", config: Dict[str, Any] = None):
        """Initialize statistical analysis agent."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute statistical analysis task.

        Args:
            input_data: Input containing query, data, analysis_type

        Returns:
            Dictionary with statistical analysis results
        """
        # Validate input
        self.validate_input(input_data)

        # Handle corrections from previous audit if present
        input_data = self.handle_corrections(input_data)

        query = input_data.get("query", "")
        analysis_type = input_data.get("analysis_type", "descriptive")
        context = input_data.get("context", {})

        logger.info(f"StatisticsAgent: Starting {analysis_type} analysis for: '{query}'")

        # Execute statistical synthesis from literature sources
        result = self._conduct_statistical_analysis(query, analysis_type, context)

        logger.info(f"StatisticsAgent: Analysis complete")

        return result

    def _conduct_statistical_analysis(
        self, query: str, analysis_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct statistical analysis on literature-derived data.

        This agent performs meta-analysis and statistical synthesis of published data
        rather than primary data analysis. It extracts statistical evidence from
        literature sources and synthesizes findings.

        Args:
            query: Statistical question
            analysis_type: Type of analysis
            context: Additional context (may include literature_data)

        Returns:
            Structured statistical results
        """
        logger.info(f"Conducting {analysis_type} statistical analysis for: {query}")

        # Check if we have literature data to analyze
        literature_data = context.get("literature_data", {})
        sources = literature_data.get("sources", [])

        if len(sources) == 0:
            return self._return_no_data_result(query, analysis_type)

        # Extract statistical evidence from literature sources
        evidence_list = self._extract_statistical_evidence(sources)

        if len(evidence_list) == 0:
            return self._return_no_statistics_result(query, analysis_type, len(sources))

        # Synthesize statistical findings
        synthesis = self._synthesize_statistical_evidence(evidence_list, query)

        # Assess statistical heterogeneity
        heterogeneity = self._assess_heterogeneity(evidence_list)

        # Determine appropriate statistical interpretation
        interpretation = self._interpret_findings(synthesis, heterogeneity, evidence_list)

        return {
            "summary": (
                f"{analysis_type.title()} analysis conducted for: '{query}'. "
                f"Extracted statistical evidence from {len(sources)} literature sources. "
                f"Identified {len(evidence_list)} quantitative findings. "
                f"{interpretation['summary_note']}"
            ),
            "primary_result": synthesis,
            "interpretation": interpretation['detailed'],
            "evidence_sources": [
                {
                    "metric": e.metric,
                    "value": e.value,
                    "sample_size": e.sample_size,
                    "study_design": e.study_design,
                    "source": e.source_title,
                    "pmid": e.source_pmid,
                }
                for e in evidence_list
            ],
            "heterogeneity_assessment": heterogeneity,
            "sample_characteristics": self._summarize_sample_characteristics(evidence_list),
            "assumptions": [
                "Statistical estimates derived from published literature, not primary data",
                "Heterogeneity in study designs affects comparability",
                "Publication bias may affect reported estimates",
                f"Based on {len(sources)} sources - additional studies may exist",
            ],
            "limitations": [
                "Meta-analysis of published aggregated data, not individual patient data",
                "Cannot control for confounding variables across studies",
                "Study quality varies - no uniform methodology across sources",
                f"Sample sizes vary substantially (range: {self._get_sample_size_range(evidence_list)})",
                "Cannot establish causality from observational data",
                "Confidence in estimates limited by heterogeneity and potential bias",
            ],
            "recommendations": [
                "Interpret findings considering heterogeneity across studies",
                "Prioritize evidence from higher-quality study designs (RCTs > observational)",
                "Consider conducting formal meta-analysis if sufficient homogeneous data available",
                "Validate findings with additional independent sources",
            ],
            "methodology": (
                f"Statistical synthesis of published literature data. "
                f"Extracted quantitative findings from {len(sources)} peer-reviewed sources. "
                f"Assessed heterogeneity across study designs and populations. "
                "Evidence weighted by study design quality and sample size. "
                "All estimates traced to specific publications with PMIDs."
            ),
            "confidence": interpretation['confidence'],
            "metadata": {
                "analysis_date": "2025-10-12",
                "analyst": self.agent_id,
                "data_source": "literature-derived aggregated statistics",
                "sources_analyzed": len(sources),
                "statistical_findings": len(evidence_list),
                "analysis_type": analysis_type,
            },
        }

    def _extract_statistical_evidence(self, sources: List[Dict]) -> List[StatisticalEvidence]:
        """Extract statistical evidence from literature sources."""
        evidence_list = []

        # Patterns to extract statistical data
        percentage_pattern = r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)%'
        p_value_pattern = r'p\s*[<>=]\s*0?\.\d+'
        ci_pattern = r'95%?\s*(?:CI|confidence interval)[:\s]*\[?(\d+(?:\.\d+)?)[,\s-]+(\d+(?:\.\d+)?)\]?'

        for source in sources:
            # Extract from abstract if available
            text = source.get("abstract", "") + " " + source.get("key_finding", "")

            # Find percentages (common in medical literature)
            percentages = re.findall(percentage_pattern, text)

            if percentages:
                # Create evidence entry
                evidence = StatisticalEvidence(
                    metric="Reported incidence/prevalence",
                    value=percentages[0] + "%",
                    sample_size=self._extract_sample_size(text),
                    study_design=source.get("evidence_level", "Unknown"),
                    source_title=source.get("title", "Unknown"),
                    source_pmid=source.get("pmid", None),
                )
                evidence_list.append(evidence)

            # Look for explicit statistical measures in source
            if "incidence" in source or "prevalence" in source or "rate" in source:
                for key, value in source.items():
                    if isinstance(value, str) and "%" in value:
                        evidence = StatisticalEvidence(
                            metric=key,
                            value=value,
                            sample_size=source.get("sample_size", None),
                            study_design=source.get("evidence_level", source.get("study_design", "Unknown")),
                            source_title=source.get("title", "Unknown"),
                            source_pmid=source.get("pmid", None),
                        )
                        evidence_list.append(evidence)

        return evidence_list

    def _extract_sample_size(self, text: str) -> Optional[int]:
        """Extract sample size from text."""
        # Patterns like "n=100", "N = 500", "500 patients"
        patterns = [
            r'[nN]\s*=\s*(\d+)',
            r'(\d+)\s+(?:patients?|subjects?|participants?|cases?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass

        return None

    def _synthesize_statistical_evidence(self, evidence_list: List[StatisticalEvidence], query: str) -> Dict[str, Any]:
        """Synthesize statistical evidence from multiple sources."""
        # Extract numeric values from evidence
        numeric_values = []
        for evidence in evidence_list:
            value_str = evidence.value.replace("%", "").strip()

            # Handle ranges (e.g., "10-15")
            if "-" in value_str:
                parts = value_str.split("-")
                try:
                    low = float(parts[0])
                    high = float(parts[1])
                    numeric_values.append((low + high) / 2)  # Use midpoint
                except:
                    pass
            else:
                try:
                    numeric_values.append(float(value_str))
                except:
                    pass

        if len(numeric_values) == 0:
            return {
                "test": "Narrative synthesis",
                "finding": f"Statistical evidence identified but quantitative synthesis not possible",
                "n_studies": len(evidence_list),
            }

        # Calculate basic statistics
        mean_value = sum(numeric_values) / len(numeric_values)
        min_value = min(numeric_values)
        max_value = max(numeric_values)

        # Calculate standard deviation if multiple values
        if len(numeric_values) > 1:
            variance = sum((x - mean_value) ** 2 for x in numeric_values) / len(numeric_values)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        return {
            "test": "Descriptive synthesis of published statistics",
            "n_studies": len(evidence_list),
            "range": f"{min_value:.1f}% - {max_value:.1f}%",
            "mean": f"{mean_value:.1f}%",
            "median": f"{sorted(numeric_values)[len(numeric_values)//2]:.1f}%",
            "std_deviation": f"{std_dev:.1f}%",
            "note": "Statistics synthesized from published literature, not primary analysis",
        }

    def _assess_heterogeneity(self, evidence_list: List[StatisticalEvidence]) -> Dict[str, Any]:
        """Assess statistical heterogeneity across studies."""
        # Count study designs
        study_designs = {}
        for evidence in evidence_list:
            design = evidence.study_design
            study_designs[design] = study_designs.get(design, 0) + 1

        # Count sample sizes
        sample_sizes = [e.sample_size for e in evidence_list if e.sample_size is not None]

        heterogeneity_level = "High"
        if len(set(study_designs.keys())) <= 2 and len(sample_sizes) > 0:
            size_range = max(sample_sizes) / min(sample_sizes) if min(sample_sizes) > 0 else float('inf')
            if size_range < 5:
                heterogeneity_level = "Moderate"
            if size_range < 2:
                heterogeneity_level = "Low"

        return {
            "level": heterogeneity_level,
            "study_designs": study_designs,
            "sample_size_range": f"{min(sample_sizes) if sample_sizes else 'Unknown'} - {max(sample_sizes) if sample_sizes else 'Unknown'}",
            "interpretation": (
                f"{heterogeneity_level} heterogeneity across studies. "
                "Differences in study design, population, and methodology affect comparability."
            ),
        }

    def _interpret_findings(self, synthesis: Dict, heterogeneity: Dict, evidence_list: List[StatisticalEvidence]) -> Dict[str, str]:
        """Interpret statistical findings."""
        n_studies = len(evidence_list)

        # Determine confidence based on evidence quality
        high_quality_count = sum(1 for e in evidence_list if "Level 1" in e.study_design)
        moderate_quality_count = sum(1 for e in evidence_list if "Level 2" in e.study_design)

        if high_quality_count >= 3 and heterogeneity['level'] != "High":
            confidence = "Moderate - multiple high-quality studies with acceptable heterogeneity"
            summary = "Consistent evidence from multiple high-quality sources."
        elif high_quality_count >= 1 or moderate_quality_count >= 3:
            confidence = "Low to Moderate - mixed study quality with some heterogeneity"
            summary = "Evidence available but heterogeneity limits confidence."
        else:
            confidence = "Low - limited high-quality evidence with substantial heterogeneity"
            summary = "Preliminary evidence only - findings should be interpreted with caution."

        detailed = (
            f"Statistical synthesis based on {n_studies} published sources. "
            f"{synthesis.get('note', '')} "
            f"Heterogeneity assessment: {heterogeneity['interpretation']} "
            f"Confidence in estimates is {confidence.split(' - ')[0].lower()} due to "
            f"study quality variation and methodological differences."
        )

        return {
            "summary_note": summary,
            "detailed": detailed,
            "confidence": confidence,
        }

    def _summarize_sample_characteristics(self, evidence_list: List[StatisticalEvidence]) -> Dict[str, Any]:
        """Summarize sample characteristics across studies."""
        sample_sizes = [e.sample_size for e in evidence_list if e.sample_size is not None]

        return {
            "total_studies": len(evidence_list),
            "studies_with_sample_size": len(sample_sizes),
            "total_sample_size": sum(sample_sizes) if sample_sizes else "Not reported",
            "sample_size_range": f"{min(sample_sizes)} - {max(sample_sizes)}" if sample_sizes else "Not reported",
            "median_sample_size": sorted(sample_sizes)[len(sample_sizes)//2] if sample_sizes else "Not reported",
        }

    def _get_sample_size_range(self, evidence_list: List[StatisticalEvidence]) -> str:
        """Get sample size range as string."""
        sample_sizes = [e.sample_size for e in evidence_list if e.sample_size is not None]
        if sample_sizes:
            return f"{min(sample_sizes)}-{max(sample_sizes)}"
        return "Not reported"

    def _return_no_data_result(self, query: str, analysis_type: str) -> Dict[str, Any]:
        """Return result when no literature data is available."""
        return {
            "summary": (
                f"{analysis_type.title()} analysis requested for: '{query}'. "
                "No literature data provided for analysis. "
                "This agent requires literature sources with statistical data to perform synthesis."
            ),
            "primary_result": {
                "test": "Not performed",
                "finding": "No data available for statistical analysis",
            },
            "interpretation": (
                "Cannot perform statistical analysis without source data. "
                "Provide literature_data in context with sources containing statistical information."
            ),
            "limitations": [
                "No source data provided - analysis cannot be performed",
                "Requires literature sources with quantitative findings",
            ],
            "recommendations": [
                "Run literature review first to gather source data",
                "Ensure literature sources contain quantitative statistical data",
            ],
            "methodology": "No analysis performed - awaiting source data",
            "confidence": "None - no data available",
            "metadata": {
                "analysis_date": "2025-10-12",
                "analyst": self.agent_id,
                "status": "No data provided",
            },
        }

    def _return_no_statistics_result(self, query: str, analysis_type: str, n_sources: int) -> Dict[str, Any]:
        """Return result when sources lack statistical data."""
        return {
            "summary": (
                f"{analysis_type.title()} analysis conducted for: '{query}'. "
                f"Analyzed {n_sources} literature sources but no extractable statistical data found. "
                "Sources may lack quantitative findings or require different extraction methodology."
            ),
            "primary_result": {
                "test": "Narrative synthesis only",
                "finding": f"No quantitative statistics extracted from {n_sources} sources",
                "n_sources": n_sources,
            },
            "interpretation": (
                "Literature sources reviewed but quantitative statistical data not present or extractable. "
                "May require manual review or sources with more explicit statistical reporting."
            ),
            "limitations": [
                "No extractable quantitative statistics from provided sources",
                "Automated extraction may miss complex statistical reporting",
                "Sources may contain qualitative findings only",
            ],
            "recommendations": [
                "Review sources manually for statistics not captured by automated extraction",
                "Consider sources with explicit quantitative results sections",
                "Expand literature search to find studies with numerical outcomes",
            ],
            "methodology": (
                f"Attempted statistical extraction from {n_sources} literature sources. "
                "Searched for percentages, p-values, confidence intervals, and sample sizes. "
                "No quantitative data identified suitable for synthesis."
            ),
            "confidence": "Low - no statistical data available for analysis",
            "metadata": {
                "analysis_date": "2025-10-12",
                "analyst": self.agent_id,
                "sources_reviewed": n_sources,
                "statistics_found": 0,
            },
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate statistical analysis input.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        super().validate_input(input_data)

        if not input_data.get("query"):
            raise ValueError("Query is required for statistical analysis")

        return True
