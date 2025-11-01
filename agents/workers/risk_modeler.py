"""Risk modeling worker agent for quantitative risk assessment."""
from typing import Dict, Any, List, Optional
import logging
import sys
import os
import math
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class RiskModelerAgent(BaseWorker):
    """
    Worker agent for conducting quantitative risk modeling and assessment.

    This agent performs:
    - Probability calculations for adverse events
    - Risk stratification across populations
    - Quantitative risk-benefit analysis
    - Bayesian risk estimation
    - Exposure-adjusted risk metrics

    Expected input:
        - query: The risk assessment question
        - context: Context including baseline rates, exposure data, etc.
        - risk_data: Structured risk data (event counts, exposure time, etc.)
        - prior_data: Prior probability data (optional)

    Output:
        - risk_estimates: Calculated risk probabilities
        - stratification: Risk stratification by subgroups
        - confidence_intervals: Statistical confidence bounds
        - assumptions: Model assumptions and limitations
        - sensitivity_analysis: Robustness of estimates
    """

    def __init__(
        self,
        agent_id: str = "risk_modeler_01",
        config: Dict[str, Any] = None
    ):
        """
        Initialize risk modeling agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute risk modeling task.

        Args:
            input_data: Input containing query, risk_data, context

        Returns:
            Dictionary with risk modeling results
        """
        # Validate input
        self.validate_input(input_data)

        # Handle corrections from previous audit if present
        input_data = self.handle_corrections(input_data)

        query = input_data.get("query", "")
        context = input_data.get("context", {})
        risk_data = input_data.get("risk_data", {})
        prior_data = input_data.get("prior_data", {})

        logger.info(f"RiskModelerAgent: Starting risk modeling for query: '{query}'")
        logger.info(f"RiskModelerAgent: Risk data keys: {list(risk_data.keys())}")

        # Execute risk modeling
        result = self._conduct_risk_modeling(query, risk_data, prior_data, context)

        logger.info(f"RiskModelerAgent: Modeling complete")

        return result

    def _conduct_risk_modeling(
        self,
        query: str,
        risk_data: Dict[str, Any],
        prior_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct quantitative risk modeling.

        Args:
            query: Risk assessment question
            risk_data: Structured risk data
            prior_data: Prior probability data
            context: Additional context

        Returns:
            Structured risk modeling results
        """
        # Extract key data elements
        events = risk_data.get("events", 0)
        total_population = risk_data.get("total_population", 0)
        person_years = risk_data.get("person_years", 0)

        # Calculate risk estimates
        risk_estimates = self._calculate_risk_estimates(
            events, total_population, person_years
        )

        # Perform risk stratification if subgroup data available
        stratification = self._stratify_risk(risk_data.get("subgroups", []))

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            events, total_population
        )

        # Bayesian risk estimation with priors
        bayesian_estimates = self._bayesian_risk_estimation(
            events, total_population, prior_data
        )

        # Sensitivity analysis
        sensitivity = self._sensitivity_analysis(risk_estimates, context)

        # Generate summary
        summary = self._generate_summary(
            query, risk_estimates, stratification, confidence_intervals
        )

        return {
            "summary": summary,
            "risk_estimates": risk_estimates,
            "stratification": stratification,
            "confidence_intervals": confidence_intervals,
            "bayesian_estimates": bayesian_estimates,
            "sensitivity_analysis": sensitivity,
            "key_findings": self._extract_key_findings(
                risk_estimates, stratification, confidence_intervals
            ),
            "confidence": self._assess_confidence(
                events, total_population, risk_data
            ),
            "limitations": self._identify_limitations(risk_data, context),
            "assumptions": self._document_assumptions(risk_data, context),
            "methodology": self._document_methodology(
                events, total_population, person_years
            ),
            "metadata": {
                "analysis_date": datetime.utcnow().isoformat(),
                "events_analyzed": events,
                "population_size": total_population,
                "person_years": person_years,
                "model_version": self.version,
            },
        }

    def _calculate_risk_estimates(
        self,
        events: int,
        total_population: int,
        person_years: float
    ) -> Dict[str, Any]:
        """
        Calculate various risk metrics.

        Args:
            events: Number of adverse events
            total_population: Total population at risk
            person_years: Total person-years of exposure

        Returns:
            Dictionary of risk estimates
        """
        estimates = {}

        # Absolute risk (crude incidence)
        if total_population > 0:
            absolute_risk = events / total_population
            estimates["absolute_risk"] = {
                "value": absolute_risk,
                "percentage": absolute_risk * 100,
                "interpretation": self._interpret_absolute_risk(absolute_risk)
            }

        # Incidence rate (per person-years)
        if person_years > 0:
            incidence_rate = events / person_years
            estimates["incidence_rate"] = {
                "value": incidence_rate,
                "per_1000_py": incidence_rate * 1000,
                "per_100000_py": incidence_rate * 100000,
                "interpretation": self._interpret_incidence_rate(incidence_rate)
            }

        # Number needed to harm (NNH)
        if total_population > 0 and events > 0:
            nnh = total_population / events
            estimates["number_needed_to_harm"] = {
                "value": nnh,
                "interpretation": (
                    f"One adverse event expected per {nnh:.1f} exposed individuals"
                )
            }

        return estimates

    def _stratify_risk(self, subgroups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform risk stratification across subgroups.

        Args:
            subgroups: List of subgroup data dictionaries

        Returns:
            Risk stratification results
        """
        if not subgroups:
            return {
                "stratified": False,
                "message": "No subgroup data available for stratification"
            }

        stratification_results = []

        for subgroup in subgroups:
            name = subgroup.get("name", "Unknown")
            events = subgroup.get("events", 0)
            population = subgroup.get("population", 0)

            if population > 0:
                risk = events / population
                stratification_results.append({
                    "subgroup": name,
                    "events": events,
                    "population": population,
                    "risk": risk,
                    "percentage": risk * 100,
                    "risk_category": self._categorize_risk_level(risk)
                })

        # Sort by risk (highest to lowest)
        stratification_results.sort(key=lambda x: x["risk"], reverse=True)

        return {
            "stratified": True,
            "subgroups": stratification_results,
            "highest_risk_group": stratification_results[0] if stratification_results else None,
            "lowest_risk_group": stratification_results[-1] if stratification_results else None,
        }

    def _calculate_confidence_intervals(
        self,
        events: int,
        total_population: int,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Calculate confidence intervals for risk estimates.

        Uses Wilson score method for binomial proportions.

        Args:
            events: Number of events
            total_population: Total population
            confidence_level: Confidence level (default 0.95 for 95% CI)

        Returns:
            Confidence interval results
        """
        if total_population == 0 or events < 0:
            return {
                "method": "Wilson score",
                "confidence_level": confidence_level,
                "error": "Invalid data for CI calculation"
            }

        # Wilson score interval for binomial proportion
        p = events / total_population
        n = total_population

        # Z-score for confidence level
        z = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%

        denominator = 1 + (z**2) / n
        center = (p + (z**2) / (2*n)) / denominator
        margin = (z / denominator) * math.sqrt(p*(1-p)/n + (z**2)/(4*n*n))

        lower = max(0, center - margin)
        upper = min(1, center + margin)

        return {
            "method": "Wilson score",
            "confidence_level": confidence_level,
            "point_estimate": p,
            "lower_bound": lower,
            "upper_bound": upper,
            "lower_bound_percentage": lower * 100,
            "upper_bound_percentage": upper * 100,
            "interpretation": (
                f"95% CI: [{lower*100:.2f}%, {upper*100:.2f}%] - "
                f"True risk likely falls within this range"
            )
        }

    def _bayesian_risk_estimation(
        self,
        events: int,
        total_population: int,
        prior_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform Bayesian risk estimation incorporating prior data.

        Uses Beta-Binomial conjugate prior.

        Args:
            events: Observed events
            total_population: Total population
            prior_data: Prior distribution parameters

        Returns:
            Bayesian risk estimates
        """
        # Extract prior parameters (default to non-informative prior)
        alpha_prior = prior_data.get("alpha", 1)  # Beta prior alpha
        beta_prior = prior_data.get("beta", 1)    # Beta prior beta

        # Update with observed data (Beta-Binomial conjugate)
        alpha_posterior = alpha_prior + events
        beta_posterior = beta_prior + (total_population - events)

        # Posterior mean (Bayesian point estimate)
        posterior_mean = alpha_posterior / (alpha_posterior + beta_posterior)

        # Credible interval (Bayesian analog of confidence interval)
        # Using simple approximation
        posterior_variance = (
            (alpha_posterior * beta_posterior) /
            ((alpha_posterior + beta_posterior)**2 * (alpha_posterior + beta_posterior + 1))
        )
        posterior_sd = math.sqrt(posterior_variance)

        # 95% credible interval (approximate)
        credible_lower = max(0, posterior_mean - 1.96 * posterior_sd)
        credible_upper = min(1, posterior_mean + 1.96 * posterior_sd)

        return {
            "method": "Beta-Binomial conjugate prior",
            "prior": {
                "alpha": alpha_prior,
                "beta": beta_prior,
                "prior_mean": alpha_prior / (alpha_prior + beta_prior),
            },
            "posterior": {
                "alpha": alpha_posterior,
                "beta": beta_posterior,
                "posterior_mean": posterior_mean,
                "posterior_percentage": posterior_mean * 100,
            },
            "credible_interval_95": {
                "lower": credible_lower,
                "upper": credible_upper,
                "lower_percentage": credible_lower * 100,
                "upper_percentage": credible_upper * 100,
            },
            "interpretation": (
                f"Bayesian estimate: {posterior_mean*100:.2f}% "
                f"(95% credible interval: [{credible_lower*100:.2f}%, {credible_upper*100:.2f}%])"
            ),
            "note": (
                "Non-informative prior used" if alpha_prior == 1 and beta_prior == 1
                else f"Informative prior: Beta({alpha_prior}, {beta_prior})"
            )
        }

    def _sensitivity_analysis(
        self,
        risk_estimates: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on risk estimates.

        Args:
            risk_estimates: Calculated risk estimates
            context: Context data

        Returns:
            Sensitivity analysis results
        """
        sensitivity = {
            "assumptions_tested": [],
            "robustness": "Moderate"
        }

        # Test assumption: missing data
        missing_data_fraction = context.get("missing_data_fraction", 0)
        if missing_data_fraction > 0:
            sensitivity["assumptions_tested"].append({
                "assumption": "Missing data is missing at random",
                "impact": "High" if missing_data_fraction > 0.1 else "Low",
                "note": f"{missing_data_fraction*100:.1f}% data missing"
            })

        # Test assumption: exposure duration
        if context.get("variable_exposure_duration", False):
            sensitivity["assumptions_tested"].append({
                "assumption": "Constant risk over exposure duration",
                "impact": "Moderate",
                "note": "Risk may vary with exposure duration"
            })

        # Overall robustness assessment
        high_impact_count = sum(
            1 for test in sensitivity["assumptions_tested"]
            if test["impact"] == "High"
        )

        if high_impact_count == 0:
            sensitivity["robustness"] = "High - estimates robust to assumptions"
        elif high_impact_count <= 1:
            sensitivity["robustness"] = "Moderate - some sensitivity to assumptions"
        else:
            sensitivity["robustness"] = "Low - estimates sensitive to multiple assumptions"

        return sensitivity

    def _interpret_absolute_risk(self, risk: float) -> str:
        """Interpret absolute risk magnitude."""
        if risk < 0.001:
            return "Very rare (< 0.1%)"
        elif risk < 0.01:
            return "Rare (0.1-1%)"
        elif risk < 0.05:
            return "Uncommon (1-5%)"
        elif risk < 0.10:
            return "Common (5-10%)"
        else:
            return "Very common (>10%)"

    def _interpret_incidence_rate(self, rate: float) -> str:
        """Interpret incidence rate magnitude."""
        rate_per_1000 = rate * 1000
        if rate_per_1000 < 1:
            return f"Low incidence ({rate_per_1000:.2f} per 1,000 person-years)"
        elif rate_per_1000 < 10:
            return f"Moderate incidence ({rate_per_1000:.2f} per 1,000 person-years)"
        else:
            return f"High incidence ({rate_per_1000:.2f} per 1,000 person-years)"

    def _categorize_risk_level(self, risk: float) -> str:
        """Categorize risk into levels."""
        if risk < 0.01:
            return "Low risk"
        elif risk < 0.05:
            return "Moderate risk"
        elif risk < 0.10:
            return "High risk"
        else:
            return "Very high risk"

    def _extract_key_findings(
        self,
        risk_estimates: Dict[str, Any],
        stratification: Dict[str, Any],
        confidence_intervals: Dict[str, Any]
    ) -> List[str]:
        """Extract key findings from risk analysis."""
        findings = []

        # Absolute risk finding
        if "absolute_risk" in risk_estimates:
            abs_risk = risk_estimates["absolute_risk"]
            findings.append(
                f"Absolute risk: {abs_risk['percentage']:.2f}% "
                f"({abs_risk['interpretation']})"
            )

        # Confidence interval finding
        if "point_estimate" in confidence_intervals:
            findings.append(confidence_intervals["interpretation"])

        # Stratification finding
        if stratification.get("stratified"):
            highest = stratification.get("highest_risk_group")
            if highest:
                findings.append(
                    f"Highest risk in {highest['subgroup']}: "
                    f"{highest['percentage']:.2f}%"
                )

        return findings

    def _assess_confidence(
        self,
        events: int,
        total_population: int,
        risk_data: Dict[str, Any]
    ) -> str:
        """Assess confidence in risk estimates."""
        # Base confidence on sample size and data quality
        if total_population < 100:
            return "Low - small sample size limits precision"
        elif total_population < 1000:
            confidence = "Moderate - adequate sample size"
        else:
            confidence = "Moderate to High - large sample size"

        # Adjust for data quality
        if risk_data.get("missing_data_fraction", 0) > 0.2:
            confidence = "Low - substantial missing data"

        return confidence

    def _identify_limitations(
        self,
        risk_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify limitations of risk modeling."""
        limitations = [
            "Risk estimates assume observed sample representative of target population",
            "Point estimates do not capture full uncertainty - see confidence intervals",
        ]

        if not risk_data.get("person_years"):
            limitations.append(
                "Person-years not provided - cannot calculate exposure-adjusted rates"
            )

        if not risk_data.get("subgroups"):
            limitations.append(
                "No subgroup analysis - risk may vary across patient characteristics"
            )

        if context.get("observational_data", True):
            limitations.append(
                "Based on observational data - cannot establish causality"
            )

        return limitations

    def _document_assumptions(
        self,
        risk_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Document key modeling assumptions."""
        assumptions = [
            "Events are independent observations",
            "Risk is constant over the observation period",
            "Missing data is missing at random (MAR)",
        ]

        if context.get("assume_constant_exposure", True):
            assumptions.append("Exposure level is constant across population")

        if not risk_data.get("competing_risks_adjusted", False):
            assumptions.append(
                "Competing risks not accounted for - may overestimate risk"
            )

        return assumptions

    def _document_methodology(
        self,
        events: int,
        total_population: int,
        person_years: float
    ) -> str:
        """Document risk modeling methodology."""
        method_parts = [
            f"Quantitative risk assessment based on {events} events "
            f"in {total_population} individuals."
        ]

        if person_years > 0:
            method_parts.append(
                f"Incidence rates calculated using {person_years:.1f} person-years. "
            )

        method_parts.append(
            "Confidence intervals calculated using Wilson score method. "
        )

        method_parts.append(
            "Bayesian estimates incorporate prior information using Beta-Binomial model."
        )

        return " ".join(method_parts)

    def _generate_summary(
        self,
        query: str,
        risk_estimates: Dict[str, Any],
        stratification: Dict[str, Any],
        confidence_intervals: Dict[str, Any]
    ) -> str:
        """Generate executive summary of risk modeling."""
        summary_parts = [
            f"Risk modeling conducted for: '{query}'."
        ]

        if "absolute_risk" in risk_estimates:
            abs_risk = risk_estimates["absolute_risk"]
            summary_parts.append(
                f"Absolute risk estimated at {abs_risk['percentage']:.2f}% "
                f"({abs_risk['interpretation']})."
            )

        if "point_estimate" in confidence_intervals:
            ci = confidence_intervals
            summary_parts.append(
                f"95% CI: [{ci['lower_bound_percentage']:.2f}%, "
                f"{ci['upper_bound_percentage']:.2f}%]."
            )

        if stratification.get("stratified"):
            summary_parts.append("Risk stratification identifies subgroup variation.")

        return " ".join(summary_parts)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate risk modeling input.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        super().validate_input(input_data)

        if not input_data.get("query"):
            raise ValueError("Query is required for risk modeling")

        risk_data = input_data.get("risk_data", {})
        if not risk_data:
            raise ValueError("risk_data is required for risk modeling")

        # Check for minimum required data
        if "events" not in risk_data and "total_population" not in risk_data:
            raise ValueError(
                "risk_data must contain at least 'events' and 'total_population'"
            )

        return True
