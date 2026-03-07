"""
SapBERT-based adverse event term classifier.

Uses the SapBERT model (cambridgeltl/SapBERT-from-PubMedBERT-fulltext) to embed
adverse event terms into dense vectors and classify free-text AE descriptions
to the nearest MedDRA Preferred Term category via cosine similarity.

SapBERT is a 110M-parameter BERT model pre-trained on UMLS synonym pairs,
making it well-suited for biomedical concept normalization and MedDRA coding.

Design:
    - Lazy model loading: the transformer is only loaded when first needed
    - Reference vocabulary embeddings are computed once and cached
    - Classification uses cosine similarity against cached reference embeddings
    - Gracefully degrades when torch/transformers are unavailable

Reference:
    Liu et al. "Self-Alignment Pretraining for Biomedical Entity
    Representations" (2021). https://arxiv.org/abs/2010.11784
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conditional imports -- gracefully handle missing torch/transformers
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn.functional as F

    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    logger.warning(
        "PyTorch not installed; AE classifier will not be available. "
        "Install with: pip install torch"
    )

try:
    from transformers import AutoModel, AutoTokenizer

    _HAS_TRANSFORMERS = True
except ImportError:
    _HAS_TRANSFORMERS = False
    logger.warning(
        "Transformers not installed; AE classifier will not be available. "
        "Install with: pip install transformers"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_NAME = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
"""HuggingFace model identifier for SapBERT."""

MAX_LENGTH = 64
"""Maximum token length for input terms (SapBERT was trained on short phrases)."""

EMBEDDING_DIM = 768
"""Dimensionality of SapBERT [CLS] embeddings."""


# ---------------------------------------------------------------------------
# MedDRA reference vocabulary
# ---------------------------------------------------------------------------
# Each category maps to a list of representative MedDRA Preferred Terms and
# common clinical synonyms.  These are embedded once and used as reference
# vectors for cosine-similarity classification.
#
# Categories align with the existing AE categories used throughout the safety
# research system (ctgov_cache.py AE_TERM_MAP, mechanisms.py AECategory,
# faers_signal.py TARGET_AES).

MEDDRA_REFERENCE_TERMS: dict[str, list[str]] = {
    "crs": [
        "cytokine release syndrome",
        "cytokine storm",
        "systemic inflammatory response",
        "CRS grade 1",
        "CRS grade 2",
        "CRS grade 3",
        "CRS grade 4",
        "fever with hypotension",
        "capillary leak syndrome",
        "hypotension requiring vasopressors",
        "hypoxia requiring supplemental oxygen",
        "high fever after infusion",
        "elevated interleukin-6",
        "elevated C-reactive protein",
        "elevated ferritin",
        "tachycardia with fever",
        "infusion related reaction",
        "cytokine elevation",
        "hemodynamic instability",
        "vascular leak",
        "disseminated intravascular coagulation",
        "tumor lysis syndrome",
        "multi-organ dysfunction",
        "coagulopathy with fever",
        "sinus tachycardia",
        "rigors and chills",
        "pyrexia",
        "hyperferritinemia",
        "elevated serum IL-6",
        "IL-6 mediated toxicity",
        "tocilizumab responsive fever",
        "post-infusion febrile reaction",
        "hemodynamic compromise",
        "organ dysfunction after cell therapy",
        "systemic cytokine elevation",
        "acute phase response",
        "inflammatory cascade activation",
        "serum cytokine surge",
        "vasodilatory shock",
        "cytokine-mediated organ injury",
    ],
    "icans": [
        "immune effector cell-associated neurotoxicity syndrome",
        "ICANS",
        "neurotoxicity",
        "encephalopathy",
        "cerebral edema",
        "aphasia",
        "confusion",
        "altered mental status",
        "tremor",
        "seizure",
        "headache after cell therapy",
        "word finding difficulty",
        "agraphia",
        "lethargy",
        "obtundation",
        "disorientation",
        "expressive aphasia",
        "receptive aphasia",
        "global aphasia",
        "dysgraphia",
        "ICE score decline",
        "delirium",
        "cognitive impairment after CAR-T",
        "somnolence",
        "ataxia",
        "myoclonus",
        "depressed consciousness",
        "focal neurological deficit",
        "hallucinations",
        "dysarthria",
        "status epilepticus",
        "raised intracranial pressure",
        "cerebral edema on MRI",
        "blood-brain barrier disruption",
        "CNS toxicity",
        "impaired handwriting",
        "inability to name objects",
        "decreased alertness",
        "brain swelling",
        "neurological deterioration",
    ],
    "cytopenias": [
        "neutropenia",
        "thrombocytopenia",
        "anemia",
        "pancytopenia",
        "leukopenia",
        "lymphopenia",
        "febrile neutropenia",
        "low platelet count",
        "low white blood cell count",
        "low red blood cell count",
        "bone marrow suppression",
        "myelosuppression",
        "aplastic anemia",
        "agranulocytosis",
        "bicytopenia",
        "prolonged cytopenia",
        "delayed count recovery",
        "severe neutropenia",
        "grade 3 neutropenia",
        "grade 4 neutropenia",
        "grade 3 thrombocytopenia",
        "grade 4 thrombocytopenia",
        "transfusion dependent anemia",
        "platelet transfusion requirement",
        "red blood cell transfusion",
        "absolute neutrophil count decrease",
        "hemoglobin decrease",
        "blood count abnormality",
        "hematologic toxicity",
        "bone marrow failure",
        "cytopenia lasting more than 28 days",
        "CAR-HEMATOTOX",
        "hematological adverse event",
        "low absolute neutrophil count",
        "decreased platelet count",
        "macrocytic anemia",
        "reticulocytopenia",
        "B-cell aplasia",
        "hypogammaglobulinemia",
        "immunoglobulin deficiency",
    ],
    "infections": [
        "infection",
        "pneumonia",
        "sepsis",
        "bacteremia",
        "fungal infection",
        "viral infection",
        "bacterial infection",
        "upper respiratory tract infection",
        "urinary tract infection",
        "catheter-related infection",
        "febrile illness",
        "opportunistic infection",
        "invasive fungal infection",
        "aspergillosis",
        "candidiasis",
        "CMV reactivation",
        "cytomegalovirus infection",
        "herpes zoster reactivation",
        "COVID-19",
        "respiratory syncytial virus",
        "influenza",
        "progressive multifocal leukoencephalopathy",
        "JC virus infection",
        "hepatitis B reactivation",
        "Clostridioides difficile infection",
        "cellulitis",
        "abscess",
        "osteomyelitis",
        "endocarditis",
        "meningitis",
        "encephalitis",
        "sinusitis",
        "bloodstream infection",
        "septic shock",
        "infectious complication",
        "neutropenic fever with positive cultures",
        "viral reactivation",
        "EBV reactivation",
        "BK virus infection",
        "Pneumocystis jirovecii pneumonia",
    ],
    "iechs": [
        "immune effector cell-associated HLH-like syndrome",
        "IEC-HS",
        "IECHS",
        "hemophagocytic lymphohistiocytosis",
        "macrophage activation syndrome",
        "HLH",
        "MAS",
        "carHLH",
        "hemophagocytosis",
        "secondary HLH",
        "reactive hemophagocytic syndrome",
        "hyperferritinemia with cytopenias",
        "elevated soluble IL-2 receptor",
        "elevated sCD25",
        "elevated sIL2R",
        "high ferritin with liver dysfunction",
        "fibrinogen consumption",
        "hypofibrinogenemia",
        "triglyceride elevation with fever",
        "hypertriglyceridemia",
        "hepatosplenomegaly",
        "liver function test elevation",
        "transaminitis with fever",
        "NK cell dysfunction",
        "impaired NK cell cytotoxicity",
        "bone marrow hemophagocytosis",
        "ferritin greater than 10000",
        "disseminated intravascular coagulation",
        "ICAHS",
        "CRS overlap syndrome",
        "fulminant cytokine storm with organ failure",
        "pancytopenia with hyperferritinemia",
        "progressive organ failure with high ferritin",
        "coagulopathy with hepatic dysfunction",
        "splenomegaly with cytopenias",
        "tissue hemophagocytosis",
        "macrophage hyperactivation",
    ],
    "secondary_malignancies": [
        "secondary malignancy",
        "second primary malignancy",
        "T-cell lymphoma",
        "myelodysplastic syndrome",
        "acute myeloid leukemia",
        "treatment-related malignancy",
        "secondary leukemia",
        "clonal hematopoiesis",
        "insertional oncogenesis",
        "CAR-positive T-cell lymphoma",
        "T-cell malignancy",
        "therapy-related myeloid neoplasm",
        "MDS",
        "AML",
        "second cancer",
        "new primary neoplasm",
        "lymphoproliferative disorder",
        "post-transplant lymphoproliferative disease",
        "PTLD",
        "clonal expansion",
        "transformation event",
        "secondary hematologic malignancy",
        "treatment-emergent neoplasm",
        "oncogenic transformation",
        "lentiviral insertion site malignancy",
        "clonal T-cell population",
        "aberrant T-cell expansion",
        "chromosomal aberration",
        "somatic mutation",
        "malignant transformation of transduced cells",
    ],
    "cardiac": [
        "cardiac toxicity",
        "cardiomyopathy",
        "heart failure",
        "myocarditis",
        "arrhythmia",
        "atrial fibrillation",
        "ventricular tachycardia",
        "troponin elevation",
        "left ventricular dysfunction",
        "cardiac arrest",
        "pericardial effusion",
        "QT prolongation",
        "bradycardia",
        "supraventricular tachycardia",
        "myocardial infarction",
        "acute coronary syndrome",
        "takotsubo cardiomyopathy",
        "stress cardiomyopathy",
        "cardiac tamponade",
        "congestive heart failure",
        "reduced ejection fraction",
        "BNP elevation",
        "NT-proBNP elevation",
        "cardiac biomarker elevation",
        "diastolic dysfunction",
        "pericarditis",
        "cardiac dysfunction",
        "acute heart failure",
        "cardiogenic shock",
        "heart rhythm abnormality",
        "ECG abnormality",
        "right ventricular strain",
        "pulmonary hypertension",
        "cardiac ischemia",
        "cardiotoxicity after immunotherapy",
    ],
    "neurological": [
        "peripheral neuropathy",
        "cranial nerve palsy",
        "Guillain-Barre syndrome",
        "autonomic neuropathy",
        "paresthesia",
        "neuropathic pain",
        "motor neuropathy",
        "sensory neuropathy",
        "progressive multifocal leukoencephalopathy",
        "leukoencephalopathy",
        "posterior reversible encephalopathy syndrome",
        "PRES",
        "movement disorder",
        "parkinsonism",
        "cognitive decline",
        "memory impairment",
        "stroke",
        "cerebrovascular accident",
        "transient ischemic attack",
        "intracranial hemorrhage",
        "subdural hematoma",
        "Bell palsy",
        "facial nerve palsy",
        "optic neuritis",
        "hearing loss",
        "vestibular dysfunction",
        "prolonged neurotoxicity",
        "delayed neurotoxicity",
        "neurocognitive deficit",
        "nerve damage",
        "demyelination",
        "radiculopathy",
        "myelopathy",
        "spinal cord injury",
        "chronic neurological sequelae",
    ],
    "gi": [
        "nausea",
        "vomiting",
        "diarrhea",
        "colitis",
        "mucositis",
        "oral mucositis",
        "stomatitis",
        "gastrointestinal hemorrhage",
        "GI bleeding",
        "esophagitis",
        "gastritis",
        "abdominal pain",
        "ileus",
        "bowel obstruction",
        "typhlitis",
        "neutropenic enterocolitis",
        "pancreatitis",
        "constipation",
        "dysphagia",
        "anorexia",
        "weight loss",
        "malnutrition",
        "GI perforation",
        "gastrointestinal toxicity",
        "enteritis",
        "proctitis",
        "gastroenteritis",
        "upper GI bleeding",
        "lower GI bleeding",
        "abdominal distension",
        "gastrointestinal obstruction",
        "xerostomia",
        "taste alteration",
        "dysgeusia",
        "intestinal inflammation",
    ],
    "hepatic": [
        "hepatotoxicity",
        "liver injury",
        "drug-induced liver injury",
        "hepatitis",
        "elevated transaminases",
        "elevated ALT",
        "elevated AST",
        "hyperbilirubinemia",
        "jaundice",
        "cholestasis",
        "hepatic failure",
        "liver failure",
        "hepatic encephalopathy",
        "ascites",
        "portal hypertension",
        "sinusoidal obstruction syndrome",
        "veno-occlusive disease",
        "VOD",
        "SOS",
        "hepatomegaly",
        "liver function test abnormality",
        "alkaline phosphatase elevation",
        "GGT elevation",
        "gamma-glutamyl transferase elevation",
        "coagulopathy with liver dysfunction",
        "hepatic vein thrombosis",
        "hepatocellular damage",
        "cholestatic liver injury",
        "mixed hepatocellular-cholestatic injury",
        "Hy law case",
        "liver enzyme elevation",
        "alanine aminotransferase increased",
        "aspartate aminotransferase increased",
        "total bilirubin increased",
        "direct bilirubin increased",
    ],
    "renal": [
        "acute kidney injury",
        "renal failure",
        "nephrotoxicity",
        "elevated creatinine",
        "decreased GFR",
        "proteinuria",
        "hematuria",
        "oliguria",
        "anuria",
        "renal tubular acidosis",
        "tubulointerstitial nephritis",
        "glomerulonephritis",
        "nephrotic syndrome",
        "electrolyte imbalance",
        "hyperkalemia",
        "hyponatremia",
        "hyperphosphatemia",
        "tumor lysis syndrome with renal failure",
        "dialysis requirement",
        "renal replacement therapy",
        "chronic kidney disease progression",
        "BUN elevation",
        "blood urea nitrogen increased",
        "creatinine clearance decreased",
        "renal impairment",
        "kidney dysfunction",
        "acute tubular necrosis",
        "renal cortical necrosis",
        "hemolytic uremic syndrome",
        "thrombotic microangiopathy",
        "contrast nephropathy",
        "uric acid nephropathy",
        "obstructive nephropathy",
        "fluid overload",
        "volume overload",
    ],
    "pulmonary": [
        "acute respiratory distress syndrome",
        "ARDS",
        "pneumonitis",
        "pulmonary edema",
        "pleural effusion",
        "respiratory failure",
        "dyspnea",
        "hypoxia",
        "pulmonary embolism",
        "pulmonary hemorrhage",
        "diffuse alveolar hemorrhage",
        "bronchospasm",
        "cough",
        "interstitial lung disease",
        "pulmonary fibrosis",
        "organizing pneumonia",
        "cryptogenic organizing pneumonia",
        "radiation pneumonitis",
        "lung infiltrates",
        "ground glass opacities",
        "oxygen desaturation",
        "mechanical ventilation requirement",
        "respiratory distress",
        "tachypnea",
        "wheezing",
        "pulmonary toxicity",
        "lung injury",
        "alveolar damage",
        "bronchoalveolar lavage abnormality",
        "pleurisy",
        "pneumothorax",
        "atelectasis",
        "upper airway obstruction",
        "laryngeal edema",
        "pulmonary infiltrate",
    ],
    "dermatological": [
        "rash",
        "maculopapular rash",
        "pruritus",
        "urticaria",
        "Stevens-Johnson syndrome",
        "toxic epidermal necrolysis",
        "dermatitis",
        "skin toxicity",
        "alopecia",
        "erythema",
        "skin ulceration",
        "bullous dermatitis",
        "skin necrosis",
        "hand-foot syndrome",
        "palmar-plantar erythrodysesthesia",
        "photosensitivity",
        "nail changes",
        "dry skin",
        "eczema",
        "psoriasiform eruption",
        "vitiligo",
        "hyperpigmentation",
        "skin rash after infusion",
        "morbilliform eruption",
        "drug eruption",
        "fixed drug eruption",
        "angioedema",
        "erythroderma",
        "skin graft versus host disease",
        "cutaneous toxicity",
        "acneiform rash",
        "petechiae",
        "purpura",
        "ecchymosis",
        "injection site reaction",
    ],
}
"""Reference vocabulary for MedDRA AE categories.

Each category contains 30-40 representative terms including MedDRA Preferred
Terms, common clinical synonyms, and typical free-text descriptions encountered
in adverse event reports and clinical trial data.
"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AEClassification:
    """Result of classifying an adverse event term.

    Attributes:
        input_term: The original free-text AE term.
        category: Best-matching MedDRA category.
        confidence: Cosine similarity score (0-1).
        matched_term: The specific reference term with highest similarity.
    """

    input_term: str
    category: str
    confidence: float
    matched_term: str


# ---------------------------------------------------------------------------
# AEClassifier -- singleton model wrapper
# ---------------------------------------------------------------------------

class AEClassifier:
    """SapBERT-based adverse event term classifier.

    Lazily loads the SapBERT model on first use and caches reference embeddings
    for fast repeated classification.  Thread-safe for read operations after
    initialization.

    Usage::

        classifier = AEClassifier()
        result = classifier.classify_ae_term("cytokine storm")
        # {'input_term': 'cytokine storm',
        #  'top_matches': [
        #      {'category': 'crs', 'confidence': 0.94, 'matched_term': 'cytokine storm'},
        #      ...
        #  ]}

        embeddings = classifier.embed_ae_terms(["fever", "neutropenia"])
        # [[0.12, -0.34, ...], [0.45, 0.67, ...]]
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        device: str | None = None,
        reference_terms: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the classifier.

        Args:
            model_name: HuggingFace model identifier.
            device: PyTorch device string ('cuda', 'cpu', etc.).
                If None, auto-detects CUDA availability.
            reference_terms: Override the default MedDRA reference vocabulary.
                Keys are category names, values are lists of representative terms.
        """
        self._model_name = model_name
        self._reference_terms = reference_terms or MEDDRA_REFERENCE_TERMS
        self._model: Any = None
        self._tokenizer: Any = None
        self._device: str = "cpu"
        self._requested_device = device
        self._reference_embeddings: dict[str, Any] = {}
        self._reference_metadata: list[dict[str, str]] = []
        self._is_loaded = False
        self._load_time: float | None = None
        self._embedding_dim: int = EMBEDDING_DIM

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load the model and compute reference embeddings if not already done."""
        if self._is_loaded:
            return

        if not _HAS_TORCH or not _HAS_TRANSFORMERS:
            raise RuntimeError(
                "AE classifier requires PyTorch and Transformers. "
                "Install with: pip install torch transformers"
            )

        start = time.monotonic()

        # Determine device
        if self._requested_device is not None:
            self._device = self._requested_device
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"

        logger.info(
            "Loading SapBERT model '%s' on device '%s'...",
            self._model_name,
            self._device,
        )

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModel.from_pretrained(self._model_name)
        self._model.to(self._device)
        self._model.eval()

        # Verify embedding dimension
        dummy = self._tokenizer("test", return_tensors="pt", padding=True, truncation=True, max_length=MAX_LENGTH)
        dummy = {k: v.to(self._device) for k, v in dummy.items()}
        with torch.no_grad():
            dummy_out = self._model(**dummy)
        self._embedding_dim = dummy_out.last_hidden_state.shape[-1]

        # Precompute reference embeddings
        self._build_reference_index()

        elapsed = time.monotonic() - start
        self._load_time = elapsed
        self._is_loaded = True

        total_terms = sum(len(v) for v in self._reference_terms.values())
        logger.info(
            "SapBERT loaded in %.2fs. %d categories, %d reference terms, "
            "embedding dim=%d, device=%s",
            elapsed,
            len(self._reference_terms),
            total_terms,
            self._embedding_dim,
            self._device,
        )

    def _build_reference_index(self) -> None:
        """Embed all reference terms and store them for cosine search."""
        self._reference_metadata = []
        all_terms: list[str] = []

        for category, terms in self._reference_terms.items():
            for term in terms:
                all_terms.append(term)
                self._reference_metadata.append(
                    {"category": category, "term": term}
                )

        # Batch-embed reference terms
        ref_embeddings = self._embed_batch(all_terms)
        # Normalize for cosine similarity (dot product = cosine on unit vectors)
        self._reference_embeddings_tensor = F.normalize(ref_embeddings, p=2, dim=1)

    def _embed_batch(
        self,
        texts: list[str],
        batch_size: int = 64,
    ) -> "torch.Tensor":
        """Embed a batch of texts using SapBERT [CLS] pooling.

        Args:
            texts: List of text strings to embed.
            batch_size: Number of texts to process at once.

        Returns:
            Tensor of shape (len(texts), embedding_dim).
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=MAX_LENGTH,
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)
                # SapBERT uses [CLS] token embedding
                cls_embeddings = outputs.last_hidden_state[:, 0, :]
                all_embeddings.append(cls_embeddings)

        return torch.cat(all_embeddings, dim=0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_ae_term(
        self,
        term: str,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Classify a free-text AE term to the nearest MedDRA category.

        Uses cosine similarity between the input term embedding and all
        reference term embeddings.  Returns the top-k matches.

        Args:
            term: Free-text adverse event description (e.g. "cytokine storm",
                "low platelets", "brain swelling").
            top_k: Number of top matches to return.

        Returns:
            Dictionary with keys:
                - ``input_term``: The original term.
                - ``top_matches``: List of dicts, each with ``category``,
                  ``confidence`` (float 0-1), and ``matched_term``.
        """
        self._ensure_loaded()

        # Embed the query term
        query_embedding = self._embed_batch([term])
        query_normalized = F.normalize(query_embedding, p=2, dim=1)

        # Cosine similarity = dot product of normalized vectors
        similarities = torch.mm(
            query_normalized, self._reference_embeddings_tensor.t()
        ).squeeze(0)

        # Get top-k
        top_k = min(top_k, len(self._reference_metadata))
        top_scores, top_indices = torch.topk(similarities, k=top_k)

        matches = []
        for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
            meta = self._reference_metadata[idx]
            matches.append(
                {
                    "category": meta["category"],
                    "confidence": round(score, 4),
                    "matched_term": meta["term"],
                }
            )

        return {
            "input_term": term,
            "top_matches": matches,
        }

    def classify_ae_terms_batch(
        self,
        terms: list[str],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Classify multiple AE terms in a single batch.

        More efficient than calling :meth:`classify_ae_term` in a loop because
        all query terms are embedded in one forward pass.

        Args:
            terms: List of free-text AE descriptions.
            top_k: Number of top matches per term.

        Returns:
            List of classification results (same format as classify_ae_term).
        """
        if not terms:
            return []

        self._ensure_loaded()

        # Batch-embed all query terms
        query_embeddings = self._embed_batch(terms)
        query_normalized = F.normalize(query_embeddings, p=2, dim=1)

        # Cosine similarity matrix: (n_queries, n_references)
        similarities = torch.mm(
            query_normalized, self._reference_embeddings_tensor.t()
        )

        results = []
        top_k_clamped = min(top_k, len(self._reference_metadata))

        for i, term in enumerate(terms):
            top_scores, top_indices = torch.topk(
                similarities[i], k=top_k_clamped
            )
            matches = []
            for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
                meta = self._reference_metadata[idx]
                matches.append(
                    {
                        "category": meta["category"],
                        "confidence": round(score, 4),
                        "matched_term": meta["term"],
                    }
                )
            results.append(
                {
                    "input_term": term,
                    "top_matches": matches,
                }
            )

        return results

    def embed_ae_terms(
        self,
        terms: list[str],
    ) -> list[list[float]]:
        """Embed a list of AE terms into dense vectors.

        Returns raw (non-normalized) SapBERT [CLS] embeddings suitable for
        downstream tasks such as clustering, visualization, or custom
        similarity computations.

        Args:
            terms: List of AE term strings.

        Returns:
            List of embedding vectors (each a list of floats with length
            equal to ``EMBEDDING_DIM``).
        """
        if not terms:
            return []

        self._ensure_loaded()

        embeddings = self._embed_batch(terms)
        return embeddings.cpu().tolist()

    def get_model_status(self) -> dict[str, Any]:
        """Return health check information about the classifier.

        Returns:
            Dictionary with model status, device, loaded categories,
            and reference term counts.
        """
        status: dict[str, Any] = {
            "available": _HAS_TORCH and _HAS_TRANSFORMERS,
            "loaded": self._is_loaded,
            "model_name": self._model_name,
            "device": self._device if self._is_loaded else None,
            "embedding_dim": self._embedding_dim if self._is_loaded else EMBEDDING_DIM,
            "load_time_seconds": round(self._load_time, 3) if self._load_time else None,
            "categories": list(self._reference_terms.keys()),
            "total_reference_terms": sum(
                len(v) for v in self._reference_terms.values()
            ),
            "terms_per_category": {
                k: len(v) for k, v in self._reference_terms.items()
            },
        }

        if self._is_loaded and _HAS_TORCH:
            status["gpu_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                status["gpu_name"] = torch.cuda.get_device_name(0)
                status["gpu_memory_allocated_mb"] = round(
                    torch.cuda.memory_allocated(0) / 1024 / 1024, 1
                )

        return status

    def get_categories(self) -> list[str]:
        """Return the list of available MedDRA categories."""
        return list(self._reference_terms.keys())

    def get_reference_terms(self, category: str) -> list[str]:
        """Return the reference terms for a specific category.

        Args:
            category: Category name (e.g. 'crs', 'icans').

        Returns:
            List of reference terms, or empty list if category not found.
        """
        return list(self._reference_terms.get(category, []))


# ---------------------------------------------------------------------------
# Module-level singleton and convenience functions
# ---------------------------------------------------------------------------

_classifier: AEClassifier | None = None


def _get_classifier() -> AEClassifier:
    """Get or create the module-level singleton classifier."""
    global _classifier
    if _classifier is None:
        _classifier = AEClassifier()
    return _classifier


def classify_ae_term(term: str, top_k: int = 3) -> dict[str, Any]:
    """Classify a free-text AE term to the nearest MedDRA category.

    Module-level convenience function using the singleton classifier.
    See :meth:`AEClassifier.classify_ae_term` for full documentation.

    Args:
        term: Free-text adverse event description.
        top_k: Number of top matches to return.

    Returns:
        Classification result with input_term and top_matches.
    """
    return _get_classifier().classify_ae_term(term, top_k=top_k)


def classify_ae_terms_batch(
    terms: list[str],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Classify multiple AE terms in a single batch.

    Module-level convenience function using the singleton classifier.
    See :meth:`AEClassifier.classify_ae_terms_batch` for full documentation.
    """
    return _get_classifier().classify_ae_terms_batch(terms, top_k=top_k)


def embed_ae_terms(terms: list[str]) -> list[list[float]]:
    """Embed a list of AE terms into dense vectors.

    Module-level convenience function using the singleton classifier.
    See :meth:`AEClassifier.embed_ae_terms` for full documentation.
    """
    return _get_classifier().embed_ae_terms(terms)


def get_model_status() -> dict[str, Any]:
    """Return health check information about the AE classifier.

    Module-level convenience function using the singleton classifier.
    See :meth:`AEClassifier.get_model_status` for full documentation.
    """
    return _get_classifier().get_model_status()
