/**
 * Demo Clinical Cases for Predictive Safety Platform
 *
 * 8 diverse CAR-T cell therapy cases with realistic lab values,
 * vitals, and clinical evolution over multiple timepoints.
 *
 * Lab reference ranges used:
 *   LDH: 120-246 U/L
 *   Creatinine: 0.6-1.2 mg/dL
 *   Platelets: 150-400 x10^9/L
 *   CRP: <10 mg/L
 *   Ferritin: 12-300 ng/mL (F), 12-300 ng/mL (M)
 *   ANC: 1.5-8.0 x10^9/L
 *   Hemoglobin: 12-16 g/dL (F), 14-18 g/dL (M)
 *   AST: 10-40 U/L
 *   ALT: 7-56 U/L
 *   Fibrinogen: 2.0-4.0 g/L
 *   Triglycerides: <1.7 mmol/L
 *   IL-6: <7 pg/mL
 *   D-dimer: <0.5 mg/L FEU
 *   Total bilirubin: 0.1-1.2 mg/dL
 *   Albumin: 3.5-5.5 g/dL
 *
 * NOTE: The `scores` objects in each timepoint are illustrative/pre-computed
 * reference values for documentation purposes only. The dashboard calls the
 * API in real-time to calculate EASIX, HScore, and CAR-HEMATOTOX scores
 * from the raw lab/clinical data. These pre-computed values may not exactly
 * match the API's calculations.
 */

const DEMO_CASES = [

  // =========================================================================
  // CASE 1: Low-risk DLBCL - Mild CRS, good recovery
  // =========================================================================
  {
    id: "DEMO-001",
    name: "Maria Chen",
    age: 62,
    sex: "F",
    weight_kg: 58,
    bsa: 1.62,
    diagnosis: "DLBCL (GCB subtype), relapsed 8 months after R-CHOP, failed R-ICE salvage",
    stage: "IIIA",
    product: "Axicabtagene ciloleucel (Yescarta)",
    infusion_date: "2025-01-15",
    cell_dose: "2.0 x 10^6 CAR-T cells/kg",
    bridging_therapy: "None (adequate disease control during manufacturing)",
    ecog: 1,
    description: "Low-risk patient, day 3 post-infusion, developing mild CRS with excellent trajectory. EASIX score low at baseline. Demonstrates textbook Grade 1 CRS with self-limited course.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 280,
          creatinine: 0.8,
          platelets: 185,
          crp: 5,
          ferritin: 250,
          anc: 4.2,
          hemoglobin: 12.1,
          ast: 22,
          alt: 18,
          fibrinogen: 3.2,
          triglycerides: 1.4,
          il6: 4,
          d_dimer: 0.3,
          total_bilirubin: 0.6,
          albumin: 4.0
        },
        vitals: {
          temperature: 36.8,
          heart_rate: 78,
          systolic_bp: 128,
          diastolic_bp: 76,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 0.74,
          hscore: 62,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Baseline assessment prior to lymphodepletion. All values within normal limits. Low tumor burden by PET-CT (SUVmax 8.2, 3 nodal sites). EASIX 0.74 (low risk). Patient in good functional status."
      },
      {
        label: "Day 1 Post-Infusion",
        day: 1,
        labs: {
          ldh: 295,
          creatinine: 0.8,
          platelets: 142,
          crp: 12,
          ferritin: 310,
          anc: 0.8,
          hemoglobin: 11.4,
          ast: 24,
          alt: 20,
          fibrinogen: 3.0,
          triglycerides: 1.5,
          il6: 18,
          d_dimer: 0.4,
          total_bilirubin: 0.7,
          albumin: 3.8
        },
        vitals: {
          temperature: 37.4,
          heart_rate: 84,
          systolic_bp: 122,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.42,
          hscore: 68,
          car_hematotox: 2
        },
        expected_risk: "low",
        clinical_note: "Day 1 post-infusion. Expected cytopenias from lymphodepletion (flu/cy completed day -3). Mild CRP rise but no fever. Patient feels well. ANC dropping as expected from conditioning."
      },
      {
        label: "Day 3 Post-Infusion",
        day: 3,
        labs: {
          ldh: 340,
          creatinine: 0.9,
          platelets: 98,
          crp: 48,
          ferritin: 620,
          anc: 0.3,
          hemoglobin: 10.8,
          ast: 32,
          alt: 28,
          fibrinogen: 2.6,
          triglycerides: 1.7,
          il6: 85,
          d_dimer: 0.8,
          total_bilirubin: 0.9,
          albumin: 3.5
        },
        vitals: {
          temperature: 38.4,
          heart_rate: 96,
          systolic_bp: 118,
          diastolic_bp: 68,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.12,
          hscore: 89,
          car_hematotox: 2
        },
        expected_risk: "low",
        clinical_note: "Fever onset 38.4C - Grade 1 CRS. CRP rising but ferritin still moderate. Hemodynamically stable, no oxygen requirement. Blood cultures sent. Supportive care with acetaminophen. IL-6 elevated but not in concerning range. This is a typical, expected inflammatory response."
      },
      {
        label: "Day 7 Post-Infusion",
        day: 7,
        labs: {
          ldh: 265,
          creatinine: 0.8,
          platelets: 72,
          crp: 15,
          ferritin: 380,
          anc: 1.1,
          hemoglobin: 10.2,
          ast: 25,
          alt: 22,
          fibrinogen: 2.8,
          triglycerides: 1.5,
          il6: 12,
          d_dimer: 0.5,
          total_bilirubin: 0.7,
          albumin: 3.6
        },
        vitals: {
          temperature: 36.9,
          heart_rate: 80,
          systolic_bp: 124,
          diastolic_bp: 74,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.94,
          hscore: 72,
          car_hematotox: 2
        },
        expected_risk: "low",
        clinical_note: "CRS resolved. Fever defervesced day 5 without intervention beyond acetaminophen. CRP and ferritin trending down. ANC beginning to recover. Platelets at nadir but no bleeding. Patient eating well, ambulatory. Plan for discharge evaluation day 10."
      }
    ],
    anticipated_tests: [
      "CBC with differential q12h during CRS, then daily",
      "CRP daily",
      "Ferritin daily during CRS",
      "Comprehensive metabolic panel daily",
      "IL-6 if fever > 38.3C",
      "Blood cultures with each fever spike",
      "ICE assessment daily"
    ],
    teaching_points: [
      "Example of a textbook low-risk CRS trajectory - Grade 1 with self-limited fever",
      "Note the gradual CRP rise preceding fever onset by ~24 hours - useful early warning",
      "Low baseline EASIX (0.74) predicted mild CRS course",
      "Ferritin peaked modestly at 620 - values >1500 would raise concern for escalation",
      "ANC nadir from lymphodepletion conditioning, not CRS itself",
      "No tocilizumab needed - supportive care with antipyretics sufficient",
      "IL-6 rose but stayed under 100 pg/mL - higher levels would prompt closer monitoring"
    ]
  },

  // =========================================================================
  // CASE 2: High-risk aggressive lymphoma - Severe CRS requiring tocilizumab
  // =========================================================================
  {
    id: "DEMO-002",
    name: "James Williams",
    age: 45,
    sex: "M",
    weight_kg: 92,
    bsa: 2.14,
    diagnosis: "DLBCL (ABC/non-GCB subtype), double-hit (MYC/BCL2), primary refractory to R-EPOCH, failed R-DHAP salvage",
    stage: "IVB",
    product: "Axicabtagene ciloleucel (Yescarta)",
    infusion_date: "2025-02-01",
    cell_dose: "2.0 x 10^6 CAR-T cells/kg",
    bridging_therapy: "Polatuzumab-bendamustine-rituximab x1 cycle (bridging during manufacturing)",
    ecog: 2,
    description: "High-risk patient with high tumor burden, elevated LDH, and double-hit genetics. Develops severe Grade 3 CRS requiring tocilizumab and ICU transfer. High baseline EASIX predicts complicated course.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 842,
          creatinine: 1.1,
          platelets: 108,
          crp: 42,
          ferritin: 890,
          anc: 3.8,
          hemoglobin: 10.2,
          ast: 58,
          alt: 45,
          fibrinogen: 4.2,
          triglycerides: 2.1,
          il6: 38,
          d_dimer: 1.2,
          total_bilirubin: 1.4,
          albumin: 2.9
        },
        vitals: {
          temperature: 37.2,
          heart_rate: 92,
          systolic_bp: 134,
          diastolic_bp: 82,
          respiratory_rate: 18,
          spo2: 96
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 11.4,
          hscore: 118,
          car_hematotox: 3
        },
        expected_risk: "high",
        clinical_note: "High-risk baseline. LDH markedly elevated (842) reflecting high tumor burden. Baseline CRP already elevated from tumor-related inflammation. Mild hepatomegaly on exam. Low albumin and borderline bilirubin suggest hepatic involvement. EASIX 11.4 - high risk for severe CRS. Splenomegaly 15cm. Pre-existing thrombocytopenia from marrow involvement."
      },
      {
        label: "Day 1 Post-Infusion",
        day: 1,
        labs: {
          ldh: 920,
          creatinine: 1.2,
          platelets: 78,
          crp: 68,
          ferritin: 1250,
          anc: 0.6,
          hemoglobin: 9.8,
          ast: 72,
          alt: 55,
          fibrinogen: 3.8,
          triglycerides: 2.4,
          il6: 145,
          d_dimer: 1.8,
          total_bilirubin: 1.6,
          albumin: 2.7
        },
        vitals: {
          temperature: 38.6,
          heart_rate: 108,
          systolic_bp: 118,
          diastolic_bp: 70,
          respiratory_rate: 20,
          spo2: 96
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 18.7,
          hscore: 138,
          car_hematotox: 3
        },
        expected_risk: "high",
        clinical_note: "Early fever day 1 - unusually rapid CRS onset correlating with high tumor burden. IL-6 already 145 pg/mL. CRP and ferritin rising steeply. Tachycardia to 108 but maintaining blood pressure. Started empiric piperacillin-tazobactam. Close monitoring q4h vitals."
      },
      {
        label: "Day 2 Post-Infusion",
        day: 2,
        labs: {
          ldh: 1180,
          creatinine: 1.5,
          platelets: 52,
          crp: 185,
          ferritin: 3400,
          anc: 0.2,
          hemoglobin: 9.1,
          ast: 128,
          alt: 88,
          fibrinogen: 2.8,
          triglycerides: 2.8,
          il6: 680,
          d_dimer: 3.2,
          total_bilirubin: 2.4,
          albumin: 2.3
        },
        vitals: {
          temperature: 39.8,
          heart_rate: 124,
          systolic_bp: 92,
          diastolic_bp: 56,
          respiratory_rate: 24,
          spo2: 93
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Mild confusion",
          ice_score: 8,
          crs_grade: 3,
          icans_grade: 1,
          oxygen_requirement: "4L nasal cannula"
        },
        scores: {
          easix: 49.6,
          hscore: 168,
          car_hematotox: 4
        },
        expected_risk: "high",
        clinical_note: "RAPID ESCALATION to Grade 3 CRS. Hypotension requiring IV fluid boluses (not responding to first bolus). Hypoxia needing 4L NC. Fever 39.8C. IL-6 surging to 680. Ferritin tripling overnight. Rising creatinine suggests early AKI. Transaminitis worsening. TOCILIZUMAB 8mg/kg ADMINISTERED. Transfer to ICU for closer monitoring. Mild confusion noted - early ICANS concern, ICE score dropped to 8."
      },
      {
        label: "Day 3 Post-Infusion (ICU Day 1)",
        day: 3,
        labs: {
          ldh: 1420,
          creatinine: 1.8,
          platelets: 38,
          crp: 245,
          ferritin: 5800,
          anc: 0.1,
          hemoglobin: 8.4,
          ast: 165,
          alt: 112,
          fibrinogen: 2.0,
          triglycerides: 3.1,
          il6: 2400,
          d_dimer: 4.8,
          total_bilirubin: 3.2,
          albumin: 2.0
        },
        vitals: {
          temperature: 39.2,
          heart_rate: 118,
          systolic_bp: 88,
          diastolic_bp: 52,
          respiratory_rate: 26,
          spo2: 92
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Disoriented to time and place, word-finding difficulty",
          ice_score: 5,
          crs_grade: 3,
          icans_grade: 2,
          oxygen_requirement: "High-flow nasal cannula 40L/min 60% FiO2"
        },
        scores: {
          easix: 81.5,
          hscore: 182,
          car_hematotox: 4
        },
        expected_risk: "high",
        clinical_note: "ICU day 1. Persistent Grade 3 CRS despite first tocilizumab dose. IL-6 paradoxically elevated post-tocilizumab (expected - receptor blockade increases serum levels). Hypotension requiring vasopressors (norepinephrine 0.08 mcg/kg/min). Escalated to HFNC. SECOND TOCILIZUMAB DOSE given. ICANS worsening - ICE 5, started dexamethasone 10mg IV q6h. Coagulopathy developing (fibrinogen dropping, D-dimer rising). HScore approaching 169 threshold - monitoring for HLH overlap."
      },
      {
        label: "Day 5 Post-Infusion (ICU Day 3)",
        day: 5,
        labs: {
          ldh: 780,
          creatinine: 1.4,
          platelets: 42,
          crp: 120,
          ferritin: 4200,
          anc: 0.1,
          hemoglobin: 8.8,
          ast: 88,
          alt: 72,
          fibrinogen: 2.2,
          triglycerides: 2.6,
          il6: 180,
          d_dimer: 2.8,
          total_bilirubin: 2.1,
          albumin: 2.4
        },
        vitals: {
          temperature: 38.2,
          heart_rate: 98,
          systolic_bp: 104,
          diastolic_bp: 64,
          respiratory_rate: 20,
          spo2: 95
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Improving - oriented to person and place, mild tremor",
          ice_score: 7,
          crs_grade: 1,
          icans_grade: 1,
          oxygen_requirement: "2L nasal cannula"
        },
        scores: {
          easix: 28.8,
          hscore: 155,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Improving after 2 doses tocilizumab + dexamethasone. Vasopressors weaned off day 4. Stepped down from HFNC to 2L NC. Fevers lower grade. CRP and ferritin trending down. Creatinine improving. ICANS improving, ICE score back to 7. Continuing dexamethasone taper. LDH dropping significantly - suggests both CRS resolution and possible tumor lysis. Plan to transfer out of ICU if continues to improve."
      },
      {
        label: "Day 10 Post-Infusion",
        day: 10,
        labs: {
          ldh: 320,
          creatinine: 1.0,
          platelets: 58,
          crp: 18,
          ferritin: 1100,
          anc: 0.4,
          hemoglobin: 9.2,
          ast: 34,
          alt: 30,
          fibrinogen: 2.8,
          triglycerides: 1.8,
          il6: 15,
          d_dimer: 0.8,
          total_bilirubin: 1.0,
          albumin: 3.2
        },
        vitals: {
          temperature: 37.0,
          heart_rate: 82,
          systolic_bp: 118,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Resolved",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 5.86,
          hscore: 98,
          car_hematotox: 3
        },
        expected_risk: "low",
        clinical_note: "CRS and ICANS fully resolved. Off supplemental oxygen, afebrile. Dexamethasone completed taper. Inflammatory markers near normal. Persistent cytopenias (ANC 0.4, platelets 58) expected to slowly recover. LDH normalizing, suggesting tumor response. CAR-T cells detected by flow cytometry - expansion confirmed. Discharge planning initiated with close outpatient follow-up."
      }
    ],
    anticipated_tests: [
      "CBC with differential q6h during Grade 3+ CRS",
      "CRP q12h during active CRS",
      "Ferritin q12h during escalation",
      "Comprehensive metabolic panel q12h in ICU",
      "IL-6 q12h during active CRS",
      "Fibrinogen daily (HLH screening)",
      "Triglycerides daily (HLH screening)",
      "D-dimer daily",
      "Blood cultures with each fever spike",
      "ICE assessment q8h during ICANS",
      "Peripheral blood CAR-T cell quantification day 7, 14, 28",
      "CT chest if persistent hypoxia"
    ],
    teaching_points: [
      "High baseline EASIX (11.4) strongly predicted severe CRS - use for risk stratification at infusion",
      "Elevated pre-infusion LDH (>500) and CRP are major risk factors for Grade 3+ CRS",
      "Double-hit lymphoma biology and high tumor burden compound CRS risk",
      "IL-6 rises paradoxically after tocilizumab due to receptor blockade - do not re-dose based on IL-6 alone",
      "CRS and ICANS can overlap - this patient developed both, requiring combined tocilizumab + steroids",
      "HScore approached 169 (day 3: 182) - important to monitor for HLH/IEC-HS transition",
      "Despite severe CRS, appropriate management with tocilizumab + dexamethasone led to full recovery",
      "Second tocilizumab dose given within 8 hours when first was insufficient - per ASTCT guidelines"
    ]
  },

  // =========================================================================
  // CASE 3: Multiple myeloma - Moderate CRS with anti-BCMA CAR-T
  // =========================================================================
  {
    id: "DEMO-003",
    name: "Patricia Rodriguez",
    age: 58,
    sex: "F",
    weight_kg: 72,
    bsa: 1.78,
    diagnosis: "Relapsed/refractory multiple myeloma, IgG kappa. 5th line (prior lenalidomide, bortezomib, carfilzomib, daratumumab, pomalidomide). t(4;14) high-risk cytogenetics.",
    stage: "ISS Stage II",
    product: "Idecabtagene vicleucel (Abecma / ide-cel)",
    infusion_date: "2025-01-20",
    cell_dose: "450 x 10^6 CAR-T cells (target dose)",
    bridging_therapy: "Dexamethasone 40mg weekly x3 (bridging)",
    ecog: 1,
    description: "Heavily pretreated myeloma patient receiving anti-BCMA CAR-T. Develops moderate Grade 2 CRS typical for ide-cel. Notable for baseline cytopenias from prior therapies and myeloma-related renal impairment.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 195,
          creatinine: 1.4,
          platelets: 92,
          crp: 8,
          ferritin: 420,
          anc: 2.1,
          hemoglobin: 9.8,
          ast: 20,
          alt: 16,
          fibrinogen: 3.8,
          triglycerides: 1.6,
          il6: 8,
          d_dimer: 0.6,
          total_bilirubin: 0.5,
          albumin: 3.2,
          serum_free_kappa: 285,
          serum_free_lambda: 12,
          beta2_microglobulin: 4.8
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 76,
          systolic_bp: 132,
          diastolic_bp: 78,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "Mild peripheral neuropathy (grade 1, bortezomib-related)",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.46,
          hscore: 78,
          car_hematotox: 3
        },
        expected_risk: "moderate",
        clinical_note: "Baseline assessment. Pre-existing cytopenias from extensive prior therapy (5 lines). Mildly elevated creatinine from myeloma-related renal involvement (eGFR 52). Elevated free kappa light chains (285 mg/L) indicating active myeloma. High-risk cytogenetics t(4;14). Moderate CAR-HEMATOTOX score due to baseline cytopenias."
      },
      {
        label: "Day 2 Post-Infusion",
        day: 2,
        labs: {
          ldh: 210,
          creatinine: 1.5,
          platelets: 65,
          crp: 32,
          ferritin: 680,
          anc: 0.4,
          hemoglobin: 9.2,
          ast: 25,
          alt: 19,
          fibrinogen: 3.4,
          triglycerides: 1.8,
          il6: 42,
          d_dimer: 0.9,
          total_bilirubin: 0.6,
          albumin: 3.0
        },
        vitals: {
          temperature: 38.2,
          heart_rate: 92,
          systolic_bp: 120,
          diastolic_bp: 70,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "Baseline neuropathy unchanged",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.54,
          hscore: 92,
          car_hematotox: 3
        },
        expected_risk: "moderate",
        clinical_note: "Day 2: Low-grade fever onset (38.2C). Grade 1 CRS. CRP rising, ferritin increasing. Hemodynamically stable. Ide-cel typically causes CRS onset day 1-3 with median Grade 1-2 severity. Monitoring closely given baseline renal impairment."
      },
      {
        label: "Day 4 Post-Infusion",
        day: 4,
        labs: {
          ldh: 285,
          creatinine: 1.7,
          platelets: 48,
          crp: 128,
          ferritin: 1850,
          anc: 0.2,
          hemoglobin: 8.6,
          ast: 45,
          alt: 35,
          fibrinogen: 2.6,
          triglycerides: 2.2,
          il6: 220,
          d_dimer: 1.8,
          total_bilirubin: 0.9,
          albumin: 2.7
        },
        vitals: {
          temperature: 39.1,
          heart_rate: 110,
          systolic_bp: 98,
          diastolic_bp: 60,
          respiratory_rate: 22,
          spo2: 95
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "Baseline neuropathy, no new symptoms",
          ice_score: 10,
          crs_grade: 2,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 6.08,
          hscore: 128,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "CRS escalated to Grade 2: fever 39.1C with hypotension responding to IV fluid bolus (1L NS). Not requiring vasopressors, so remains Grade 2 per ASTCT criteria. CRP surged to 128, ferritin approaching 2000. Creatinine worsening (1.7 from baseline 1.4) - likely CRS-related AKI on chronic kidney disease. Administering TOCILIZUMAB 8mg/kg given Grade 2 CRS with risk factors (renal impairment, high ferritin trajectory)."
      },
      {
        label: "Day 6 Post-Infusion",
        day: 6,
        labs: {
          ldh: 230,
          creatinine: 1.5,
          platelets: 42,
          crp: 55,
          ferritin: 1200,
          anc: 0.3,
          hemoglobin: 8.4,
          ast: 32,
          alt: 26,
          fibrinogen: 2.8,
          triglycerides: 1.9,
          il6: 380,
          d_dimer: 1.2,
          total_bilirubin: 0.7,
          albumin: 2.9
        },
        vitals: {
          temperature: 37.6,
          heart_rate: 88,
          systolic_bp: 114,
          diastolic_bp: 68,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "Baseline neuropathy only",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 5.33,
          hscore: 108,
          car_hematotox: 4
        },
        expected_risk: "low",
        clinical_note: "Significant improvement post-tocilizumab. Fever downtrending, hemodynamically stable without fluids. CRP and ferritin declining. Creatinine improving toward baseline. IL-6 elevated post-tocilizumab (expected). CRS downgraded to Grade 1. Continue monitoring. Platelet nadir expected around day 7-10."
      },
      {
        label: "Day 14 Post-Infusion",
        day: 14,
        labs: {
          ldh: 178,
          creatinine: 1.3,
          platelets: 35,
          crp: 8,
          ferritin: 520,
          anc: 0.8,
          hemoglobin: 8.8,
          ast: 22,
          alt: 18,
          fibrinogen: 3.2,
          triglycerides: 1.5,
          il6: 10,
          d_dimer: 0.5,
          total_bilirubin: 0.5,
          albumin: 3.3,
          serum_free_kappa: 45,
          serum_free_lambda: 14
        },
        vitals: {
          temperature: 36.8,
          heart_rate: 78,
          systolic_bp: 126,
          diastolic_bp: 74,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "Baseline neuropathy only",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 6.37,
          hscore: 82,
          car_hematotox: 3
        },
        expected_risk: "low",
        clinical_note: "Day 14: CRS fully resolved. Inflammatory markers normalized. Creatinine near baseline. Encouraging early response - free kappa light chains dropped from 285 to 45 mg/L (84% reduction). Persistent cytopenias (ANC 0.8, platelets 35) typical post-ide-cel. Filgrastim initiated for ANC <0.5 x3 days. Transfusion support for platelets <10 or active bleeding. Discharge with twice-weekly CBC monitoring."
      }
    ],
    anticipated_tests: [
      "CBC with differential daily (twice daily during CRS)",
      "CRP daily",
      "Ferritin daily during CRS",
      "BMP q12h during CRS (renal monitoring)",
      "IL-6 with each CRS grade change",
      "Serum free light chains weekly",
      "SPEP/UPEP day 28",
      "Bone marrow biopsy day 28-30 (response assessment)",
      "CAR-T cell quantification day 7, 14, 28",
      "Immunoglobulin levels monthly"
    ],
    teaching_points: [
      "Ide-cel (anti-BCMA CAR-T) typically causes milder CRS than CD19-directed products",
      "Pre-existing renal impairment in myeloma requires close creatinine monitoring during CRS",
      "Baseline cytopenias from prior therapies predict prolonged post-infusion cytopenias",
      "Early tocilizumab at Grade 2 CRS was appropriate given renal risk factors",
      "Free light chain response at day 14 is an encouraging early efficacy signal",
      "Myeloma patients often have pre-existing immunosuppression affecting CRS risk profile differently than lymphoma"
    ]
  },

  // =========================================================================
  // CASE 4: Developing HLH/IEC-HS - CRS transitions to hemophagocytic syndrome
  // =========================================================================
  {
    id: "DEMO-004",
    name: "Robert Kim",
    age: 55,
    sex: "M",
    weight_kg: 78,
    bsa: 1.92,
    diagnosis: "Transformed follicular lymphoma to DLBCL, failed R-CHOP, R-DHAP, and polatuzumab-BR",
    stage: "IVA",
    product: "Tisagenlecleucel (Kymriah / tisa-cel)",
    infusion_date: "2025-02-10",
    cell_dose: "3.0 x 10^8 CAR-T cells (total, weight-independent dosing)",
    bridging_therapy: "Gemcitabine-oxaliplatin x1 cycle",
    ecog: 1,
    description: "Patient develops what initially appears to be typical CRS but transitions into IEC-HS (immune effector cell-associated HLH-like syndrome). Ferritin skyrockets >10,000, fibrinogen drops below 1.5, HScore crosses the 169 diagnostic threshold. Critical teaching case for recognizing HLH overlap.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 380,
          creatinine: 0.9,
          platelets: 165,
          crp: 15,
          ferritin: 480,
          anc: 3.5,
          hemoglobin: 11.8,
          ast: 28,
          alt: 22,
          fibrinogen: 3.6,
          triglycerides: 1.8,
          il6: 12,
          d_dimer: 0.5,
          total_bilirubin: 0.8,
          albumin: 3.6
        },
        vitals: {
          temperature: 36.9,
          heart_rate: 82,
          systolic_bp: 130,
          diastolic_bp: 78,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.51,
          hscore: 82,
          car_hematotox: 2
        },
        expected_risk: "moderate",
        clinical_note: "Baseline assessment. Moderate LDH elevation (380) from active lymphoma. Mild splenomegaly (14cm). Ferritin mildly elevated (480) at baseline - will need to track trajectory. Otherwise relatively preserved organ function."
      },
      {
        label: "Day 2 Post-Infusion",
        day: 2,
        labs: {
          ldh: 425,
          creatinine: 0.9,
          platelets: 118,
          crp: 55,
          ferritin: 920,
          anc: 0.5,
          hemoglobin: 10.8,
          ast: 38,
          alt: 30,
          fibrinogen: 3.2,
          triglycerides: 2.0,
          il6: 68,
          d_dimer: 0.8,
          total_bilirubin: 0.9,
          albumin: 3.3
        },
        vitals: {
          temperature: 38.5,
          heart_rate: 96,
          systolic_bp: 118,
          diastolic_bp: 72,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.42,
          hscore: 96,
          car_hematotox: 2
        },
        expected_risk: "moderate",
        clinical_note: "Day 2: Fever onset 38.5C - Grade 1 CRS. Appears typical at this point. CRP and ferritin rising proportionally. Tisa-cel CRS onset is typically later (days 3-5), so early onset is somewhat atypical. Monitoring closely."
      },
      {
        label: "Day 4 Post-Infusion",
        day: 4,
        labs: {
          ldh: 680,
          creatinine: 1.2,
          platelets: 72,
          crp: 188,
          ferritin: 4500,
          anc: 0.2,
          hemoglobin: 9.6,
          ast: 88,
          alt: 62,
          fibrinogen: 2.0,
          triglycerides: 3.2,
          il6: 340,
          d_dimer: 3.5,
          total_bilirubin: 1.8,
          albumin: 2.6
        },
        vitals: {
          temperature: 39.6,
          heart_rate: 118,
          systolic_bp: 96,
          diastolic_bp: 58,
          respiratory_rate: 24,
          spo2: 93
        },
        clinical: {
          organomegaly: 2,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Mild headache",
          ice_score: 9,
          crs_grade: 3,
          icans_grade: 0,
          oxygen_requirement: "3L nasal cannula"
        },
        scores: {
          easix: 16.2,
          hscore: 158,
          car_hematotox: 4
        },
        expected_risk: "high",
        clinical_note: "ESCALATION: Grade 3 CRS with hypotension and hypoxia. BUT KEY CONCERN: Ferritin velocity is disproportionate (480 -> 920 -> 4500). Trajectory suggests HLH-like process rather than pure CRS. Fibrinogen dropping (3.6 -> 2.0). Triglycerides rising (1.8 -> 3.2). Splenomegaly worsening. HScore 158 - approaching 169 threshold. TOCILIZUMAB administered. Starting to consider IEC-HS diagnosis."
      },
      {
        label: "Day 5 Post-Infusion",
        day: 5,
        labs: {
          ldh: 920,
          creatinine: 1.6,
          platelets: 38,
          crp: 265,
          ferritin: 12800,
          anc: 0.1,
          hemoglobin: 8.2,
          ast: 185,
          alt: 128,
          fibrinogen: 1.2,
          triglycerides: 4.1,
          il6: 890,
          d_dimer: 6.8,
          total_bilirubin: 3.4,
          albumin: 2.1
        },
        vitals: {
          temperature: 40.1,
          heart_rate: 128,
          systolic_bp: 84,
          diastolic_bp: 48,
          respiratory_rate: 28,
          spo2: 90
        },
        clinical: {
          organomegaly: 2,
          cytopenias: 3,
          hemophagocytosis: true,
          immunosuppression: false,
          neurologic_symptoms: "Somnolent, disoriented",
          ice_score: 4,
          crs_grade: 3,
          icans_grade: 3,
          oxygen_requirement: "High-flow nasal cannula 50L/min 80% FiO2"
        },
        scores: {
          easix: 56.8,
          hscore: 212,
          car_hematotox: 4
        },
        expected_risk: "critical",
        clinical_note: "IEC-HS CONFIRMED. Ferritin exploded to 12,800 (>10,000 = highly suggestive). Fibrinogen dropped to 1.2 g/L (<1.5 = HLH criterion). Triglycerides 4.1 (>3.0 = HLH criterion). HScore 212 (>169 = >93% probability HLH). Hemophagocytosis noted on peripheral smear. Worsening hepatitis (AST 185, bilirubin 3.4). DIC picture (D-dimer 6.8, fibrinogen 1.2). ICU transfer. HIGH-DOSE METHYLPREDNISOLONE 1g IV initiated (pulse steroids for IEC-HS). Second tocilizumab given. Considering anakinra if no improvement in 24h."
      },
      {
        label: "Day 7 Post-Infusion (ICU Day 2)",
        day: 7,
        labs: {
          ldh: 620,
          creatinine: 1.4,
          platelets: 28,
          crp: 145,
          ferritin: 8200,
          anc: 0.1,
          hemoglobin: 7.8,
          ast: 120,
          alt: 95,
          fibrinogen: 1.5,
          triglycerides: 3.4,
          il6: 420,
          d_dimer: 4.2,
          total_bilirubin: 2.6,
          albumin: 2.2
        },
        vitals: {
          temperature: 38.8,
          heart_rate: 108,
          systolic_bp: 94,
          diastolic_bp: 56,
          respiratory_rate: 24,
          spo2: 93
        },
        clinical: {
          organomegaly: 2,
          cytopenias: 3,
          hemophagocytosis: true,
          immunosuppression: false,
          neurologic_symptoms: "Improving, oriented to person",
          ice_score: 6,
          crs_grade: 2,
          icans_grade: 2,
          oxygen_requirement: "HFNC 40L/min 50% FiO2"
        },
        scores: {
          easix: 44.6,
          hscore: 195,
          car_hematotox: 4
        },
        expected_risk: "high",
        clinical_note: "Gradual improvement on pulse methylprednisolone (day 2 of 3). Ferritin trending down (12800 -> 8200) but still markedly elevated. Fibrinogen stabilizing at 1.5 with cryoprecipitate support. DIC improving. Vasopressors weaned to low dose. Oxygen requirement decreased. ICANS improving. Anakinra not needed at this time. Plan to transition to dexamethasone 10mg q6h after pulse steroids complete. Blood product support (pRBC for Hb <7, cryoprecipitate for fibrinogen <1.5, platelets for <10 or bleeding)."
      },
      {
        label: "Day 12 Post-Infusion",
        day: 12,
        labs: {
          ldh: 310,
          creatinine: 1.0,
          platelets: 32,
          crp: 35,
          ferritin: 2800,
          anc: 0.2,
          hemoglobin: 8.5,
          ast: 48,
          alt: 42,
          fibrinogen: 2.2,
          triglycerides: 2.4,
          il6: 28,
          d_dimer: 1.5,
          total_bilirubin: 1.2,
          albumin: 2.8
        },
        vitals: {
          temperature: 37.2,
          heart_rate: 88,
          systolic_bp: 112,
          diastolic_bp: 68,
          respiratory_rate: 18,
          spo2: 96
        },
        clinical: {
          organomegaly: 1,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Resolved",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "2L nasal cannula"
        },
        scores: {
          easix: 9.38,
          hscore: 122,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "IEC-HS resolving. Ferritin down to 2800 from peak of 12,800. Fibrinogen recovered above 2.0 without cryoprecipitate for 48h. Hepatitis resolving. Off vasopressors, weaning oxygen. Steroid taper ongoing (dexamethasone 4mg daily, tapering over 7 days). Persistent pancytopenia expected to be prolonged. Key question: will aggressive steroid use impact CAR-T efficacy? CAR-T cell levels being tracked. Concern about steroid-mediated loss of CAR-T expansion."
      }
    ],
    anticipated_tests: [
      "CBC with differential q6h during IEC-HS",
      "CRP q8h",
      "Ferritin q8h (KEY biomarker for HLH trajectory)",
      "Fibrinogen q8h (critical for DIC monitoring)",
      "Triglycerides daily",
      "DIC panel (PT/PTT/fibrinogen/D-dimer) q12h",
      "LFTs q12h during hepatic involvement",
      "Peripheral smear for hemophagocytes daily",
      "Soluble IL-2 receptor (sCD25) - send out lab",
      "NK cell activity if available",
      "Bone marrow biopsy if diagnostic uncertainty",
      "CAR-T cell quantification (concern re: steroid impact)"
    ],
    teaching_points: [
      "IEC-HS (immune effector cell-associated HLH-like syndrome) is distinct from CRS and requires different management",
      "KEY DIFFERENTIATOR: Ferritin velocity - CRS ferritin rises proportionally; IEC-HS ferritin rises exponentially (>10,000 ng/mL)",
      "Fibrinogen <1.5 g/L is a critical threshold - in CRS fibrinogen is typically preserved or mildly reduced",
      "HScore >169 has >93% probability of HLH - this is a crucial scoring threshold",
      "Triglycerides >3.0 mmol/L (fasting) is an HLH criterion often missed in acute care",
      "Pulse methylprednisolone (1g x3 days) is first-line for IEC-HS, not tocilizumab alone",
      "Anakinra (IL-1 receptor antagonist) is second-line for refractory IEC-HS",
      "Steroids for IEC-HS may compromise CAR-T efficacy - this clinical tension is a key management challenge",
      "Early recognition is critical: by the time ferritin >10,000 and fibrinogen <1.5, the syndrome is established"
    ]
  },

  // =========================================================================
  // CASE 5: ICANS without significant CRS - Neurotoxicity dominant picture
  // =========================================================================
  {
    id: "DEMO-005",
    name: "Sarah Thompson",
    age: 71,
    sex: "F",
    weight_kg: 65,
    bsa: 1.68,
    diagnosis: "Mantle cell lymphoma, relapsed after BTKi (ibrutinib) and venetoclax, TP53 mutated",
    stage: "IVA",
    product: "Lisocabtagene maraleucel (Breyanzi / liso-cel)",
    infusion_date: "2025-01-28",
    cell_dose: "100 x 10^6 CAR-T cells (50 x 10^6 CD8+ and 50 x 10^6 CD4+)",
    bridging_therapy: "Bendamustine-rituximab x1 cycle",
    ecog: 1,
    description: "Elderly patient with minimal CRS but develops isolated Grade 3 ICANS with ICE score deterioration. Demonstrates that neurotoxicity can occur independently of significant CRS. Age >65 is a risk factor for ICANS.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 245,
          creatinine: 0.9,
          platelets: 142,
          crp: 6,
          ferritin: 180,
          anc: 3.2,
          hemoglobin: 11.2,
          ast: 25,
          alt: 20,
          fibrinogen: 3.4,
          triglycerides: 1.5,
          il6: 5,
          d_dimer: 0.4,
          total_bilirubin: 0.6,
          albumin: 3.8
        },
        vitals: {
          temperature: 36.6,
          heart_rate: 72,
          systolic_bp: 138,
          diastolic_bp: 80,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None (MMSE 28/30, mild age-related changes)",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.53,
          hscore: 58,
          car_hematotox: 1
        },
        expected_risk: "moderate",
        clinical_note: "Baseline assessment. Age 71 - known risk factor for ICANS. MMSE 28/30 at baseline (important for comparison). TP53-mutated MCL is aggressive but relatively low tumor burden currently (post-bridging). Liso-cel has defined CD4/CD8 composition designed for consistent dosing."
      },
      {
        label: "Day 3 Post-Infusion",
        day: 3,
        labs: {
          ldh: 260,
          creatinine: 0.9,
          platelets: 95,
          crp: 28,
          ferritin: 380,
          anc: 0.6,
          hemoglobin: 10.4,
          ast: 30,
          alt: 24,
          fibrinogen: 3.0,
          triglycerides: 1.6,
          il6: 35,
          d_dimer: 0.6,
          total_bilirubin: 0.7,
          albumin: 3.5
        },
        vitals: {
          temperature: 38.0,
          heart_rate: 84,
          systolic_bp: 130,
          diastolic_bp: 76,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.35,
          hscore: 72,
          car_hematotox: 2
        },
        expected_risk: "low",
        clinical_note: "Day 3: Mild fever 38.0C - Grade 1 CRS. Hemodynamically stable. Very modest inflammatory marker elevation. CRS appears mild as expected with liso-cel (lower CRS rates than axi-cel). ICE score remains 10/10."
      },
      {
        label: "Day 5 Post-Infusion",
        day: 5,
        labs: {
          ldh: 240,
          creatinine: 0.9,
          platelets: 82,
          crp: 18,
          ferritin: 320,
          anc: 0.4,
          hemoglobin: 10.0,
          ast: 28,
          alt: 22,
          fibrinogen: 2.8,
          triglycerides: 1.6,
          il6: 22,
          d_dimer: 0.5,
          total_bilirubin: 0.6,
          albumin: 3.4
        },
        vitals: {
          temperature: 37.2,
          heart_rate: 78,
          systolic_bp: 132,
          diastolic_bp: 78,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Mild word-finding difficulty, handwriting slightly tremulous",
          ice_score: 7,
          crs_grade: 0,
          icans_grade: 1,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.60,
          hscore: 68,
          car_hematotox: 2
        },
        expected_risk: "moderate",
        clinical_note: "CRS RESOLVING (afebrile, CRP downtrending) BUT new neurologic symptoms emerging. ICE score dropped to 7/10: orientation intact, naming 2/3 objects, writing ability impaired (tremor, incomplete sentence), attention intact. Grade 1 ICANS. This is the classic pattern of ICANS developing as CRS wanes. CRP and inflammatory markers are actually improving. Started neuro checks q4h."
      },
      {
        label: "Day 7 Post-Infusion",
        day: 7,
        labs: {
          ldh: 255,
          creatinine: 0.9,
          platelets: 78,
          crp: 12,
          ferritin: 280,
          anc: 0.5,
          hemoglobin: 9.8,
          ast: 26,
          alt: 20,
          fibrinogen: 2.8,
          triglycerides: 1.5,
          il6: 15,
          d_dimer: 0.4,
          total_bilirubin: 0.6,
          albumin: 3.4
        },
        vitals: {
          temperature: 36.8,
          heart_rate: 76,
          systolic_bp: 128,
          diastolic_bp: 74,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Disoriented to date, cannot write sentence, follows commands but slow, expressive aphasia",
          ice_score: 3,
          crs_grade: 0,
          icans_grade: 3,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.78,
          hscore: 65,
          car_hematotox: 2
        },
        expected_risk: "high",
        clinical_note: "ICANS ESCALATED to Grade 3 despite CRS being fully resolved. ICE score dropped to 3/10: disoriented to year/date, names 1/3 objects, cannot write a sentence, follows simple commands but not complex ones, attention impaired. Expressive aphasia prominent. NO concurrent CRS (afebrile, stable vitals, low CRP). This dissociation between CRS and ICANS severity is important. DEXAMETHASONE 10mg IV q6h initiated. MRI brain ordered to rule out structural cause. EEG if seizure concern. Seizure prophylaxis with levetiracetam 500mg BID started."
      },
      {
        label: "Day 11 Post-Infusion",
        day: 11,
        labs: {
          ldh: 220,
          creatinine: 0.9,
          platelets: 88,
          crp: 6,
          ferritin: 210,
          anc: 1.2,
          hemoglobin: 10.0,
          ast: 22,
          alt: 18,
          fibrinogen: 3.0,
          triglycerides: 1.4,
          il6: 8,
          d_dimer: 0.3,
          total_bilirubin: 0.5,
          albumin: 3.6
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 72,
          systolic_bp: 130,
          diastolic_bp: 76,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "Mild residual word-finding difficulty, handwriting improving, oriented x3",
          ice_score: 8,
          crs_grade: 0,
          icans_grade: 1,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.16,
          hscore: 55,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "ICANS improving on dexamethasone. ICE score recovered to 8/10 from nadir of 3. Orientation restored. Writing ability improving but not fully recovered. MRI brain showed no structural abnormality (reversible process). Continuing dexamethasone taper (currently 4mg BID, will taper over 5 days). Levetiracetam to continue for 30 days post-ICANS resolution. Some residual word-finding difficulty may persist in elderly patients."
      }
    ],
    anticipated_tests: [
      "ICE assessment q4h during active ICANS (q8h when Grade 1)",
      "CBC with differential daily",
      "CRP daily",
      "MRI brain (if Grade 2+ ICANS or focal deficits)",
      "EEG (if concern for subclinical seizures)",
      "Opening pressure with LP if papilledema or Grade 4 ICANS",
      "Fundoscopic exam daily during Grade 2+ ICANS",
      "Levetiracetam level if breakthrough seizure",
      "Daily neurologic exam by treating physician"
    ],
    teaching_points: [
      "ICANS can occur with minimal or no significant CRS - they are partially independent syndromes",
      "Age >65 is a significant independent risk factor for ICANS, regardless of CRS severity",
      "ICE score is the standard assessment tool: Orientation (4) + Naming (3) + Writing (1) + Attention (1) + Following commands (1) = 10",
      "Classic ICANS timeline: often peaks as CRS resolves (days 5-8), suggesting different pathophysiology",
      "Dexamethasone is first-line for ICANS (not tocilizumab, which has poor CNS penetration)",
      "Seizure prophylaxis with levetiracetam is recommended during Grade 2+ ICANS",
      "MRI brain is important to rule out structural causes (hemorrhage, edema, infection)",
      "Elderly patients may have slower ICANS recovery and residual subtle deficits",
      "Baseline cognitive assessment (MMSE or ICE) is essential for comparison during ICANS evaluation"
    ]
  },

  // =========================================================================
  // CASE 6: Late-onset CRS - Unusual timing with cilta-cel
  // =========================================================================
  {
    id: "DEMO-006",
    name: "David Okafor",
    age: 48,
    sex: "M",
    weight_kg: 85,
    bsa: 2.02,
    diagnosis: "Relapsed/refractory multiple myeloma, IgA lambda. 4th line (prior lenalidomide-dexamethasone, daratumumab-VRd, carfilzomib-pomalidomide-dexamethasone). Standard risk cytogenetics.",
    stage: "ISS Stage III",
    product: "Ciltacabtagene autoleucel (Carvykti / cilta-cel)",
    infusion_date: "2025-02-05",
    cell_dose: "0.75 x 10^6 CAR-T cells/kg",
    bridging_therapy: "Pomalidomide-dexamethasone x1 cycle",
    ecog: 1,
    description: "Patient appears to have an uncomplicated early course but develops late-onset CRS beginning day 10 - unusual timing that could be missed if monitoring relaxed too early. Cilta-cel is known for potential late-onset CRS and other delayed toxicities. Teaches importance of prolonged vigilance.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 210,
          creatinine: 1.0,
          platelets: 175,
          crp: 10,
          ferritin: 320,
          anc: 3.8,
          hemoglobin: 12.4,
          ast: 22,
          alt: 18,
          fibrinogen: 3.4,
          triglycerides: 1.6,
          il6: 6,
          d_dimer: 0.4,
          total_bilirubin: 0.7,
          albumin: 3.5
        },
        vitals: {
          temperature: 36.8,
          heart_rate: 76,
          systolic_bp: 126,
          diastolic_bp: 78,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.23,
          hscore: 64,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Baseline assessment for cilta-cel infusion. All values within normal limits. Good performance status. Standard-risk cytogenetics. ISS III based on elevated beta-2 microglobulin (6.2) and low albumin (3.5). Cilta-cel uses lower cell dose than CD19 products."
      },
      {
        label: "Day 3 Post-Infusion",
        day: 3,
        labs: {
          ldh: 205,
          creatinine: 1.0,
          platelets: 128,
          crp: 8,
          ferritin: 290,
          anc: 0.8,
          hemoglobin: 11.8,
          ast: 20,
          alt: 16,
          fibrinogen: 3.2,
          triglycerides: 1.5,
          il6: 5,
          d_dimer: 0.3,
          total_bilirubin: 0.6,
          albumin: 3.4
        },
        vitals: {
          temperature: 36.9,
          heart_rate: 74,
          systolic_bp: 124,
          diastolic_bp: 76,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.46,
          hscore: 62,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Day 3: Completely unremarkable. No fever, no CRS signs. CRP and ferritin stable. Expected ANC drop from lymphodepletion. Patient feeling well. This is NOT unusual for cilta-cel, which has later CRS onset (median day 7, range 1-12+)."
      },
      {
        label: "Day 7 Post-Infusion",
        day: 7,
        labs: {
          ldh: 195,
          creatinine: 0.9,
          platelets: 105,
          crp: 6,
          ferritin: 270,
          anc: 1.2,
          hemoglobin: 11.4,
          ast: 18,
          alt: 15,
          fibrinogen: 3.2,
          triglycerides: 1.4,
          il6: 4,
          d_dimer: 0.3,
          total_bilirubin: 0.6,
          albumin: 3.5
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 72,
          systolic_bp: 128,
          diastolic_bp: 78,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.47,
          hscore: 58,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Day 7: Still no CRS. All inflammatory markers normal. ANC recovering. Patient requesting discharge. CAUTION: Cilta-cel has documented late-onset CRS (up to day 12+). Recommend maintaining monitoring through day 14 minimum. Some centers would discharge with strict return precautions and daily outpatient labs."
      },
      {
        label: "Day 10 Post-Infusion",
        day: 10,
        labs: {
          ldh: 285,
          creatinine: 1.1,
          platelets: 98,
          crp: 65,
          ferritin: 780,
          anc: 1.8,
          hemoglobin: 11.0,
          ast: 35,
          alt: 28,
          fibrinogen: 2.8,
          triglycerides: 1.9,
          il6: 85,
          d_dimer: 0.8,
          total_bilirubin: 0.8,
          albumin: 3.2
        },
        vitals: {
          temperature: 38.6,
          heart_rate: 98,
          systolic_bp: 116,
          diastolic_bp: 70,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.14,
          hscore: 88,
          car_hematotox: 1
        },
        expected_risk: "moderate",
        clinical_note: "LATE-ONSET CRS BEGINS DAY 10. First fever 38.6C after 9 days of being completely well. CRP jumped from 6 to 65 overnight. Ferritin tripling. IL-6 rising. This correlates with delayed CAR-T expansion kinetics seen with cilta-cel. Grade 1 CRS currently. Blood cultures sent. Empiric antibiotics started (cannot exclude infection in this timeframe). Close monitoring resumed - q4h vitals."
      },
      {
        label: "Day 12 Post-Infusion",
        day: 12,
        labs: {
          ldh: 340,
          creatinine: 1.3,
          platelets: 82,
          crp: 142,
          ferritin: 2100,
          anc: 2.2,
          hemoglobin: 10.4,
          ast: 52,
          alt: 40,
          fibrinogen: 2.4,
          triglycerides: 2.2,
          il6: 245,
          d_dimer: 1.4,
          total_bilirubin: 1.2,
          albumin: 2.9
        },
        vitals: {
          temperature: 39.4,
          heart_rate: 112,
          systolic_bp: 98,
          diastolic_bp: 60,
          respiratory_rate: 20,
          spo2: 96
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 2,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 5.42,
          hscore: 112,
          car_hematotox: 2
        },
        expected_risk: "moderate",
        clinical_note: "Late CRS escalated to Grade 2. Fever 39.4C, hypotension responding to fluid bolus. CRP and ferritin rapidly rising. No hypoxia. Blood cultures negative at 48h - confirms CRS rather than infection. TOCILIZUMAB 8mg/kg administered for Grade 2 CRS. Close monitoring. Of note, ANC is preserved (2.2) - unlike early CRS where conditioning-related neutropenia coexists. This is because the late timing allows ANC recovery before CRS onset."
      },
      {
        label: "Day 16 Post-Infusion",
        day: 16,
        labs: {
          ldh: 220,
          creatinine: 1.0,
          platelets: 95,
          crp: 22,
          ferritin: 680,
          anc: 2.8,
          hemoglobin: 10.8,
          ast: 28,
          alt: 22,
          fibrinogen: 3.0,
          triglycerides: 1.6,
          il6: 18,
          d_dimer: 0.5,
          total_bilirubin: 0.7,
          albumin: 3.3
        },
        vitals: {
          temperature: 37.0,
          heart_rate: 78,
          systolic_bp: 122,
          diastolic_bp: 74,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.00,
          hscore: 72,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Late CRS fully resolved after single tocilizumab dose. All inflammatory markers downtrending. Patient stable and well. Discharge with education about delayed neurotoxicity risk (cilta-cel-specific: movement disorders, cranial nerve palsies reported weeks to months post-infusion). Monthly neurology follow-up recommended. CAR-T expansion confirmed by flow cytometry - delayed expansion correlates with late CRS timing."
      }
    ],
    anticipated_tests: [
      "CBC with differential daily through day 14 minimum (even if well)",
      "CRP daily through day 14 (KEY for detecting late-onset CRS)",
      "Ferritin daily during active CRS",
      "BMP daily during CRS",
      "IL-6 with fever onset and q12h during CRS",
      "Blood cultures to rule out infection (important in late-onset presentation)",
      "CAR-T cell quantification day 7, 14, 28",
      "Serum free light chains day 28",
      "Neurologic assessment monthly for 6 months (cilta-cel specific delayed neurotoxicity)",
      "MRI brain if any neurologic symptoms develop"
    ],
    teaching_points: [
      "Cilta-cel has unique late-onset CRS kinetics - median onset day 7, can occur up to day 12+",
      "A 'silent' first week does NOT mean the patient is in the clear with cilta-cel",
      "Late CRS correlates with delayed CAR-T expansion peak, not initial T-cell activation",
      "Minimum 14-day monitoring recommended for cilta-cel (vs. 10 days for CD19 products)",
      "Late-onset CRS may be confused with infection - blood cultures are essential in differential",
      "ANC is often recovered by the time late CRS appears (unlike early CRS overlapping with conditioning neutropenia)",
      "Cilta-cel also carries risk of delayed neurotoxicity (movement disorders, parkinsonian features) weeks to months later",
      "Product-specific toxicity profiles should guide monitoring duration and follow-up plans"
    ]
  },

  // =========================================================================
  // CASE 7: Prolonged cytopenias - CAR-HEMATOTOX high, CRS resolves but counts don't
  // =========================================================================
  {
    id: "DEMO-007",
    name: "Linda Park",
    age: 66,
    sex: "F",
    weight_kg: 60,
    bsa: 1.64,
    diagnosis: "DLBCL NOS, relapsed after R-CHOP and auto-SCT. Post-transplant relapse at 14 months.",
    stage: "IIIB",
    product: "Axicabtagene ciloleucel (Yescarta)",
    infusion_date: "2025-01-10",
    cell_dose: "2.0 x 10^6 CAR-T cells/kg",
    bridging_therapy: "R-GDP x1 cycle",
    ecog: 1,
    description: "Patient whose CRS resolves without major issue (Grade 1) but develops severe prolonged cytopenias extending beyond day 28. High CAR-HEMATOTOX score at baseline predicts this outcome. Prior autologous SCT significantly damaged bone marrow reserve. Teaching case for hematologic toxicity management.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 310,
          creatinine: 0.7,
          platelets: 98,
          crp: 12,
          ferritin: 580,
          anc: 1.6,
          hemoglobin: 10.2,
          ast: 20,
          alt: 16,
          fibrinogen: 3.4,
          triglycerides: 1.5,
          il6: 8,
          d_dimer: 0.5,
          total_bilirubin: 0.6,
          albumin: 3.4,
          reticulocytes: 1.2,
          mpv: 10.8
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 80,
          systolic_bp: 122,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 2,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.18,
          hscore: 82,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Baseline: Pre-existing cytopenias (platelets 98, Hb 10.2) from prior auto-SCT 14 months ago. Marrow reserve likely compromised. Elevated ferritin (580) suggests inflammatory marrow. CAR-HEMATOTOX score HIGH (4) driven by: low baseline ANC (1.6), low platelets (98), low hemoglobin (10.2), and elevated CRP (12). This predicts prolonged cytopenias post-CAR-T. Plan for extended growth factor and transfusion support."
      },
      {
        label: "Day 3 Post-Infusion",
        day: 3,
        labs: {
          ldh: 345,
          creatinine: 0.8,
          platelets: 52,
          crp: 42,
          ferritin: 720,
          anc: 0.2,
          hemoglobin: 9.4,
          ast: 28,
          alt: 22,
          fibrinogen: 2.8,
          triglycerides: 1.7,
          il6: 55,
          d_dimer: 0.7,
          total_bilirubin: 0.7,
          albumin: 3.2,
          reticulocytes: 0.4,
          mpv: 10.2
        },
        vitals: {
          temperature: 38.2,
          heart_rate: 88,
          systolic_bp: 118,
          diastolic_bp: 68,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.32,
          hscore: 95,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Grade 1 CRS - mild fever 38.2C. Manageable. BUT note the rapid count decline: platelets 98->52 in 8 days, ANC 1.6->0.2, Hb 10.2->9.4. This accelerated cytopenia trajectory is characteristic of patients with poor marrow reserve. Reticulocytes dropping (1.2->0.4%) indicates suppressed erythropoiesis. Started filgrastim prophylactically."
      },
      {
        label: "Day 7 Post-Infusion",
        day: 7,
        labs: {
          ldh: 280,
          creatinine: 0.7,
          platelets: 28,
          crp: 15,
          ferritin: 480,
          anc: 0.1,
          hemoglobin: 8.2,
          ast: 22,
          alt: 18,
          fibrinogen: 2.8,
          triglycerides: 1.5,
          il6: 10,
          d_dimer: 0.4,
          total_bilirubin: 0.5,
          albumin: 3.3,
          reticulocytes: 0.2,
          mpv: 9.8
        },
        vitals: {
          temperature: 36.8,
          heart_rate: 82,
          systolic_bp: 120,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.42,
          hscore: 78,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "CRS fully resolved (afebrile from day 5, CRP normalized). Patient feels well overall. BUT: profound pancytopenia: ANC 0.1 (severe neutropenia), platelets 28 (severe thrombocytopenia), Hb 8.2 (transfusion threshold approaching). Reticulocytes nearly absent (0.2%) - bone marrow not recovering. Filgrastim continued. Transfusion triggers: platelets <10 or active bleeding, Hb <7. Antimicrobial prophylaxis: levofloxacin, acyclovir, fluconazole."
      },
      {
        label: "Day 14 Post-Infusion",
        day: 14,
        labs: {
          ldh: 250,
          creatinine: 0.7,
          platelets: 15,
          crp: 8,
          ferritin: 420,
          anc: 0.1,
          hemoglobin: 7.4,
          ast: 20,
          alt: 16,
          fibrinogen: 3.0,
          triglycerides: 1.4,
          il6: 6,
          d_dimer: 0.3,
          total_bilirubin: 0.5,
          albumin: 3.4,
          reticulocytes: 0.3,
          mpv: 9.2
        },
        vitals: {
          temperature: 36.9,
          heart_rate: 92,
          systolic_bp: 114,
          diastolic_bp: 68,
          respiratory_rate: 18,
          spo2: 97
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.59,
          hscore: 75,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Day 14: No CRS/ICANS but SEVERE PERSISTENT CYTOPENIAS. Platelets dropped to 15 - transfused 1 unit apheresis platelets. Hb 7.4 - transfused 1 unit pRBC. ANC remains 0.1 despite filgrastim. No signs of recovery. This is 'late' cytopenias per the biphasic pattern described for CAR-T: initial nadir from conditioning, brief partial recovery, then secondary prolonged suppression from ongoing inflammation and CAR-T-mediated marrow effects. Bone marrow biopsy planned if no recovery by day 21."
      },
      {
        label: "Day 21 Post-Infusion",
        day: 21,
        labs: {
          ldh: 235,
          creatinine: 0.7,
          platelets: 12,
          crp: 5,
          ferritin: 380,
          anc: 0.2,
          hemoglobin: 8.0,
          ast: 18,
          alt: 15,
          fibrinogen: 3.2,
          triglycerides: 1.3,
          il6: 5,
          d_dimer: 0.3,
          total_bilirubin: 0.4,
          albumin: 3.5,
          reticulocytes: 0.5,
          mpv: 9.5
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 84,
          systolic_bp: 118,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 4.00,
          hscore: 72,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Day 21: Persistent severe pancytopenia. Bone marrow biopsy performed today: hypocellular marrow (15% cellularity, expected >30% for age), no lymphoma detected (good sign for treatment response), no hemophagocytosis. Marrow shows maturation arrest in myeloid and erythroid lineages - consistent with post-CAR-T marrow suppression in patient with poor reserve. Very faint early recovery signals: reticulocytes 0.5% (was 0.2%), ANC 0.2 (was 0.1). Continuing supportive care. TPO receptor agonist (eltrombopag) considered for refractory thrombocytopenia."
      },
      {
        label: "Day 28 Post-Infusion",
        day: 28,
        labs: {
          ldh: 220,
          creatinine: 0.7,
          platelets: 22,
          crp: 4,
          ferritin: 340,
          anc: 0.5,
          hemoglobin: 8.4,
          ast: 18,
          alt: 14,
          fibrinogen: 3.4,
          triglycerides: 1.3,
          il6: 4,
          d_dimer: 0.2,
          total_bilirubin: 0.4,
          albumin: 3.6,
          reticulocytes: 0.8,
          mpv: 10.2
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 78,
          systolic_bp: 120,
          diastolic_bp: 74,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 3,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 3.09,
          hscore: 68,
          car_hematotox: 4
        },
        expected_risk: "moderate",
        clinical_note: "Day 28: Slow early recovery beginning. ANC 0.5 (first time above 0.3 since infusion). Platelets still critically low (22) but MPV rising (10.2) suggesting new platelet production. Reticulocytes 0.8% - erythroid recovery starting. Hemoglobin stabilizing with less transfusion need. This meets criteria for 'prolonged cytopenias' (not recovered by day 28). Expected to continue for weeks. Plan: twice-weekly CBC, continue filgrastim until ANC >1.5 x3 days, transfusion support, antimicrobial prophylaxis, consider eltrombopag if platelets remain <20 at day 35."
      },
      {
        label: "Day 42 Post-Infusion",
        day: 42,
        labs: {
          ldh: 200,
          creatinine: 0.7,
          platelets: 48,
          crp: 3,
          ferritin: 280,
          anc: 1.2,
          hemoglobin: 9.2,
          ast: 18,
          alt: 14,
          fibrinogen: 3.4,
          triglycerides: 1.3,
          il6: 4,
          d_dimer: 0.2,
          total_bilirubin: 0.4,
          albumin: 3.7,
          reticulocytes: 1.4,
          mpv: 10.8
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 74,
          systolic_bp: 122,
          diastolic_bp: 74,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: true,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 2.52,
          hscore: 58,
          car_hematotox: 2
        },
        expected_risk: "low",
        clinical_note: "Day 42: Meaningful recovery emerging. ANC 1.2 (filgrastim discontinued day 35 when ANC >1.0). Platelets 48 - no longer requiring transfusions (last transfusion day 32). Hemoglobin 9.2 - reticulocytes 1.4% indicate active erythropoiesis. Full platelet recovery may take 2-3 more months. Interim PET-CT shows complete metabolic response - excellent treatment outcome despite hematologic toxicity. Continue weekly CBC, reassess at day 60."
      }
    ],
    anticipated_tests: [
      "CBC with differential daily while inpatient, twice weekly after discharge",
      "Reticulocyte count twice weekly (early recovery marker)",
      "CRP daily during CRS, then weekly",
      "Ferritin weekly (iron overload from transfusions)",
      "Comprehensive metabolic panel weekly",
      "Bone marrow biopsy day 21 if no count recovery",
      "Peripheral smear weekly (morphology assessment)",
      "CMV/EBV PCR weekly (reactivation risk in prolonged cytopenias)",
      "Type and screen maintained (frequent transfusion need)",
      "PET-CT day 30 or day 90 (response assessment)"
    ],
    teaching_points: [
      "CAR-HEMATOTOX score at baseline predicts prolonged cytopenia risk - this patient scored 4 (highest)",
      "Key CAR-HEMATOTOX inputs: baseline ANC, platelets, hemoglobin, CRP, ferritin - all assessable pre-infusion",
      "Prior autologous SCT is a major risk factor for prolonged cytopenias due to reduced marrow reserve",
      "Cytopenias can follow a biphasic pattern: initial nadir (conditioning), brief partial recovery, then prolonged secondary suppression",
      "Day 28 ANC <1.0 defines 'prolonged cytopenias' - occurs in ~30% of patients",
      "Bone marrow biopsy at day 21 helps exclude: relapse, hemophagocytosis, infection, and guides supportive care",
      "Reticulocyte count and MPV are early indicators of marrow recovery before absolute counts improve",
      "Growth factors (G-CSF), transfusion support, and antimicrobial prophylaxis are the mainstays of management",
      "Despite severe hematologic toxicity, anti-tumor efficacy was excellent - CRS severity does not predict response",
      "TPO receptor agonists (eltrombopag/romiplostim) may help refractory thrombocytopenia but evidence is limited"
    ]
  },

  // =========================================================================
  // CASE 8: Optimal outcome - Everything goes perfectly
  // =========================================================================
  {
    id: "DEMO-008",
    name: "Michael Santos",
    age: 52,
    sex: "M",
    weight_kg: 80,
    bsa: 1.96,
    diagnosis: "DLBCL (GCB subtype), relapsed 18 months after R-CHOP, not eligible for auto-SCT due to chemo-refractory disease on R-ICE",
    stage: "IIA",
    product: "Lisocabtagene maraleucel (Breyanzi / liso-cel)",
    infusion_date: "2025-02-15",
    cell_dose: "100 x 10^6 CAR-T cells (50 x 10^6 CD8+ and 50 x 10^6 CD4+)",
    bridging_therapy: "None required (limited disease, adequate control)",
    ecog: 0,
    description: "The 'ideal' case - everything goes as well as possible. Mild Grade 1 CRS, rapid resolution, no ICANS, good hematologic recovery, and early evidence of response. Shows what an optimal CAR-T trajectory looks like for benchmarking against more complicated cases.",
    timepoints: [
      {
        label: "Baseline (Day -5)",
        day: -5,
        labs: {
          ldh: 195,
          creatinine: 0.9,
          platelets: 225,
          crp: 3,
          ferritin: 120,
          anc: 5.2,
          hemoglobin: 14.8,
          ast: 18,
          alt: 15,
          fibrinogen: 3.2,
          triglycerides: 1.2,
          il6: 3,
          d_dimer: 0.2,
          total_bilirubin: 0.5,
          albumin: 4.2
        },
        vitals: {
          temperature: 36.6,
          heart_rate: 68,
          systolic_bp: 122,
          diastolic_bp: 74,
          respiratory_rate: 14,
          spo2: 99
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 0.68,
          hscore: 42,
          car_hematotox: 0
        },
        expected_risk: "low",
        clinical_note: "Ideal baseline profile. Normal LDH (low tumor burden). All counts excellent - strong marrow reserve. Low CRP and ferritin (minimal systemic inflammation). ECOG 0. EASIX 0.68 (very low - predicts mild CRS). CAR-HEMATOTOX 0 (predicts rapid count recovery). Limited-stage disease (IIA) with low bulk. This is the patient profile where CAR-T outcomes are best."
      },
      {
        label: "Day 2 Post-Infusion",
        day: 2,
        labs: {
          ldh: 210,
          creatinine: 0.9,
          platelets: 168,
          crp: 18,
          ferritin: 200,
          anc: 1.2,
          hemoglobin: 13.6,
          ast: 20,
          alt: 16,
          fibrinogen: 3.0,
          triglycerides: 1.3,
          il6: 22,
          d_dimer: 0.3,
          total_bilirubin: 0.5,
          albumin: 4.0
        },
        vitals: {
          temperature: 37.8,
          heart_rate: 80,
          systolic_bp: 120,
          diastolic_bp: 72,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.08,
          hscore: 52,
          car_hematotox: 0
        },
        expected_risk: "low",
        clinical_note: "Day 2: Subclinical inflammation. Low-grade temperature 37.8C (below 38.0C ASTCT threshold for CRS Grade 1). CRP mildly elevated but no fever by criteria. All other parameters excellent. Hemodynamically rock-solid. Counts holding up well - platelets only mildly decreased, Hb preserved. Liso-cel's defined CD4/CD8 composition contributing to controlled immune activation. Supportive care only. Monitoring for progression."
      },
      {
        label: "Day 5 Post-Infusion",
        day: 5,
        labs: {
          ldh: 240,
          creatinine: 0.9,
          platelets: 125,
          crp: 32,
          ferritin: 340,
          anc: 0.6,
          hemoglobin: 12.8,
          ast: 25,
          alt: 20,
          fibrinogen: 2.8,
          triglycerides: 1.4,
          il6: 45,
          d_dimer: 0.4,
          total_bilirubin: 0.6,
          albumin: 3.8
        },
        vitals: {
          temperature: 38.2,
          heart_rate: 84,
          systolic_bp: 118,
          diastolic_bp: 70,
          respiratory_rate: 16,
          spo2: 98
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 1,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 1,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 1.55,
          hscore: 65,
          car_hematotox: 1
        },
        expected_risk: "low",
        clinical_note: "Day 5: CRS peak - but only Grade 1. Fever 38.2C, well-appearing. CRP peaked at 32 (mild). Ferritin 340 (moderate elevation only). IL-6 at 45 - confirming CAR-T activation without excessive inflammation. No hypotension, no hypoxia. ICE 10/10 - no neurotoxicity. ANC at nadir from conditioning but patient on prophylactic levofloxacin. This is the CRS peak - all indicators suggest it will resolve quickly."
      },
      {
        label: "Day 10 Post-Infusion",
        day: 10,
        labs: {
          ldh: 185,
          creatinine: 0.8,
          platelets: 142,
          crp: 5,
          ferritin: 160,
          anc: 2.8,
          hemoglobin: 12.2,
          ast: 18,
          alt: 15,
          fibrinogen: 3.2,
          triglycerides: 1.2,
          il6: 5,
          d_dimer: 0.2,
          total_bilirubin: 0.5,
          albumin: 4.0
        },
        vitals: {
          temperature: 36.7,
          heart_rate: 72,
          systolic_bp: 122,
          diastolic_bp: 74,
          respiratory_rate: 14,
          spo2: 99
        },
        clinical: {
          organomegaly: 0,
          cytopenias: 0,
          hemophagocytosis: false,
          immunosuppression: false,
          neurologic_symptoms: "None",
          ice_score: 10,
          crs_grade: 0,
          icans_grade: 0,
          oxygen_requirement: "None"
        },
        scores: {
          easix: 0.96,
          hscore: 44,
          car_hematotox: 0
        },
        expected_risk: "low",
        clinical_note: "Day 10: Complete recovery. Afebrile since day 7. All inflammatory markers normalized. CRP back to baseline. Ferritin back to normal. LDH actually DECREASED below baseline (185 vs 195) - encouraging sign of tumor response. Counts essentially recovered: ANC 2.8, platelets 142, Hb 12.2. No ICANS at any point. CAR-T cells detected and expanding by flow cytometry. DISCHARGE today. Follow-up: weekly labs x4 weeks, then monthly. PET-CT at day 30 for response assessment. This is the ideal outcome - demonstrates that CAR-T can be well-tolerated with excellent early signals of efficacy."
      }
    ],
    anticipated_tests: [
      "CBC with differential daily while inpatient",
      "CRP daily",
      "Comprehensive metabolic panel daily",
      "ICE assessment daily",
      "Post-discharge: CBC weekly x4 weeks, then monthly",
      "Immunoglobulin levels monthly (B-cell aplasia monitoring)",
      "PET-CT day 30 (response assessment)",
      "CAR-T cell quantification day 14, 28, 90",
      "CT scan q3 months for surveillance year 1"
    ],
    teaching_points: [
      "This case represents the optimal trajectory - use as a benchmark when evaluating other patients",
      "Low baseline EASIX (0.68) and CAR-HEMATOTOX (0) predicted this uncomplicated course",
      "Key favorable factors: low tumor burden, good ECOG, normal baseline labs, no prior SCT, younger age",
      "LDH dropping below baseline early is an encouraging sign of anti-tumor activity",
      "Liso-cel's defined CD4/CD8 composition may contribute to more controlled CRS kinetics",
      "Even in optimal cases, ANC nadirs from conditioning and requires monitoring/prophylaxis",
      "Rapid count recovery (ANC >1.5 by day 10) correlates with low CAR-HEMATOTOX score",
      "Discharge by day 10 is feasible for uncomplicated cases - reduces healthcare costs significantly",
      "Long-term monitoring for B-cell aplasia and hypogammaglobulinemia remains important even in ideal cases",
      "Not all patients need tocilizumab - this demonstrates supportive care alone can be sufficient"
    ]
  }

];
