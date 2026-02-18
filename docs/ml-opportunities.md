# ML Opportunities for the Safety Research System

**Date:** 2026-02-17
**Server:** gpuserver1 (192.168.1.100)
**Author:** Research analysis (Claude Code)

---

## 1. Hardware Inventory

### GPU
- **Model:** NVIDIA GeForce RTX 5090
- **VRAM:** 33.67 GB (32,607 MiB reported by nvidia-smi)
- **Driver:** 570.144, CUDA 12.8
- **Current load:** ~256 MiB used (Xorg + Chrome only), 5% utilization
- **Available VRAM for ML:** ~32 GB (effectively the full card)

### System
- **RAM:** 125 GB total, ~3.1 GB used, ~121 GB available
- **Swap:** 8 GB (unused)
- **Disk (root):** 100 GB volume, 33 GB free
- **Disk (docker):** 1.7 TB volume, ~1.7 TB free (at /var/lib/docker)
- **HuggingFace cache:** 2.1 GB (TinyLlama 1.1B only model cached)

### Installed ML Stack
| Package | Version | Notes |
|---------|---------|-------|
| Python | 3.10.12 | |
| PyTorch | 2.11.0.dev (CUDA 12.8) | Nightly build |
| Transformers | 4.57.3 | Current |
| Accelerate | 1.12.0 | Multi-GPU / offloading |
| torch-geometric | 2.7.0 | Graph neural networks |
| scikit-learn | 1.7.2 | Classical ML |
| scipy | 1.15.3 | Statistical computing |
| pandas | 2.3.3 | Data manipulation |
| numpy | 2.2.6 | Numerical computing |
| networkx | 3.4.2 | Graph algorithms |
| safetensors | 0.7.0 | Model weight format |
| tokenizers | 0.22.1 | Fast tokenization |
| sentencepiece | 0.2.1 | Tokenization |

### Not Yet Installed (Would Need)
- bitsandbytes (INT8/INT4 quantization)
- auto-gptq or auto-awq (GPTQ/AWQ quantized model loading)
- peft (parameter-efficient fine-tuning / LoRA)
- flash-attn or xformers (attention optimization)
- vllm (high-throughput inference server)
- datasets (HuggingFace datasets library)
- evaluate (HuggingFace evaluation metrics)

---

## 2. VRAM Budget: What Models Can We Run?

With 33.67 GB VRAM and 125 GB system RAM, model capacity depends on precision:

### Full Precision (FP32) -- 4 bytes per parameter
| Model Size | VRAM Required | Fits? |
|-----------|--------------|-------|
| 1B | ~4 GB | Yes |
| 3B | ~12 GB | Yes |
| 7B | ~28 GB | Yes (tight) |
| 13B | ~52 GB | No |

### Half Precision (FP16/BF16) -- 2 bytes per parameter
| Model Size | VRAM Required | Fits? |
|-----------|--------------|-------|
| 1B | ~2 GB | Yes |
| 3B | ~6 GB | Yes |
| 7B | ~14 GB | Yes |
| 13B | ~26 GB | Yes |
| 20B | ~40 GB | No |

### INT8 Quantization -- 1 byte per parameter (requires bitsandbytes)
| Model Size | VRAM Required | Fits? |
|-----------|--------------|-------|
| 7B | ~7 GB | Yes |
| 13B | ~13 GB | Yes |
| 30B | ~30 GB | Yes (tight) |
| 70B | ~70 GB | No |

### INT4 Quantization (GPTQ/AWQ/GGUF) -- 0.5 bytes per parameter
| Model Size | VRAM Required | Fits? |
|-----------|--------------|-------|
| 7B | ~4 GB | Yes |
| 13B | ~7 GB | Yes |
| 30B | ~16 GB | Yes |
| 70B | ~35 GB | Tight, possibly with offloading |

### Practical Sweet Spots for This Hardware
- **Embedding models (0.1-1B):** Run many simultaneously, trivial VRAM
- **7B models in FP16:** 14 GB, leaving room for batch inference
- **13B models in FP16:** 26 GB, fits comfortably
- **70B models in INT4 (GPTQ/AWQ):** ~35 GB, borderline -- may need CPU offloading for KV cache
- **Sentence transformers (< 1B):** Multiple can coexist in VRAM

### Recommended Starter Models by Task
| Task | Model | Size | VRAM |
|------|-------|------|------|
| Text embeddings | `BAAI/bge-large-en-v1.5` | 335M | ~1.3 GB |
| Text embeddings | `intfloat/e5-large-v2` | 335M | ~1.3 GB |
| Biomedical embeddings | `microsoft/BiomedNLP-BiomedBERT-base` | 110M | ~0.5 GB |
| Biomedical NER | `alvaroalon2/biobert_diseases_ner` | 110M | ~0.5 GB |
| MedDRA coding | `cambridgeltl/SapBERT-from-PubMedBERT` | 110M | ~0.5 GB |
| Clinical NLP | `emilyalsentzer/Bio_ClinicalBERT` | 110M | ~0.5 GB |
| General LLM (reasoning) | `meta-llama/Llama-3.1-8B-Instruct` | 8B | ~16 GB FP16 |
| Medical LLM | `epfl-llm/meditron-7b` | 7B | ~14 GB FP16 |
| Graph learning | Custom GNN via torch-geometric | N/A | ~1-2 GB |

---

## 3. Existing Data Assets

### Analysis Results (~/safety-research-system/analysis/results/)

| File | Size | Contents |
|------|------|----------|
| ct_gov_ae_data.json | 6.3 MB | AE data from 47 ClinicalTrials.gov trials |
| faers_product_comparison.json | 99 KB | FAERS disproportionality signals for 6 CAR-T products (Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti) |
| analysis_results.json | 12 KB | Statistical analysis outputs |
| statistical_summary.txt | 6 KB | Summary statistics |
| Various figures/tables | ~15 KB | Forest plots, demographics, AE rates, model comparisons |

### Structured Knowledge (src/data/)

1. **Pharma simulation** (`pharma_simulation.py`, `pharma_org.py`): Simulated Phase I FIH trial with 28 enrolled patients, 42 ICSRs (8 serious), 6 CRS cases, 2 ICANS cases. Org hierarchy, regulatory mapping, quality metrics.

2. **FAERS signal detection** (`faers_cache.py`, `src/models/faers_signal.py`): Real openFDA FAERS queries computing PRR, ROR, and EBGM disproportionality metrics for CAR-T products across AE categories (CRS, neurotoxicity, infections, cytopenias, secondary malignancies, mortality).

3. **ClinicalTrials.gov data** (`ctgov_cache.py`): Normalized AE data from 47 cell therapy trials with AE term normalization mapping (CRS, ICANS, cytopenias, infections, HLH). Computed AE rates per trial.

4. **Knowledge graph** (`src/data/graph/`): In-memory biological pathway graph with 11 node types (Gene, Protein, Cytokine, Receptor, Cell_Type, Pathway, Adverse_Event, Drug, Biomarker, Organ, Clinical_Sign) and 19 edge types. Pre-built CRS, ICANS, and HLH pathway definitions with literature-grounded mechanism chains.

5. **Mechanism chains** (`src/data/knowledge/mechanisms.py`): Complete therapy-to-AE mechanism chains for 11 therapy modalities (CAR-T CD19/BCMA/dual, TCR-T, CAR-NK, TIL, CAR-M, gene therapy, Treg, MSC) covering 10 AE categories. Each chain includes temporal onset, biomarkers, branching points, intervention opportunities, and PubMed references.

6. **Signaling pathways** (`src/data/knowledge/pathways.py`): Directed signaling pathway graphs with confidence weights, temporal windows, feedback loops, intervention points, and drug annotations.

7. **Molecular targets** (`src/data/knowledge/molecular_targets.py`): Druggable target database.

8. **References** (`src/data/knowledge/references.py`): PubMed reference library.

### Existing Models (src/models/)

1. **Bayesian risk model** (`bayesian_risk.py`): Beta-Binomial conjugate framework with informative priors for CRS, ICANS, ICAHS rate estimation. Sequential evidence accrual.

2. **Biomarker scoring ensemble** (`biomarker_scores.py`, `ensemble_runner.py`): Seven deterministic clinical scoring models -- EASIX, Modified EASIX, Pre-Modified EASIX, HScore, CAR-HEMATOTOX, Teachey Cytokine, Hay Binary Classifier. Two-layer ensemble (standard labs vs. cytokine-augmented).

3. **FAERS signal detection** (`faers_signal.py`): PRR, ROR, EBGM disproportionality analysis with signal strength classification.

4. **Signal triangulation** (`signal_triangulation.py`): Cross-source comparison of FAERS spontaneous reports vs. ClinicalTrials.gov controlled trial rates.

5. **Model registry** (`model_registry.py`): Seven statistical approaches -- Bayesian Beta-Binomial, Clopper-Pearson exact, Wilson score, DerSimonian-Laird random-effects meta-analysis, empirical Bayes shrinkage, Kaplan-Meier, predictive posterior.

6. **Model validation** (`model_validation.py`): Validation framework.

### Engine (src/engine/)
- **SafetyEngine** (`core.py`): Full prediction pipeline -- routing, model calls, normalization, mechanistic validation, ensemble, Safety Index, hypothesis generation, alerting, audit.
- **Orchestrator** (`orchestrator/`): Prompt routing to foundation models, response normalization, ensemble aggregation, secure API gateway.
- **Reasoning** (`reasoning/`): Hypothesis generation and mechanistic validation.
- **Integration** (`integration/`): Alert engine with threshold-based triggering, audit trail.

### Safety Index (src/safety_index/)
- **Patient scorer** (`patient/scorer.py`): Individual patient risk via biomarker trajectories, knowledge graph pathway activation, and foundation model predictions. Evidence-based thresholds for CRS, ICANS, HLH biomarkers (IL-6, IFN-gamma, TNF-alpha, CRP, ferritin, Ang2, VWF, D-dimer, fibrinogen, IL-18, sCD25).
- **Population analyzer** (`population/analyzer.py`): Trial-level aggregate metrics, subgroup stratification, trend detection, early stopping signals.

---

## 4. What Is Currently Running

### Cron Jobs
| Schedule | Job |
|----------|-----|
| Every 2 hours | `/home/alton/sartor/periodic-analysis.sh` |
| Every 30 min | Sartor gateway cron (`gateway_cron.py`) |

### Running Processes
| Process | PID | Started |
|---------|-----|---------|
| `dashboard/app.py` (Sartor dashboard, port 5000) | 484706 | Feb 6 |
| `safety_api.py` (Sartor safety API) | 1350019 | Feb 8 |
| `uvicorn src.api.app:app` (Safety research FastAPI, port 8000) | 2444305 | Feb 10 |

### tmux Sessions
| Session | Created |
|---------|---------|
| `claude` | Feb 6 |
| `safety-test` | Feb 9 |

### GPU Usage
Only Xorg (59 MiB) and Chrome (176 MiB) are using the GPU. No ML workloads are currently running. The GPU is essentially idle.

---

## 5. Concrete ML Feature Opportunities

### Opportunity 1: AE Report Classification Using Embeddings

**What:** Encode adverse event narratives, MedDRA terms, and ICSR text into dense vector embeddings. Use these for semantic similarity search, automatic MedDRA coding, duplicate detection, and clustering of AE reports.

**Why it matters:** The system already has AE term normalization (`ctgov_cache.py` with `AE_TERM_MAP`) using substring matching. Embedding-based classification would be more robust -- handling synonyms, misspellings, novel terms, and cross-language reports.

**How:**
1. Load a biomedical embedding model (SapBERT or BiomedBERT, ~500 MB VRAM).
2. Embed all AE terms from the 47 CT.gov trials and FAERS product data.
3. Build a vector index (FAISS or simple cosine similarity) for nearest-neighbor MedDRA coding.
4. Replace substring-based `normalize_ae_term()` in `ctgov_cache.py` with embedding-based classification.
5. Add a `/api/v1/classify-ae` endpoint to the FastAPI server.

**VRAM cost:** < 1 GB. **Complexity:** Low. **Impact:** Medium.

**Recommended model:** `cambridgeltl/SapBERT-from-PubMedBERT` (110M params, trained on UMLS synonyms, ideal for MedDRA term mapping).

---

### Opportunity 2: Signal Detection Using Anomaly Detection / Time Series

**What:** Augment the existing statistical disproportionality analysis (PRR/ROR/EBGM) with ML-based anomaly detection on FAERS reporting patterns over time.

**Why it matters:** The current FAERS signal module computes point-in-time disproportionality metrics. ML anomaly detection could identify emerging signals earlier by detecting trend breaks, seasonal patterns, and multi-dimensional outliers across product-AE-time combinations.

**How:**
1. Pull FAERS quarterly report counts via openFDA API for each product-AE pair.
2. Train lightweight time-series anomaly detectors (Isolation Forest, autoencoders, or Prophet).
3. Flag product-AE pairs where recent reporting rates deviate from historical baselines.
4. Integrate into the `signal_triangulation.py` module as an additional evidence source.

**VRAM cost:** Negligible (scikit-learn / CPU-based). **Complexity:** Medium. **Impact:** High.

**Alternative GPU approach:** Train a small transformer-based time-series model on FAERS temporal data for multivariate anomaly detection.

---

### Opportunity 3: NLP Extraction from Clinical Narratives

**What:** Use biomedical NER (Named Entity Recognition) and relation extraction models to automatically parse clinical narratives, ICSR descriptions, and trial protocols into structured data.

**Why it matters:** The `narrative_engine.py` currently generates narratives from structured data using templates. The inverse process -- extracting structured data from narratives -- would enable ingestion of unstructured clinical documents, FDA safety reviews, published case reports, and DSUR narratives.

**How:**
1. Deploy a biomedical NER model (Bio_ClinicalBERT or PubMedBERT fine-tuned for NER).
2. Extract entities: drugs, AEs, dosages, temporal expressions, severity grades, biomarker values.
3. Use relation extraction to link entities (drug-AE pairs, biomarker-severity associations).
4. Feed extracted entities into the knowledge graph as new nodes and edges.
5. Add a `/api/v1/extract` endpoint for document processing.

**VRAM cost:** ~1 GB for NER model. **Complexity:** Medium-High. **Impact:** High.

**Recommended models:**
- NER: `d4data/biomedical-ner-all` or `alvaroalon2/biobert_diseases_ner`
- Relation extraction: `allenai/scibert_scivocab_uncased` fine-tuned, or use the 8B LLM for zero-shot extraction

---

### Opportunity 4: Knowledge Graph Link Prediction and Embedding

**What:** Use graph neural networks (GNN) to learn embeddings of the biological knowledge graph, enabling link prediction (predicting missing edges), node classification, and graph-based reasoning.

**Why it matters:** The knowledge graph in `src/data/graph/` has rich mechanistic biology but is manually curated. GNN-based link prediction could suggest missing pathway connections, predict novel drug-AE associations, and identify underexplored mechanism chains. The system already has torch-geometric installed.

**How:**
1. Export the knowledge graph nodes and edges to torch-geometric format.
2. Train a GNN (GraphSAGE, GAT, or R-GCN for heterogeneous graphs) on the existing graph.
3. Use the trained model for:
   - **Link prediction:** Predict missing edges (e.g., does Drug X inhibit Pathway Y?).
   - **Node embeddings:** Cluster similar AEs, find analogous mechanisms across therapy modalities.
   - **Pathway completion:** Suggest missing steps in mechanism chains.
4. Integrate predictions as "suggested edges" in the knowledge graph with confidence scores.

**VRAM cost:** 1-2 GB. **Complexity:** Medium. **Impact:** High.

**Key advantage:** torch-geometric 2.7.0 is already installed. The graph schema (`schema.py`) defines 11 node types and 19 edge types, which maps directly to a heterogeneous GNN architecture.

---

### Opportunity 5: Patient Risk Prediction Enhancement

**What:** Replace or augment the deterministic biomarker scoring models (EASIX, HScore, CAR-HEMATOTOX) with learned models that can capture non-linear interactions between biomarkers and clinical features.

**Why it matters:** The current ensemble runner (`ensemble_runner.py`) uses seven deterministic published formulas. These are clinically validated but cannot adapt to new data patterns or capture higher-order interactions between biomarkers. An ML layer could learn from the simulated trial data and, eventually, from real patient outcomes.

**How:**
1. Generate a training dataset from the simulation engine (28 patients with lab trajectories, AE outcomes, and biomarker time series).
2. Train a gradient-boosted model (XGBoost/LightGBM) or small neural network on biomarker features to predict CRS/ICANS grade.
3. Add the ML model as Layer 2 in the ensemble runner (alongside Layer 0: standard labs, Layer 1: cytokines).
4. Use the ML model's feature importance to validate or challenge the deterministic models.

**VRAM cost:** Negligible (CPU-based for tree models) or ~1 GB (for neural network). **Complexity:** Medium. **Impact:** Medium.

**Important caveat:** With only 28 simulated patients, overfitting is the primary risk. Cross-validation and comparison against the deterministic models is essential. The ML model should augment, not replace, the published formulas.

---

### Opportunity 6: Biomedical LLM for Mechanism Reasoning

**What:** Run a local biomedical or general-purpose LLM (7-13B) for mechanism hypothesis generation, safety narrative generation, and interactive clinical reasoning.

**Why it matters:** The `narrative_engine.py` already has a placeholder for Claude API integration. A local LLM could provide similar capabilities without external API costs or latency, while keeping sensitive patient data on-premises. The orchestrator (`engine/orchestrator/`) is already designed to route queries to multiple model backends.

**How:**
1. Install bitsandbytes and PEFT for efficient inference.
2. Download Llama 3.1 8B Instruct (or Meditron-7B for biomedical domain).
3. Integrate as a new `ModelBackend` in the existing `PromptRouter` (`orchestrator/router.py`).
4. Use for: mechanism hypothesis generation, narrative drafting, safety report summarization, regulatory document Q&A.
5. The existing `SecureAPIGateway` and `ResponseNormalizer` can be reused.

**VRAM cost:** ~14-16 GB for 7-8B FP16, or ~8 GB INT8. **Complexity:** Medium. **Impact:** High.

**Recommended models:**
- General: `meta-llama/Llama-3.1-8B-Instruct` (16 GB FP16)
- Biomedical: `epfl-llm/meditron-7b` (14 GB FP16)
- Both could run simultaneously in INT8 (~7 GB each, totaling ~14 GB)

---

### Opportunity 7: Semantic Search Over Regulatory Documents

**What:** Build a RAG (Retrieval-Augmented Generation) pipeline over regulatory frameworks, published guidelines, and PubMed references already cataloged in the system.

**Why it matters:** The system contains extensive regulatory mappings (`pharma_org.py`), PubMed references (`references.py`), and mechanism citations. A semantic search layer would let users query across all these sources in natural language (e.g., "What are the FDA requirements for CRS reporting in Phase I CAR-T trials?").

**How:**
1. Chunk and embed all regulatory text, references, and mechanism descriptions.
2. Store embeddings in a local FAISS or ChromaDB index.
3. Use the local LLM (Opportunity 6) for answer generation with retrieved context.
4. Add a `/api/v1/search` endpoint and a search tab in the dashboard.

**VRAM cost:** ~1 GB (embedding model) + LLM cost from Opportunity 6. **Complexity:** Medium. **Impact:** Medium.

---

## 6. Prioritized Implementation Roadmap

### Phase 1: Quick Wins (1-2 days each)

| # | Opportunity | VRAM | Packages Needed | Notes |
|---|------------|------|-----------------|-------|
| 1 | AE embedding classification | < 1 GB | None (HF transformers already installed) | Direct improvement to existing `normalize_ae_term()` |
| 2 | Anomaly detection on FAERS | 0 (CPU) | None (scikit-learn already installed) | Extends existing `faers_signal.py` |

### Phase 2: Medium Effort (1-2 weeks each)

| # | Opportunity | VRAM | Packages Needed | Notes |
|---|------------|------|-----------------|-------|
| 4 | Knowledge graph GNN | 1-2 GB | None (torch-geometric installed) | Leverages existing graph schema |
| 3 | Biomedical NER | ~1 GB | None | New capability for document ingestion |

### Phase 3: Larger Projects (2-4 weeks each)

| # | Opportunity | VRAM | Packages Needed | Notes |
|---|------------|------|-----------------|-------|
| 6 | Local biomedical LLM | 14-16 GB | bitsandbytes, peft | Replaces external API dependency |
| 7 | RAG pipeline | +1 GB | chromadb or faiss-gpu | Depends on Opportunity 6 |
| 5 | ML risk prediction | ~1 GB | xgboost or lightgbm | Needs more training data |

### Package Installation Plan
```bash
# Phase 1 -- no new packages needed

# Phase 2 -- no new packages needed

# Phase 3
pip install bitsandbytes peft faiss-gpu chromadb xgboost lightgbm
pip install flash-attn --no-build-isolation  # optional, for faster LLM inference
```

---

## 7. Disk Space Considerations

- Root volume has only **33 GB free**. Model downloads should target the docker volume or a new mount.
- A 7B FP16 model is ~14 GB on disk; a 13B is ~26 GB.
- Recommend creating a symlink: `ln -s /var/lib/docker/hf-cache ~/.cache/huggingface` or setting `HF_HOME` to a path on the docker volume.
- The 1.7 TB docker volume has ample space for any model we want to run.

---

## 8. Coexistence with Running Services

The following services are already running and must not be disrupted:

| Service | Port | RAM | GPU |
|---------|------|-----|-----|
| Sartor dashboard | 5000 | ~60 MB | None |
| Sartor safety API | N/A | ~130 MB | None |
| Safety research FastAPI | 8000 | ~137 MB | None |

Total current memory usage is ~3.1 GB of 125 GB RAM and ~256 MB of 33 GB VRAM. There is ample headroom for ML workloads. Even loading a 13B model in FP16 (26 GB VRAM, ~30 GB RAM) would leave comfortable margins.

---

## 9. Key Findings Summary

1. **The GPU is idle.** 33.67 GB VRAM is sitting unused. The RTX 5090 can comfortably run 7-13B models in FP16, or up to 30B models quantized to INT8.

2. **The ML stack is 80% ready.** PyTorch, Transformers, torch-geometric, scikit-learn, and accelerate are all installed. Only quantization libraries (bitsandbytes, auto-gptq) and fine-tuning tools (peft) are missing.

3. **The data is rich and well-structured.** 47 clinical trials with normalized AE data, FAERS disproportionality signals for 6 CAR-T products, a biological knowledge graph with 11 node types and 19 edge types, and detailed mechanism chains for 11 therapy modalities.

4. **The architecture is ready for ML integration.** The orchestrator pattern (`PromptRouter`, `ResponseNormalizer`, `EnsembleAggregator`) is explicitly designed for multiple model backends. The narrative engine has a placeholder for LLM integration. The ensemble runner has a layered architecture that can accommodate ML models as a new layer.

5. **Highest-impact first steps** are embedding-based AE classification (Opportunity 1) and knowledge graph GNN (Opportunity 4), which leverage existing infrastructure with zero new package installations.
