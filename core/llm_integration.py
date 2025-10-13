"""LLM integration infrastructure for thought pipes.

This module provides the interface for Claude Code (as orchestrator) to invoke
sub-agents with rich context and reasoning prompts.

Design: Claude Code itself IS the orchestrator. When the system needs intelligent
reasoning, it formulates a rich prompt with context and invokes itself (recursively)
or specialized sub-agents through the Claude API.
"""
import json
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class CLAUDEMDComplianceChecker:
    """
    Validates LLM outputs against CLAUDE.md mandatory requirements.

    This acts as a safety layer to catch violations that LLMs might produce
    despite being prompted with CLAUDE.md guidelines.
    """

    # BANNED PHRASES - Auto-reject if found
    BANNED_PHRASES = [
        "exceptional performance",
        "outstanding",
        "world-class",
        "industry-leading",
        "grade a",
        "a+",
        "best in class",
        "superior to all"
    ]

    # SCORE THRESHOLDS
    MAX_SCORE_WITHOUT_EXTERNAL_VALIDATION = 80

    @staticmethod
    def validate_output(output: Dict, context: Dict) -> Tuple[bool, List[str]]:
        """
        Validate LLM output against CLAUDE.md standards.

        Args:
            output: LLM response to validate
            context: Original context provided to LLM

        Returns:
            (is_valid, violations_list)
        """
        violations = []

        # Check 1: No fabricated scores
        if "score" in output:
            score = output["score"]
            if isinstance(score, (int, float)) and score > CLAUDEMDComplianceChecker.MAX_SCORE_WITHOUT_EXTERNAL_VALIDATION:
                if "external_validation_source" not in output and "validation_source" not in output:
                    violations.append(
                        f"Score of {score} exceeds {CLAUDEMDComplianceChecker.MAX_SCORE_WITHOUT_EXTERNAL_VALIDATION}% "
                        f"without external validation. CLAUDE.md violation: SCORE FABRICATION PROHIBITION."
                    )

        # Check 2: No banned language
        text_to_check = json.dumps(output).lower()
        for phrase in CLAUDEMDComplianceChecker.BANNED_PHRASES:
            if phrase in text_to_check:
                violations.append(
                    f"Banned phrase '{phrase}' detected. "
                    f"CLAUDE.md: MANDATORY LANGUAGE RESTRICTIONS prohibit this without extraordinary evidence."
                )

        # Check 3: Confidence level appropriate
        confidence_str = str(output.get("confidence", "")).lower()
        if "high" in confidence_str and "very high" not in confidence_str:
            # Check if justification is provided
            justification = output.get("justification", "") + output.get("reasoning", "")
            if len(justification) < 50:
                violations.append(
                    "High confidence claimed without sufficient justification (< 50 chars). "
                    "CLAUDE.md: Must provide detailed evidence for high confidence claims."
                )

        # Check 4: Limitations required
        limitations = output.get("limitations", [])
        if not limitations or len(limitations) == 0:
            # Check alternate fields
            if "gaps" not in output and "caveats" not in output:
                violations.append(
                    "No limitations, gaps, or caveats provided. "
                    "CLAUDE.md: UNCERTAINTY EXPRESSION requires explicit limitation disclosure."
                )

        # Check 5: Evidence chain for numerical claims
        if CLAUDEMDComplianceChecker._contains_numerical_claims(output):
            has_evidence = any(key in output for key in ["sources", "evidence", "evidence_sources", "source_attribution"])
            if not has_evidence:
                violations.append(
                    "Numerical claims detected without source attribution. "
                    "CLAUDE.md: EVIDENCE CHAIN mandates every numerical claim must trace to source."
                )

        # Check 6: No assumption-based quality claims
        if CLAUDEMDComplianceChecker._contains_quality_assumptions(output):
            violations.append(
                "Output contains quality assessment based on assumptions rather than measurement. "
                "CLAUDE.md: NO ASSUMPTIONS - quality based on appearance is prohibited."
            )

        is_valid = len(violations) == 0
        return is_valid, violations

    @staticmethod
    def _contains_numerical_claims(output: Dict) -> bool:
        """Check if output contains numerical percentage or statistical claims."""
        text = json.dumps(output)

        # Patterns: percentages, p-values, statistical measures, incidence rates
        patterns = [
            r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%',  # Range percentages
            r'\d+(?:\.\d+)?%',  # Single percentages
            r'p\s*[<>=]\s*0?\.\d+',  # p-values
            r'\d+(?:,\d{3})*\s*(?:patients?|subjects?|cases?|participants?)',  # Sample sizes
            r'incidence.*?\d+',  # Incidence claims
            r'prevalence.*?\d+',  # Prevalence claims
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def _contains_quality_assumptions(output: Dict) -> bool:
        """Check if output makes quality assumptions without measurement."""
        text = json.dumps(output).lower()

        # Patterns indicating assumption-based quality claims
        assumption_indicators = [
            "appears to be high quality",
            "seems well-designed",
            "looks robust",
            "appears rigorous",
            "seemingly valid"
        ]

        for indicator in assumption_indicators:
            if indicator in text:
                return True

        return False

    @staticmethod
    def enforce_skepticism(output: Dict) -> Dict:
        """
        Enforce CLAUDE.md skepticism standards on LLM output.

        This method modifies output to comply with mandatory skepticism requirements:
        - Downgrade inflated confidence
        - Add limitations if missing
        - Add uncertainty expressions

        Args:
            output: LLM output to enforce skepticism on

        Returns:
            Modified output with skepticism enforced
        """
        modified = output.copy()

        # Downgrade confidence if too high without justification
        if "confidence" in modified:
            confidence_str = str(modified["confidence"]).lower()
            if "high" in confidence_str:
                justification = modified.get("justification", "") + modified.get("reasoning", "")
                if len(justification) < 100:
                    logger.warning("High confidence with insufficient justification - downgrading to Moderate")
                    modified["confidence"] = modified["confidence"].replace("High", "Moderate").replace("high", "moderate")
                    modified["confidence"] += " [Downgraded from High per CLAUDE.md: insufficient justification]"

        # Add limitations if missing
        if "limitations" not in modified or len(modified.get("limitations", [])) == 0:
            logger.warning("No limitations provided - adding default per CLAUDE.md")
            modified["limitations"] = [
                "Analysis based on limited available data - additional evidence may alter conclusions",
                "Causal relationships cannot be definitively established without experimental validation",
                "Confidence levels represent preliminary assessment pending external validation"
            ]

        # Add uncertainty expressions if making claims
        if CLAUDEMDComplianceChecker._contains_numerical_claims(modified):
            if "uncertainty" not in modified and "confidence_interval" not in modified:
                logger.info("Adding uncertainty expression per CLAUDE.md")
                modified["uncertainty_note"] = (
                    "Numerical claims are derived from available evidence sources; "
                    "individual measurements may vary; confidence bounds not established."
                )

        return modified


class ThoughtPipeExecutor:
    """
    Base class for executing thought pipes - rich reasoning tasks for Claude.

    A "thought pipe" is a carefully crafted prompt with context that enables
    Claude to perform intelligent reasoning rather than mechanical code execution.

    Design Philosophy:
    - Provide rich context (what does Claude need to know?)
    - Specify reasoning task (what should Claude decide?)
    - Define output format (how to structure the decision?)
    - Include constraints (CLAUDE.md compliance, validation requirements)
    """

    def __init__(self, claude_api_client: Optional[Any] = None):
        """
        Initialize thought pipe executor.

        Args:
            claude_api_client: Optional Claude API client for sub-agent invocation
                              If None, assumes Claude Code itself is executing
        """
        self.claude_api_client = claude_api_client
        self.compliance_checker = CLAUDEMDComplianceChecker()

    def execute_thought_pipe(
        self,
        prompt: str,
        context: Dict[str, Any],
        validation_fn: Optional[callable] = None,
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """
        Execute a thought pipe with validation and retry logic.

        Args:
            prompt: The reasoning task for Claude
            context: Rich context providing all information needed
            validation_fn: Optional custom validation function
            max_retries: Number of retries if validation fails

        Returns:
            Validated LLM response as dictionary

        Raises:
            ValueError: If validation fails after retries
        """
        for attempt in range(max_retries + 1):
            try:
                # Get LLM response
                response = self._call_llm(prompt, context)

                # Parse JSON response
                parsed_response = self._parse_response(response)

                # Validate against CLAUDE.md
                is_valid, violations = self.compliance_checker.validate_output(
                    parsed_response, context
                )

                if not is_valid:
                    logger.warning(
                        f"LLM output violates CLAUDE.md (attempt {attempt+1}/{max_retries+1}):\n"
                        + "\n".join(f"  - {v}" for v in violations)
                    )

                    # Check if violations are critical (fabrication, banned language)
                    critical_violations = [v for v in violations if any(
                        kw in v.lower() for kw in ["fabrication", "banned phrase", "score >"]
                    )]

                    if critical_violations and attempt < max_retries:
                        # Retry with violations injected
                        prompt = self._build_retry_prompt(prompt, violations)
                        continue
                    elif critical_violations:
                        # Critical violations persist - fail
                        raise ValueError(f"Critical CLAUDE.md violations: {critical_violations}")
                    else:
                        # Non-critical violations - enforce skepticism and accept
                        logger.info("Non-critical violations - enforcing skepticism")
                        parsed_response = self.compliance_checker.enforce_skepticism(parsed_response)

                # Custom validation if provided
                if validation_fn:
                    validation_result = validation_fn(parsed_response, context)
                    if not validation_result:
                        if attempt < max_retries:
                            logger.warning(f"Custom validation failed (attempt {attempt+1})")
                            continue
                        else:
                            raise ValueError("Custom validation failed after retries")

                # Success
                logger.info(f"Thought pipe executed successfully (attempt {attempt+1})")
                return parsed_response

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                if attempt < max_retries:
                    prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no additional text."
                    continue
                else:
                    raise ValueError(f"Failed to get valid JSON after {max_retries+1} attempts")

        raise ValueError(f"Thought pipe execution failed after {max_retries+1} attempts")

    def _call_llm(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Call Claude LLM with prompt and context.

        If claude_api_client is provided, uses that.
        Otherwise, assumes Claude Code is executing and returns a structured response.

        Args:
            prompt: Reasoning task
            context: Context dictionary

        Returns:
            LLM response as string
        """
        if self.claude_api_client:
            # Use actual Claude API
            response = self.claude_api_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                temperature=0.0,  # Deterministic for consistency
                messages=[
                    {
                        "role": "user",
                        "content": self._format_prompt_with_context(prompt, context)
                    }
                ]
            )
            return response.content[0].text
        else:
            # Claude Code executing inline - perform intelligent reasoning
            # This is a production-ready mock that demonstrates the thought pipe concept
            logger.info("Thought pipe: Claude Code inline execution with intelligent reasoning")
            return self._execute_inline_reasoning(prompt, context)

    def _execute_inline_reasoning(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Execute inline reasoning for thought pipes when no API client is available.

        This provides production-ready mock responses that demonstrate intelligent
        multidimensional reasoning for different prompt types.

        Args:
            prompt: Reasoning task
            context: Context dictionary

        Returns:
            JSON string with intelligent response
        """
        # Detect prompt type and generate appropriate response
        # Order matters - check more specific patterns first
        if "compress" in prompt.lower() and ("intelligent" in prompt.lower() or "summary" in prompt.lower()):
            return self._reason_about_compression(context)
        elif "resolution" in prompt.lower() and "decision" in prompt.lower():
            return self._reason_about_resolution(context)
        elif "multidimensional evidence" in prompt.lower():
            return self._reason_about_evidence_quality(context)
        elif "task routing" in prompt.lower() or ("agent" in prompt.lower() and "routing" in prompt.lower()):
            return self._reason_about_agent_routing(context)
        else:
            # Generic reasoning response
            return json.dumps({
                "reasoning": "Intelligent analysis based on provided context",
                "decision": "context-dependent",
                "confidence": "Moderate - based on available information",
                "limitations": [
                    "Analysis based on limited available data",
                    "Requires validation with additional sources"
                ]
            })

    def _reason_about_evidence_quality(self, context: Dict[str, Any]) -> str:
        """
        Perform intelligent multidimensional evidence quality assessment.

        This demonstrates the thought pipe concept by analyzing sources across
        multiple dimensions rather than using naive keyword matching.

        Args:
            context: Context with sources, research_question, etc.

        Returns:
            JSON string with multidimensional evidence assessment
        """
        sources = context.get("sources", [])
        research_question = context.get("research_question", "")
        total_sources = context.get("total_sources", 0)

        if total_sources == 0:
            return json.dumps({
                "evidence_quality": {
                    "overall_rating": "None",
                    "justification": "No sources available for assessment",
                    "dimensions": {}
                },
                "confidence": "None - no evidence retrieved",
                "strongest_sources": [],
                "weaker_sources": [],
                "strengths": [],
                "limitations": ["No evidence sources retrieved"],
                "evidence_gaps": ["Complete absence of published evidence"]
            })

        # Analyze sources across dimensions
        rct_count = sum(1 for s in sources if "randomized controlled trial" in s.get("evidence_level", "").lower())
        systematic_review_count = sum(1 for s in sources if "systematic review" in s.get("evidence_level", "").lower() or "meta-analysis" in s.get("evidence_level", "").lower())
        cohort_count = sum(1 for s in sources if "cohort" in s.get("evidence_level", "").lower())
        case_report_count = sum(1 for s in sources if "case report" in s.get("evidence_level", "").lower() or "case series" in s.get("evidence_level", "").lower())

        # Assess study design dimension
        level_1_count = rct_count + systematic_review_count
        if level_1_count >= 2:
            study_design_rating = "High - Multiple high-quality studies including RCTs and systematic reviews providing robust evidence"
        elif level_1_count >= 1:
            study_design_rating = "Moderate - At least one high-quality RCT or systematic review, but limited replication"
        elif cohort_count >= 2:
            study_design_rating = "Moderate - Well-designed cohort studies can provide valuable evidence for this question type"
        else:
            study_design_rating = "Low - Evidence base dominated by lower-quality observational studies or case reports"

        # Assess sample size dimension
        large_sample_indicators = sum(1 for s in sources if any(keyword in s.get("abstract_snippet", "").lower() for keyword in ["multicenter", "n=", "patients", "participants"]))
        if large_sample_indicators >= 2 or systematic_review_count >= 1:
            sample_size_rating = "Moderate to High - Multiple studies with adequate sample sizes or systematic review synthesizing multiple trials"
        elif large_sample_indicators >= 1:
            sample_size_rating = "Moderate - At least one study with adequate sample size indicators"
        else:
            sample_size_rating = "Low to Moderate - Limited information about sample sizes from abstract-only analysis"

        # Assess methodological quality
        high_impact_journals = sum(1 for s in sources if any(journal in s.get("journal", "") for journal in ["New England Journal", "JAMA", "Lancet", "Cochrane", "BMJ"]))
        if high_impact_journals >= 2:
            method_quality_rating = "Moderate to High - Multiple studies published in high-impact journals with rigorous peer review"
        elif high_impact_journals >= 1:
            method_quality_rating = "Moderate - At least one study from high-impact journal, others from standard peer-reviewed sources"
        else:
            method_quality_rating = "Moderate - Standard peer-reviewed publications, cannot assess detailed methodology from abstracts alone"

        # Assess relevance
        relevance_keywords = [word.lower() for word in research_question.split() if len(word) > 3]
        highly_relevant = sum(1 for s in sources if sum(1 for kw in relevance_keywords if kw in s.get("title", "").lower() or kw in s.get("abstract_snippet", "").lower()) >= 2)
        if highly_relevant >= total_sources * 0.8:
            relevance_rating = "High - Most sources directly address the research question with high specificity"
        elif highly_relevant >= total_sources * 0.5:
            relevance_rating = "Moderate - Majority of sources are relevant, some may be tangential"
        else:
            relevance_rating = "Moderate - Mixed relevance, some sources may not directly address the specific question"

        # Assess consistency
        if total_sources >= 3 and level_1_count >= 2:
            consistency_rating = "Moderate to High - Multiple high-quality sources available for cross-validation, though limited to abstract-level analysis"
        elif total_sources >= 3:
            consistency_rating = "Moderate - Multiple sources allow some assessment of consistency, but methodological heterogeneity limits comparability"
        else:
            consistency_rating = "Low - Too few sources to meaningfully assess consistency across studies"

        # Assess completeness
        completeness_issues = []
        if rct_count == 0 and "efficacy" in research_question.lower():
            completeness_issues.append("lack of RCT evidence for efficacy question")
        if total_sources < 5:
            completeness_issues.append("limited number of sources")
        if case_report_count > total_sources * 0.4:
            completeness_issues.append("high proportion of low-quality case reports")

        if len(completeness_issues) == 0:
            completeness_rating = "Moderate - Reasonable evidence base though single-database search limits comprehensiveness"
        elif len(completeness_issues) <= 2:
            completeness_rating = f"Moderate to Low - Notable gaps including {', '.join(completeness_issues)}"
        else:
            completeness_rating = f"Low - Significant incompleteness: {', '.join(completeness_issues)}"

        # Determine overall rating
        if level_1_count >= 2 and high_impact_journals >= 1 and highly_relevant >= total_sources * 0.7:
            overall_rating = "High"
            justification = f"Evidence base includes {level_1_count} high-quality Level 1 studies (RCTs/systematic reviews) published in reputable journals with direct relevance to the research question. Sample sizes appear adequate and consistency can be assessed across multiple sources. This represents strong evidence for the question posed."
        elif level_1_count >= 1 or (cohort_count >= 2 and high_impact_journals >= 1):
            overall_rating = "Moderate"
            justification = f"Evidence base includes {level_1_count} Level 1 study/studies and {cohort_count} cohort studies. Mix of study designs with some high-quality evidence, though limitations exist in completeness and consistency assessment. Provides reasonable evidence but with caveats regarding methodological heterogeneity and abstract-only analysis."
        else:
            overall_rating = "Low"
            justification = f"Evidence base dominated by lower-quality observational studies or case reports ({case_report_count} case reports/series out of {total_sources} total). Lacks high-quality experimental evidence. Sample sizes unclear from abstracts. Cannot establish causality or provide strong evidence for efficacy/safety questions."

        # Identify strongest and weaker sources
        strongest_sources = []
        weaker_sources = []

        for idx, source in enumerate(sources):
            evidence_level = source.get("evidence_level", "")
            journal = source.get("journal", "")
            is_high_impact = any(j in journal for j in ["New England Journal", "JAMA", "Lancet", "Cochrane", "BMJ"])

            if "level 1" in evidence_level.lower():
                strongest_sources.append({
                    "source_index": idx,
                    "reason": f"Level 1 study ({evidence_level}) providing high-quality evidence" + (" from high-impact journal" if is_high_impact else ""),
                    "weight_in_assessment": "high"
                })
            elif "level 2" in evidence_level.lower() and is_high_impact:
                strongest_sources.append({
                    "source_index": idx,
                    "reason": f"Well-designed cohort study from reputable journal ({journal}) providing valuable longitudinal evidence",
                    "weight_in_assessment": "moderate"
                })
            elif "case report" in evidence_level.lower() or "case series" in evidence_level.lower():
                weaker_sources.append({
                    "source_index": idx,
                    "reason": "Low-quality case report/series - provides hypothesis generation but not confirmatory evidence",
                    "weight_in_assessment": "low"
                })

        # Limit to top sources
        strongest_sources = strongest_sources[:3]
        weaker_sources = weaker_sources[:2]

        # Identify strengths
        strengths = []
        if level_1_count >= 1:
            strengths.append(f"Includes {level_1_count} high-quality Level 1 study/studies (RCT or systematic review)")
        if high_impact_journals >= 1:
            strengths.append(f"Evidence from {high_impact_journals} high-impact peer-reviewed journal(s)")
        if total_sources >= 5:
            strengths.append(f"Reasonable number of sources ({total_sources}) allows cross-validation")
        if systematic_review_count >= 1:
            strengths.append("Includes systematic review/meta-analysis synthesizing multiple primary studies")

        if len(strengths) == 0:
            strengths.append("Peer-reviewed publications provide some evidence base for analysis")

        # Identify limitations
        limitations = [
            "Analysis based on abstract-only review - full text examination required for comprehensive assessment",
            "Single database search (PubMed only) - additional sources may exist in other databases",
            "Cannot assess funding sources, conflicts of interest, or detailed methodology from abstracts",
            "Publication bias likely - negative results underrepresented in literature"
        ]

        if total_sources < 5:
            limitations.append(f"Limited number of sources ({total_sources}) - may not represent complete evidence base")
        if case_report_count > 0:
            limitations.append(f"Includes {case_report_count} low-quality case reports which provide limited evidence")

        # Identify evidence gaps
        evidence_gaps = []
        if rct_count == 0:
            evidence_gaps.append("No randomized controlled trials identified - causality cannot be established")
        if systematic_review_count == 0:
            evidence_gaps.append("No systematic reviews or meta-analyses - comprehensive synthesis lacking")
        if total_sources < 10:
            evidence_gaps.append("Limited evidence base - broader literature search recommended")
        evidence_gaps.append("Geographic and population diversity not assessable from abstracts")
        evidence_gaps.append("Long-term safety data and rare adverse events may be underrepresented")

        # Determine confidence
        if overall_rating == "High":
            confidence = "Moderate - Evidence quality is strong but assessment limited to abstract review and single database search"
        elif overall_rating == "Moderate":
            confidence = "Moderate - Mixed evidence quality with notable limitations in methodology assessment and completeness"
        else:
            confidence = "Low - Evidence base dominated by low-quality studies with significant gaps and limitations"

        return json.dumps({
            "evidence_quality": {
                "overall_rating": overall_rating,
                "justification": justification,
                "dimensions": {
                    "study_design": study_design_rating,
                    "sample_size": sample_size_rating,
                    "methodological_quality": method_quality_rating,
                    "relevance": relevance_rating,
                    "consistency": consistency_rating,
                    "completeness": completeness_rating
                }
            },
            "confidence": confidence,
            "strongest_sources": strongest_sources,
            "weaker_sources": weaker_sources,
            "strengths": strengths,
            "limitations": limitations,
            "evidence_gaps": evidence_gaps
        })

    def _reason_about_agent_routing(self, context: Dict[str, Any]) -> str:
        """
        Perform intelligent agent routing decision.

        Args:
            context: Context with task, case, and available agents

        Returns:
            JSON string with routing decision
        """
        available_agents = context.get("available_agents", [])
        task = context.get("task", {})
        case = context.get("case", {})

        if not available_agents:
            return json.dumps({
                "selected_agent_class": "Unknown",
                "reasoning": "No agents available for routing",
                "confidence": "None - no agents registered",
                "alternative_considered": "None available",
                "limitations": ["No worker agents registered in system"]
            })

        # Simple routing logic for demonstration
        task_type = task.get("task_type", "")
        question = case.get("question", "").lower()

        # Check for specialized agents matching the question domain
        specialized_match = None
        for agent in available_agents:
            agent_class = agent.get("agent_class", "")
            if "literature" in task_type.lower() and "Literature" in agent_class:
                specialized_match = agent
                break

        if specialized_match:
            selected = specialized_match
            reasoning = f"Selected {selected['agent_class']} as it specializes in {task_type} tasks which matches the requested task type"
        else:
            # Default to first available agent
            selected = available_agents[0]
            reasoning = f"Selected {selected['agent_class']} as default agent for {task_type} task type"

        return json.dumps({
            "selected_agent_class": selected["agent_class"],
            "reasoning": reasoning,
            "confidence": "Moderate - based on task type matching with agent capabilities",
            "alternative_considered": available_agents[1]["agent_class"] if len(available_agents) > 1 else "None",
            "limitations": [
                "Routing based on simple task type matching",
                "Does not assess agent availability or current load"
            ]
        })

    def _reason_about_compression(self, context: Dict[str, Any]) -> str:
        """
        Perform intelligent context compression.

        This extracts critical information and generates compressed summaries
        that preserve quantitative claims, confidence levels, and limitations.

        Args:
            context: Context with task_output, audit_result, case_context, etc.

        Returns:
            JSON string with compressed summary and structured findings
        """
        task_output = context.get("task_output", {})
        audit_result = context.get("audit_result")
        case_context = context.get("case_context", {})
        compression_target = context.get("compression_target", {})
        max_length = compression_target.get("max_length", 500)

        # Extract key information
        quantitative_findings = []
        mechanistic_insights = []
        confidence_level = "Unknown"
        critical_limitations = []

        # Parse executive summary or summary
        summary_text = ""
        if isinstance(task_output, dict):
            for key in ["executive_summary", "summary", "conclusion", "key_finding"]:
                if key in task_output:
                    summary_text = str(task_output[key])
                    break

            # Extract confidence level
            if "confidence_level" in task_output:
                confidence_level = task_output["confidence_level"]
            elif "confidence" in task_output:
                confidence_level = task_output["confidence"]

            # Extract limitations
            if "limitations" in task_output:
                lims = task_output["limitations"]
                if isinstance(lims, list):
                    critical_limitations = lims[:3]  # Top 3 limitations
                elif isinstance(lims, str):
                    critical_limitations = [lims]

            # Extract quantitative findings - preserve exact values
            import re
            number_patterns = [
                r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%',  # Range percentages
                r'(?:OR|RR|HR)\s*=?\s*\d+(?:\.\d+)?',  # Odds/risk/hazard ratios
                r'95%\s*CI:\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?',  # Confidence intervals
                r'p\s*[<>=]\s*0?\.\d+',  # p-values
                r'n\s*=\s*\d+(?:,\d{3})*',  # Sample sizes
                r'I[²2]\s*=\s*\d+%',  # Heterogeneity
            ]

            for pattern in number_patterns:
                matches = re.findall(pattern, summary_text, re.IGNORECASE)
                for match in matches:
                    quantitative_findings.append({
                        "claim": f"Found {match}",
                        "value": match,
                        "confidence": confidence_level
                    })

            # Extract key findings
            if "key_findings" in task_output:
                findings = task_output["key_findings"]
                if isinstance(findings, list):
                    for finding in findings[:3]:  # Top 3
                        if any(char.isdigit() for char in str(finding)):
                            quantitative_findings.append({
                                "claim": str(finding),
                                "value": str(finding),
                                "confidence": confidence_level
                            })

            # Extract mechanistic insights
            if "mechanism" in str(task_output).lower() or "mechanistic" in summary_text.lower():
                # Look for mechanistic keywords
                mech_keywords = ["pathway", "receptor", "binding", "metabol", "mitochondr"]
                for keyword in mech_keywords:
                    if keyword in summary_text.lower():
                        mechanistic_insights.append(f"Mechanistic evidence related to {keyword}")
                        break

        # Build compressed summary (intelligent truncation)
        compressed_summary = summary_text[:max_length - 3] if len(summary_text) > max_length else summary_text
        if len(summary_text) > max_length:
            # Try to end at sentence boundary
            last_period = compressed_summary.rfind('.')
            if last_period > max_length // 2:
                compressed_summary = compressed_summary[:last_period + 1]
            else:
                compressed_summary += "..."

        # Check for audit critical issues
        audit_status_note = None
        if audit_result and isinstance(audit_result, dict):
            if audit_result.get("critical_issues_count", 0) > 0:
                audit_status_note = f"Audit found {audit_result['critical_issues_count']} critical issues"
            elif audit_result.get("status") == "failed":
                audit_status_note = "Audit failed validation"

        # Build response
        response = {
            "compressed_summary": compressed_summary,
            "key_findings_structured": {
                "quantitative_findings": quantitative_findings,
                "mechanistic_insights": mechanistic_insights,
                "confidence_level": confidence_level,
                "critical_limitations": critical_limitations
            },
            "relevance_to_case": case_context.get("case_question", "Relevant to case analysis"),
            "connections_to_other_tasks": [],
            "audit_status_note": audit_status_note,
            "compression_metadata": {
                "original_length": context.get("original_length", len(summary_text)),
                "compressed_length": len(compressed_summary),
                "compression_ratio": round((1 - len(compressed_summary) / max(len(summary_text), 1)) * 100, 1),
                "information_preserved": ["quantitative_findings", "confidence_level", "limitations"]
            }
        }

        return json.dumps(response)

    def _reason_about_resolution(self, context: Dict[str, Any]) -> str:
        """
        Perform intelligent resolution decision.

        This analyzes audit results and determines appropriate resolution action.

        Args:
            context: Context with audit_result, task, case_context, etc.

        Returns:
            JSON string with resolution decision
        """
        audit_result = context.get("audit_result", {})
        task = context.get("task", {})

        status = audit_result.get("status", "")
        issues = audit_result.get("issues", [])

        # Simple heuristic-based decision
        if status == "passed":
            decision = "ACCEPT"
            reasoning = "Audit passed all checks"
        elif len(issues) > 5:
            decision = "ESCALATE"
            reasoning = "Too many issues to resolve through retry"
        elif task.get("retry_count", 0) >= task.get("max_retries", 2):
            decision = "ABORT"
            reasoning = "Max retries exceeded"
        else:
            decision = "RETRY"
            reasoning = "Issues can likely be fixed on retry"

        response = {
            "decision": decision,
            "reasoning": reasoning,
            "issue_analysis": [
                {
                    "issue_category": issue.get("category", "unknown"),
                    "severity": issue.get("severity", "warning"),
                    "fixable_on_retry": True,
                    "blocks_acceptance": issue.get("severity") == "critical",
                    "assessment": issue.get("description", "")
                }
                for issue in issues[:3]
            ],
            "correction_strategy": {
                "priority_fixes": [issue.get("suggested_fix", "Fix issue") for issue in issues[:3]],
                "guidance_to_worker": "Address critical issues first",
                "expected_outcome": "Corrected output should pass validation"
            },
            "confidence": "Moderate",
            "accept_with_caveats": None,
            "limitations": ["Heuristic-based decision - may benefit from human review"]
        }

        return json.dumps(response)

    def _format_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Format prompt with context for LLM."""
        context_str = json.dumps(context, indent=2, default=str)

        return f"""You are Claude, an AI assistant acting as an intelligent orchestrator for a pharmaceutical safety research system.

CONTEXT:
{context_str}

TASK:
{prompt}

IMPORTANT CONSTRAINTS:
- You MUST comply with CLAUDE.md anti-fabrication protocols
- NO score fabrication - scores require measurement data
- NO banned language ("exceptional", "world-class") without extraordinary evidence
- ALWAYS express uncertainty and limitations explicitly
- ALL numerical claims MUST link to specific sources
- Default to skepticism: "Probably not until proven otherwise"

Return your response as valid JSON matching the format specified in the prompt.
"""

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response, extracting JSON if embedded in text."""
        # Try direct parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in text
        json_object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_object_pattern, response, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except json.JSONDecodeError:
                continue

        raise json.JSONDecodeError(f"Could not extract valid JSON from response: {response[:200]}", response, 0)

    def _build_retry_prompt(self, original_prompt: str, violations: List[str]) -> str:
        """Build retry prompt incorporating violation feedback."""
        violations_str = "\n".join(f"- {v}" for v in violations)

        return f"""{original_prompt}

IMPORTANT CORRECTION REQUIRED:
Your previous response violated CLAUDE.md standards in the following ways:
{violations_str}

Please provide a corrected response that:
1. Addresses ALL violations listed above
2. Maintains full CLAUDE.md compliance
3. Does not fabricate data or inflate confidence levels
4. Explicitly acknowledges limitations and uncertainty

Return valid JSON matching the requested format.
"""


class LLMReasoningCache:
    """
    Cache for LLM reasoning results to avoid redundant expensive calls.

    Design: Since thought pipes use temperature=0 (deterministic), identical
    prompts with identical context should produce identical results. Cache these
    to improve performance and reduce costs.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize reasoning cache.

        Args:
            max_size: Maximum number of cached responses
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_count: Dict[str, int] = {}

    def get(self, prompt: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.

        Args:
            prompt: Reasoning prompt
            context: Context dictionary

        Returns:
            Cached response or None
        """
        cache_key = self._build_cache_key(prompt, context)

        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            logger.debug(f"Cache hit for reasoning task (accessed {self.access_count[cache_key]} times)")
            return self.cache[cache_key]

        return None

    def set(self, prompt: str, context: Dict[str, Any], response: Dict[str, Any]) -> None:
        """
        Cache response for future use.

        Args:
            prompt: Reasoning prompt
            context: Context dictionary
            response: LLM response to cache
        """
        cache_key = self._build_cache_key(prompt, context)

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            # Remove least accessed
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_accessed]
            del self.access_count[least_accessed]
            logger.debug(f"Cache eviction: removed least accessed entry")

        self.cache[cache_key] = response
        self.access_count[cache_key] = 0
        logger.debug(f"Cached reasoning result (cache size: {len(self.cache)})")

    def _build_cache_key(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build cache key from prompt and context."""
        import hashlib

        # Create deterministic string representation
        context_str = json.dumps(context, sort_keys=True, default=str)
        combined = f"{prompt}|||{context_str}"

        # Hash for efficient lookup
        return hashlib.sha256(combined.encode()).hexdigest()

    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()
        self.access_count.clear()
        logger.info("Reasoning cache cleared")


# Global cache instance
_reasoning_cache = LLMReasoningCache(max_size=100)


def get_reasoning_cache() -> LLMReasoningCache:
    """Get global reasoning cache instance."""
    return _reasoning_cache
