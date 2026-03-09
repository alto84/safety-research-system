"""
Regulatory Framework Data for Patient Safety Dashboard Expandable Detail Panels.

Contains structured regulatory data for Sections 5-8 of the Prosinertimib dashboard:
- Section 5: ICSR Case Processing
- Section 6: Signal Detection & Management
- Section 7: Aggregate Reporting
- Section 8: Risk Management

All data sourced from primary regulatory documents with exact references.
"""

# =============================================================================
# SECTION 5: ICSR CASE PROCESSING
# =============================================================================

ICSR_CASE_PROCESSING = {
    "title": "Individual Case Safety Report (ICSR) Processing",
    "regulatory_framework": {
        "fda_ind_safety": {
            "title": "FDA IND Safety Reporting (Pre-Marketing)",
            "regulation": "21 CFR 312.32",
            "source_url": "https://www.law.cornell.edu/cfr/text/21/312.32",
            "definitions": {
                "adverse_event": (
                    "Any untoward medical occurrence associated with the use of a drug "
                    "in humans, whether or not considered drug related."
                ),
                "serious_adverse_event": (
                    "Results in: death, life-threatening event, inpatient hospitalization "
                    "or prolongation of existing hospitalization, persistent or significant "
                    "disability/incapacity, congenital anomaly/birth defect, or important "
                    "medical events requiring intervention to prevent one of these outcomes."
                ),
                "suspected_adverse_reaction": (
                    "An adverse event for which there is a reasonable possibility that the "
                    "drug caused the adverse event. 'Reasonable possibility' means there is "
                    "evidence to suggest a causal relationship between the drug and the "
                    "adverse event."
                ),
                "unexpected": (
                    "Not listed in the current investigator's brochure; or, if no IB, not "
                    "consistent with the risk information described in the general "
                    "investigational plan or elsewhere in the IND application."
                ),
            },
            "reporting_timelines": {
                "seven_day_report": {
                    "trigger": "Unexpected fatal or life-threatening suspected adverse reaction",
                    "timeline": "As soon as possible, no later than 7 calendar days after initial receipt",
                    "follow_up": "15-day follow-up report with complete information",
                    "recipient": "FDA (via MedWatch/FAERS)",
                    "cfr_reference": "21 CFR 312.32(c)(2)",
                },
                "fifteen_day_report": {
                    "trigger": "Any of the following: (1) Serious and unexpected suspected adverse "
                               "reaction; (2) Findings from epidemiological or clinical studies "
                               "suggesting significant risk; (3) Clinically important increase in "
                               "rate of a serious suspected adverse reaction; (4) Animal/in vitro "
                               "findings suggesting significant risk (mutagenicity, teratogenicity, "
                               "carcinogenicity)",
                    "timeline": "As soon as possible, no later than 15 calendar days after determination "
                                "that information qualifies for reporting",
                    "recipient": "FDA and all participating investigators",
                    "cfr_reference": "21 CFR 312.32(c)(1)",
                    "examples_strongly_associated": [
                        "Angioedema",
                        "Hepatic injury",
                        "Stevens-Johnson Syndrome",
                    ],
                },
                "follow_up": {
                    "requirement": "Promptly investigate all safety information; submit relevant "
                                   "follow-up as soon as information is available",
                    "reclassification": "If initially non-reportable event is later determined "
                                        "reportable, report within 15 calendar days of determination",
                    "cfr_reference": "21 CFR 312.32(d)",
                },
            },
            "report_format": {
                "options": [
                    "FDA Form 3500A (MedWatch)",
                    "CIOMS I Form",
                    "Narrative format",
                    "Electronic format (E2B)",
                ],
                "labeling": "Must be prominently identified as 'IND Safety Report'",
            },
        },
        "fda_postmarketing": {
            "title": "FDA Post-Marketing Reporting",
            "regulation": "21 CFR 314.80",
            "source_url": "https://www.law.cornell.edu/cfr/text/21/314.80",
            "definitions": {
                "adverse_drug_experience": (
                    "Any adverse event associated with the use of a drug in humans, "
                    "whether or not considered drug related, including events from: "
                    "overdose, abuse, withdrawal, and failure of expected pharmacological action."
                ),
                "unexpected_adverse_drug_experience": (
                    "Any adverse drug experience that is not listed in the current labeling "
                    "for the drug product, including events that may be symptomatically and "
                    "pathophysiologically related but differ in severity or specificity "
                    "from labeled events."
                ),
            },
            "reporting_timelines": {
                "fifteen_day_alert_report": {
                    "trigger": "Adverse drug experience that is BOTH serious AND unexpected, "
                               "whether foreign or domestic",
                    "timeline": "As soon as possible, no later than 15 calendar days from "
                                "initial receipt of information",
                    "follow_up": "Promptly investigate; follow-up within 15 calendar days "
                                 "of receipt of new information or as requested by FDA",
                    "cfr_reference": "21 CFR 314.80(c)(1)",
                },
                "periodic_reports": {
                    "quarterly": {
                        "duration": "First 3 years after NDA approval",
                        "deadline": "Within 30 days of close of each quarter",
                        "quarter_start": "First quarter begins on date of NDA approval",
                    },
                    "annual": {
                        "duration": "After first 3 years, ongoing",
                        "deadline": "Within 60 days of anniversary date of NDA approval",
                    },
                    "cfr_reference": "21 CFR 314.80(c)(2)",
                    "note": "FDA may extend, reestablish, or modify periodic reporting requirements",
                },
            },
            "required_information": {
                "patient_info": [
                    "Patient identification code",
                    "Age or date of birth",
                    "Gender",
                    "Weight",
                ],
                "adverse_experience_info": [
                    "Outcome attributed to the adverse experience",
                    "Date of onset",
                    "Description of event",
                    "Medical narrative (including treatment and outcome)",
                    "Relevant diagnostic tests/lab data",
                    "Patient medical history",
                ],
                "product_info": [
                    "Drug name (proprietary and established)",
                    "Dose, frequency, route of administration",
                    "Therapy dates",
                    "Indication for use",
                    "NDC number",
                    "Lot number and expiration date (if available)",
                ],
                "reporter_info": [
                    "Name and contact information",
                    "Whether healthcare professional",
                    "Report source",
                ],
            },
        },
        "ema_gvp_module_vi": {
            "title": "EMA GVP Module VI: Collection, Management and Submission of ICSRs",
            "guideline": "GVP Module VI Rev 2",
            "source_url": "https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/"
                          "pharmacovigilance-post-authorisation/periodic-safety-update-reports-psurs",
            "reporting_timelines": {
                "serious_icsr": {
                    "timeline": "15 calendar days from receipt (Day 0 = date of awareness)",
                    "scope": "All serious suspected adverse reactions, domestic and foreign",
                    "destination": "EudraVigilance",
                    "gvp_reference": "GVP Module VI, Section VI.B.6",
                },
                "non_serious_icsr": {
                    "timeline": "90 calendar days from receipt",
                    "scope": "Non-serious suspected adverse reactions from spontaneous reports",
                    "destination": "EudraVigilance",
                    "gvp_reference": "GVP Module VI, Section VI.B.7",
                },
                "follow_up_reports": {
                    "timeline": "Within 15 calendar days for serious (new significant info); "
                                "within 90 calendar days for non-serious follow-up",
                    "gvp_reference": "GVP Module VI, Section VI.B.8",
                },
            },
            "case_validation_criteria": {
                "description": "A valid ICSR requires four minimum elements (GVP Module VI.B.1):",
                "minimum_elements": [
                    "An identifiable reporter",
                    "An identifiable patient",
                    "At least one suspected adverse reaction",
                    "At least one suspect medicinal product",
                ],
                "note": "Day 0 (clock start) is defined as the date the MAH first becomes "
                        "aware of the case meeting all four minimum criteria.",
            },
            "electronic_submission": {
                "format": "ICH E2B(R3) — XML-based, HL7v3 derived",
                "system": "EudraVigilance (EU), FAERS (US), VigiBase (WHO)",
            },
        },
    },
    "meddra_coding": {
        "title": "MedDRA Coding Requirements",
        "current_version": "27.1 (September 2024; updates released March and September each year)",
        "maintained_by": "MedDRA MSSO (Maintenance and Support Services Organization)",
        "hierarchy_levels": {
            "SOC": {
                "full_name": "System Organ Class",
                "count": 27,
                "description": "Highest level; groups by etiology, manifestation site, or purpose "
                               "(e.g., 'Respiratory, thoracic and mediastinal disorders')",
                "level": 1,
            },
            "HLGT": {
                "full_name": "High-Level Group Term",
                "description": "Superordinate grouping of HLTs linked to at least one SOC and one HLT",
                "level": 2,
            },
            "HLT": {
                "full_name": "High-Level Term",
                "description": "Groups PTs by clinical/anatomical/physiological/functional affinity",
                "level": 3,
            },
            "PT": {
                "full_name": "Preferred Term",
                "description": "Fundamental coding level for adverse events; each PT maps to at "
                               "least one SOC (primary SOC assignment used for primary classification)",
                "level": 4,
            },
            "LLT": {
                "full_name": "Lowest Level Term",
                "description": "Most granular level; each LLT maps to exactly one PT. Includes "
                               "synonyms, lexical variants, sub-concepts, and verbatim reporter terms.",
                "level": 5,
            },
        },
        "special_groupings": {
            "SMQ": {
                "full_name": "Standardised MedDRA Query",
                "description": "Validated groupings of PTs for retrieving cases of specific "
                               "medical conditions (e.g., 'Interstitial lung disease' SMQ). "
                               "Narrow and Broad search scopes available.",
            },
        },
        "icsr_coding_rules": [
            "Code adverse events at the PT level (LLT may be captured for verbatim term)",
            "Use current MedDRA version for all new and updated ICSRs",
            "Primary SOC assignment determines primary classification for aggregate reporting",
            "Reporter's verbatim term should be coded to the most specific applicable PT",
            "Medical review may recode terms if clinical context warrants more accurate coding",
        ],
    },
    "e2b_r3_format": {
        "title": "ICH E2B(R3) ICSR Electronic Transmission Standard",
        "ich_reference": "ICH E2B(R3) Implementation Guide",
        "format": "XML based on HL7 version 3 messaging standard",
        "key_features": [
            "Replaced E2B(R2) with expanded fields and standardized terminology",
            "Supports structured data with controlled vocabularies",
            "Null Flavors allowed for Date and Text fields when data unavailable",
            "Each ICSR message has unique batch identifier",
        ],
        "standardized_terminologies": {
            "adverse_reactions": "MedDRA (Preferred Terms)",
            "country_codes": "ISO 3166",
            "gender_codes": "ISO/HL7",
            "language_codes": "ISO 639",
            "units_of_measurement": "UCUM (Unified Code for Units of Measure)",
            "medicinal_products": "ISO IDMP (Identification of Medicinal Products)",
        },
        "key_data_sections": {
            "A": "Administrative and identification information",
            "B": {
                "B.1": "Patient characteristics (age, sex, weight, height, medical history)",
                "B.2": "Reaction(s)/Event(s) (MedDRA coded, onset date, duration, outcome, seriousness criteria)",
                "B.3": "Results of tests and procedures",
                "B.4": "Drug information (suspect, concomitant, interacting)",
                "B.5": "Narrative (case summary and reporter's comments)",
            },
            "C": "Literature reference (if applicable)",
            "D": "Study identification (if from clinical trial)",
        },
        "validation_rules": [
            "XML validated against XSD (XML Schema Definition) automatically during generation",
            "All mandatory data elements must be present in ICSR message",
            "Batch transmission requires: batch number, sender ID, receiver ID, transmission date",
            "MedDRA terms must match current version dictionary",
            "Date formats must follow ISO 8601 (YYYYMMDD or partial dates permitted)",
            "Null Flavor values accepted for unknown/masked data elements",
        ],
    },
    "icsr_workflow": {
        "title": "ICSR Case Processing Workflow",
        "steps": {
            "1_intake": {
                "name": "Case Intake / Receipt",
                "description": "Initial receipt of adverse event information from any source",
                "sources": [
                    "Spontaneous reports (HCPs, patients, consumers)",
                    "Clinical trial SAE reports",
                    "Literature / medical journals",
                    "Regulatory authority reports",
                    "Patient support programs",
                    "Social media / digital sources",
                    "Solicited reports (market research, patient surveys)",
                ],
                "key_action": "Assign Day 0 (date of first awareness of reportable information)",
                "typical_time": "Same day as receipt",
            },
            "2_triage": {
                "name": "Triage and Prioritization",
                "description": "Assess against minimum validity criteria and prioritize by regulatory deadline",
                "key_actions": [
                    "Verify 4 minimum validity elements (reporter, patient, drug, event)",
                    "Assess seriousness (death, life-threatening, hospitalization, disability, congenital anomaly)",
                    "Check expectedness against product labeling / Reference Safety Information",
                    "Assess listedness (EU) / labeledness (US)",
                    "Flag expedited cases (serious unexpected = 15 days; fatal/life-threatening unexpected = 7 days)",
                    "Identify duplicates",
                ],
                "typical_time": "Within 24 hours of receipt (Day 0 to Day 1)",
            },
            "3_data_entry": {
                "name": "Data Entry and Coding",
                "description": "Enter all case data into safety database; code terms",
                "key_actions": [
                    "Enter patient demographics, medical history, concomitant medications",
                    "Enter adverse event verbatim term and code to MedDRA PT/LLT",
                    "Enter suspect drug details (dose, route, frequency, start/stop dates)",
                    "Code drug names using WHODrug dictionary",
                    "Enter reporter details and report source",
                    "Enter seriousness criteria and outcome",
                ],
                "typical_time": "Days 1-5 (depending on complexity)",
            },
            "4_medical_review": {
                "name": "Medical Review / Assessment",
                "description": "Physician or qualified medical reviewer assesses the case",
                "key_actions": [
                    "Causality assessment (WHO-UMC scale or company-specific algorithm)",
                    "Confirm seriousness and expectedness classification",
                    "Evaluate for potential signals",
                    "Write/review clinical narrative (structured medical summary)",
                    "Assess need for follow-up information",
                    "Document medical reviewer's assessment and rationale",
                ],
                "causality_categories": [
                    "Certain", "Probable/Likely", "Possible",
                    "Unlikely", "Conditional/Unclassified", "Unassessable/Unclassifiable",
                ],
                "typical_time": "Days 3-8",
            },
            "5_quality_control": {
                "name": "Quality Control (QC)",
                "description": "Independent review of case for accuracy and completeness",
                "key_actions": [
                    "Verify data entry accuracy against source document",
                    "Confirm MedDRA coding accuracy",
                    "Verify seriousness and expectedness classification",
                    "Check regulatory reporting determination is correct",
                    "Verify case narrative is clinically accurate and complete",
                    "Confirm E2B(R3) fields populated correctly",
                ],
                "typical_time": "Days 5-10 (expedited); Days 10-80 (non-expedited)",
            },
            "6_submission": {
                "name": "Regulatory Submission",
                "description": "Submit finalized ICSR to applicable regulatory authorities",
                "key_actions": [
                    "Generate E2B(R3) XML file from safety database",
                    "Validate against XSD schema",
                    "Transmit to EudraVigilance (EU), FAERS (US), VigiBase (WHO) as applicable",
                    "Confirm acknowledgment receipt from regulatory gateway",
                    "Document submission date and confirmation",
                ],
                "deadlines": {
                    "fatal_life_threatening_unexpected": "Day 7 (FDA IND) / Day 15 (post-marketing)",
                    "serious_unexpected": "Day 15",
                    "serious_expected": "Periodic report (if applicable)",
                    "non_serious": "Day 90 (EU via EudraVigilance)",
                },
            },
        },
        "kpis": {
            "title": "Typical Case Processing KPIs",
            "metrics": {
                "expedited_compliance": {
                    "description": "Percentage of expedited ICSRs submitted within regulatory deadline",
                    "target": ">= 95% submitted within 15 calendar days",
                    "industry_benchmark": "Top quartile: >= 98%",
                },
                "seven_day_compliance": {
                    "description": "Fatal/life-threatening unexpected IND cases reported within 7 days",
                    "target": "100% compliance (regulatory requirement)",
                },
                "case_processing_time": {
                    "description": "Average time from Day 0 to submission-ready",
                    "target_expedited": "<= 10 calendar days (allow 5-day buffer before 15-day deadline)",
                    "target_non_expedited": "<= 60 calendar days (for 90-day non-serious)",
                },
                "data_entry_accuracy": {
                    "description": "Percentage of cases passing QC without rework",
                    "target": ">= 90% first-pass accuracy",
                },
                "duplicate_detection_rate": {
                    "description": "Percentage of duplicate cases identified before processing",
                    "target": ">= 95% detection rate",
                },
                "backlog": {
                    "description": "Number of cases pending beyond target processing time",
                    "target": "Zero cases past regulatory deadline",
                },
                "follow_up_rate": {
                    "description": "Percentage of cases where follow-up was requested and received",
                    "target": ">= 60% response rate on follow-up requests",
                },
            },
        },
    },
}


# =============================================================================
# SECTION 6: SIGNAL DETECTION & MANAGEMENT
# =============================================================================

SIGNAL_DETECTION_MANAGEMENT = {
    "title": "Signal Detection and Management",
    "regulatory_framework": {
        "gvp_module_ix": {
            "title": "GVP Module IX: Signal Management (Rev 1)",
            "guideline": "EMA/827661/2011 Rev 1",
            "source_url": "https://www.ema.europa.eu/en/human-regulatory-overview/"
                          "post-authorisation/pharmacovigilance-post-authorisation",
            "signal_definition": (
                "Information that arises from one or multiple sources, including observations "
                "and experiments, which suggests a new potentially causal association, or a "
                "new aspect of a known association, between an intervention and an event or "
                "set of related events, either adverse or beneficial, that is judged to be "
                "of sufficient likelihood to justify verificatory action."
            ),
            "signal_definition_source": "CIOMS VIII Working Group / WHO",
        },
        "ich_e2c_r2": {
            "title": "ICH E2C(R2): Periodic Benefit-Risk Evaluation Report (PBRER)",
            "description": "Signals must be evaluated in Section 15 (Overview of Signals) and "
                           "Section 16 (Signal and Risk Evaluation) of the PBRER. New, ongoing, "
                           "and closed signals during the reporting interval must be summarized.",
            "reference": "ICH E2C(R2), Sections 15-16",
        },
    },
    "statistical_methods": {
        "disproportionality_analysis": {
            "description": "Statistical methods that compare the observed count of a drug-event "
                           "combination with what would be expected if drug and event were "
                           "independent (using a 2x2 contingency table).",
            "contingency_table": {
                "description": "a = target drug + target event; b = target drug + all other events; "
                               "c = all other drugs + target event; d = all other drugs + all other events",
            },
        },
        "prr": {
            "full_name": "Proportional Reporting Ratio",
            "category": "Frequentist",
            "formula": "PRR = [a/(a+b)] / [c/(c+d)]",
            "interpretation": "Ratio of the proportion of a specific event reported for the "
                              "drug of interest vs. the proportion for all other drugs",
            "signal_criteria": {
                "evans_2001": {
                    "description": "Evans et al. (2001) minimum signal criteria — most widely cited",
                    "thresholds": {
                        "PRR": ">= 2",
                        "case_count": ">= 3 cases (N >= 3)",
                        "chi_squared": ">= 4 (equivalent to p < 0.05 for 1 df)",
                    },
                    "reference": "Evans SJW, Waller PC, Davis S. Pharmacoepidemiol Drug Saf. 2001;10:483-486",
                },
            },
            "strengths": "Simple, transparent, easily interpretable",
            "limitations": "Unstable with small counts; does not account for confounding",
        },
        "ror": {
            "full_name": "Reporting Odds Ratio",
            "category": "Frequentist",
            "formula": "ROR = (a*d) / (b*c) = (a/c) / (b/d)",
            "interpretation": "Odds of the event being reported for the drug of interest vs. "
                              "odds for all other drugs",
            "signal_criteria": {
                "thresholds": {
                    "ROR_lower_CI": "Lower bound of 95% CI > 1",
                    "case_count": ">= 3 cases",
                },
            },
            "strengths": "Statistically well-understood (logistic regression analog); "
                         "similar performance to PRR in most scenarios",
            "limitations": "Same data quality issues as PRR; sensitive to sparse data",
            "note": "PRR and ROR perform equivalently in most practical scenarios (Waller et al.)",
        },
        "ebgm": {
            "full_name": "Empirical Bayes Geometric Mean",
            "category": "Bayesian",
            "method": "Multi-item Gamma-Poisson Shrinker (MGPS)",
            "developed_by": "FDA / DuMouchel (1999)",
            "used_in": "FAERS (FDA Adverse Event Reporting System)",
            "formula": "Bayesian shrinkage estimator of the ratio of observed-to-expected counts",
            "signal_criteria": {
                "primary": {
                    "EB05": ">= 2 (lower bound of 90% credibility interval around EBGM)",
                    "description": "Most commonly used threshold; conservative measure",
                },
                "alternative": {
                    "EBGM": "> 2 AND EB05 > 1",
                    "description": "Less conservative alternative combining point estimate and lower bound",
                },
                "case_count": ">= 3 cases (practical minimum)",
            },
            "strengths": "Robust with sparse data due to Bayesian shrinkage; reduces false signals "
                         "for rare drug-event combinations",
            "limitations": "Less transparent (black box); computationally more complex",
        },
        "bcpnn": {
            "full_name": "Bayesian Confidence Propagation Neural Network",
            "category": "Bayesian",
            "metric": "Information Component (IC)",
            "developed_by": "WHO Uppsala Monitoring Centre (Bate et al., 1998)",
            "used_in": "VigiBase (WHO Global ICSR Database)",
            "signal_criteria": {
                "IC025": "> 0 (lower bound of 95% credibility interval of IC)",
                "description": "IC is the log2 of the ratio of observed to expected; "
                               "IC025 > 0 means observed significantly exceeds expected",
            },
            "strengths": "Well-suited for large international databases; handles multi-drug multi-event",
            "limitations": "Less intuitive than frequentist measures",
        },
    },
    "signal_management_workflow": {
        "title": "Signal Management Workflow (per GVP Module IX)",
        "steps": {
            "1_detection": {
                "name": "Signal Detection",
                "description": "Active, systematic searching for new safety signals",
                "data_sources": [
                    "Spontaneous reporting databases (EudraVigilance, FAERS, VigiBase)",
                    "Company safety database (own ICSRs)",
                    "Clinical trial data (ongoing and completed studies)",
                    "Published literature (PubMed, Embase)",
                    "Non-interventional / observational studies",
                    "Toxicological / non-clinical data",
                    "Drug utilization data",
                ],
                "methods": [
                    "Disproportionality analysis (PRR, ROR, EBGM, IC)",
                    "Clinical review of individual serious ICSRs",
                    "Periodic aggregate review of case series",
                    "Literature surveillance (structured searches)",
                    "Observed-vs-expected analysis in clinical trials",
                ],
                "frequency": "MAHs: at least monthly for own data; EMA: continuous monitoring "
                             "of EudraVigilance using EVDAS (EudraVigilance Data Analysis System)",
                "gvp_reference": "GVP Module IX, Section IX.B.2",
            },
            "2_validation": {
                "name": "Signal Validation",
                "description": "Evaluating detected signals to determine whether they represent "
                               "a true new safety concern warranting further analysis",
                "criteria": [
                    "Strength of the disproportionality (magnitude of PRR/ROR/EBGM)",
                    "Clinical plausibility (known pharmacology, class effects)",
                    "Temporal relationship (appropriate time to onset)",
                    "Biological plausibility (mechanism of action)",
                    "Consistency across data sources",
                    "Dose-response relationship",
                    "Number and quality of cases",
                    "Previous awareness (is this truly new information?)",
                    "Seriousness and public health impact",
                    "Dechallenge/rechallenge data",
                ],
                "outcome": {
                    "validated_signal": "New potentially causal association confirmed as warranting "
                                        "further assessment. Proceeds to prioritization.",
                    "refuted_signal": "Evidence does not support a new causal association after review. "
                                      "Document rationale and close.",
                },
                "gvp_reference": "GVP Module IX, Section IX.B.3",
            },
            "3_prioritization": {
                "name": "Signal Prioritization",
                "description": "Ranking validated signals by urgency and public health impact",
                "criteria": [
                    "Seriousness of the adverse reaction (fatal, life-threatening, disabling)",
                    "Strength of evidence (number of cases, quality, consistency)",
                    "Novelty (completely new signal vs. new aspect of known risk)",
                    "Clinical context (availability of alternative treatments)",
                    "Public health impact (size of exposed population)",
                    "Potential for risk minimization",
                    "Reversibility of the adverse reaction",
                    "Preventability of the adverse reaction",
                ],
                "gvp_reference": "GVP Module IX, Section IX.B.4",
            },
            "4_assessment": {
                "name": "Signal Assessment",
                "description": "Comprehensive evaluation of all available evidence for a validated signal",
                "activities": [
                    "In-depth review of all available ICSRs (case series analysis)",
                    "Cumulative review of non-clinical and clinical data",
                    "Literature review (systematic if warranted)",
                    "Analysis of clinical trial data (if available)",
                    "Consultation with external experts (if needed)",
                    "Pharmacoepidemiological study (if needed for causal assessment)",
                    "Benefit-risk impact assessment",
                ],
                "output": "Signal assessment report documenting conclusions and recommended actions",
                "gvp_reference": "GVP Module IX, Section IX.B.5",
            },
            "5_recommendation_action": {
                "name": "Recommendation and Action",
                "description": "Determine and implement appropriate regulatory or risk management actions",
                "possible_actions": [
                    "Update product information (SmPC / USPI) with new safety information",
                    "Update Reference Safety Information (RSI) or Investigator's Brochure (IB)",
                    "Issue Dear Healthcare Professional Communication (DHPC)",
                    "Implement additional risk minimization measures",
                    "Initiate post-authorization safety study (PASS)",
                    "Restrict indication, add contraindication, or modify dose",
                    "Update RMP / REMS",
                    "Suspend or withdraw marketing authorization (extreme cases)",
                    "No action required (continue routine monitoring)",
                ],
                "gvp_reference": "GVP Module IX, Section IX.B.6",
            },
            "6_tracking": {
                "name": "Tracking and Documentation",
                "description": "All steps must be documented and auditable",
                "requirements": [
                    "Signal tracking tool/system recording all steps and decisions",
                    "Document who performed each step and when",
                    "Record rationale for all decisions (including refuted signals)",
                    "Include signal status in PBRER/PSUR (Section 15: Overview of Signals)",
                    "Maintain audit trail for regulatory inspection readiness",
                ],
                "gvp_reference": "GVP Module IX, Section IX.C",
            },
        },
    },
    "prac_signal_assessment": {
        "title": "PRAC Signal Assessment Procedures (EMA)",
        "full_name": "Pharmacovigilance Risk Assessment Committee",
        "process": {
            "eudravigilance_screening": (
                "EMA continuously screens EudraVigilance using EVDAS (EudraVigilance Data "
                "Analysis System). Statistical signals of disproportionate reporting (SDRs) "
                "are generated and reviewed."
            ),
            "signal_detection_by_ema": (
                "EMA signal detection team identifies potential signals and presents them "
                "to PRAC for validation and assessment."
            ),
            "prac_monthly_review": (
                "PRAC reviews new signals at monthly meetings. MAHs may be requested to "
                "provide assessment reports within defined timelines (typically 60 days)."
            ),
            "prac_assessment_outcomes": [
                "Signal confirmed — request SmPC update or risk minimization",
                "Signal requires further data — request PASS or other studies",
                "Signal refuted — no action, close signal tracking",
                "Referral procedure initiated (Article 31 or Article 20 of Regulation 726/2004)",
            ],
            "publication": "PRAC signal assessment outcomes published on EMA website and in "
                           "PRAC meeting highlights",
        },
    },
    "signal_dossier_contents": {
        "title": "Signal Dossier / Signal Assessment Report Contents",
        "sections": [
            "Executive summary",
            "Signal description (drug-event combination, source of signal)",
            "Background (pharmacology, known safety profile, labeled risks)",
            "Methodology (detection method, databases searched, statistical analysis)",
            "Case series analysis (demographics, time to onset, dose, dechallenge/rechallenge, outcomes)",
            "Line listing of relevant ICSRs",
            "Disproportionality analysis results (PRR, ROR, EBGM with confidence intervals)",
            "Literature review summary",
            "Non-clinical data review",
            "Clinical trial data review (if applicable)",
            "Biological plausibility assessment",
            "Causality assessment (Bradford Hill criteria consideration)",
            "Benefit-risk impact assessment",
            "Conclusions and recommended actions",
            "Appendices (individual case narratives, statistical output, literature references)",
        ],
    },
    "potential_vs_validated_signal": {
        "potential_signal": {
            "definition": "A drug-event combination identified through statistical screening or "
                          "clinical review that exceeds predefined detection thresholds but has "
                          "not yet been clinically evaluated for causality",
            "examples": [
                "New SDR (signal of disproportionate reporting) exceeding PRR >= 2, N >= 3, chi2 >= 4",
                "Cluster of serious ICSRs with similar presentation identified in clinical review",
                "Published case report or case series in literature",
            ],
            "status": "Requires validation (clinical evaluation of evidence)",
        },
        "validated_signal": {
            "definition": "A signal for which the signal validation process has confirmed that "
                          "the evidence is sufficient to suggest a new potentially causal "
                          "association, or a new aspect of a known association, warranting "
                          "further assessment",
            "criteria_met": [
                "Clinical plausibility established",
                "Temporal relationship appropriate",
                "Evidence reviewed from multiple sources",
                "Previously not adequately characterized in product information",
                "Clinical review confirms the signal is not explained by confounding alone",
            ],
            "status": "Proceeds to prioritization and full assessment",
        },
    },
}


# =============================================================================
# SECTION 7: AGGREGATE REPORTING
# =============================================================================

AGGREGATE_REPORTING = {
    "title": "Aggregate Safety Reporting",
    "report_types": {
        "dsur": {
            "title": "Development Safety Update Report (DSUR)",
            "ich_guideline": "ICH E2F",
            "source_url": "https://database.ich.org/sites/default/files/E2F_Guideline.pdf",
            "purpose": "Annual safety report for drugs under clinical development. Intended to "
                       "replace both the US IND Annual Report safety sections and the EU Annual "
                       "Safety Report (ASR) with a single harmonized format.",
            "timeline": {
                "frequency": "Annually, based on DIBD",
                "dibd_definition": "Development International Birth Date: the date of first "
                                   "authorization (in any country) to conduct a clinical trial "
                                   "for the investigational drug",
                "submission_deadline": "Within 60 calendar days after each DIBD anniversary",
                "reporting_period": "12 months (DIBD anniversary to next DIBD anniversary)",
                "first_dsur": "May be submitted anytime within 1 year after DIBD, but not "
                              "longer than 1 year after the birth date",
            },
            "data_scope": {
                "interval_data": "New safety data from the 12-month reporting period "
                                 "(line listings of serious adverse reactions, new signals)",
                "cumulative_data": "Cumulative summary tabulations of all serious adverse events "
                                   "across the entire development program to date",
            },
            "sections": {
                "1": {"title": "Introduction", "content": "Report number, DIBD, reporting period, "
                      "drug name, mechanism of action, therapeutic indication, scope of document"},
                "2": {"title": "Worldwide Marketing Approval Status", "content": "First approval, "
                      "indication(s), approved dose(s), country of first approval"},
                "3": {"title": "Actions Taken for Safety Reasons", "content": "Regulatory/sponsor "
                      "actions including trial suspensions, recalls, clinical holds, protocol "
                      "modifications, IB updates, informed consent changes"},
                "4": {"title": "Changes to Reference Safety Information", "content": "Updates to "
                      "Investigator's Brochure: new exclusions, contraindications, warnings, "
                      "serious ADRs, precautions"},
                "5": {"title": "Inventory of Clinical Trials", "content": "Tabular overview of all "
                      "ongoing and completed trials by status, phase, design, indication, dosage"},
                "6": {"title": "Estimated Cumulative Exposure", "content": "Number of subjects "
                      "exposed in development program and marketed setting (if applicable), "
                      "by study, dose, duration"},
                "7": {"title": "Data in Line Listings and Summary Tabulations", "content": "Interval "
                      "line listings of SARs; cumulative summary tabulations of all SAEs by SOC and PT"},
                "8": {"title": "Significant Findings from Clinical Trials", "content": "Completed "
                      "and ongoing trial results, long-term follow-up data, combination therapy safety"},
                "9": {"title": "Safety Findings from Non-Interventional Studies", "content": "Data "
                      "from observational studies, registries, active surveillance, patient support programs"},
                "10": {"title": "Other Clinical Trial/Study Safety Information", "content": "Published "
                       "results from co-sponsored trials, pooled analyses, meta-analyses, "
                       "investigator-initiated studies"},
                "11": {"title": "Safety Findings from Marketing Experience", "content": "Post-marketing "
                       "safety data (if drug also marketed), labeling changes, risk management updates"},
                "12": {"title": "Nonclinical Data", "content": "Relevant findings from animal "
                       "studies completed during the reporting interval (carcinogenicity, "
                       "reproductive toxicity, etc.)"},
                "13": {"title": "Literature", "content": "Published and unpublished safety findings "
                       "from scientific literature relevant to the investigational drug"},
                "14": {"title": "Other DSURs", "content": "Cross-reference to DSURs for the same "
                       "active substance in different development programs/indications"},
                "15": {"title": "Lack of Efficacy", "content": "Safety implications of inadequate "
                       "drug efficacy, particularly for serious or life-threatening conditions"},
                "16": {"title": "Region-Specific Information", "content": "National or regional "
                       "regulatory compliance requirements and local appendices"},
                "17": {"title": "Late-Breaking Information", "content": "Important safety findings "
                       "arising after the data lock point but before report submission"},
                "18": {"title": "Overall Safety Assessment", "content": "Integrated evaluation of "
                       "all new relevant clinical, nonclinical, and epidemiological information; "
                       "updated characterization of safety profile"},
                "19": {"title": "Summary of Important Risks", "content": "Cumulative, issue-by-issue "
                       "list of important identified risks and potential risks with characterization"},
                "20": {"title": "Conclusions", "content": "Significant changes to safety knowledge "
                       "during reporting period; proposed actions for the development program; "
                       "statement on whether benefit-risk remains favorable"},
            },
        },
        "pbrer": {
            "title": "Periodic Benefit-Risk Evaluation Report (PBRER)",
            "ich_guideline": "ICH E2C(R2)",
            "source_url": "https://database.ich.org/sites/default/files/E2C_R2_Guideline.pdf",
            "purpose": "Post-marketing periodic safety report providing comprehensive, concise, "
                       "and critical analysis of new or emerging information on the risks of the "
                       "medicinal product and, where appropriate, on the benefits, in the context "
                       "of cumulative information on risks and benefits.",
            "timeline": {
                "frequency": "Defined by EURD list (EU) or IBD-based schedule",
                "ibd_definition": "International Birth Date: the date of first marketing "
                                  "authorization for the drug in any country worldwide",
                "submission_schedule_eu": {
                    "years_0_2": "Every 6 months (first 2 years after authorization)",
                    "years_2_4": "Annually (years 2-4 after authorization — some products)",
                    "years_4_plus": "Every 3 years (or as defined by EURD list)",
                    "note": "EURD list may specify different frequency; EURD list takes precedence",
                },
                "submission_deadline": "Within 70 calendar days of data lock point (DLP) in EU; "
                                       "within 120 calendar days for active substance-level assessment",
                "data_lock_point": "Aligned across all MAHs for the same active substance per EURD list",
            },
            "data_scope": {
                "interval_data": "New information obtained during the reporting interval "
                                 "(new clinical trials, new spontaneous reports, new literature)",
                "cumulative_data": "Overall safety profile based on all available data since "
                                   "first authorization; cumulative exposure estimates; "
                                   "cumulative summary tabulations",
            },
            "sections": {
                "1": {"title": "Introduction"},
                "2": {"title": "Worldwide Marketing Authorisation Status"},
                "3": {"title": "Actions Taken in the Reporting Interval for Safety Reasons"},
                "4": {"title": "Changes to Reference Safety Information"},
                "5": {"title": "Estimated Exposure and Use Patterns"},
                "6": {"title": "Data in Summary Tabulations"},
                "7": {"title": "Summaries of Significant Findings from Clinical Trials "
                      "During the Reporting Period"},
                "8": {"title": "Findings from Non-Interventional Studies"},
                "9": {"title": "Information from Other Clinical Trials and Sources"},
                "10": {"title": "Nonclinical Data"},
                "11": {"title": "Literature"},
                "12": {"title": "Other Periodic Reports"},
                "13": {"title": "Lack of Efficacy in Controlled Clinical Trials"},
                "14": {"title": "Late-Breaking Information"},
                "15": {"title": "Overview of Signals: New, Ongoing, or Closed"},
                "16": {"title": "Signal and Risk Evaluation"},
                "17": {"title": "Benefit Evaluation"},
                "18": {"title": "Integrated Benefit-Risk Analysis for Approved Indications"},
                "19": {"title": "Conclusions and Actions"},
            },
            "key_features": [
                "Formal benefit evaluation is a key feature (distinguishes PBRER from old PSUR)",
                "Integrated benefit-risk analysis required for each approved indication",
                "Signals section (15-16) must cover new, ongoing, and closed signals",
                "Section 19 must include proposed or initiated actions",
            ],
        },
        "psur_psusa": {
            "title": "PSUR / PSUR Single Assessment (PSUSA)",
            "description": "In the EU, the term PSUR is used in legislation. The format and content "
                           "requirements are those of the PBRER (per ICH E2C(R2)). The terms are "
                           "used interchangeably in practice.",
            "psusa_process": {
                "description": "PSUR Single Assessment (PSUSA) is the EU procedure whereby PSURs "
                               "for all products containing the same active substance are assessed "
                               "together, even if held by different MAHs in different Member States.",
                "introduced": "2012, under EU Pharmacovigilance legislation (Directive 2010/84/EU, "
                              "Regulation 1235/2010)",
                "eurd_list": "European Union Reference Dates (EURD) list harmonizes DLPs and "
                             "submission frequencies for all MAHs of the same active substance",
                "assessor": "PRAC (for centrally authorized products and substances in EURD list); "
                            "National Competent Authorities (for nationally authorized only, "
                            "not in EURD list)",
                "outcome": "PRAC recommendation may lead to variation of marketing authorizations "
                           "across the EU (harmonized labeling changes, risk minimization, etc.)",
            },
            "relationship_to_pbrer": (
                "The EU PSUR IS the PBRER. EU legislation requires that the format and content "
                "of PSURs follow ICH E2C(R2). The PBRER replaced the older PSUR format "
                "(per ICH E2C original) which had fewer sections and no formal benefit evaluation."
            ),
        },
        "ind_annual_report": {
            "title": "IND Annual Report (FDA)",
            "regulation": "21 CFR 312.33",
            "source_url": "https://www.law.cornell.edu/cfr/text/21/312.33",
            "purpose": "Annual progress report for investigational drugs under IND to FDA. "
                       "Note: If a DSUR is submitted per ICH E2F, it may replace the safety "
                       "sections of the IND Annual Report.",
            "timeline": {
                "deadline": "Within 60 days of the anniversary date the IND went into effect",
                "frequency": "Annually",
            },
            "required_content": {
                "a_individual_study_info": {
                    "title": "Individual Study Information (312.33(a))",
                    "content": [
                        "Brief summary of status of each study (in progress and completed)",
                        "Study title and protocol number",
                        "Study purpose",
                        "Patient population description",
                        "Completion status",
                        "Total subjects planned vs. enrolled (by age, gender, race)",
                        "Number completed as planned vs. dropped out",
                    ],
                },
                "b_safety_information": {
                    "title": "Safety Information (312.33(b))",
                    "content": [
                        "Summary of all IND safety reports submitted during past year",
                        "List of subjects who died during investigation (with cause of death)",
                        "List of subjects who dropped out due to adverse experiences",
                    ],
                },
                "c_scientific_information": {
                    "title": "Scientific Information (312.33(c))",
                    "content": [
                        "Dose-response information",
                        "Information from controlled trials",
                        "Bioavailability data",
                        "Preclinical studies completed or in progress (with major findings)",
                        "Significant manufacturing or microbiological changes",
                    ],
                },
                "d_future_planning": {
                    "title": "General Investigational Plan (312.33(d))",
                    "content": [
                        "Investigational plan for the coming year",
                        "Revised Investigator's Brochure (if applicable)",
                        "Significant Phase 1 protocol modifications not previously reported",
                    ],
                },
                "e_additional": {
                    "title": "Additional Information (312.33(e))",
                    "content": [
                        "Significant foreign marketing developments",
                        "Outstanding business/requests pending with FDA",
                    ],
                },
            },
        },
    },
    "interval_vs_cumulative_data": {
        "title": "Interval vs. Cumulative Data Across Report Types",
        "comparison": {
            "dsur": {
                "interval": "Line listings of SARs from 12-month reporting period; new signals; "
                            "new non-clinical findings; new literature",
                "cumulative": "Summary tabulations of all SAEs across entire development program; "
                              "cumulative exposure data; cumulative risk characterization",
            },
            "pbrer": {
                "interval": "New ICSRs received during reporting interval; new clinical trial "
                            "results; new literature; new signals detected; actions taken",
                "cumulative": "Overall safety profile characterization; cumulative exposure; "
                              "cumulative tabulations; integrated benefit-risk based on all data",
            },
            "ind_annual": {
                "interval": "IND safety reports from past year; study progress in past year",
                "cumulative": "Cumulative enrollment data; overall development plan",
            },
        },
    },
}


# =============================================================================
# SECTION 8: RISK MANAGEMENT
# =============================================================================

RISK_MANAGEMENT = {
    "title": "Risk Management",
    "eu_rmp": {
        "title": "EU Risk Management Plan (EU-RMP)",
        "guideline": "GVP Module V: Risk Management Systems (Rev 2)",
        "legal_basis": "Directive 2001/83/EC, Article 8(3)(ia); Regulation (EC) No 726/2004",
        "format_guidance": "EMA/164014/2018 Rev 2.0.1 — Guidance on format of the RMP in the EU",
        "source_url": "https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/"
                      "guidance-format-risk-management-plan-rmp-eu-integrated-format-rev-201_en.pdf",
        "when_required": [
            "All new marketing authorization applications (mandatory)",
            "Significant change to existing MA (new indication, new dosage form, new route)",
            "At request of regulatory authority based on safety concerns",
            "Generic/biosimilar applications if reference product has RMP with additional RMMs",
        ],
        "structure": {
            "part_i": {
                "title": "Part I: Product Overview",
                "content": [
                    "Product/active substance name and details",
                    "RMP version number and data lock point (DLP; must be <= 6 months old)",
                    "Marketing authorization details (procedure type, indication, dosage forms)",
                    "Brief description of the product (pharmacology, mechanism of action)",
                    "Regulatory status worldwide",
                ],
            },
            "part_ii": {
                "title": "Part II: Safety Specification",
                "description": "Comprehensive summary of the safety profile and identification "
                               "of what is known and not known about the product's safety",
                "modules": {
                    "SI": {
                        "title": "Module SI: Epidemiology of the Indication(s) and Target Population(s)",
                        "content": "Incidence, prevalence, demographics, comorbidities of target disease",
                    },
                    "SII": {
                        "title": "Module SII: Non-Clinical Part of the Safety Specification",
                        "content": "Key non-clinical safety findings (carcinogenicity, reproductive "
                                   "toxicity, organ toxicity, phototoxicity, other relevant findings)",
                    },
                    "SIII": {
                        "title": "Module SIII: Clinical Trial Exposure",
                        "content": "Numbers of patients exposed in clinical trials by study, "
                                   "dose, duration, age, sex, race",
                    },
                    "SIV": {
                        "title": "Module SIV: Populations Not Studied in Clinical Trials",
                        "content": "Pediatric, elderly, pregnant/lactating, hepatic/renal impairment, "
                                   "immunocompromised, other subpopulations with limited data",
                    },
                    "SV": {
                        "title": "Module SV: Post-Authorisation Experience",
                        "content": "Post-marketing exposure, regulatory actions taken, "
                                   "post-authorization studies, effectiveness of risk minimization",
                    },
                    "SVI": {
                        "title": "Module SVI: Additional EU Requirements for the Safety Specification",
                        "content": "Potential for overuse/misuse/abuse/medication errors/off-label use",
                    },
                    "SVII": {
                        "title": "Module SVII: Identified and Potential Risks",
                        "content": "Detailed characterization of each identified risk, potential risk, "
                                   "and important identified interactions. For each risk: frequency, "
                                   "seriousness, potential mechanism, risk factors, preventability, "
                                   "reversibility, impact on patient.",
                    },
                    "SVIII": {
                        "title": "Module SVIII: Summary of the Safety Concerns",
                        "content": "Consolidated table of: (1) Important identified risks, "
                                   "(2) Important potential risks, (3) Missing information",
                    },
                },
                "safety_concern_categories": {
                    "important_identified_risks": {
                        "definition": "Adverse events or effects for which there is adequate evidence "
                                      "of an association with the medicinal product and that have "
                                      "potential impact on the benefit-risk balance",
                        "evidence_sources": [
                            "Clinical trials with significant incidence",
                            "Post-marketing spontaneous reports with established causality",
                            "Epidemiological study results",
                            "Class effects supported by pharmacological plausibility",
                        ],
                    },
                    "important_potential_risks": {
                        "definition": "Adverse events for which there is some basis for suspicion "
                                      "of an association but where the association has not been confirmed",
                        "evidence_sources": [
                            "Non-clinical signals not yet confirmed in humans",
                            "Adverse events observed in clinical trials with uncertain causality",
                            "Known class effects not yet observed for this specific product",
                            "Pharmacological concerns (e.g., QTc from hERG binding)",
                        ],
                    },
                    "missing_information": {
                        "definition": "Gaps in knowledge about the safety of the product, relating "
                                      "to populations not adequately studied or situations of use "
                                      "not adequately evaluated",
                        "examples": [
                            "Use in pediatric populations",
                            "Use in pregnancy/lactation",
                            "Long-term safety (>2 years)",
                            "Use in severe hepatic/renal impairment",
                            "Drug-drug interactions not fully characterized",
                        ],
                    },
                },
            },
            "part_iii": {
                "title": "Part III: Pharmacovigilance Plan",
                "description": "Plan for monitoring safety concerns and detecting new risks",
                "components": {
                    "routine_pharmacovigilance": {
                        "description": "Activities performed for all medicinal products beyond "
                                       "the minimum legal requirements",
                        "activities": [
                            "Adverse reaction reporting and ICSR processing",
                            "Signal detection from spontaneous reports",
                            "PSUR / PBRER preparation and submission",
                            "Continuous benefit-risk assessment",
                            "Post-authorization safety communication",
                            "Monitoring literature for safety information",
                        ],
                    },
                    "additional_pharmacovigilance": {
                        "description": "Specific activities to address safety concerns beyond "
                                       "routine measures (detailed in Annex)",
                        "examples": [
                            "Post-Authorization Safety Study (PASS) — may be imposed or voluntary",
                            "Drug utilization study",
                            "Pregnancy registry / exposure registry",
                            "Targeted follow-up questionnaire for specific AEs",
                            "Sentinel site surveillance",
                            "Active surveillance / enhanced pharmacovigilance",
                        ],
                    },
                },
            },
            "part_iv": {
                "title": "Part IV: Plans for Post-Authorisation Efficacy Studies",
                "content": "Studies required by regulatory authority or voluntarily conducted "
                           "to further characterize efficacy in approved indications, "
                           "particularly when efficacy evidence at authorization was limited",
            },
            "part_v": {
                "title": "Part V: Risk Minimisation Measures",
                "components": {
                    "routine_risk_minimization": {
                        "definition": "Standard measures applicable to all medicines that "
                                      "contribute to safe use",
                        "measures": [
                            "Summary of Product Characteristics (SmPC) — prescriber information",
                            "Patient Information Leaflet (PIL) — patient-facing information",
                            "Labeling (packaging, labeling of container)",
                            "Pack size appropriate to treatment duration",
                            "Legal status (prescription-only, controlled substance, etc.)",
                        ],
                        "focus": "SmPC should include specific clinical measures to address "
                                 "each important identified risk (monitoring recommendations, "
                                 "dose adjustments, contraindications, warnings)",
                    },
                    "additional_risk_minimization": {
                        "definition": "Measures beyond routine that are considered essential for "
                                      "safe and effective use of the product",
                        "examples": [
                            "Educational materials for healthcare providers",
                            "Patient alert cards / patient brochures",
                            "Healthcare professional training programs",
                            "Controlled access/distribution programs",
                            "Pregnancy prevention programs",
                            "Specific monitoring requirements",
                            "Hepatic function testing protocols",
                            "Cardiac monitoring programs (ECG before and during treatment)",
                        ],
                    },
                },
            },
            "part_vi": {
                "title": "Part VI: Summary of the Risk Management Plan",
                "content": "Stand-alone, public-facing summary written in plain language. "
                           "Must accurately reflect the full RMP without promotional content. "
                           "Intended for healthcare professionals and patients. Published on "
                           "EMA website for centrally authorized products.",
            },
            "part_vii": {
                "title": "Part VII: Annexes",
                "content": [
                    "Annex 1: EudraVigilance interface",
                    "Annex 2: Tabulated summary of planned/ongoing additional PV activities",
                    "Annex 3: Protocols for PASS and other PV studies",
                    "Annex 4: Specific adverse drug reaction follow-up forms",
                    "Annex 5: Protocols for proposed post-authorization efficacy studies",
                    "Annex 6: Details of proposed additional risk minimization activities",
                    "Annex 7: Other supporting data (internationally agreed summary tables)",
                    "Annex 8: Summary of changes to the RMP over time",
                ],
            },
        },
    },
    "fda_rems": {
        "title": "FDA Risk Evaluation and Mitigation Strategy (REMS)",
        "legal_basis": "FDA Amendments Act of 2007 (FDAAA), Section 505-1 of the FD&C Act",
        "source_url": "https://www.fda.gov/drugs/drug-safety-and-availability/"
                      "risk-evaluation-and-mitigation-strategies-rems",
        "when_required": (
            "FDA may require a REMS if it determines that a REMS is necessary to ensure that "
            "the benefits of a drug outweigh its risks. Can be required at approval or "
            "post-approval if new safety information emerges."
        ),
        "components": {
            "medication_guide": {
                "title": "Medication Guide",
                "regulation": "21 CFR Part 208",
                "description": "FDA-approved patient-friendly labeling distributed with the drug",
                "triggers": [
                    "Patient labeling could help prevent serious adverse effects",
                    "Product has serious risks that could affect patient's decision to use/continue",
                    "Patient adherence to directions is crucial to product effectiveness",
                ],
                "requirements": [
                    "Written in language understandable by patients",
                    "Distributed by pharmacist with each new prescription and refill",
                    "Must include specific risk information",
                ],
            },
            "communication_plan": {
                "title": "Communication Plan",
                "description": "Targeted communications to healthcare providers to support "
                               "safe use of the drug",
                "activities": [
                    "Dear Healthcare Provider letters",
                    "Information dissemination through professional societies",
                    "Information about safety protocols (e.g., required laboratory monitoring)",
                    "Training materials for prescribers",
                ],
            },
            "etasu": {
                "title": "Elements to Assure Safe Use (ETASU)",
                "description": "Most restrictive REMS component; required medical interventions "
                               "or actions by healthcare professionals prior to prescribing/dispensing",
                "purpose": "Provide safe access to drugs with known serious risks that would "
                           "otherwise be unavailable",
                "possible_elements": [
                    "Prescriber certification (prescribers must be specially certified)",
                    "Pharmacy certification (dispensing only from certified pharmacies)",
                    "Patient enrollment in a registry",
                    "Drug dispensed only in certain healthcare settings (e.g., hospitals, infusion centers)",
                    "Monitoring requirements (specific lab tests before/during treatment)",
                    "Documentation of safe-use conditions before dispensing",
                    "Patient informed consent / acknowledgment form",
                ],
                "examples_oncology": [
                    "Lenalidomide (Revlimid) REMS — pregnancy prevention, prescriber/pharmacy "
                    "certification, patient survey",
                    "Thalidomide (Thalomid) REMS (S.T.E.P.S.) — strictest pregnancy prevention "
                    "program in oncology",
                ],
            },
            "implementation_system": {
                "title": "Implementation System",
                "description": "Infrastructure to monitor and enforce ETASU requirements",
                "components": [
                    "Centralized database or hub for enrollment tracking",
                    "Verification systems (pharmacy checks prescriber certification)",
                    "REMS assessments submitted to FDA at specified intervals",
                    "Metrics tracking (enrollment rates, compliance, adverse outcomes)",
                ],
            },
        },
        "rems_assessment": {
            "description": "FDA requires periodic REMS assessments to evaluate whether the "
                           "REMS is meeting its goals",
            "timeline": "Typically 18 months, 3 years, and 7 years after approval; then "
                        "every 7 years (FDA may specify other intervals)",
            "content": [
                "Assessment of whether REMS goals are being met",
                "Data on REMS compliance (prescriber/pharmacy enrollment, patient enrollment)",
                "Analysis of whether serious adverse outcomes are being prevented",
                "Proposals for REMS modifications (strengthen, relax, or remove)",
            ],
        },
    },
    "egfr_tki_risk_examples": {
        "title": "EGFR TKI Class-Specific Risk Examples (for Prosinertimib Context)",
        "description": "Real-world safety data from marketed EGFR TKIs, particularly 3rd-generation "
                       "(osimertinib/Tagrisso), to inform the Prosinertimib risk profile",
        "source": "FLAURA trial (Soria et al., NEJM 2018; Ramalingam et al., NEJM 2020); "
                  "FDA FAERS disproportionality analyses; published safety reviews",
        "identified_risks": {
            "ild_pneumonitis": {
                "risk_name": "Interstitial Lung Disease (ILD) / Pneumonitis",
                "meddra_soc": "Respiratory, thoracic and mediastinal disorders",
                "meddra_pts": ["Interstitial lung disease", "Pneumonitis", "Pulmonary fibrosis"],
                "meddra_smq": "Interstitial lung disease (SMQ)",
                "incidence_osimertinib": "~4% overall (FLAURA); up to 12% in Japanese populations",
                "severity": "Grade 3-4 in ~1%; fatal cases reported (leading cause of EGFR TKI "
                            "treatment-related death — 58% of all EGFR TKI treatment-related deaths)",
                "time_to_onset": "Median 2-3 months (range: days to >1 year)",
                "management": "Permanently discontinue for Grade >= 2; corticosteroids for treatment; "
                              "CT imaging for diagnosis",
                "risk_factors": ["Japanese ethnicity", "Pre-existing lung disease", "Smoking history",
                                 "Prior radiation therapy", "Poor performance status"],
                "risk_minimization": "Black Box Warning (osimertinib label); monitoring guidance in SmPC; "
                                     "patient education on symptoms (dyspnea, cough, fever)",
                "rmp_category": "Important identified risk",
            },
            "hepatotoxicity": {
                "risk_name": "Hepatotoxicity",
                "meddra_soc": "Hepatobiliary disorders",
                "meddra_pts": ["Hepatotoxicity", "Alanine aminotransferase increased",
                               "Aspartate aminotransferase increased", "Drug-induced liver injury",
                               "Hepatic failure"],
                "incidence_osimertinib": "ALT/AST elevations in ~12% of patients; Grade 3-4 in ~2-4%",
                "time_to_onset": "Typically within first 3 months",
                "management": "LFT monitoring at baseline and periodically; dose interruption/reduction "
                              "for Grade 3; discontinue for Grade 4 or clinical hepatotoxicity",
                "risk_factors": ["Age >= 65", "Liver metastasis", "Concomitant hepatotoxic drugs",
                                 "Pre-existing hepatic impairment"],
                "risk_minimization": "LFT monitoring schedule in labeling; dose modification guidance",
                "rmp_category": "Important identified risk",
            },
            "qtc_prolongation": {
                "risk_name": "QTc Prolongation",
                "meddra_soc": "Cardiac disorders / Investigations",
                "meddra_pts": ["Electrocardiogram QT prolonged", "Long QT syndrome",
                               "Torsade de pointes", "Ventricular tachycardia"],
                "incidence_osimertinib": "QTc prolongation reported in 14% (osimertinib) vs 5% "
                                          "(comparator) in FLAURA; Grade 3-4 rare (<1%)",
                "mechanism": "hERG potassium channel inhibition (pharmacological class effect)",
                "management": "ECG and electrolytes at baseline and periodically; withhold if QTcF "
                              ">500 ms; permanently discontinue if combined with life-threatening "
                              "arrhythmia; correct hypokalemia/hypomagnesemia",
                "risk_factors": ["Concomitant QT-prolonging drugs", "Electrolyte abnormalities",
                                 "Baseline QTc prolongation", "Cardiac disease",
                                 "Bradycardia"],
                "risk_minimization": "ECG monitoring in labeling; drug interaction guidance; "
                                     "electrolyte correction guidance",
                "rmp_category": "Important identified risk",
            },
            "skin_toxicity": {
                "risk_name": "Skin Toxicity (Rash, Dermatitis Acneiform, Dry Skin, Paronychia)",
                "meddra_soc": "Skin and subcutaneous tissue disorders",
                "meddra_pts": ["Rash", "Dermatitis acneiform", "Dry skin", "Pruritus",
                               "Paronychia", "Stomatitis"],
                "incidence_osimertinib": "Rash: 58% (osimertinib) vs 81% (1st-gen comparators) "
                                          "in FLAURA; paronychia: 40%; Grade 3 skin AEs: ~1%",
                "note": "3rd-gen EGFR TKIs (osimertinib) generally have LESS skin toxicity than "
                        "1st-gen (erlotinib, gefitinib) due to reduced wild-type EGFR inhibition",
                "management": "Topical treatments; dose interruption for Grade 3; dermatology referral",
                "rmp_category": "Important identified risk",
            },
            "diarrhea": {
                "risk_name": "Diarrhea",
                "meddra_soc": "Gastrointestinal disorders",
                "meddra_pts": ["Diarrhoea"],
                "incidence_osimertinib": "54% all-grade (FLAURA); Grade 3-4: ~2%",
                "management": "Anti-diarrheal agents; dose interruption for Grade 3; hydration",
                "rmp_category": "Important identified risk",
            },
            "cardiac_effects": {
                "risk_name": "Cardiac Toxicity (Decreased Ejection Fraction / Heart Failure)",
                "meddra_soc": "Cardiac disorders",
                "meddra_pts": ["Ejection fraction decreased", "Cardiac failure",
                               "Left ventricular dysfunction"],
                "incidence_osimertinib": "Ejection fraction decrease: 5% (osimertinib) vs 2% (comparator) "
                                          "in FLAURA; heart failure events: ~2-3%",
                "management": "Cardiac function assessment at baseline; monitor during treatment; "
                              "dose modification for significant decline",
                "rmp_category": "Important identified risk",
            },
        },
        "potential_risks": {
            "embryo_fetal_toxicity": {
                "risk_name": "Embryo-Fetal Toxicity",
                "basis": "Non-clinical reproductive toxicity data; class effect for EGFR TKIs",
                "risk_minimization": "Contraception requirements; pregnancy testing; labeled warning",
                "rmp_category": "Important potential risk",
            },
            "ocular_toxicity": {
                "risk_name": "Ocular Toxicity (Keratitis, Dry Eye)",
                "basis": "EGFR expressed in corneal epithelium; reported with other EGFR TKIs",
                "rmp_category": "Important potential risk",
            },
        },
        "missing_information": [
            "Long-term safety beyond 3 years",
            "Use in patients with severe hepatic impairment (Child-Pugh C)",
            "Use in patients with severe renal impairment (CrCl <15 mL/min)",
            "Pediatric use",
            "Use in pregnancy and lactation (human data)",
            "Interactions with strong CYP3A4 inhibitors at steady state",
        ],
    },
    "routine_vs_additional_risk_minimization": {
        "title": "Routine vs Additional Risk Minimization — Comparison",
        "routine": {
            "definition": "Standard measures applicable to all medicinal products",
            "measures": [
                "Summary of Product Characteristics (SmPC) with appropriate warnings, "
                "precautions, contraindications, and dose modification guidance",
                "Patient Information Leaflet (PIL) with patient-friendly safety information",
                "Appropriate labeling and packaging",
                "Appropriate pack size",
                "Legal status of the product (prescription-only)",
            ],
            "who_implements": "Part of standard regulatory approval process",
            "assessment": "Effectiveness assessed in aggregate reports (PBRER/PSUR)",
        },
        "additional": {
            "definition": "Measures beyond routine, considered essential when routine measures "
                          "alone are insufficient to manage an important risk",
            "measures": [
                "Educational materials (HCP guides, patient brochures, alert cards)",
                "Controlled distribution/access programs",
                "Pregnancy prevention programs with mandatory testing",
                "Mandatory prescriber/pharmacy training or certification",
                "Patient registries for monitoring specific outcomes",
                "Specific monitoring protocols (e.g., mandatory ECG, LFT schedule)",
                "Direct Healthcare Professional Communications (DHPC)",
            ],
            "who_implements": "MAH, with regulatory authority oversight; details specified in RMP Part V",
            "assessment": "Effectiveness must be specifically assessed and reported (milestones "
                          "and metrics defined in RMP)",
            "examples_egfr_tki": [
                "ILD awareness card for patients (symptoms to watch for: new/worsening dyspnea, cough, fever)",
                "HCP guide on ILD monitoring and management algorithm",
                "ECG monitoring protocol card (baseline, monthly for 3 months, then every 3 months)",
                "LFT monitoring schedule (baseline, monthly for 6 months, then periodically)",
                "Pregnancy prevention materials with contraception requirements",
            ],
        },
    },
}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_section_data(section_number: int) -> dict:
    """Return the structured data for a given dashboard section (5-8)."""
    sections = {
        5: ICSR_CASE_PROCESSING,
        6: SIGNAL_DETECTION_MANAGEMENT,
        7: AGGREGATE_REPORTING,
        8: RISK_MANAGEMENT,
    }
    return sections.get(section_number, {})


def get_all_regulatory_data() -> dict:
    """Return all regulatory framework data for sections 5-8."""
    return {
        "section_5_icsr_processing": ICSR_CASE_PROCESSING,
        "section_6_signal_detection": SIGNAL_DETECTION_MANAGEMENT,
        "section_7_aggregate_reporting": AGGREGATE_REPORTING,
        "section_8_risk_management": RISK_MANAGEMENT,
    }


def get_reporting_timelines_summary() -> dict:
    """Return a quick-reference summary of all regulatory reporting timelines."""
    return {
        "pre_marketing": {
            "7_day": "Fatal/life-threatening unexpected suspected adverse reaction (21 CFR 312.32(c)(2))",
            "15_day": "Serious unexpected suspected adverse reaction (21 CFR 312.32(c)(1))",
            "annual": "IND Annual Report — 60 days after IND anniversary (21 CFR 312.33)",
            "dsur": "DSUR — 60 days after DIBD anniversary (ICH E2F)",
        },
        "post_marketing_fda": {
            "15_day_alert": "Serious AND unexpected ADE (21 CFR 314.80(c)(1))",
            "quarterly": "First 3 years after NDA approval, within 30 days of quarter close",
            "annual": "After year 3, within 60 days of NDA approval anniversary",
        },
        "post_marketing_ema": {
            "15_day": "Serious suspected adverse reactions — EudraVigilance (GVP Module VI)",
            "90_day": "Non-serious suspected adverse reactions — EudraVigilance (GVP Module VI)",
            "psur_pbrer": "Per EURD list schedule (6-monthly, annual, or 3-yearly)",
        },
    }
