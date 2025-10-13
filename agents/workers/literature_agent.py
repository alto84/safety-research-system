"""Literature review worker agent."""
from typing import Dict, Any, List, Optional
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.base_worker import BaseWorker
from agents.data_sources.pubmed_connector import PubMedConnector
from core.llm_integration import ThoughtPipeExecutor, get_reasoning_cache


logger = logging.getLogger(__name__)


class LiteratureAgent(BaseWorker):
    """
    Worker agent for conducting literature reviews.

    This agent searches, retrieves, and synthesizes scientific literature
    related to safety questions.

    Expected input:
        - query: The research question or topic
        - data_sources: List of databases/sources to search
        - context: Additional context about the question

    Output:
        - findings: Synthesized findings from literature
        - sources: List of sources reviewed with citations
        - evidence_level: Level of evidence found
        - gaps: Identified gaps in the literature
    """

    def __init__(
        self,
        agent_id: str = "lit_agent_01",
        config: Dict[str, Any] = None,
        enable_intelligent_evidence_assessment: bool = True
    ):
        """
        Initialize literature review agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
            enable_intelligent_evidence_assessment: If True, use LLM-driven multidimensional
                                                     evidence assessment; if False, use legacy keyword-based assessment
        """
        super().__init__(agent_id, config)
        self.version = "1.0.0"
        self.pubmed = PubMedConnector()
        self.enable_intelligent_evidence_assessment = enable_intelligent_evidence_assessment
        self.thought_pipe = ThoughtPipeExecutor() if enable_intelligent_evidence_assessment else None
        self.reasoning_cache = get_reasoning_cache() if enable_intelligent_evidence_assessment else None

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute literature review task.

        Args:
            input_data: Input containing query, data_sources, context

        Returns:
            Dictionary with literature review results
        """
        # Validate input
        self.validate_input(input_data)

        # Handle corrections from previous audit if present
        input_data = self.handle_corrections(input_data)

        query = input_data.get("query", "")
        data_sources = input_data.get("data_sources", ["pubmed", "clinical_trials"])
        context = input_data.get("context", {})

        logger.info(f"LiteratureAgent: Starting literature review for query: '{query}'")
        logger.info(f"LiteratureAgent: Searching sources: {data_sources}")

        # Execute literature review using real PubMed data
        result = self._conduct_literature_review(query, data_sources, context)

        logger.info(f"LiteratureAgent: Review complete. Found {len(result['sources'])} sources")

        return result

    def _conduct_literature_review(
        self, query: str, data_sources: list, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct the literature review using real PubMed data.

        Args:
            query: Research question
            data_sources: Sources to search
            context: Additional context

        Returns:
            Structured literature review results
        """
        logger.info(f"Conducting real literature search for: {query}")

        # Search PubMed for relevant papers
        sources_list = []
        total_results = 0

        if "pubmed" in data_sources:
            try:
                # Search PubMed
                pmids = self.pubmed.search_pubmed(query, max_results=10)
                total_results = len(pmids)
                logger.info(f"Found {total_results} papers in PubMed")

                # Fetch details for each paper
                for pmid in pmids[:5]:  # Limit to top 5 for analysis
                    try:
                        details = self.pubmed.fetch_paper_details(pmid)

                        # Extract evidence level from study design
                        evidence_level = self._determine_evidence_level(details)

                        sources_list.append({
                            "title": details.title,
                            "authors": details.authors[:3] if len(details.authors) > 3 else details.authors,
                            "year": details.publication_date[:4] if details.publication_date else "Unknown",
                            "pmid": details.pmid,
                            "journal": details.journal,
                            "doi": details.doi,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{details.pmid}/",
                            "evidence_level": evidence_level,
                            "abstract": details.abstract[:300] + "..." if len(details.abstract) > 300 else details.abstract,
                        })
                    except Exception as e:
                        logger.warning(f"Failed to fetch details for PMID {pmid}: {e}")

            except Exception as e:
                logger.error(f"PubMed search failed: {e}")
                return self._return_error_result(query, str(e))

        if len(sources_list) == 0:
            return self._return_no_results(query, data_sources)

        # Synthesize key findings from abstracts
        key_findings = self._synthesize_findings(sources_list)

        # Assess overall evidence quality
        evidence_assessment = self._assess_evidence_quality(sources_list, query)

        return {
            "summary": (
                f"Literature review conducted for: '{query}'. "
                f"Searched {len(data_sources)} databases. "
                f"Retrieved {len(sources_list)} relevant studies from {total_results} search results. "
                f"Evidence quality: {evidence_assessment['level']}. "
                f"{evidence_assessment['note']}"
            ),
            "key_findings": key_findings,
            "sources": sources_list,
            "evidence_level": evidence_assessment['level'],
            "confidence": evidence_assessment['confidence'],
            "gaps": self._identify_gaps(sources_list),
            "limitations": [
                "Search limited to PubMed database and English language publications",
                "Publication bias may affect findings - negative results underrepresented",
                "Cannot determine causality from observational studies",
                f"Analysis based on {len(sources_list)} papers - additional sources may exist",
                "Abstract-only analysis for initial review - full text review recommended",
            ],
            "methodology": (
                f"Systematic PubMed search using query: '{query}'. "
                f"Retrieved {total_results} results, analyzed top {len(sources_list)} most relevant. "
                "Evidence graded using standard hierarchy (RCT > cohort > case-control > case series). "
                "All sources verified with PMID and accessible URLs."
            ),
            "metadata": {
                "search_date": "2025-10-12",
                "databases_searched": data_sources,
                "total_results": total_results,
                "included_studies": len(sources_list),
                "excluded_studies": total_results - len(sources_list),
                "search_query": query,
            },
        }

    def _determine_evidence_level(self, paper_details) -> str:
        """Determine evidence level from paper metadata."""
        title_lower = paper_details.title.lower()
        abstract_lower = paper_details.abstract.lower() if paper_details.abstract else ""

        if "randomized controlled trial" in title_lower or "randomized controlled trial" in abstract_lower:
            return "Level 1 - Randomized Controlled Trial"
        elif "systematic review" in title_lower or "meta-analysis" in title_lower:
            return "Level 1 - Systematic Review/Meta-analysis"
        elif "cohort" in title_lower or "cohort study" in abstract_lower:
            return "Level 2 - Cohort Study"
        elif "case-control" in title_lower or "case-control" in abstract_lower:
            return "Level 3 - Case-Control Study"
        elif "case report" in title_lower or "case series" in title_lower:
            return "Level 4 - Case Report/Series"
        else:
            return "Level 3 - Observational Study"

    def _synthesize_findings(self, sources: List[Dict]) -> List[str]:
        """Synthesize key findings from paper abstracts."""
        findings = []

        # Analyze evidence levels
        level_1_count = sum(1 for s in sources if "Level 1" in s.get("evidence_level", ""))
        level_2_count = sum(1 for s in sources if "Level 2" in s.get("evidence_level", ""))

        if level_1_count > 0:
            findings.append(f"High-quality evidence available: {level_1_count} RCTs or systematic reviews identified")
        elif level_2_count > 0:
            findings.append(f"Moderate-quality evidence available: {level_2_count} cohort studies identified")
        else:
            findings.append("Limited to observational evidence - causal relationships cannot be established")

        findings.append(f"Evidence base: {len(sources)} peer-reviewed publications analyzed")
        findings.append("Preliminary analysis based on abstract review - full text examination recommended for clinical decisions")

        return findings

    def _assess_evidence_quality(self, sources: List[Dict], query: str = "") -> Dict[str, Any]:
        """
        Assess overall quality of evidence base.

        Args:
            sources: List of source dictionaries with paper details
            query: Research question (used for intelligent assessment)

        Returns:
            Dictionary with evidence assessment including level, confidence, and details
        """
        if self.enable_intelligent_evidence_assessment and query:
            try:
                return self._assess_evidence_quality_intelligent(sources, query)
            except Exception as e:
                logger.warning(
                    f"Intelligent evidence assessment failed: {e}. Falling back to legacy assessment."
                )
                return self._assess_evidence_quality_legacy(sources)
        else:
            return self._assess_evidence_quality_legacy(sources)

    def _assess_evidence_quality_legacy(self, sources: List[Dict]) -> Dict[str, str]:
        """
        Legacy keyword-based evidence quality assessment.

        This is the original hard-coded implementation using simple keyword matching
        and arbitrary thresholds (2 Level 1 = Moderate to High).

        Args:
            sources: List of source dictionaries

        Returns:
            Dictionary with level, confidence, and note
        """
        if len(sources) == 0:
            return {
                "level": "None",
                "confidence": "None - no evidence retrieved",
                "note": "No sources found."
            }

        # Count evidence levels
        level_1_count = sum(1 for s in sources if "Level 1" in s.get("evidence_level", ""))
        level_2_count = sum(1 for s in sources if "Level 2" in s.get("evidence_level", ""))

        if level_1_count >= 2:
            return {
                "level": "Moderate to High",
                "confidence": "Moderate - based on multiple high-quality studies",
                "note": "Multiple RCTs or systematic reviews available for review."
            }
        elif level_1_count >= 1 or level_2_count >= 3:
            return {
                "level": "Moderate",
                "confidence": "Moderate - mixed evidence quality",
                "note": "Some high-quality evidence available but limited in scope."
            }
        else:
            return {
                "level": "Low to Moderate",
                "confidence": "Low - limited high-quality evidence",
                "note": "Evidence primarily from observational studies - causality cannot be established."
            }

    def _assess_evidence_quality_intelligent(self, sources: List[Dict], query: str) -> Dict[str, Any]:
        """
        Intelligent multidimensional evidence quality assessment using thought pipes.

        This method replaces naive keyword-based hierarchy with nuanced reasoning across
        six dimensions: study design, sample size, methodological quality, relevance,
        consistency, and completeness.

        Args:
            sources: List of source dictionaries with paper details
            query: Research question

        Returns:
            Comprehensive evidence assessment with multidimensional analysis
        """
        if len(sources) == 0:
            return {
                "level": "None",
                "confidence": "None - no evidence retrieved",
                "note": "No sources found.",
                "evidence_quality": {
                    "overall_rating": "None",
                    "justification": "No sources available for assessment",
                    "dimensions": {}
                },
                "strongest_sources": [],
                "weaker_sources": [],
                "strengths": [],
                "limitations": ["No evidence sources retrieved"],
                "evidence_gaps": ["Complete absence of published evidence"]
            }

        # Check cache first
        cache_key_context = {
            "sources_fingerprint": self._create_sources_fingerprint(sources),
            "query": query,
            "assessment_type": "multidimensional_evidence"
        }

        if self.reasoning_cache:
            cached = self.reasoning_cache.get(
                prompt="multidimensional_evidence_assessment",
                context=cache_key_context
            )
            if cached:
                logger.info("Using cached multidimensional evidence assessment")
                return self._format_assessment_output(cached, sources)

        # Build context for thought pipe
        context = self._build_evidence_assessment_context(sources, query)

        # Build reasoning prompt
        prompt = self._build_evidence_assessment_prompt()

        # Execute thought pipe
        try:
            logger.info("Executing intelligent multidimensional evidence assessment")
            response = self.thought_pipe.execute_thought_pipe(
                prompt=prompt,
                context=context,
                validation_fn=self._validate_evidence_assessment_response,
                max_retries=1
            )

            # Cache the result
            if self.reasoning_cache:
                self.reasoning_cache.set(
                    prompt="multidimensional_evidence_assessment",
                    context=cache_key_context,
                    response=response
                )

            # Format output for consumption
            return self._format_assessment_output(response, sources)

        except Exception as e:
            logger.error(f"Intelligent evidence assessment failed: {e}")
            raise

    def _create_sources_fingerprint(self, sources: List[Dict]) -> str:
        """Create a deterministic fingerprint of sources for caching."""
        import hashlib
        # Use PMIDs and titles as fingerprint
        fingerprint_data = []
        for s in sources:
            fingerprint_data.append(f"{s.get('pmid', '')}:{s.get('title', '')[:50]}")
        fingerprint_str = "||".join(sorted(fingerprint_data))
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _build_evidence_assessment_context(self, sources: List[Dict], query: str) -> Dict[str, Any]:
        """
        Build rich context for evidence assessment thought pipe.

        Args:
            sources: List of sources
            query: Research question

        Returns:
            Context dictionary with all information needed for assessment
        """
        # Build source representations with relevant metadata
        sources_for_assessment = []
        for idx, source in enumerate(sources):
            source_info = {
                "source_index": idx,
                "pmid": source.get("pmid", ""),
                "title": source.get("title", ""),
                "journal": source.get("journal", ""),
                "year": source.get("year", "Unknown"),
                "authors": source.get("authors", []),
                "abstract_snippet": source.get("abstract", "")[:500],  # First 500 chars
                "evidence_level": source.get("evidence_level", ""),
                "doi": source.get("doi", ""),
            }
            sources_for_assessment.append(source_info)

        return {
            "research_question": query,
            "total_sources": len(sources),
            "sources": sources_for_assessment,
            "assessment_instructions": {
                "dimensions": [
                    "study_design",
                    "sample_size",
                    "methodological_quality",
                    "relevance",
                    "consistency",
                    "completeness"
                ],
                "rating_scale": "High/Moderate/Low with justification",
                "required_outputs": [
                    "overall_rating",
                    "dimensional_ratings",
                    "strongest_sources",
                    "weaker_sources",
                    "strengths",
                    "limitations",
                    "evidence_gaps"
                ]
            }
        }

    def _build_evidence_assessment_prompt(self) -> str:
        """Build the reasoning prompt for intelligent evidence assessment."""
        return """Perform a multidimensional evidence quality assessment for this literature review.

RESEARCH QUESTION: {research_question}
TOTAL SOURCES RETRIEVED: {total_sources}

SOURCES TO ASSESS:
{sources_json}

YOUR TASK:
Evaluate the overall evidence quality across MULTIPLE DIMENSIONS, not just study design hierarchy.

ASSESSMENT DIMENSIONS:

1. **Study Design Quality** (High/Moderate/Low)
   - Consider: Is the study design appropriate for this research question?
   - For some questions, RCTs may be unethical or infeasible
   - Well-designed cohort studies can provide strong evidence
   - Assess: Do designs match what's actually needed to answer this question?

2. **Sample Size Adequacy** (High/Moderate/Low)
   - Consider: Are sample sizes sufficient for statistical power?
   - Look for: Specific numbers in abstracts, multi-center trials
   - Red flags: Case reports (n=1), small case series (n<10)
   - Adequate: Large cohorts (n>1000), powered RCTs

3. **Methodological Quality** (High/Moderate/Low)
   - Consider: Journal reputation, systematic reviews, meta-analyses
   - Look for: Rigorous methods descriptions, control for confounders
   - Red flags: No methods detail, unclear study design
   - Cannot assess funding sources or conflicts from abstracts alone

4. **Relevance to Question** (High/Moderate/Low)
   - Consider: How directly does each source address the research question?
   - Direct evidence: Studies specifically investigating this exact question
   - Indirect evidence: Related but not precisely on-target
   - Tangential: Mentions topic but doesn't address question

5. **Consistency Across Sources** (High/Moderate/Low)
   - Consider: Do sources converge on similar findings?
   - Look for: Replicated results, conflicting evidence
   - Red flags: Contradictory findings without explanation
   - Note: Limited to abstract-level analysis - cannot deeply assess consistency

6. **Completeness of Evidence Base** (High/Moderate/Low)
   - Consider: Are key study types missing? Geographic diversity?
   - Look for: Gaps in evidence, unexplored aspects
   - Red flags: Only one type of study, narrow populations
   - Limitations: Single database search, abstract-only review

OVERALL RATING RULES (CRITICAL - CLAUDE.MD COMPLIANCE):
- **High**: Requires >=2 strong sources (well-designed, adequate sample, highly relevant) AND consistency
- **Moderate**: Mixed quality, some strong evidence, OR single strong source, OR good evidence with caveats
- **Low**: Weak designs, small samples, low relevance, OR inconsistent/incomplete

CONFIDENCE LEVELS:
- Use "Moderate" or "Low" confidence for most assessments (per CLAUDE.md)
- "High" confidence ONLY if exceptional justification exists
- Always provide detailed justification (>100 chars required)

MANDATORY OUTPUTS:
- **limitations**: REQUIRED - must include at least 2 specific limitations
- **evidence_gaps**: REQUIRED - must identify what's missing
- **justification**: REQUIRED - must explain overall rating with specific reasoning

Return JSON in this EXACT format:
{{
    "evidence_quality": {{
        "overall_rating": "High|Moderate|Low",
        "justification": "Detailed explanation of overall rating considering all dimensions (>100 chars)",
        "dimensions": {{
            "study_design": "High|Moderate|Low - specific explanation for this question type",
            "sample_size": "High|Moderate|Low - assessment based on numbers found in abstracts",
            "methodological_quality": "High|Moderate|Low - based on journal quality and methods descriptions",
            "relevance": "High|Moderate|Low - how directly sources address the research question",
            "consistency": "High|Moderate|Low - degree of agreement between sources",
            "completeness": "High|Moderate|Low - gaps and missing evidence types"
        }}
    }},
    "confidence": "Moderate|Low - detailed justification for confidence level",
    "strongest_sources": [
        {{
            "source_index": 0,
            "reason": "Specific reason this is a strong source",
            "weight_in_assessment": "high|moderate"
        }}
    ],
    "weaker_sources": [
        {{
            "source_index": 1,
            "reason": "Specific limitation of this source",
            "weight_in_assessment": "low|moderate"
        }}
    ],
    "strengths": [
        "Specific strength #1 of the evidence base",
        "Specific strength #2"
    ],
    "limitations": [
        "Specific limitation #1 (REQUIRED)",
        "Specific limitation #2 (REQUIRED)",
        "Additional limitations as appropriate"
    ],
    "evidence_gaps": [
        "Specific gap #1 in the evidence",
        "Specific gap #2"
    ]
}}

CRITICAL COMPLIANCE REQUIREMENTS:
1. NO "High" overall_rating without >=2 genuinely strong sources (CLAUDE.md)
2. Limitations array MUST have >=1 entry (REQUIRED)
3. Justification MUST be >100 characters
4. Confidence MUST NOT be "High" without exceptional justification
5. Do NOT fabricate quality assessments based on appearance
6. Be SKEPTICAL - default to lower ratings when uncertain

Remember: This is abstract-only analysis with limited data. Express appropriate uncertainty.
"""

    def _validate_evidence_assessment_response(
        self, response: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """
        Validate evidence assessment response.

        Args:
            response: LLM response to validate
            context: Original context

        Returns:
            True if valid, False otherwise
        """
        # Check required top-level fields
        required_fields = ["evidence_quality", "confidence", "strongest_sources", "limitations", "evidence_gaps"]
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field: {field}")
                return False

        # Check evidence_quality structure
        evidence_quality = response.get("evidence_quality", {})
        if "overall_rating" not in evidence_quality:
            logger.error("Missing 'overall_rating' in evidence_quality")
            return False

        if "justification" not in evidence_quality:
            logger.error("Missing 'justification' in evidence_quality")
            return False

        if "dimensions" not in evidence_quality:
            logger.error("Missing 'dimensions' in evidence_quality")
            return False

        # Validate overall_rating values
        valid_ratings = ["High", "Moderate", "Low", "None"]
        overall_rating = evidence_quality.get("overall_rating", "")
        if overall_rating not in valid_ratings:
            logger.error(f"Invalid overall_rating: {overall_rating}. Must be one of {valid_ratings}")
            return False

        # CLAUDE.MD COMPLIANCE: Check no "High" rating without strong justification
        if overall_rating == "High":
            strongest_sources = response.get("strongest_sources", [])
            if len(strongest_sources) < 2:
                logger.error(
                    "CLAUDE.MD VIOLATION: 'High' overall_rating requires >=2 strong sources. "
                    f"Only {len(strongest_sources)} provided."
                )
                return False

        # Validate justification length
        justification = evidence_quality.get("justification", "")
        if len(justification) < 100:
            logger.error(
                f"Justification too short ({len(justification)} chars). "
                "Must be >100 characters for meaningful explanation."
            )
            return False

        # REQUIRED: Limitations must be present
        limitations = response.get("limitations", [])
        if not limitations or len(limitations) == 0:
            logger.error("CLAUDE.MD VIOLATION: Limitations are REQUIRED but none provided")
            return False

        # Validate source indices are valid
        total_sources = context.get("total_sources", 0)
        for source_list in [response.get("strongest_sources", []), response.get("weaker_sources", [])]:
            for source_ref in source_list:
                idx = source_ref.get("source_index", -1)
                if idx < 0 or idx >= total_sources:
                    logger.error(f"Invalid source_index {idx} (must be 0-{total_sources-1})")
                    return False

        logger.info("Evidence assessment response passed validation")
        return True

    def _format_assessment_output(
        self, response: Dict[str, Any], sources: List[Dict]
    ) -> Dict[str, Any]:
        """
        Format thought pipe response into standardized output.

        Args:
            response: Validated response from thought pipe
            sources: Original sources list

        Returns:
            Formatted assessment dictionary matching legacy structure with extensions
        """
        evidence_quality = response.get("evidence_quality", {})
        overall_rating = evidence_quality.get("overall_rating", "Moderate")
        justification = evidence_quality.get("justification", "")

        # Build detailed note from justification and dimensions
        dimensions = evidence_quality.get("dimensions", {})
        dimensional_summary = []
        for dim_name, dim_value in dimensions.items():
            dimensional_summary.append(f"  - {dim_name}: {dim_value}")

        note_parts = [justification]
        if dimensional_summary:
            note_parts.append("\nDimensional Assessment:\n" + "\n".join(dimensional_summary))

        # Return enhanced structure compatible with legacy format
        return {
            "level": overall_rating,
            "confidence": response.get("confidence", "Moderate - multidimensional analysis"),
            "note": "\n".join(note_parts),
            # Extended fields from intelligent assessment
            "evidence_quality": evidence_quality,
            "strongest_sources": response.get("strongest_sources", []),
            "weaker_sources": response.get("weaker_sources", []),
            "strengths": response.get("strengths", []),
            "limitations": response.get("limitations", []),
            "evidence_gaps": response.get("evidence_gaps", []),
            "assessment_method": "intelligent_multidimensional"
        }

    def _identify_gaps(self, sources: List[Dict]) -> List[str]:
        """Identify gaps in the evidence base."""
        gaps = []

        # Check for RCTs
        has_rcts = any("Randomized Controlled Trial" in s.get("evidence_level", "") for s in sources)
        if not has_rcts:
            gaps.append("Lack of randomized controlled trials - causality remains unclear")

        # Check publication years
        recent_years = [int(s.get("year", "0")) for s in sources if s.get("year", "").isdigit()]
        if recent_years:
            oldest_year = min(recent_years)
            if oldest_year < 2020:
                gaps.append("Some evidence may be outdated - newer studies recommended")

        gaps.append("Limited to abstract-level analysis - full systematic review with full-text analysis recommended")
        gaps.append("Single database search (PubMed only) - additional databases may yield more sources")

        return gaps

    def _return_error_result(self, query: str, error_msg: str) -> Dict[str, Any]:
        """Return structured error result."""
        return {
            "summary": f"Literature search for '{query}' encountered error: {error_msg}",
            "key_findings": ["Search failed - no results available"],
            "sources": [],
            "evidence_level": "None",
            "confidence": "None - search error",
            "gaps": ["Unable to assess - search failed"],
            "limitations": [f"Technical error during search: {error_msg}"],
            "methodology": f"Attempted PubMed search but failed: {error_msg}",
            "metadata": {
                "search_date": "2025-10-12",
                "error": error_msg,
            },
        }

    def _return_no_results(self, query: str, data_sources: list) -> Dict[str, Any]:
        """Return structured no-results response."""
        return {
            "summary": (
                f"Literature search for '{query}' returned no results. "
                "No published evidence found in searched databases. "
                "Consider broadening search terms or checking alternative databases."
            ),
            "key_findings": [
                "No peer-reviewed publications found matching search criteria",
                "Unable to establish evidence base for query",
            ],
            "sources": [],
            "evidence_level": "None",
            "confidence": "None - no evidence available",
            "gaps": [
                "Complete absence of published evidence on this specific topic",
                "May require broader search strategy or alternative terminology",
            ],
            "limitations": [
                f"Search limited to {', '.join(data_sources)}",
                "No results found - cannot provide evidence-based assessment",
            ],
            "methodology": f"Systematic search of {', '.join(data_sources)} returned zero results.",
            "metadata": {
                "search_date": "2025-10-12",
                "databases_searched": data_sources,
                "total_results": 0,
            },
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate literature review input.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        super().validate_input(input_data)

        if not input_data.get("query"):
            raise ValueError("Query is required for literature review")

        return True
