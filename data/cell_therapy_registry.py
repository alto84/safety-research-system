"""
Cell Therapy Registry — Comprehensive adverse event profiles for all cell therapy types.

This module provides structured data on cell therapy categories, their approved and pipeline
products, adverse event profiles with published incidence rates, onset timing, duration,
risk factors, and references to primary literature.

Data sources include FDA prescribing information, pivotal trial publications, meta-analyses,
real-world evidence studies, and regulatory safety communications (2017-2026).

Author: Sartor Safety Research System
Last updated: 2026-02-08
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Core data classes
# ---------------------------------------------------------------------------

@dataclass
class TherapyType:
    """Represents a cell/gene therapy modality with its adverse-event profile."""

    id: str
    name: str
    category: str  # e.g. "CAR-T", "TCR-T", "NK Cell", "TIL", "Gene Therapy", etc.
    target_antigens: list[str]
    applicable_aes: list[str]  # keys into AE_TAXONOMY
    approved_products: list[dict]  # [{name, target, approval_year, indication, sponsor}]
    pipeline_products: list[dict]  # [{name, target, phase, sponsor, notes}]
    default_ae_rates: dict  # {ae_name: {any_grade: float, grade3_plus: float, onset_days: str, duration: str, notes: str}}
    risk_factors: list[str]
    data_sources: list[str]
    references: list[str]
    notes: str = ""


# ---------------------------------------------------------------------------
# Adverse Event Taxonomy — 20+ AE types with definitions and grading criteria
# ---------------------------------------------------------------------------

AE_TAXONOMY: dict[str, dict] = {
    "cytokine_release_syndrome": {
        "name": "Cytokine Release Syndrome (CRS)",
        "description": (
            "Systemic inflammatory response triggered by massive cytokine release "
            "from activated immune effector cells. Characterised by fever, hypotension, "
            "hypoxia, and multi-organ dysfunction in severe cases."
        ),
        "grading_system": "ASTCT Lee 2019 Consensus Grading",
        "grade_1": "Fever >= 38C; no hypotension or hypoxia",
        "grade_2": "Fever with hypotension not requiring vasopressors and/or hypoxia requiring low-flow nasal cannula",
        "grade_3": "Fever with hypotension requiring one vasopressor +/- vasopressin and/or hypoxia requiring high-flow nasal cannula, facemask, nonrebreather, or Venturi mask",
        "grade_4": "Fever with hypotension requiring multiple vasopressors (not vasopressin) and/or hypoxia requiring positive pressure ventilation",
        "grade_5": "Death",
        "management": "Tocilizumab (IL-6R blockade), corticosteroids, supportive care",
        "biomarkers": ["IL-6", "CRP", "ferritin", "IFN-gamma"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL", "BiTE", "CAR-NK"],
    },
    "icans": {
        "name": "Immune Effector Cell-Associated Neurotoxicity Syndrome (ICANS)",
        "description": (
            "Neurotoxicity associated with immune effector cell therapies, presenting as "
            "encephalopathy, aphasia, tremor, seizures, and cerebral edema in severe cases."
        ),
        "grading_system": "ASTCT ICE score-based grading",
        "grade_1": "ICE score 7-9; awakens spontaneously",
        "grade_2": "ICE score 3-6; awakens to voice",
        "grade_3": "ICE score 0-2; awakens only to tactile stimulus; any seizure that resolves rapidly; focal/local edema on neuroimaging",
        "grade_4": "ICE score 0; patient unarousable or requires vigorous stimuli; prolonged/repetitive seizures; diffuse cerebral edema; decerebrate/decorticate posturing",
        "grade_5": "Death",
        "management": "Corticosteroids (dexamethasone), anti-seizure prophylaxis, ICU monitoring",
        "biomarkers": ["IL-6", "IL-1", "MCP-1", "quinolinic acid"],
        "applicable_therapies": ["CAR-T", "TCR-T"],
    },
    "hlh_mas": {
        "name": "Hemophagocytic Lymphohistiocytosis / Macrophage Activation Syndrome (HLH/MAS)",
        "description": (
            "Severe hyperinflammatory syndrome with uncontrolled macrophage and T-cell "
            "activation leading to hemophagocytosis, multi-organ failure. Also termed "
            "immune effector cell-associated HLH-like syndrome (IEC-HS)."
        ),
        "grading_system": "HLH-2004 criteria / IEC-HS consensus",
        "grade_1": "Not applicable — typically grade 3+ at presentation",
        "grade_2": "Not applicable",
        "grade_3": "Meets HLH criteria, organ dysfunction manageable",
        "grade_4": "Life-threatening multi-organ failure",
        "grade_5": "Death",
        "management": "Anakinra (IL-1 blockade), ruxolitinib, etoposide, emapalumab",
        "biomarkers": ["ferritin", "soluble IL-2R", "triglycerides", "fibrinogen (decreased)"],
        "applicable_therapies": ["CAR-T", "TCR-T", "BiTE"],
    },
    "prolonged_cytopenias": {
        "name": "Prolonged Cytopenias",
        "description": (
            "Extended reduction in blood cell counts (neutropenia, thrombocytopenia, anemia) "
            "persisting beyond 28 days post-infusion. May last months to years. Includes "
            "biphasic pattern with initial recovery followed by secondary decline."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "Mild decrease below LLN",
        "grade_2": "Moderate decrease",
        "grade_3": "ANC <1000/mm3; Platelets <50,000/mm3; Hgb <8 g/dL",
        "grade_4": "ANC <500/mm3; Platelets <25,000/mm3; life-threatening",
        "grade_5": "Death",
        "management": "G-CSF, TPO agonists, transfusion support, autologous stem cell boost",
        "biomarkers": ["CBC", "reticulocyte count", "bone marrow biopsy"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL", "Gene Therapy"],
    },
    "b_cell_aplasia": {
        "name": "B-Cell Aplasia / Hypogammaglobulinemia",
        "description": (
            "On-target, off-tumor depletion of normal B cells by CD19/CD20/BCMA-targeting "
            "therapies, leading to hypogammaglobulinemia and increased infection risk. "
            "Expected pharmacologic effect that may persist for months to years."
        ),
        "grading_system": "IgG levels and clinical assessment",
        "grade_1": "IgG 400-500 mg/dL, no infections",
        "grade_2": "IgG 200-400 mg/dL or recurrent minor infections",
        "grade_3": "IgG <200 mg/dL or serious infection requiring IV antibiotics",
        "grade_4": "Life-threatening infection in setting of agammaglobulinemia",
        "grade_5": "Death from infectious complication",
        "management": "IVIG replacement, antimicrobial prophylaxis, vaccination post-recovery",
        "biomarkers": ["IgG", "IgA", "IgM", "CD19+ B cell count"],
        "applicable_therapies": ["CAR-T (CD19)", "CAR-T (BCMA)", "CAR-NK (CD19)"],
    },
    "infections": {
        "name": "Infections (Bacterial, Viral, Fungal)",
        "description": (
            "Increased susceptibility to infections due to lymphodepletion conditioning, "
            "prolonged cytopenias, hypogammaglobulinemia, and T-cell impairment. Includes "
            "bacterial sepsis, viral reactivation (CMV, HHV-6, BK virus), and invasive "
            "fungal infections."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "Localized, requiring local intervention",
        "grade_2": "Requiring oral intervention",
        "grade_3": "Requiring IV antibiotics/antifungals; hospitalization",
        "grade_4": "Life-threatening (sepsis, septic shock)",
        "grade_5": "Death",
        "management": "Prophylactic antimicrobials, monitoring, early empiric treatment",
        "biomarkers": ["procalcitonin", "blood cultures", "CMV PCR", "beta-D-glucan"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL", "Gene Therapy", "MSC", "NK Cell"],
    },
    "secondary_malignancy": {
        "name": "Secondary Malignancy (including T-cell lymphoma)",
        "description": (
            "Development of new cancers following cell/gene therapy, including T-cell "
            "malignancies (some CAR-positive), MDS, AML. FDA mandated boxed warning for "
            "all approved CAR-T products in January 2024. Risk may be related to insertional "
            "mutagenesis from viral vectors or prior therapy exposure."
        ),
        "grading_system": "Binary (present/absent) with classification by type",
        "grade_1": "Not applicable",
        "grade_2": "Not applicable",
        "grade_3": "Secondary malignancy diagnosed",
        "grade_4": "Aggressive/life-threatening secondary malignancy",
        "grade_5": "Death from secondary malignancy",
        "management": "Lifelong monitoring (minimum 15 years), standard oncologic treatment",
        "biomarkers": ["CBC", "peripheral smear", "flow cytometry", "bone marrow biopsy"],
        "applicable_therapies": ["CAR-T", "Gene Therapy"],
    },
    "tumor_lysis_syndrome": {
        "name": "Tumor Lysis Syndrome (TLS)",
        "description": (
            "Metabolic complications from rapid tumor cell destruction releasing intracellular "
            "contents. Characterised by hyperuricemia, hyperkalemia, hyperphosphatemia, "
            "hypocalcemia, and acute kidney injury."
        ),
        "grading_system": "Cairo-Bishop classification",
        "grade_1": "Laboratory TLS only (2+ lab criteria met)",
        "grade_2": "Laboratory TLS with mild clinical findings",
        "grade_3": "Clinical TLS with creatinine >= 1.5x ULN, cardiac arrhythmia, or seizure",
        "grade_4": "Life-threatening (renal failure requiring dialysis, fatal arrhythmia)",
        "grade_5": "Death",
        "management": "Rasburicase, allopurinol, IV hydration, electrolyte monitoring",
        "biomarkers": ["uric acid", "potassium", "phosphorus", "calcium", "LDH", "creatinine"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL", "BiTE"],
    },
    "coagulopathy_dic": {
        "name": "Coagulopathy / Disseminated Intravascular Coagulation (DIC)",
        "description": (
            "Systemic activation of coagulation pathways leading to widespread clot formation "
            "and paradoxical bleeding. Often associated with severe CRS. Elevated D-dimer "
            "in 50% of CAR-T recipients; overt DIC in severe CRS cases."
        ),
        "grading_system": "ISTH DIC scoring",
        "grade_1": "Subclinical coagulation changes",
        "grade_2": "Abnormal labs without clinical bleeding",
        "grade_3": "Clinical bleeding requiring transfusion",
        "grade_4": "Life-threatening hemorrhage or thrombosis",
        "grade_5": "Death",
        "management": "Treat underlying CRS, cryoprecipitate, FFP, platelet transfusion, anticoagulation",
        "biomarkers": ["D-dimer", "fibrinogen", "PT/INR", "aPTT", "platelet count"],
        "applicable_therapies": ["CAR-T", "TCR-T"],
    },
    "gvhd": {
        "name": "Graft-versus-Host Disease (GvHD)",
        "description": (
            "Donor immune cells attack recipient tissues. Primary concern for allogeneic "
            "cell therapies. Acute GvHD affects skin, liver, GI tract. Chronic GvHD has "
            "broader multi-organ involvement. Notably minimal with NK cell therapies."
        ),
        "grading_system": "Modified Glucksberg / NIH Consensus",
        "grade_1": "Skin involvement only (maculopapular rash <25% BSA)",
        "grade_2": "Skin (25-50% BSA) or GI (diarrhea 500-1000 mL/day) or liver (bilirubin 2-3 mg/dL)",
        "grade_3": "Skin (generalized erythroderma) or GI (>1500 mL/day) or liver (bilirubin 3-15 mg/dL)",
        "grade_4": "Skin (desquamation/bullae) or severe GI (ileus/hemorrhage) or liver (bilirubin >15 mg/dL)",
        "grade_5": "Death",
        "management": "Corticosteroids, ruxolitinib, ibrutinib, ECP, calcineurin inhibitors",
        "biomarkers": ["skin biopsy", "liver function tests", "stool volume"],
        "applicable_therapies": ["Allogeneic CAR-T", "Allogeneic NK", "MSC (used to treat GvHD)"],
    },
    "neurotoxicity_delayed": {
        "name": "Delayed Neurotoxicity (Parkinsonism, Movement Disorders)",
        "description": (
            "Late-onset neurological complications occurring weeks to months after cell "
            "therapy. Includes parkinsonism, cranial nerve palsies, Guillain-Barre syndrome, "
            "and progressive movement disorders. Particularly associated with BCMA-targeting "
            "CAR-T (Carvykti)."
        ),
        "grading_system": "CTCAE v5.0 Neurology",
        "grade_1": "Mild symptoms, not interfering with function",
        "grade_2": "Moderate, limiting instrumental ADL",
        "grade_3": "Severe, limiting self-care ADL",
        "grade_4": "Life-threatening, urgent intervention indicated",
        "grade_5": "Death",
        "management": "Neurology consultation, dopaminergic agents, supportive rehabilitation",
        "biomarkers": ["MRI brain", "DAT scan", "CSF analysis"],
        "applicable_therapies": ["CAR-T (BCMA)", "CAR-T (CD19)"],
    },
    "hepatotoxicity": {
        "name": "Hepatotoxicity",
        "description": (
            "Liver injury ranging from transaminase elevation to acute liver failure. "
            "Especially significant with AAV-based gene therapies (Zolgensma). May be "
            "immune-mediated. Fatal cases reported."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "ALT/AST 1-3x ULN",
        "grade_2": "ALT/AST 3-5x ULN",
        "grade_3": "ALT/AST 5-20x ULN",
        "grade_4": "ALT/AST >20x ULN or acute liver failure",
        "grade_5": "Death",
        "management": "Corticosteroids (prolonged taper), liver function monitoring, hepatology consult",
        "biomarkers": ["ALT", "AST", "bilirubin", "INR", "albumin"],
        "applicable_therapies": ["Gene Therapy (AAV)", "CAR-T"],
    },
    "thrombotic_microangiopathy": {
        "name": "Thrombotic Microangiopathy (TMA)",
        "description": (
            "Endothelial damage with microangiopathic hemolytic anemia, thrombocytopenia, "
            "and organ damage. Reported with AAV gene therapies (Zolgensma) and high-dose "
            "CAR-T regimens. Typically occurs within first 2 weeks post-infusion."
        ),
        "grading_system": "CTCAE v5.0 / clinical criteria",
        "grade_1": "Lab evidence only (schistocytes)",
        "grade_2": "Mild organ involvement",
        "grade_3": "Renal impairment, requiring intervention",
        "grade_4": "Life-threatening (renal failure, CNS involvement)",
        "grade_5": "Death",
        "management": "Plasma exchange, complement inhibition (eculizumab), supportive care",
        "biomarkers": ["schistocytes", "LDH", "haptoglobin", "creatinine", "platelet count"],
        "applicable_therapies": ["Gene Therapy (AAV)", "CAR-T"],
    },
    "veno_occlusive_disease": {
        "name": "Veno-Occlusive Disease / Sinusoidal Obstruction Syndrome (VOD/SOS)",
        "description": (
            "Hepatic endothelial injury from conditioning chemotherapy, leading to sinusoidal "
            "obstruction, hepatomegaly, ascites, and multi-organ failure. Risk with busulfan-based "
            "myeloablative conditioning for gene therapy."
        ),
        "grading_system": "EBMT Severity Grading",
        "grade_1": "Mild (resolves spontaneously)",
        "grade_2": "Moderate (requires treatment)",
        "grade_3": "Severe (MOD requiring intervention)",
        "grade_4": "Very severe (MOF)",
        "grade_5": "Death",
        "management": "Defibrotide, supportive care, fluid management",
        "biomarkers": ["bilirubin", "weight gain", "hepatic ultrasound with Doppler"],
        "applicable_therapies": ["Gene Therapy", "CAR-T (post-HSCT)"],
    },
    "infusion_reactions": {
        "name": "Infusion-Related Reactions / Hypersensitivity",
        "description": (
            "Acute reactions during or shortly after cell product infusion, including fever, "
            "rigors, hypotension, tachycardia, dyspnea, rash. Generally mild and self-limiting. "
            "Distinct from CRS which occurs later."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "Mild transient reaction; infusion interruption not indicated",
        "grade_2": "Requires therapy or infusion interruption; responds to symptomatic treatment",
        "grade_3": "Prolonged; not rapidly responsive to symptomatic medication; recurrence after improvement; hospitalization indicated",
        "grade_4": "Life-threatening; urgent intervention indicated",
        "grade_5": "Death",
        "management": "Premedication (corticosteroids, antihistamines, acetaminophen), infusion rate adjustment",
        "biomarkers": ["tryptase", "IgE (if allergic mechanism suspected)"],
        "applicable_therapies": ["MSC", "NK Cell", "Gene Therapy", "CAR-T", "TIL"],
    },
    "cardiovascular_events": {
        "name": "Cardiovascular Events",
        "description": (
            "Cardiac complications including arrhythmias, cardiomyopathy, heart failure, "
            "and cardiac arrest. Often secondary to CRS-related hemodynamic stress. "
            "Tachycardia is common; severe cardiac events are rare but life-threatening."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "Asymptomatic; intervention not indicated",
        "grade_2": "Symptomatic; medical intervention indicated",
        "grade_3": "Severe; hospitalization/intervention indicated",
        "grade_4": "Life-threatening hemodynamic compromise; urgent intervention",
        "grade_5": "Death",
        "management": "Cardiac monitoring, vasopressors, anti-arrhythmics, cardiology consult",
        "biomarkers": ["troponin", "BNP/NT-proBNP", "echocardiography", "ECG"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL"],
    },
    "febrile_neutropenia": {
        "name": "Febrile Neutropenia",
        "description": (
            "Fever in the setting of severe neutropenia (ANC < 500/mm3), typically "
            "following lymphodepleting chemotherapy. A medical emergency requiring "
            "immediate broad-spectrum antibiotics."
        ),
        "grading_system": "CTCAE v5.0",
        "grade_1": "Not applicable (febrile neutropenia is grade 3 by definition)",
        "grade_2": "Not applicable",
        "grade_3": "ANC <1000/mm3 with single fever >=38.3C or sustained >=38.0C for >1hr",
        "grade_4": "Life-threatening hemodynamic compromise; urgent intervention",
        "grade_5": "Death",
        "management": "Empiric broad-spectrum antibiotics, G-CSF, hospitalization",
        "biomarkers": ["ANC", "blood cultures", "procalcitonin"],
        "applicable_therapies": ["CAR-T", "TCR-T", "TIL", "Gene Therapy"],
    },
    "myelodysplastic_syndrome": {
        "name": "Myelodysplastic Syndrome (MDS) / Acute Myeloid Leukemia (AML)",
        "description": (
            "Clonal hematopoietic disorder that may arise after gene therapy with "
            "lentiviral/retroviral vectors due to insertional mutagenesis, or as a "
            "late effect of prior alkylating agent exposure. Particularly concerning "
            "with Skysona (15% incidence in clinical trials)."
        ),
        "grading_system": "WHO Classification / IPSS-R",
        "grade_1": "Not applicable",
        "grade_2": "Not applicable",
        "grade_3": "Low/intermediate risk MDS",
        "grade_4": "High-risk MDS or transformation to AML",
        "grade_5": "Death",
        "management": "Allogeneic HSCT, hypomethylating agents, monitoring",
        "biomarkers": ["CBC", "bone marrow biopsy", "cytogenetics", "molecular panel"],
        "applicable_therapies": ["Gene Therapy (lentiviral)", "CAR-T"],
    },
    "ocular_adverse_events": {
        "name": "Ocular Adverse Events",
        "description": (
            "Eye-specific complications of subretinal gene therapy including conjunctival "
            "hyperemia, cataract, increased intraocular pressure, retinal tears/detachment, "
            "macular hole, foveal thinning, and chorioretinal atrophy. Specific to Luxturna "
            "and other retinal gene therapies."
        ),
        "grading_system": "CTCAE v5.0 Ophthalmology",
        "grade_1": "Mild; intervention not indicated",
        "grade_2": "Moderate; limiting instrumental ADL",
        "grade_3": "Severe; limiting self-care; surgical intervention indicated",
        "grade_4": "Blindness (20/200 or worse)",
        "grade_5": "Not applicable",
        "management": "Ophthalmologic monitoring, corticosteroids, surgical intervention as needed",
        "biomarkers": ["IOP measurement", "OCT", "fundoscopy", "visual acuity"],
        "applicable_therapies": ["Gene Therapy (subretinal)"],
    },
    "engraftment_failure": {
        "name": "Engraftment Failure / Graft Failure",
        "description": (
            "Failure of transplanted/modified cells to engraft and establish sustained "
            "hematopoiesis or therapeutic function. Relevant to gene therapies requiring "
            "myeloablative conditioning and stem cell infusion."
        ),
        "grading_system": "Binary with timing classification",
        "grade_1": "Delayed engraftment (ANC recovery day 28-42)",
        "grade_2": "Not applicable",
        "grade_3": "Primary graft failure (no ANC recovery by day 42)",
        "grade_4": "Secondary graft failure (loss of graft after initial recovery)",
        "grade_5": "Death from graft failure complications",
        "management": "Stem cell boost, second transplant, supportive care",
        "biomarkers": ["ANC", "chimerism analysis", "vector copy number", "bone marrow biopsy"],
        "applicable_therapies": ["Gene Therapy", "CAR-T (post-HSCT)"],
    },
    "immune_suppression_risk": {
        "name": "Immunosuppression-Related Opportunistic Infections",
        "description": (
            "Theoretical and observed risk of increased susceptibility to infections and "
            "reduced tumor surveillance due to immunosuppressive therapy mechanisms. "
            "Relevant to Treg therapy which suppresses effector T-cell responses."
        ),
        "grading_system": "CTCAE v5.0 Infections",
        "grade_1": "Asymptomatic pathogen detection",
        "grade_2": "Symptomatic, requiring oral treatment",
        "grade_3": "Severe infection requiring IV therapy",
        "grade_4": "Life-threatening (sepsis)",
        "grade_5": "Death",
        "management": "Antimicrobial prophylaxis, immune monitoring, dose adjustment",
        "biomarkers": ["lymphocyte subsets", "immunoglobulin levels", "pathogen-specific PCR"],
        "applicable_therapies": ["Treg", "MSC"],
    },
}


# ---------------------------------------------------------------------------
# THERAPY_TYPES — keyed by therapy id
# ---------------------------------------------------------------------------

THERAPY_TYPES: dict[str, TherapyType] = {

    # ===================================================================
    # 1. CAR-T CD19
    # ===================================================================
    "cart_cd19": TherapyType(
        id="cart_cd19",
        name="CAR-T Cell Therapy (CD19-directed)",
        category="CAR-T",
        target_antigens=["CD19"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "icans",
            "hlh_mas",
            "prolonged_cytopenias",
            "b_cell_aplasia",
            "infections",
            "secondary_malignancy",
            "tumor_lysis_syndrome",
            "coagulopathy_dic",
            "cardiovascular_events",
            "febrile_neutropenia",
        ],
        approved_products=[
            {
                "name": "Kymriah (tisagenlecleucel)",
                "target": "CD19",
                "approval_year": 2017,
                "indication": "R/R B-cell ALL (pediatric/young adult); R/R DLBCL; R/R FL",
                "sponsor": "Novartis",
            },
            {
                "name": "Yescarta (axicabtagene ciloleucel)",
                "target": "CD19",
                "approval_year": 2017,
                "indication": "R/R LBCL; R/R FL; 2L LBCL",
                "sponsor": "Kite/Gilead",
            },
            {
                "name": "Tecartus (brexucabtagene autoleucel)",
                "target": "CD19",
                "approval_year": 2020,
                "indication": "R/R MCL; R/R B-cell ALL (adult)",
                "sponsor": "Kite/Gilead",
            },
            {
                "name": "Breyanzi (lisocabtagene maraleucel)",
                "target": "CD19",
                "approval_year": 2021,
                "indication": "R/R LBCL; 2L LBCL",
                "sponsor": "Bristol Myers Squibb",
            },
        ],
        pipeline_products=[
            {
                "name": "obecabtagene autoleucel (obe-cel)",
                "target": "CD19",
                "phase": "Phase 3 / Approved EU 2024",
                "sponsor": "Autolus Therapeutics",
                "notes": "Fast-off rate CD19 CAR designed to reduce toxicity",
            },
            {
                "name": "huCART19-IL18 (armored)",
                "target": "CD19",
                "phase": "Phase 1",
                "sponsor": "University of Pennsylvania",
                "notes": "IL-18-secreting armored CAR-T for enhanced efficacy",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.57,
                "grade3_plus": 0.08,
                "onset_days": "1-14 (median day 2-5)",
                "duration": "5-10 days (median 7 days)",
                "notes": (
                    "Product-specific: Yescarta any-grade ~69%, grade3+ ~7%; "
                    "Kymriah any-grade ~44%, grade3+ ~3%; "
                    "Tecartus any-grade ~91%, grade3+ ~24%; "
                    "Breyanzi any-grade ~52%, grade3+ ~2%"
                ),
            },
            "icans": {
                "any_grade": 0.28,
                "grade3_plus": 0.12,
                "onset_days": "2-17 (median day 4-7)",
                "duration": "2-21 days (median 14 days)",
                "notes": (
                    "Product-specific: Yescarta ~33%, grade3+ ~12%; "
                    "Kymriah ~22%, grade3+ ~3%; "
                    "Tecartus ~60%, grade3+ ~31%; "
                    "Breyanzi ~16%, grade3+ ~10%"
                ),
            },
            "hlh_mas": {
                "any_grade": 0.01,
                "grade3_plus": 0.008,
                "onset_days": "5-30 (typically overlaps severe CRS)",
                "duration": "Variable, weeks if untreated",
                "notes": "Incidence 0.87% across 6,234 recipients. Higher with axi-cel (0.79%), tisa-cel (1.91%)",
            },
            "prolonged_cytopenias": {
                "any_grade": 0.58,
                "grade3_plus": 0.35,
                "onset_days": "0-14 (from lymphodepletion)",
                "duration": "Months; grade3+ neutropenia in 30% at day 30, 7% at 1 year",
                "notes": "Biphasic pattern: initial recovery then secondary decline in some patients",
            },
            "b_cell_aplasia": {
                "any_grade": 0.67,
                "grade3_plus": 0.15,
                "onset_days": "7-28",
                "duration": "Months to years; may be indefinite with persistent CAR-T",
                "notes": "IgG <400 mg/dL in 27-46% at days 15-90; 67% beyond 90 days in ALL",
            },
            "infections": {
                "any_grade": 0.45,
                "grade3_plus": 0.20,
                "onset_days": "7-365",
                "duration": "Variable",
                "notes": "Risk highest in first 90 days; viral reactivation (CMV, HHV-6) common",
            },
            "secondary_malignancy": {
                "any_grade": 0.065,
                "grade3_plus": 0.065,
                "onset_days": "30-730 (range 1-19 months for T-cell malignancies)",
                "duration": "Permanent if not treated",
                "notes": (
                    "FDA boxed warning Jan 2024. T-cell malignancy rate ~0.09% in meta-analysis. "
                    "Overall secondary cancer ~6.5% at 3-year follow-up (Stanford study)"
                ),
            },
            "coagulopathy_dic": {
                "any_grade": 0.50,
                "grade3_plus": 0.07,
                "onset_days": "6-20",
                "duration": "Resolves with CRS treatment",
                "notes": "D-dimer elevation in 50%, DIC in 7% with grade3+ CRS. Fatality rate 47.7% if DIC develops",
            },
            "febrile_neutropenia": {
                "any_grade": 0.20,
                "grade3_plus": 0.20,
                "onset_days": "3-14",
                "duration": "Until neutrophil recovery",
                "notes": "Related to lymphodepleting conditioning (Flu/Cy)",
            },
        },
        risk_factors=[
            "High tumor burden",
            "Pre-existing neurologic comorbidities",
            "High-dose lymphodepletion regimen",
            "Elevated baseline LDH/ferritin/CRP",
            "Prior lines of therapy (3+)",
            "Thrombocytopenia at baseline",
            "Product-specific (Tecartus highest CRS/ICANS rates)",
            "Prior allogeneic HSCT",
        ],
        data_sources=[
            "FDA prescribing information (Kymriah, Yescarta, Tecartus, Breyanzi)",
            "ZUMA-1, ZUMA-2, ZUMA-7 clinical trials (Kite/Gilead)",
            "JULIET, ELARA clinical trials (Novartis)",
            "TRANSCEND NHL 001, TRANSFORM clinical trials (BMS)",
            "National Inpatient Sample (NIS) real-world analysis",
            "FDA FAERS database",
            "ASTCT consensus grading (Lee et al., 2019)",
        ],
        references=[
            "Lee DW et al. ASTCT Consensus Grading for CRS and Neurologic Toxicity. Biol Blood Marrow Transplant. 2019;25(4):625-638",
            "Neelapu SS et al. Axicabtagene Ciloleucel CAR T-Cell Therapy in Refractory Large B-Cell Lymphoma. NEJM. 2017;377(26):2531-2544",
            "Schuster SJ et al. Tisagenlecleucel in Adult Relapsed or Refractory DLBCL. NEJM. 2019;380(1):45-56",
            "Abramson JS et al. Lisocabtagene maraleucel for R/R large B-cell lymphoma. Lancet. 2020;396(10254):839-852",
            "Wang M et al. KTE-X19 CAR T-Cell Therapy in Relapsed or Refractory Mantle-Cell Lymphoma. NEJM. 2020;382(14):1331-1342",
            "FDA Safety Communication: T-cell Malignancies Following CAR T-cell Therapy. January 2024",
            "Strati P et al. Secondary cancers after CAR-T cell therapy. Stanford Medicine. 2024",
        ],
        notes="Most established cell therapy category. Six approved CD19-targeting products globally.",
    ),

    # ===================================================================
    # 2. CAR-T BCMA
    # ===================================================================
    "cart_bcma": TherapyType(
        id="cart_bcma",
        name="CAR-T Cell Therapy (BCMA-directed)",
        category="CAR-T",
        target_antigens=["BCMA (B-Cell Maturation Antigen)"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "icans",
            "hlh_mas",
            "prolonged_cytopenias",
            "infections",
            "secondary_malignancy",
            "neurotoxicity_delayed",
            "coagulopathy_dic",
            "cardiovascular_events",
            "febrile_neutropenia",
        ],
        approved_products=[
            {
                "name": "Abecma (idecabtagene vicleucel, ide-cel)",
                "target": "BCMA",
                "approval_year": 2021,
                "indication": "R/R multiple myeloma (4L+, expanded to 2L+ in 2024)",
                "sponsor": "Bristol Myers Squibb / 2seventy bio",
            },
            {
                "name": "Carvykti (ciltacabtagene autoleucel, cilta-cel)",
                "target": "BCMA",
                "approval_year": 2022,
                "indication": "R/R multiple myeloma (4L+, expanded to 2L+ in 2024)",
                "sponsor": "Janssen / Legend Biotech",
            },
        ],
        pipeline_products=[
            {
                "name": "ALLO-605 (allogeneic BCMA CAR-T)",
                "target": "BCMA",
                "phase": "Phase 1",
                "sponsor": "Allogene Therapeutics",
                "notes": "Allogeneic off-the-shelf approach using TALEN gene editing",
            },
            {
                "name": "PHE885",
                "target": "BCMA",
                "phase": "Phase 2",
                "sponsor": "Novartis",
                "notes": "T-Charge platform for faster manufacturing",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.84,
                "grade3_plus": 0.05,
                "onset_days": "1-14 (median day 7)",
                "duration": "5-14 days",
                "notes": (
                    "Abecma: CRS 16.1% of all AE reports; "
                    "Carvykti: CRS 10.3% of all AE reports. "
                    "Carvykti CRS any-grade ~95%, grade3+ ~4%"
                ),
            },
            "icans": {
                "any_grade": 0.18,
                "grade3_plus": 0.03,
                "onset_days": "3-21",
                "duration": "Variable, most resolve within 2 weeks",
                "notes": "Lower ICANS rate than CD19 products",
            },
            "neurotoxicity_delayed": {
                "any_grade": 0.06,
                "grade3_plus": 0.03,
                "onset_days": "14-180+ (can be very late onset)",
                "duration": "Weeks to months; may be irreversible",
                "notes": (
                    "Carvykti: 7 Parkinsonism cases, 13 Bell's palsy cases. "
                    "Abecma: 4 Parkinsonism cases, 0 Bell's palsy. "
                    "Carries boxed warning for Parkinsonism and Guillain-Barre syndrome"
                ),
            },
            "hlh_mas": {
                "any_grade": 0.02,
                "grade3_plus": 0.015,
                "onset_days": "7-30",
                "duration": "Variable",
                "notes": "ide-cel highest HLH incidence at 2.01% across products",
            },
            "prolonged_cytopenias": {
                "any_grade": 0.65,
                "grade3_plus": 0.40,
                "onset_days": "0-14",
                "duration": "Months; carries boxed warning for prolonged/recurrent cytopenias (Carvykti)",
                "notes": "Thrombocytopenia grade 3-4 in ~60% of myeloma patients",
            },
            "infections": {
                "any_grade": 0.60,
                "grade3_plus": 0.25,
                "onset_days": "7-365",
                "duration": "Variable",
                "notes": "Hypogammaglobulinemia and prolonged cytopenias compound infection risk",
            },
            "secondary_malignancy": {
                "any_grade": 0.065,
                "grade3_plus": 0.065,
                "onset_days": "60-730",
                "duration": "Permanent if not treated",
                "notes": "FDA boxed warning Jan 2024. MDS/AML and T-cell malignancies reported",
            },
        },
        risk_factors=[
            "High tumor burden",
            "Prior lines of therapy (heavily pretreated myeloma)",
            "Elevated baseline ferritin/CRP",
            "Renal impairment",
            "Bridging therapy intensity",
            "Older age (>65)",
            "Prior autologous HSCT",
        ],
        data_sources=[
            "FDA prescribing information (Abecma, Carvykti)",
            "KarMMa, KarMMa-3 clinical trials (BMS/2seventy bio)",
            "CARTITUDE-1, CARTITUDE-4 clinical trials (Janssen/Legend)",
            "FDA FAERS database",
            "FDA ODAC meetings (2024)",
        ],
        references=[
            "Munshi NC et al. Idecabtagene Vicleucel in Relapsed and Refractory Multiple Myeloma. NEJM. 2021;384(8):705-716",
            "Berdeja JG et al. Ciltacabtagene autoleucel, a BCMA-directed CAR T-cell therapy for R/R myeloma. Lancet. 2021;398(10297):314-324",
            "San-Miguel J et al. Cilta-cel vs Standard of Care in Lenalidomide-Refractory Multiple Myeloma (CARTITUDE-4). NEJM. 2023",
            "FDA Safety Communication: T-cell Malignancies Following CAR T-cell Therapy. January 2024",
            "FDA FAERS disproportionality analysis: BCMA therapy AEs. Fierce Pharma. 2024",
        ],
        notes="Two approved BCMA CAR-T products. Unique delayed neurotoxicity profile (Parkinsonism) vs CD19 products.",
    ),

    # ===================================================================
    # 3. CAR-T Dual-target / CD22
    # ===================================================================
    "cart_dual_cd19_cd22": TherapyType(
        id="cart_dual_cd19_cd22",
        name="CAR-T Cell Therapy (Dual-target CD19/CD22)",
        category="CAR-T",
        target_antigens=["CD19", "CD22"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "icans",
            "prolonged_cytopenias",
            "b_cell_aplasia",
            "infections",
            "secondary_malignancy",
            "febrile_neutropenia",
        ],
        approved_products=[],
        pipeline_products=[
            {
                "name": "CD19/CD22 tandem CAR-T (AUTO1/22)",
                "target": "CD19/CD22",
                "phase": "Phase 1/2",
                "sponsor": "Autolus Therapeutics",
                "notes": "Tandem bispecific CAR design",
            },
            {
                "name": "GC022F",
                "target": "CD19/CD22",
                "phase": "Phase 2",
                "sponsor": "Gracell Biotechnologies",
                "notes": "FasT CAR-T platform for rapid manufacturing",
            },
            {
                "name": "CD19/CD22 sequential CAR-T",
                "target": "CD19 then CD22",
                "phase": "Phase 1/2",
                "sponsor": "Multiple academic centers",
                "notes": "Sequential infusion strategy to prevent antigen escape",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.78,
                "grade3_plus": 0.06,
                "onset_days": "1-14",
                "duration": "5-10 days",
                "notes": "CD19 infusion CRS ~78%, CD22 infusion CRS ~39% (lower with second infusion)",
            },
            "icans": {
                "any_grade": 0.10,
                "grade3_plus": 0.03,
                "onset_days": "3-14",
                "duration": "5-14 days",
                "notes": "Lower ICANS vs CD19 mono-target; no ICANS reported with CD22 component alone",
            },
            "prolonged_cytopenias": {
                "any_grade": 0.55,
                "grade3_plus": 0.30,
                "onset_days": "0-14",
                "duration": "Weeks to months",
                "notes": "Grade3+ hematologic AEs comparable between CD19 and CD22 infusions",
            },
            "b_cell_aplasia": {
                "any_grade": 0.60,
                "grade3_plus": 0.12,
                "onset_days": "7-28",
                "duration": "Months to years",
                "notes": "Dual targeting may lead to deeper B-cell depletion",
            },
            "infections": {
                "any_grade": 0.40,
                "grade3_plus": 0.18,
                "onset_days": "14-180",
                "duration": "Variable",
                "notes": "Similar infection profile to CD19 mono-target",
            },
        },
        risk_factors=[
            "High tumor burden",
            "Prior CD19 CAR-T failure",
            "Cumulative lymphodepletion from sequential approach",
            "Antigen-loss escape variants",
        ],
        data_sources=[
            "Phase 1 trials (NCI, multiple centers)",
            "Frontiers in Immunology meta-analysis 2023",
            "Nature Medicine phase 1 trials (Schultz 2021, Shah 2021)",
        ],
        references=[
            "Schultz LM et al. CAR T cells with dual targeting of CD19 and CD22 in pediatric/young adult B-ALL. Nature Medicine. 2021;27:1797-1805",
            "Shah NN et al. CD19/CD22 dual-target CAR T cells in adult B-cell malignancies. Nature Medicine. 2021;27:1419-1431",
            "ESMO 2025: Dual-target CD19/CD22 CAR-T shows 100% ORR in R/R LBCL (poster presentation)",
        ],
        notes="Investigational strategy to overcome CD19 antigen escape. Lower severe CRS/ICANS rates than CD19 monotherapy.",
    ),

    # ===================================================================
    # 4. TCR-T Cell Therapy
    # ===================================================================
    "tcr_t": TherapyType(
        id="tcr_t",
        name="TCR-T Cell Therapy",
        category="TCR-T",
        target_antigens=["MAGE-A4", "NY-ESO-1", "AFP", "KRAS G12D", "HPV E6/E7"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "icans",
            "prolonged_cytopenias",
            "infections",
            "febrile_neutropenia",
            "cardiovascular_events",
            "infusion_reactions",
        ],
        approved_products=[
            {
                "name": "Tecelra (afamitresgene autoleucel, afami-cel)",
                "target": "MAGE-A4",
                "approval_year": 2024,
                "indication": "Metastatic synovial sarcoma (HLA-A*02+ patients, post-chemo)",
                "sponsor": "Adaptimmune",
            },
        ],
        pipeline_products=[
            {
                "name": "ADP-A2M4CD8 (next-gen MAGE-A4 TCR-T)",
                "target": "MAGE-A4",
                "phase": "Phase 2",
                "sponsor": "Adaptimmune",
                "notes": "Enhanced CD8 co-receptor for improved T-cell activation",
            },
            {
                "name": "KRAS G12D TCR-T",
                "target": "KRAS G12D neoantigen",
                "phase": "Phase 1/2",
                "sponsor": "NCI / multiple",
                "notes": "Targeting common oncogenic mutation in pancreatic/colorectal cancer",
            },
            {
                "name": "NY-ESO-1 TCR-T",
                "target": "NY-ESO-1",
                "phase": "Phase 1/2",
                "sponsor": "Multiple (Adaptimmune, GSK legacy)",
                "notes": "Cancer-testis antigen targeted in synovial sarcoma, melanoma, NSCLC",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.70,
                "grade3_plus": 0.05,
                "onset_days": "1-14 (median day 3-7)",
                "duration": "3-7 days",
                "notes": "70% overall CRS rate; 90% were grade 1-2. Manageable with standard CRS protocols",
            },
            "prolonged_cytopenias": {
                "any_grade": 1.0,
                "grade3_plus": 1.0,
                "onset_days": "0-7 (from lymphodepletion)",
                "duration": "14-28 days for recovery",
                "notes": "All patients experienced grade 3+ hematologic toxicities in phase 1",
            },
            "infections": {
                "any_grade": 0.40,
                "grade3_plus": 0.15,
                "onset_days": "7-60",
                "duration": "Variable",
                "notes": "Related to prolonged cytopenias from lymphodepletion",
            },
            "icans": {
                "any_grade": 0.05,
                "grade3_plus": 0.02,
                "onset_days": "3-14",
                "duration": "3-7 days",
                "notes": "Lower ICANS rate than CD19 CAR-T products",
            },
        },
        risk_factors=[
            "HLA-restricted (HLA-A*02 required for afami-cel)",
            "Cross-reactivity risk with normal tissue antigens",
            "Lymphodepletion intensity",
            "Tumor burden",
            "Performance status",
        ],
        data_sources=[
            "FDA prescribing information (Tecelra)",
            "SPEARHEAD-1 pivotal trial (Adaptimmune)",
            "Phase 1 dose-escalation studies (Nature Medicine 2022)",
        ],
        references=[
            "D'Angelo SP et al. Afamitresgene autoleucel for advanced synovial sarcoma and myxoid round cell liposarcoma (SPEARHEAD-1). Lancet. 2024;403:1460-1471",
            "Hong DS et al. Autologous T cell therapy for MAGE-A4+ solid cancers in HLA-A*02+ patients. Nature Medicine. 2023;29:104-114",
            "FDA Approval: Tecelra (afamitresgene autoleucel) for metastatic synovial sarcoma. August 2024",
        ],
        notes="First TCR-T therapy approved by FDA (Aug 2024). First engineered cell therapy for solid tumors. HLA-restricted.",
    ),

    # ===================================================================
    # 5. NK Cell Therapy
    # ===================================================================
    "nk_cell": TherapyType(
        id="nk_cell",
        name="NK Cell Therapy (including CAR-NK)",
        category="NK Cell",
        target_antigens=["CD19 (CAR-NK)", "CD20", "HER2", "NKG2D ligands", "Non-antigen specific (allogeneic NK)"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "infusion_reactions",
            "infections",
            "prolonged_cytopenias",
        ],
        approved_products=[],
        pipeline_products=[
            {
                "name": "FT596 (iPSC-derived CAR-NK)",
                "target": "CD19 (with CD16 Fc receptor and IL-15/IL-15R)",
                "phase": "Phase 1 completed",
                "sponsor": "Fate Therapeutics",
                "notes": "iPSC-derived, off-the-shelf, 3 antitumor modalities. CR 85% in r/r FL",
            },
            {
                "name": "FT500 (iPSC-derived NK)",
                "target": "Non-antigen specific",
                "phase": "Phase 1",
                "sponsor": "Fate Therapeutics",
                "notes": "First iPSC-NK in clinical trial; no DLTs or GvHD observed",
            },
            {
                "name": "TAK-007 (cord blood-derived CAR-NK)",
                "target": "CD19",
                "phase": "Phase 2",
                "sponsor": "Takeda / MD Anderson",
                "notes": "Umbilical cord blood-derived; ORR 50% at higher dose levels",
            },
            {
                "name": "NKX019 (CAR-NK)",
                "target": "CD19",
                "phase": "Phase 1",
                "sponsor": "Nkarta Therapeutics",
                "notes": "Engineered with OX40/CD3z signaling and IL-15 membrane-bound",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.10,
                "grade3_plus": 0.0,
                "onset_days": "1-7",
                "duration": "1-3 days",
                "notes": (
                    "FT596: CRS 6% (grade 1 only) monotherapy, 13% with rituximab (max grade 2). "
                    "TAK-007: no severe CRS (grade 2+) reported. "
                    "Dramatically lower CRS than CAR-T products"
                ),
            },
            "icans": {
                "any_grade": 0.0,
                "grade3_plus": 0.0,
                "onset_days": "Not observed",
                "duration": "Not observed",
                "notes": "No neurotoxicity observed across FT596, FT500, or TAK-007 trials",
            },
            "infusion_reactions": {
                "any_grade": 0.08,
                "grade3_plus": 0.01,
                "onset_days": "Day 0 (during infusion)",
                "duration": "Hours",
                "notes": "Mild infusion reactions; no severe hypersensitivity",
            },
            "infections": {
                "any_grade": 0.20,
                "grade3_plus": 0.05,
                "onset_days": "7-60",
                "duration": "Variable",
                "notes": "Lower infection rates than CAR-T due to less intensive lymphodepletion",
            },
            "prolonged_cytopenias": {
                "any_grade": 0.15,
                "grade3_plus": 0.05,
                "onset_days": "0-14",
                "duration": "Shorter than CAR-T; typically resolves within 4 weeks",
                "notes": "TAK-007: only 1 severe AE (grade 3+ anemia)",
            },
        },
        risk_factors=[
            "Dose-dependent (higher cell doses may increase mild CRS)",
            "Combination with rituximab may increase CRS",
            "Limited persistence may require re-dosing",
            "Lymphodepletion regimen intensity",
        ],
        data_sources=[
            "FT596 Phase 1 trial (NCT04245722) — Lancet 2025",
            "FT500 Phase 1 trial (NCT03841110)",
            "TAK-007 Phase 1/2 (MD Anderson / Takeda)",
            "ASH 2024 Annual Meeting abstracts (CAR-NK updates)",
        ],
        references=[
            "Cichocki F et al. iPSC-derived CD19-CAR NK cells in B-cell lymphoma: phase 1 first-in-human trial. Lancet. 2025;405:127-138",
            "Liu E et al. Use of CAR-Transduced Natural Killer Cells in CD19-Positive Lymphoid Tumors. NEJM. 2020;382(6):545-553",
            "ASH 2024: CAR-NK cell therapy latest updates (multiple abstracts)",
        ],
        notes=(
            "Key advantage: dramatically lower CRS/ICANS vs CAR-T; no GvHD risk (allogeneic). "
            "Off-the-shelf potential. Trade-off: limited persistence may reduce durability."
        ),
    ),

    # ===================================================================
    # 6. TIL Therapy
    # ===================================================================
    "til": TherapyType(
        id="til",
        name="Tumor-Infiltrating Lymphocyte (TIL) Therapy",
        category="TIL",
        target_antigens=["Tumor neoantigens (polyclonal, patient-specific)"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "prolonged_cytopenias",
            "infections",
            "febrile_neutropenia",
            "cardiovascular_events",
            "infusion_reactions",
        ],
        approved_products=[
            {
                "name": "Amtagvi (lifileucel)",
                "target": "Tumor neoantigens (melanoma)",
                "approval_year": 2024,
                "indication": "Unresectable or metastatic melanoma (post-PD-1 and BRAF inhibitor if BRAF V600+)",
                "sponsor": "Iovance Biotherapeutics",
            },
        ],
        pipeline_products=[
            {
                "name": "IOV-4001 (next-gen TIL for melanoma)",
                "target": "Tumor neoantigens",
                "phase": "Phase 2",
                "sponsor": "Iovance Biotherapeutics",
                "notes": "Optimized TIL manufacturing process",
            },
            {
                "name": "IOV-LUN-202 (TIL for NSCLC)",
                "target": "Tumor neoantigens (lung cancer)",
                "phase": "Phase 2",
                "sponsor": "Iovance Biotherapeutics",
                "notes": "TIL therapy expansion into non-small cell lung cancer",
            },
            {
                "name": "ITIL-306 (cryopreserved TIL)",
                "target": "Tumor neoantigens",
                "phase": "Phase 1/2",
                "sponsor": "Instil Bio",
                "notes": "Genetically modified TIL with improved persistence",
            },
        ],
        default_ae_rates={
            "prolonged_cytopenias": {
                "any_grade": 0.95,
                "grade3_plus": 0.78,
                "onset_days": "0-7 (from conditioning)",
                "duration": "14-28 days for count recovery",
                "notes": (
                    "Grade 3-4: thrombocytopenia 78.2%, neutropenia 69.2%, anemia 58.3%. "
                    "Related to NMA lymphodepletion (Flu/Cy) and high-dose IL-2"
                ),
            },
            "cytokine_release_syndrome": {
                "any_grade": 0.032,
                "grade3_plus": 0.01,
                "onset_days": "1-7",
                "duration": "3-5 days",
                "notes": "CRS incidence only 3.2% — much lower than CAR-T",
            },
            "infections": {
                "any_grade": 0.40,
                "grade3_plus": 0.20,
                "onset_days": "7-30",
                "duration": "Variable",
                "notes": "Related to prolonged cytopenias from conditioning and IL-2",
            },
            "febrile_neutropenia": {
                "any_grade": 0.30,
                "grade3_plus": 0.30,
                "onset_days": "3-14",
                "duration": "Until count recovery",
                "notes": "Expected from myeloablative-like conditioning",
            },
            "infusion_reactions": {
                "any_grade": 0.064,
                "grade3_plus": 0.01,
                "onset_days": "Day 0",
                "duration": "Hours",
                "notes": "Anaphylactic reactions 1.3%",
            },
            "cardiovascular_events": {
                "any_grade": 0.15,
                "grade3_plus": 0.05,
                "onset_days": "1-14 (related to IL-2)",
                "duration": "Resolves with IL-2 cessation",
                "notes": "Tachycardia, hypotension, arrhythmia — largely IL-2 related. One fatal arrhythmia reported",
            },
        },
        risk_factors=[
            "High-dose IL-2 administration (primary toxicity driver)",
            "Non-myeloablative lymphodepletion conditioning (Flu/Cy)",
            "Cardiac comorbidities (IL-2 contraindication)",
            "Renal impairment",
            "Poor performance status (ECOG 2+)",
            "Low body weight",
        ],
        data_sources=[
            "FDA prescribing information (Amtagvi)",
            "C-144-01 pivotal trial (Iovance)",
            "Pooled safety analysis (N=156 patients)",
        ],
        references=[
            "Chesney J et al. Lifileucel (LN-144/LN-145-S1) for advanced melanoma. C-144-01 trial results. JCO. 2022",
            "Rohaan MW et al. TIL therapy versus ipilimumab in advanced melanoma. NEJM. 2022;387:2113-2125",
            "FDA Approval: Amtagvi (lifileucel) for unresectable/metastatic melanoma. February 2024",
        ],
        notes=(
            "First TIL therapy approved (Feb 2024). Toxicity profile dominated by conditioning "
            "regimen and IL-2, not the cell product itself. Distinct from CAR-T toxicity pattern."
        ),
    ),

    # ===================================================================
    # 7. CAR-Macrophage
    # ===================================================================
    "car_macrophage": TherapyType(
        id="car_macrophage",
        name="CAR-Macrophage Therapy",
        category="CAR-Macrophage",
        target_antigens=["HER2"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "infusion_reactions",
            "infections",
        ],
        approved_products=[],
        pipeline_products=[
            {
                "name": "CT-0508 (anti-HER2 CAR-Macrophage)",
                "target": "HER2",
                "phase": "Phase 1",
                "sponsor": "Carisma Therapeutics",
                "notes": (
                    "First CAR-macrophage in clinical trials. Published in Nature Medicine Feb 2025. "
                    "Phase 1b with pembrolizumab ongoing"
                ),
            },
            {
                "name": "CT-0525 (anti-HER2 CAR-M + anti-PD1)",
                "target": "HER2",
                "phase": "Phase 1",
                "sponsor": "Carisma Therapeutics",
                "notes": "Combination approach with checkpoint inhibitor",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.14,
                "grade3_plus": 0.0,
                "onset_days": "1-3",
                "duration": "1-3 days",
                "notes": (
                    "2 cases of CRS (grade 1-2) among 14 patients. No grade 3+ CRS observed. "
                    "Dramatically lower than CAR-T"
                ),
            },
            "infusion_reactions": {
                "any_grade": 0.07,
                "grade3_plus": 0.07,
                "onset_days": "Day 0",
                "duration": "Hours",
                "notes": "1 serious infusion reaction (grade 3) out of 14 patients",
            },
            "infections": {
                "any_grade": 0.10,
                "grade3_plus": 0.0,
                "onset_days": "7-30",
                "duration": "Variable",
                "notes": "Low infection risk — no myeloablative conditioning required",
            },
        },
        risk_factors=[
            "HER2 overexpression status (must be HER2 3+)",
            "Prior treatment history",
            "Very early clinical data — limited sample size (N=14)",
        ],
        data_sources=[
            "NCT04660929 Phase 1 trial (Carisma Therapeutics)",
            "Nature Medicine 2025 publication",
            "ASCO 2022 abstract",
        ],
        references=[
            "Klichinsky M et al. CAR-macrophage therapy for HER2-overexpressing advanced solid tumors: phase 1 trial. Nature Medicine. 2025;31(4):1044-1053",
            "Klichinsky M et al. Phase 1 first-in-human study of CT-0508 in HER2-overexpressing solid tumors. JCO. 2022;40(suppl):2533",
        ],
        notes=(
            "Earliest-stage therapy category. Favorable safety profile — no severe CRS/ICANS. "
            "No DLTs reached. Designed for solid tumors with TME remodeling capability."
        ),
    ),

    # ===================================================================
    # 8. Gene Therapy — Ex Vivo (Hematopoietic)
    # ===================================================================
    "gene_therapy_hematopoietic": TherapyType(
        id="gene_therapy_hematopoietic",
        name="Gene Therapy (Hematopoietic / Ex Vivo)",
        category="Gene Therapy",
        target_antigens=["HBB gene (Casgevy, Zynteglo)", "ABCD1 gene (Skysona)"],
        applicable_aes=[
            "prolonged_cytopenias",
            "febrile_neutropenia",
            "veno_occlusive_disease",
            "infections",
            "secondary_malignancy",
            "myelodysplastic_syndrome",
            "engraftment_failure",
            "infusion_reactions",
        ],
        approved_products=[
            {
                "name": "Casgevy (exagamglogene autotemcel)",
                "target": "BCL11A (CRISPR/Cas9 gene editing for SCD and TDT)",
                "approval_year": 2023,
                "indication": "Sickle cell disease (age 12+) with recurrent VOCs; transfusion-dependent beta-thalassemia",
                "sponsor": "Vertex / CRISPR Therapeutics",
            },
            {
                "name": "Zynteglo (betibeglogene autotemcel)",
                "target": "Beta-globin gene (lentiviral gene addition)",
                "approval_year": 2022,
                "indication": "Beta-thalassemia requiring regular transfusions",
                "sponsor": "bluebird bio",
            },
            {
                "name": "Skysona (elivaldogene autotemcel)",
                "target": "ABCD1 gene (lentiviral gene addition)",
                "approval_year": 2022,
                "indication": "Cerebral adrenoleukodystrophy (CALD) without HLA-matched donor (updated 2025)",
                "sponsor": "bluebird bio",
            },
        ],
        pipeline_products=[
            {
                "name": "Lyfgenia (lovotibeglogene autotemcel)",
                "target": "Beta-globin gene (lentiviral)",
                "phase": "Approved (2023)",
                "sponsor": "bluebird bio",
                "notes": "For SCD; carries boxed warning for hematologic malignancy",
            },
            {
                "name": "nula-cel (CRISPR-edited fetal hemoglobin)",
                "target": "HBG1/HBG2 promoter",
                "phase": "Phase 1/2",
                "sponsor": "Editas Medicine / Vertex",
                "notes": "Next-generation gene editing approach",
            },
        ],
        default_ae_rates={
            "prolonged_cytopenias": {
                "any_grade": 1.0,
                "grade3_plus": 1.0,
                "onset_days": "0-7 (from myeloablative conditioning)",
                "duration": "14-42 days to engraftment",
                "notes": "100% of patients experience grade 3-4 neutropenia and thrombocytopenia from busulfan conditioning",
            },
            "febrile_neutropenia": {
                "any_grade": 0.72,
                "grade3_plus": 0.72,
                "onset_days": "3-14",
                "duration": "Until engraftment",
                "notes": "Febrile neutropenia in 72% (Skysona); related to myeloablative conditioning",
            },
            "veno_occlusive_disease": {
                "any_grade": 0.02,
                "grade3_plus": 0.01,
                "onset_days": "10-21",
                "duration": "12-30 days with treatment",
                "notes": "Casgevy: 1 case (2%) in SCD cohort, resolved with defibrotide. Risk from busulfan conditioning",
            },
            "myelodysplastic_syndrome": {
                "any_grade": 0.15,
                "grade3_plus": 0.15,
                "onset_days": "420-3650 (14 months to 10 years)",
                "duration": "Permanent",
                "notes": (
                    "Skysona: 10/67 (15%) developed MDS/AML (updated 2025). "
                    "Zynteglo: no cases observed but 15-year monitoring required. "
                    "Casgevy: 2 PMR studies mandated (CRISPR off-target monitoring)"
                ),
            },
            "infections": {
                "any_grade": 0.50,
                "grade3_plus": 0.25,
                "onset_days": "7-90",
                "duration": "Variable",
                "notes": (
                    "Skysona: grade 3+ bacterial 12%, viral 3%, unspecified 6%. "
                    "High risk during aplastic period from myeloablative conditioning"
                ),
            },
            "engraftment_failure": {
                "any_grade": 0.05,
                "grade3_plus": 0.03,
                "onset_days": "28-42 (if primary failure); variable (if secondary)",
                "duration": "Requires rescue HSCT",
                "notes": "Rare but life-threatening. Backup stem cells collected as safety net",
            },
        },
        risk_factors=[
            "Myeloablative busulfan conditioning (primary toxicity driver)",
            "Prior iron overload (SCD, thalassemia)",
            "Hepatic impairment (VOD risk)",
            "Lentiviral vector insertional mutagenesis risk (Skysona, Zynteglo)",
            "CRISPR off-target editing risk (Casgevy — theoretical)",
            "Age (pediatric patients)",
        ],
        data_sources=[
            "FDA prescribing information (Casgevy, Zynteglo, Skysona)",
            "CLIMB-121 and CLIMB-131 trials (Vertex/CRISPR)",
            "HGB-206, HGB-210 trials (bluebird bio)",
            "ALD-102, ALD-104 trials (bluebird bio)",
            "FDA safety communications (Skysona MDS risk, 2024-2025)",
        ],
        references=[
            "Frangoul H et al. Exagamglogene Autotemcel for Severe Sickle Cell Disease. NEJM. 2024;390:1649-1662",
            "Locatelli F et al. Betibeglogene Autotemcel Gene Therapy for Non-beta0/beta0 Genotype beta-Thalassemia. NEJM. 2022;386(5):415-427",
            "FDA Safety Communication: Skysona hematologic malignancy risk update. November 2024",
            "FDA Required Labeling Changes: Skysona indication restriction. August 2025",
        ],
        notes=(
            "Toxicity dominated by myeloablative conditioning, not cell product. "
            "Skysona MDS risk (15%) led to indication restriction. "
            "Casgevy is first CRISPR therapy approved (Dec 2023)."
        ),
    ),

    # ===================================================================
    # 9. Gene Therapy — In Vivo (AAV-based)
    # ===================================================================
    "gene_therapy_aav": TherapyType(
        id="gene_therapy_aav",
        name="Gene Therapy (In Vivo / AAV-based)",
        category="Gene Therapy",
        target_antigens=["SMN1 gene (Zolgensma)", "RPE65 gene (Luxturna)"],
        applicable_aes=[
            "hepatotoxicity",
            "thrombotic_microangiopathy",
            "infusion_reactions",
            "ocular_adverse_events",
            "infections",
        ],
        approved_products=[
            {
                "name": "Zolgensma (onasemnogene abeparvovec)",
                "target": "SMN1 gene (AAV9 vector, IV)",
                "approval_year": 2019,
                "indication": "Spinal muscular atrophy (SMA) in children <2 years",
                "sponsor": "Novartis Gene Therapies",
            },
            {
                "name": "Luxturna (voretigene neparvovec-rzyl)",
                "target": "RPE65 gene (AAV2 vector, subretinal)",
                "approval_year": 2017,
                "indication": "Biallelic RPE65 mutation-associated retinal dystrophy",
                "sponsor": "Spark Therapeutics / Roche",
            },
        ],
        pipeline_products=[
            {
                "name": "Elevidys (delandistrogene moxeparvovec)",
                "target": "Dystrophin micro-gene (AAV, IV)",
                "phase": "Approved (2023, accelerated)",
                "sponsor": "Sarepta Therapeutics",
                "notes": "For Duchenne muscular dystrophy; hepatotoxicity monitoring required",
            },
            {
                "name": "Hemgenix (etranacogene dezaparvovec)",
                "target": "Factor IX gene (AAV5, IV)",
                "phase": "Approved (2022)",
                "sponsor": "CSL Behring",
                "notes": "For hemophilia B; monitoring for hepatotoxicity and thromboembolic events",
            },
        ],
        default_ae_rates={
            "hepatotoxicity": {
                "any_grade": 0.43,
                "grade3_plus": 0.10,
                "onset_days": "1-30 (most within first 8 days, some after 1 year)",
                "duration": "Weeks to months with steroid taper",
                "notes": (
                    "Zolgensma: hepatotoxicity 43% (mostly isolated AST/ALT elevations). "
                    "Fatal acute liver failure reported (2 deaths in Russia/Kazakhstan). "
                    "Requires prolonged corticosteroid prophylaxis"
                ),
            },
            "thrombotic_microangiopathy": {
                "any_grade": 0.02,
                "grade3_plus": 0.02,
                "onset_days": "1-14",
                "duration": "Weeks with treatment",
                "notes": "Zolgensma: 3 patients (2%) developed TMA. More common in patients >= 8.5 kg",
            },
            "infusion_reactions": {
                "any_grade": 0.10,
                "grade3_plus": 0.02,
                "onset_days": "Day 0",
                "duration": "Hours",
                "notes": "Fever and vomiting most common (>= 5% incidence for Zolgensma)",
            },
            "ocular_adverse_events": {
                "any_grade": 0.50,
                "grade3_plus": 0.10,
                "onset_days": "1-365",
                "duration": "Variable; chorioretinal atrophy may be progressive",
                "notes": (
                    "Luxturna-specific: conjunctival hyperemia 22%, cataract 20%, IOP elevation 15%, "
                    "retinal tear 10%, macular hole 7%. Post-marketing: chorioretinal atrophy 13-50%"
                ),
            },
        },
        risk_factors=[
            "Pre-existing hepatic disease (Zolgensma)",
            "Body weight >= 8.5 kg increases TMA risk (Zolgensma)",
            "Pre-existing AAV antibodies (may reduce efficacy/increase immune response)",
            "Age at treatment",
            "Corticosteroid taper compliance (hepatotoxicity risk)",
            "Surgical technique (Luxturna — subretinal injection)",
        ],
        data_sources=[
            "FDA prescribing information (Zolgensma, Luxturna)",
            "STR1VE, SPR1NT clinical trials (Novartis)",
            "FDA FAERS database (Zolgensma post-marketing)",
            "EMA pharmacovigilance (EudraVigilance)",
        ],
        references=[
            "Mendell JR et al. Single-Dose Gene-Replacement Therapy for SMA. NEJM. 2017;377(18):1713-1722",
            "Russell S et al. Efficacy and Safety of Voretigene Neparvovec in RPE65-Mediated Inherited Retinal Dystrophy. Lancet. 2017;390(10097):849-860",
            "FDA Safety Communication: Zolgensma hepatotoxicity monitoring. 2023",
            "Frontiers in Pharmacology. FAERS analysis of Zolgensma adverse events. 2024",
        ],
        notes=(
            "In vivo gene therapies have distinct AE profiles from ex vivo approaches. "
            "Hepatotoxicity is the primary concern for systemic AAV vectors. "
            "Ocular AEs specific to subretinal delivery (Luxturna)."
        ),
    ),

    # ===================================================================
    # 10. MSC Therapy
    # ===================================================================
    "msc": TherapyType(
        id="msc",
        name="Mesenchymal Stromal Cell (MSC) Therapy",
        category="MSC",
        target_antigens=["Immunomodulatory (no specific antigen target)"],
        applicable_aes=[
            "infusion_reactions",
            "infections",
            "febrile_neutropenia",
        ],
        approved_products=[
            {
                "name": "Ryoncil (remestemcel-L)",
                "target": "Immunomodulatory MSC",
                "approval_year": 2024,
                "indication": "Steroid-refractory acute graft-versus-host disease (SR-aGvHD) in pediatric patients",
                "sponsor": "Mesoblast",
            },
        ],
        pipeline_products=[
            {
                "name": "Temestemcel-L (Mesoblast)",
                "target": "Immunomodulatory MSC",
                "phase": "Phase 3",
                "sponsor": "Mesoblast",
                "notes": "For chronic heart failure (ischemic cardiomyopathy)",
            },
            {
                "name": "CYP-001 (iPSC-derived MSC)",
                "target": "Immunomodulatory",
                "phase": "Phase 1",
                "sponsor": "Cynata Therapeutics",
                "notes": "iPSC-derived MSC platform for GvHD and other inflammatory conditions",
            },
        ],
        default_ae_rates={
            "infusion_reactions": {
                "any_grade": 0.15,
                "grade3_plus": 0.05,
                "onset_days": "Day 0 (during infusion)",
                "duration": "Hours",
                "notes": "3 patients discontinued due to acute infusion reactions; 1 for hypotension",
            },
            "infections": {
                "any_grade": 0.50,
                "grade3_plus": 0.19,
                "onset_days": "7-60",
                "duration": "Variable",
                "notes": (
                    "Grade 3+: bacterial 19%, viral 15%, pathogen unspecified 15%. "
                    "Reflects underlying immunocompromised state of SR-aGvHD patients"
                ),
            },
            "febrile_neutropenia": {
                "any_grade": 0.09,
                "grade3_plus": 0.09,
                "onset_days": "1-14",
                "duration": "Until resolution",
                "notes": "Pyrexia 9% (serious), respiratory failure 9% (serious)",
            },
        },
        risk_factors=[
            "Underlying immunocompromised state (GvHD patients)",
            "Concurrent immunosuppressive therapy",
            "Pediatric population vulnerability",
            "Theoretical long-term tumorigenicity risk (not observed)",
        ],
        data_sources=[
            "FDA prescribing information (Ryoncil)",
            "MSB-GVHD001 Phase 3 trial (Mesoblast)",
            "ISCT MSC committee statements",
        ],
        references=[
            "Kurtzberg J et al. Remestemcel-L for pediatric SR-aGvHD: Phase 3 trial results. Blood. 2020;136(Suppl 1):48",
            "Mesoblast FDA approval announcement. December 2024",
            "ISCT statement on FDA approval of allogenic MSC therapy. 2025",
        ],
        notes=(
            "First FDA-approved MSC therapy (Dec 2024). Generally favorable safety profile. "
            "AEs largely reflect underlying disease state rather than cell product toxicity. "
            "Allogeneic product — no GvHD from MSCs themselves."
        ),
    ),

    # ===================================================================
    # 11. Treg Therapy
    # ===================================================================
    "treg": TherapyType(
        id="treg",
        name="Regulatory T Cell (Treg) Therapy",
        category="Treg",
        target_antigens=["Polyclonal Treg", "HLA-A2-specific CAR-Treg", "Disease-specific Treg"],
        applicable_aes=[
            "infusion_reactions",
            "infections",
            "immune_suppression_risk",
        ],
        approved_products=[],
        pipeline_products=[
            {
                "name": "Sanegrity-1 (polyclonal Treg)",
                "target": "Polyclonal immunosuppression",
                "phase": "Phase 1/2",
                "sponsor": "Sangamo Therapeutics / Sanofi",
                "notes": "For kidney transplant tolerance",
            },
            {
                "name": "QEL-001 (CAR-Treg)",
                "target": "HLA-A2",
                "phase": "Phase 1/2",
                "sponsor": "Quell Therapeutics",
                "notes": "CAR-Treg for liver transplant tolerance",
            },
            {
                "name": "Polyclonal expanded Treg",
                "target": "Non-specific",
                "phase": "Phase 1/2 (multiple trials)",
                "sponsor": "Multiple academic centers",
                "notes": "Being studied in T1DM, GvHD, SLE, Crohn's disease, transplant rejection",
            },
        ],
        default_ae_rates={
            "infusion_reactions": {
                "any_grade": 0.05,
                "grade3_plus": 0.0,
                "onset_days": "Day 0",
                "duration": "Hours",
                "notes": "Mild flu-like symptoms and eosinophilia reported. No serious infusion reactions",
            },
            "infections": {
                "any_grade": 0.05,
                "grade3_plus": 0.0,
                "onset_days": "Variable",
                "duration": "Variable",
                "notes": (
                    "No opportunistic infections reported in T1DM trial (31-month follow-up). "
                    "No infections in kidney transplant trial (2-year follow-up). "
                    "Theoretical risk from immunosuppression"
                ),
            },
            "immune_suppression_risk": {
                "any_grade": 0.02,
                "grade3_plus": 0.0,
                "onset_days": "Variable",
                "duration": "Duration of Treg persistence",
                "notes": (
                    "Theoretical risk of reduced tumor surveillance and infection susceptibility. "
                    "No malignancies observed in clinical trials to date. "
                    "CAR-Treg cytotoxicity risk under investigation"
                ),
            },
        },
        risk_factors=[
            "Immunosuppressive mechanism of action (theoretical malignancy risk)",
            "Potential Treg instability and conversion to effector T cells",
            "Manufacturing challenges (purity of Treg product)",
            "Concurrent immunosuppressive medications",
            "Very limited clinical data (early-phase trials only)",
        ],
        data_sources=[
            "Phase 1/2 clinical trials (multiple centers, multiple indications)",
            "Frontiers in Immunology 2025 review",
            "Frontiers in Cell and Developmental Biology 2022 review",
        ],
        references=[
            "Bluestone JA et al. Type 1 diabetes immunotherapy using polyclonal regulatory T cells. Science Translational Medicine. 2015;7(315):315ra189",
            "Sawitzki B et al. Regulatory T cell therapy in transplantation: moving to the clinic. Science Immunology. 2020;5(48):eaax5397",
            "Frontiers review: Regulatory T cell therapies: from patient data to biological insights. 2025",
        ],
        notes=(
            "Earliest clinical stage of all categories. Remarkably clean safety profile "
            "to date — no life-threatening AEs in any trial. Unique mechanism: immunosuppressive "
            "rather than immunostimulatory."
        ),
    ),

    # ===================================================================
    # 12. Gamma-Delta T Cell Therapy
    # ===================================================================
    "gamma_delta_t": TherapyType(
        id="gamma_delta_t",
        name="Gamma-Delta T Cell Therapy",
        category="Gamma-Delta T Cell",
        target_antigens=["NKG2D ligands", "Phosphoantigens (via Vgamma9Vdelta2 TCR)", "CD20 (CAR-gd-T)"],
        applicable_aes=[
            "cytokine_release_syndrome",
            "icans",
            "infusion_reactions",
            "infections",
        ],
        approved_products=[],
        pipeline_products=[
            {
                "name": "ADI-001 (anti-CD20 CAR gamma-delta T)",
                "target": "CD20",
                "phase": "Phase 1",
                "sponsor": "Adicet Bio / Regeneron",
                "notes": "Allogeneic CAR-engineered gamma-delta T cells for B-cell malignancies",
            },
            {
                "name": "INB-100 (gamma-delta T for HSCT support)",
                "target": "Non-specific (innate immunity)",
                "phase": "Phase 1",
                "sponsor": "Incysus (now IN8bio)",
                "notes": "Post-haploidentical HSCT gamma-delta T infusion for leukemia",
            },
            {
                "name": "Allogeneic Vgamma9Vdelta2 T cells",
                "target": "Phosphoantigen-reactive",
                "phase": "Phase 1/2",
                "sponsor": "Multiple academic centers",
                "notes": "For lung cancer, liver cancer; zoledronic acid + IL-2 activation",
            },
        ],
        default_ae_rates={
            "cytokine_release_syndrome": {
                "any_grade": 0.11,
                "grade3_plus": 0.0,
                "onset_days": "1-7",
                "duration": "1-3 days",
                "notes": "ADI-001: 2 CRS cases out of ~18 patients (both grade 1-2). Very low CRS rate",
            },
            "icans": {
                "any_grade": 0.06,
                "grade3_plus": 0.0,
                "onset_days": "3-14",
                "duration": "Days",
                "notes": "ADI-001: 1 case of ICANS. No severe neurotoxicity observed",
            },
            "infusion_reactions": {
                "any_grade": 0.10,
                "grade3_plus": 0.02,
                "onset_days": "Day 0",
                "duration": "Hours",
                "notes": "Mild fever, chills reported. Generally well tolerated",
            },
            "infections": {
                "any_grade": 0.15,
                "grade3_plus": 0.05,
                "onset_days": "7-30",
                "duration": "Variable",
                "notes": "Low infection rate. No increased opportunistic infection risk observed",
            },
        },
        risk_factors=[
            "Allogeneic product (theoretical GvHD risk — not observed)",
            "Dose-dependent toxicity potential",
            "Limited clinical data (small phase 1 trials)",
            "Combination with zoledronic acid may cause flu-like symptoms",
        ],
        data_sources=[
            "ADI-001 Phase 1 trial (ASCO 2022)",
            "Allogeneic Vgamma9Vdelta2 T-cell study (Cellular & Molecular Immunology 2020)",
            "HILDEGAZ Phase 1 trial",
            "29 ongoing/completed trials as of Jan 2025 (ClinicalTrials.gov)",
        ],
        references=[
            "Neelapu SS et al. ADI-001: Anti-CD20 CAR-engineered allogeneic gamma delta T cells. JCO. 2022;40(suppl):7509",
            "Xu Y et al. Allogeneic Vgamma9Vdelta2 T-cell immunotherapy in late-stage lung/liver cancer. Cellular & Molecular Immunology. 2021;18:1083-1085",
            "Frontiers review: Gamma Delta T-Cell Based Cancer Immunotherapy. 2022",
        ],
        notes=(
            "Allogeneic off-the-shelf potential without GvHD risk. Very favorable safety "
            "profile — most AEs grade 1-2. Both innate and adaptive immune recognition. "
            "78% of treatment-related AEs were grade 1/2 in ADI-001 trial."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_therapy_types_by_category(category: str) -> list[TherapyType]:
    """Return all TherapyType entries matching the given category string.

    Parameters
    ----------
    category : str
        Category to filter by (e.g. "CAR-T", "Gene Therapy", "NK Cell").
        Matching is case-insensitive.

    Returns
    -------
    list[TherapyType]
        Matching therapy types, empty list if none found.
    """
    cat_lower = category.lower()
    return [
        t for t in THERAPY_TYPES.values()
        if t.category.lower() == cat_lower
    ]


def get_applicable_aes(therapy_id: str) -> list[str]:
    """Return the list of applicable adverse-event keys for a given therapy.

    Parameters
    ----------
    therapy_id : str
        Key into THERAPY_TYPES.

    Returns
    -------
    list[str]
        AE taxonomy keys, empty list if therapy_id not found.
    """
    therapy = THERAPY_TYPES.get(therapy_id)
    if therapy is None:
        return []
    return therapy.applicable_aes


def get_ae_definition(ae_name: str) -> dict:
    """Look up the full AE definition from AE_TAXONOMY.

    Parameters
    ----------
    ae_name : str
        Key into AE_TAXONOMY (e.g. "cytokine_release_syndrome").

    Returns
    -------
    dict
        Full AE definition dict, or empty dict if not found.
    """
    return AE_TAXONOMY.get(ae_name, {})


def get_all_categories() -> list[str]:
    """Return sorted list of unique therapy categories."""
    return sorted({t.category for t in THERAPY_TYPES.values()})


def get_approved_therapies() -> list[TherapyType]:
    """Return only therapy types that have at least one approved product."""
    return [t for t in THERAPY_TYPES.values() if t.approved_products]


def get_ae_rates_for_therapy(therapy_id: str, ae_name: str) -> dict:
    """Get the default AE rate data for a specific therapy and adverse event.

    Parameters
    ----------
    therapy_id : str
        Key into THERAPY_TYPES.
    ae_name : str
        Key into the therapy's default_ae_rates.

    Returns
    -------
    dict
        Rate data dict with keys: any_grade, grade3_plus, onset_days, duration, notes.
        Empty dict if not found.
    """
    therapy = THERAPY_TYPES.get(therapy_id)
    if therapy is None:
        return {}
    return therapy.default_ae_rates.get(ae_name, {})


def summary_stats() -> dict:
    """Return summary statistics about the registry."""
    total_therapies = len(THERAPY_TYPES)
    total_aes = len(AE_TAXONOMY)
    total_approved = sum(len(t.approved_products) for t in THERAPY_TYPES.values())
    total_pipeline = sum(len(t.pipeline_products) for t in THERAPY_TYPES.values())
    categories = get_all_categories()
    return {
        "total_therapy_types": total_therapies,
        "total_ae_types": total_aes,
        "total_approved_products": total_approved,
        "total_pipeline_products": total_pipeline,
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    stats = summary_stats()
    print(f"Cell Therapy Registry loaded successfully.")
    print(f"  Therapy types:     {stats['total_therapy_types']}")
    print(f"  AE types:          {stats['total_ae_types']}")
    print(f"  Approved products: {stats['total_approved_products']}")
    print(f"  Pipeline products: {stats['total_pipeline_products']}")
    print(f"  Categories:        {', '.join(stats['categories'])}")
    print()
    for tid, t in THERAPY_TYPES.items():
        approved_count = len(t.approved_products)
        ae_count = len(t.applicable_aes)
        rate_count = len(t.default_ae_rates)
        print(f"  [{tid}] {t.name}")
        print(f"    Category: {t.category} | Approved: {approved_count} | AEs: {ae_count} | Rate entries: {rate_count}")
