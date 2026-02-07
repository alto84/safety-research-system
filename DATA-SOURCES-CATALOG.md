# Public Data Sources Catalog
## Cell Therapy Safety Prediction System

**Version:** 1.0.0
**Date:** 2026-02-07
**Purpose:** Comprehensive inventory of publicly available databases, APIs, and data resources for building a predictive safety system for CRS, ICANS, and IEC-HS/HLH in cell therapy.

---

## Summary

**Total Data Sources Cataloged: 75+**

| Category | Count | Key Sources |
|---|---|---|
| Adverse Event Databases | 4 | FAERS, VigiBase, EudraVigilance, JADER |
| Drug-Target Databases | 6 | ChEMBL, DrugBank, DGIdb, STITCH, BindingDB, TTD |
| Protein Interaction Networks | 5 | STRING, BioGRID, IntAct, MINT, HuRI |
| Pathway Databases | 5 | Reactome, KEGG, WikiPathways, Pathway Commons, BioCyc |
| Side Effect Databases | 3 | SIDER, OFFSIDES/TWOSIDES, ADReCS |
| Ontologies/Terminologies | 7 | MedDRA, SNOMED CT, GO, Disease Ontology, ATC, HPO, LOINC |
| Genomics/Pharmacogenomics | 7 | PharmGKB, ClinVar, GWAS Catalog, GTEx, gnomAD, OMIM, ClinGen |
| Clinical Trials | 3 | ClinicalTrials.gov, EU CTR/CTIS, WHO ICTRP |
| Literature | 4 | PubMed, Semantic Scholar, OpenAlex, Europe PMC |
| Cell Therapy Specific | 4 | CIBMTR, EBMT, FDA REMS, CTGTAC Materials |
| Cytokine/Immune | 6 | ImmPort, ImmunoGlobe, Interferome, DICE, CytReg, Immunome |
| Toxicity Prediction | 4 | ToxCast/CompTox, Tox21, eTOX, OpenTox |
| Real-World Evidence | 4 | OHDSI/OMOP, Sentinel, PCORnet, Flatiron |
| Biomarker/Protein Reference | 5 | BEST, OncoKB, CIViC, Human Protein Atlas, UniProt |
| Transcriptomic Repositories | 3 | GEO, ArrayExpress, Single Cell Portal/HCA |
| Regulatory Resources | 3 | DailyMed, Drugs@FDA, EMA EPARs |
| Network/Systems Biology | 5 | NDEx, SIGNOR, OmniPath, MSigDB, DisGeNET |
| Harmonization Standards | 3 | RxNorm, HGNC, LOINC |

---

## Integration Architecture

The data sources map to five functional layers in the prediction pipeline:

### Layer 1 -- Data Harmonization

MedDRA, SNOMED CT, RxNorm, LOINC, HGNC, ATC, Disease Ontology, HPO, Gene Ontology.

These provide the common vocabularies and identifier mappings that enable cross-database integration.

### Layer 2 -- Molecular Knowledge Graph

STRING, BioGRID, IntAct, Reactome, KEGG, WikiPathways, OmniPath, SIGNOR, ChEMBL, DrugBank, PhosphoSitePlus, UniProt, STITCH, ImmunoGlobe, CytReg, Interferome.

These build the mechanistic network model of CRS/ICANS/HLH cascades from receptor activation through signaling to gene expression and phenotype.

### Layer 3 -- Genetic Risk Scoring

PharmGKB, ClinVar, GWAS Catalog, GTEx, gnomAD, DICE, ClinGen, OMIM, DisGeNET, GEO, HCA.

These provide the genotype-to-phenotype mappings for patient-level genetic risk stratification.

### Layer 4 -- Clinical Evidence and Training Data

FAERS, VigiBase, EudraVigilance, ClinicalTrials.gov, CIBMTR, EBMT, OHDSI/OMOP, Flatiron, PCORnet, DailyMed, Drugs@FDA, EMA EPARs, SIDER, OFFSIDES/TWOSIDES.

These provide the clinical outcome data for model training, validation, and calibration.

### Layer 5 -- Literature Intelligence

PubMed, Semantic Scholar, OpenAlex, Europe PMC.

These provide continuous evidence updating through NLP-driven literature monitoring and knowledge extraction.

---

## Critical Path Data Sources (Highest Priority for Integration)

1. **CIBMTR** -- Richest patient-level CAR-T CRS/ICANS dataset (requires research collaboration)
2. **FAERS/OpenFDA** -- Largest freely accessible adverse event database with CAR-T reports
3. **ClinicalTrials.gov** -- Structured clinical trial CRS/ICANS outcome data
4. **Reactome + KEGG** -- Curated pathway knowledge for CRS mechanistic modeling
5. **STRING + OmniPath** -- Comprehensive molecular interaction networks
6. **ImmPort + ImmunoGlobe** -- Immune-specific gene lists and cytokine-cell interaction maps
7. **PharmGKB + ClinVar** -- Pharmacogenomic and genetic variant data
8. **OMOP/OHDSI** -- Standardized EHR data model for multi-site real-world evidence
9. **MedDRA + SNOMED CT + LOINC** -- Essential harmonization ontologies
10. **MSigDB (Hallmark + immuneSigDB)** -- Validated gene sets for pathway activity scoring

---

## Detailed Source Profiles

### Adverse Event Databases

#### FAERS / OpenFDA
- **URL:** https://open.fda.gov/apis/drug/event/
- **Organization:** FDA
- **Content:** Post-market adverse event reports for all marketed drugs including all 6 approved CAR-T products (Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti)
- **Format:** REST API (JSON), quarterly data files (ASCII/XML)
- **Size:** 27+ million adverse event reports (total), growing quarterly
- **License:** Public domain
- **CRS/ICANS Relevance:** CAR-T-specific reports coded with MedDRA PTs for CRS, ICANS, cytokine storm, neurotoxicity, HLH/MAS. Supports signal detection via disproportionality analysis (PRR, ROR, EBGM). Population-level incidence monitoring.
- **Integration:** Signal detection layer; population-level CRS/ICANS rate monitoring; calibration target for post-market predictions.

#### VigiBase (WHO)
- **URL:** https://www.who-umc.org/vigibase/
- **Organization:** Uppsala Monitoring Centre (WHO)
- **Content:** Global individual case safety reports (ICSRs) from 170+ countries
- **Size:** 35+ million reports
- **License:** Research access via collaboration agreement
- **CRS/ICANS Relevance:** Global perspective beyond US-only FAERS. Captures international CAR-T experience.

#### EudraVigilance
- **URL:** https://www.adrreports.eu/
- **Organization:** European Medicines Agency
- **Content:** European adverse event reports
- **License:** Public access to aggregated data; line-level data requires EMA agreement
- **CRS/ICANS Relevance:** European CAR-T safety data, potentially different product mix than US

#### JADER (Japanese)
- **URL:** https://www.pmda.go.jp/safety/info-services/drugs/adr-info/suspected-adr/0003.html
- **Organization:** PMDA (Japan)
- **Content:** Japanese adverse event reports
- **License:** Public download
- **CRS/ICANS Relevance:** Asian-specific safety data; potential pharmacogenomic differences in CRS susceptibility

### Drug-Target Databases

#### ChEMBL
- **URL:** https://www.ebi.ac.uk/chembl/
- **Organization:** EMBL-EBI
- **Content:** Bioactivity data from medicinal chemistry literature. 2.4M+ compounds, 15K+ targets, 20M+ activity measurements
- **Format:** REST API (JSON), PostgreSQL dump, SDF files, RDF
- **License:** CC BY-SA 3.0
- **CRS/ICANS Relevance:** Drug-target binding affinities for CRS management drugs (tocilizumab, ruxolitinib, anakinra, siltuximab, dexamethasone). Off-target effects that may modulate CRS risk.

#### DrugBank
- **URL:** https://go.drugbank.com/
- **Organization:** OMx Personal Health Analytics
- **Content:** Comprehensive drug data: targets, pathways, interactions, PK/PD, indications
- **Size:** 16,000+ drug entries, 5,400+ protein targets
- **License:** CC BY-NC 4.0 (academic); commercial license available
- **CRS/ICANS Relevance:** Complete pharmacological profiles for CRS management agents. Drug-drug interaction checking for concomitant medications.

#### DGIdb (Drug-Gene Interaction Database)
- **URL:** https://www.dgidb.org/
- **Organization:** Washington University
- **Content:** Drug-gene interactions aggregated from 30+ sources
- **License:** Open access
- **CRS/ICANS Relevance:** Identifies druggable genes in CRS/ICANS pathways

#### STITCH
- **URL:** http://stitch.embl.de/
- **Organization:** EMBL / STRING Consortium
- **Content:** Chemical-protein interactions (known and predicted). 430K+ chemicals, 9.6M+ proteins
- **License:** CC BY 4.0 (academic)
- **CRS/ICANS Relevance:** Chemical modulation of CRS-relevant proteins. Lymphodepletion agent interactions with immune pathway proteins.

### Protein Interaction Networks

#### STRING
- **URL:** https://string-db.org/
- **Organization:** EMBL / Swiss Institute of Bioinformatics / University of Copenhagen
- **Content:** Known and predicted protein-protein interactions. Combines experimental data, text mining, co-expression, genomic context.
- **Size:** 67M+ proteins, 20B+ interactions across 14,000+ organisms
- **Format:** REST API, TSV bulk download, MySQL dump
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Primary PPI network for the knowledge graph. CRS cascade: IFNG-IFNGR1-JAK1-STAT1, IL6-IL6R-IL6ST-JAK1-STAT3, TNF-TNFRSF1A-NFKB1. All high-confidence interactions (>700 score).

#### BioGRID
- **URL:** https://thebiogrid.org/
- **Organization:** University of Toronto
- **Content:** Curated physical and genetic interactions from literature
- **Size:** 2.4M+ interactions, 80K+ publications curated
- **License:** MIT license
- **CRS/ICANS Relevance:** Experimentally validated protein interactions. Higher curation stringency than STRING.

#### IntAct
- **URL:** https://www.ebi.ac.uk/intact/
- **Organization:** EMBL-EBI
- **Content:** Molecular interaction data from literature curation and direct data depositions
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** High-quality curated binary interactions with experimental evidence codes

#### HuRI (Human Reference Interactome)
- **URL:** http://www.interactome-atlas.org/
- **Organization:** Center for Cancer Systems Biology (Dana-Farber)
- **Content:** Systematic binary protein-protein interactions from yeast two-hybrid
- **Size:** ~53,000 interactions covering ~8,300 proteins
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Unbiased interactome (not literature-biased). May reveal novel interactions in CRS pathways.

### Pathway Databases

#### Reactome
- **URL:** https://reactome.org/
- **Organization:** Ontario Institute for Cancer Research / EMBL-EBI / NYU
- **Content:** Curated biological pathways and reactions in humans. Hierarchical pathway structure from broad biological processes to individual biochemical reactions.
- **Size:** 2,600+ pathways, 13,000+ reactions, 11,000+ proteins
- **Format:** REST API (JSON), BioPAX, SBML, Neo4j graph database
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Key pathways: "Signaling by Interleukins" (R-HSA-449147), "Cytokine Signaling in Immune system" (R-HSA-1280215), "JAK-STAT signaling" (multiple), "NF-kB signaling" (R-HSA-9020702), "Toll-Like Receptor Cascades" (R-HSA-168898). Complete reaction-level detail for CRS cascade modeling.

#### KEGG
- **URL:** https://www.kegg.jp/
- **Organization:** Kanehisa Laboratories, Kyoto University
- **Content:** Pathway maps, molecular networks, disease pathways, drug pathways
- **Format:** REST API, KGML (pathway markup language)
- **License:** Academic use free; commercial license required
- **CRS/ICANS Relevance:** JAK-STAT signaling (hsa04630), NF-kB signaling (hsa04064), TNF signaling (hsa04668), Cytokine-cytokine receptor interaction (hsa04060), CAR-T cell signaling pathway (hsa04659).

#### WikiPathways
- **URL:** https://www.wikipathways.org/
- **Organization:** Maastricht University / Gladstone Institutes
- **Content:** Community-curated biological pathways
- **License:** CC BY 3.0
- **CRS/ICANS Relevance:** Community-curated CAR-T therapy pathway (WP4934), Cytokine storm pathway models

#### Pathway Commons
- **URL:** https://www.pathwaycommons.org/
- **Organization:** University of Toronto / Memorial Sloan Kettering
- **Content:** Integrated biological pathway and interaction data from 22 public databases
- **Size:** 5,700+ pathways, 2.3M+ interactions
- **License:** Free for academic use
- **CRS/ICANS Relevance:** Pre-integrated pathway data that aggregates Reactome, KEGG, WikiPathways, PhosphoSitePlus, and others

### Side Effect Databases

#### SIDER
- **URL:** http://sideeffects.embl.de/
- **Organization:** EMBL
- **Content:** Drug-side effect associations mined from drug labels. Includes frequency data (common, uncommon, rare, very rare).
- **Size:** 1,430 drugs, 5,868 side effects, 139,756 drug-SE pairs
- **License:** CC BY-NC-SA 4.0
- **CRS/ICANS Relevance:** Baseline side effect frequencies for CRS-relevant drugs. Context for what is expected vs. novel in safety signals.

#### OFFSIDES / TWOSIDES
- **URL:** http://tatonettilab.org/offsides/
- **Organization:** Columbia University (Tatonetti Lab)
- **Content:** Off-label side effects (OFFSIDES) and drug-drug interaction side effects (TWOSIDES) mined from FAERS using statistical methods
- **License:** CC BY-NC-SA 3.0
- **CRS/ICANS Relevance:** Drug-drug interaction effects relevant to concomitant medications during CAR-T therapy

### Ontologies and Terminologies

#### MedDRA
- **URL:** https://www.meddra.org/
- **Organization:** MedDRA MSSO (ICH)
- **Content:** Standardized medical terminology for regulatory activities. 5-level hierarchy: SOC > HLGT > HLT > PT > LLT
- **License:** Subscription-based (free for regulators and academic researchers in some jurisdictions)
- **CRS/ICANS Relevance:** Standard coding for CRS (PT: Cytokine release syndrome, 10081639), ICANS (PT: Immune effector cell-associated neurotoxicity syndrome), HLH (PT: Haemophagocytic lymphohistiocytosis). Required for FAERS/VigiBase/EudraVigilance data analysis.

#### LOINC
- **URL:** https://loinc.org/
- **Organization:** Regenstrief Institute
- **Content:** Universal standard for identifying medical laboratory observations
- **Size:** 100,000+ observation codes
- **License:** Free (requires free registration)
- **CRS/ICANS Relevance:** Standardizes lab test identification: CRP (1988-5), ferritin (2276-4), IL-6 (26881-3), fibrinogen (3255-7), LDH (2532-0), D-dimer (48065-7). Essential for EHR data extraction.

#### Gene Ontology (GO)
- **URL:** http://geneontology.org/
- **Organization:** GO Consortium
- **Content:** Structured vocabulary for gene and protein function. Three domains: Molecular Function, Biological Process, Cellular Component.
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Functional annotations for CRS-relevant genes. GO terms like "inflammatory response" (GO:0006954), "cytokine production" (GO:0001816), "immune response" (GO:0006955).

### Genomics and Pharmacogenomics

#### PharmGKB
- **URL:** https://www.pharmgkb.org/
- **Organization:** Stanford University
- **Content:** Pharmacogenomic relationships: gene-drug associations, variant annotations, clinical guidelines, drug labels
- **License:** CC BY-SA 4.0
- **CRS/ICANS Relevance:** Genetic variants affecting drug metabolism for CRS management agents. HLA associations potentially relevant to immune-mediated toxicity risk.

#### ClinVar
- **URL:** https://www.ncbi.nlm.nih.gov/clinvar/
- **Organization:** NCBI/NIH
- **Content:** Aggregation of clinical interpretations of genomic variants
- **License:** Public domain
- **CRS/ICANS Relevance:** Pathogenic variants in HLH-associated genes (PRF1, UNC13D, STX11, STXBP2, LYST, AP3B1). Variants affecting immune function genes.

#### GTEx (Genotype-Tissue Expression)
- **URL:** https://gtexportal.org/
- **Organization:** NIH Common Fund
- **Content:** Gene expression across 54 human tissues from 948 donors
- **License:** Open access (dbGaP for individual-level data)
- **CRS/ICANS Relevance:** Tissue-specific expression of CRS-relevant genes. BBB-specific gene expression relevant to ICANS.

#### GWAS Catalog
- **URL:** https://www.ebi.ac.uk/gwas/
- **Organization:** EMBL-EBI / NHGRI
- **Content:** Curated collection of published genome-wide association studies
- **License:** Open access
- **CRS/ICANS Relevance:** Genetic risk variants for inflammatory/immune phenotypes. Potential genetic predictors of CRS susceptibility.

### Clinical Trials

#### ClinicalTrials.gov
- **URL:** https://clinicaltrials.gov/
- **Organization:** NLM/NIH
- **Content:** Registry of clinical studies. Structured data on study design, eligibility, interventions, outcomes, adverse events.
- **Format:** REST API (JSON), bulk download (pipe-delimited, XML)
- **Size:** 500,000+ registered studies
- **License:** Public domain
- **CRS/ICANS Relevance:** All registered CAR-T trials with reported CRS/ICANS rates. Systematic extraction of safety data across development programs.

### Cell Therapy Specific

#### CIBMTR
- **URL:** https://www.cibmtr.org/
- **Organization:** Medical College of Wisconsin / NMDP
- **Content:** Registry data from transplant and cell therapy centers. 15,000+ US CAR-T recipients with detailed outcome data.
- **Access:** Research data access via proposal (DUA required)
- **CRS/ICANS Relevance:** Richest patient-level CAR-T safety dataset. Real-world CRS/ICANS grading, timing, management, and outcomes across all commercial products.

#### EBMT
- **URL:** https://www.ebmt.org/
- **Organization:** European Society for Blood and Marrow Transplantation
- **Content:** European transplant and cell therapy registry. 5,000+ CAR-T recipients.
- **Access:** Research collaboration required
- **CRS/ICANS Relevance:** European CAR-T safety data. Complements CIBMTR with different population and practice patterns.

### Cytokine and Immune Databases

#### ImmPort
- **URL:** https://www.immport.org/
- **Organization:** NIAID/NIH
- **Content:** Immunology data repository. Curated gene lists for immune cell types, cytokine classifications, flow cytometry standards.
- **License:** ImmPort data sharing agreement (free)
- **CRS/ICANS Relevance:** Curated immune gene sets. Cytokine receptor-ligand pairs. Immune cell type markers for deconvolution.

#### ImmunoGlobe
- **URL:** https://immunoglobe.org/
- **Organization:** Published research resource
- **Content:** Curated database of cytokine-cell directional interactions with activation/inhibition annotations
- **License:** Open access
- **CRS/ICANS Relevance:** Directional cytokine-cell type interactions. Maps which cell types produce and respond to each CRS-relevant cytokine.

### Real-World Evidence

#### OHDSI / OMOP CDM
- **URL:** https://www.ohdsi.org/
- **Organization:** OHDSI Consortium
- **Content:** Observational Health Data Sciences and Informatics. Common Data Model (OMOP CDM) standardizing EHR data across institutions.
- **License:** Apache 2.0 (tools); data access per institution
- **CRS/ICANS Relevance:** Standardized EHR data model for multi-site real-world evidence studies. Enables federated analyses across institutions without data sharing.

### Network and Systems Biology

#### OmniPath
- **URL:** https://omnipathdb.org/
- **Organization:** Heidelberg University (Saez-Rodriguez Lab)
- **Content:** Integrated database from 100+ original resources. 100,000+ literature-curated signaling interactions, 50,000+ TF-target interactions, 35,000+ ligand-receptor interactions.
- **Format:** REST API, Python (omnipath/pypath), R (OmnipathR)
- **License:** Free for academic use
- **CRS/ICANS Relevance:** Most comprehensive integrated resource for building multi-layer CRS signaling models. Ligand-receptor + signaling + TF-target = complete signal-to-gene-expression models.

#### SIGNOR
- **URL:** https://signor.uniroma2.it/
- **Organization:** University of Rome Tor Vergata
- **Content:** Causal relationships between biological entities. 36,000+ causal relationships with mechanism annotations.
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Directional (causal) signaling relationships essential for CRS cascade modeling. Distinguishes activates vs. inhibits.

#### MSigDB (Molecular Signatures Database)
- **URL:** https://www.gsea-msigdb.org/gsea/msigdb/
- **Organization:** Broad Institute / UC San Diego
- **Content:** Curated gene set collections. Hallmark gene sets (50 well-defined biological states/processes), immuneSigDB (5,000+ immune-relevant gene sets).
- **License:** CC BY 4.0
- **CRS/ICANS Relevance:** Validated gene sets for pathway activity scoring. Hallmark inflammatory response, TNF-alpha signaling via NF-kB, IL-6/JAK/STAT3 signaling, interferon gamma response sets directly relevant to CRS.

### Regulatory Resources

#### DailyMed
- **URL:** https://dailymed.nlm.nih.gov/
- **Organization:** NLM
- **Content:** FDA-approved drug labeling in structured format (SPL). Complete prescribing information including CRS/ICANS warnings, adverse reaction tables, REMS requirements.
- **License:** Public domain
- **CRS/ICANS Relevance:** Authoritative FDA-reviewed CRS/ICANS safety data for each approved CAR-T product. Calibration benchmarks.

#### Drugs@FDA
- **URL:** https://www.accessdata.fda.gov/scripts/cder/daf/
- **Organization:** FDA
- **Content:** BLA review documents, clinical review memos, statistical review reports for each approved product.
- **License:** Public domain
- **CRS/ICANS Relevance:** Most detailed regulatory safety analyses available. Risk factor multivariate analyses, subgroup analyses, time-to-event data.

#### EMA EPARs
- **URL:** https://www.ema.europa.eu/en/medicines
- **Organization:** European Medicines Agency
- **Content:** European Public Assessment Reports with scientific discussion, SmPC, risk management plan summaries.
- **License:** Public access
- **CRS/ICANS Relevance:** European regulatory perspective. May include different risk factor analyses and post-authorization study requirements.

---

*This catalog was compiled from systematic review of publicly available biomedical databases relevant to cell therapy safety prediction. Last updated: 2026-02-07.*
