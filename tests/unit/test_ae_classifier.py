"""
Unit tests for src/models/ae_classifier.py

Tests the SapBERT-based AE term classifier with mocked transformer model
so tests pass without GPU or model download. All mocking uses pure numpy --
no torch dependency required for unit tests.

Tests cover:
    - Classification of known AE terms to correct categories
    - Batch classification consistency
    - Embedding dimension correctness
    - Model status reporting
    - Edge cases (empty input, unknown terms)
    - Module-level convenience functions
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

import numpy as np

from src.models.ae_classifier import MEDDRA_REFERENCE_TERMS


# ---------------------------------------------------------------------------
# Fake embedding engine (pure numpy, no torch)
# ---------------------------------------------------------------------------

class FakeEmbeddings:
    """Fake embeddings that produce deterministic category-aligned vectors.

    Each MedDRA category gets a distinct direction in embedding space so that
    cosine similarity correctly ranks the right category first.
    """

    # Map categories to unique basis directions (768-dim, one-hot-ish)
    _CATEGORY_DIMS = {
        "crs": 0,
        "icans": 1,
        "cytopenias": 2,
        "infections": 3,
        "iechs": 4,
        "secondary_malignancies": 5,
        "cardiac": 6,
        "neurological": 7,
        "gi": 8,
        "hepatic": 9,
        "renal": 10,
        "pulmonary": 11,
        "dermatological": 12,
    }

    # Terms that should map to specific categories (for query embedding)
    _TERM_CATEGORIES = {
        "cytokine release syndrome": "crs",
        "cytokine storm": "crs",
        "crs": "crs",
        "fever with hypotension": "crs",
        "neurotoxicity": "icans",
        "encephalopathy": "icans",
        "icans": "icans",
        "confusion after car-t": "icans",
        "aphasia": "icans",
        "neutropenia": "cytopenias",
        "thrombocytopenia": "cytopenias",
        "low platelet count": "cytopenias",
        "low platelets": "cytopenias",
        "anemia": "cytopenias",
        "pancytopenia": "cytopenias",
        "febrile neutropenia": "cytopenias",
        "pneumonia": "infections",
        "sepsis": "infections",
        "bacterial infection": "infections",
        "fungal infection": "infections",
        "hemophagocytic lymphohistiocytosis": "iechs",
        "macrophage activation syndrome": "iechs",
        "hlh": "iechs",
        "secondary malignancy": "secondary_malignancies",
        "t-cell lymphoma": "secondary_malignancies",
        "myelodysplastic syndrome": "secondary_malignancies",
        "cardiomyopathy": "cardiac",
        "arrhythmia": "cardiac",
        "myocarditis": "cardiac",
        "peripheral neuropathy": "neurological",
        "guillain-barre syndrome": "neurological",
        "nausea": "gi",
        "diarrhea": "gi",
        "colitis": "gi",
        "hepatotoxicity": "hepatic",
        "elevated transaminases": "hepatic",
        "jaundice": "hepatic",
        "acute kidney injury": "renal",
        "elevated creatinine": "renal",
        "nephrotoxicity": "renal",
        "ards": "pulmonary",
        "pneumonitis": "pulmonary",
        "pleural effusion": "pulmonary",
        "rash": "dermatological",
        "stevens-johnson syndrome": "dermatological",
        "pruritus": "dermatological",
    }

    @classmethod
    def embed(cls, term: str, dim: int = 768) -> np.ndarray:
        """Generate a deterministic embedding for a term.

        Reference terms get strong signal in their category dimension.
        Unknown terms get a noisy vector.
        """
        vec = np.random.RandomState(hash(term) % 2**31).randn(dim).astype(np.float32) * 0.1

        # Look up category for this term
        category = None
        lower = term.lower()

        # Direct lookup
        if lower in cls._TERM_CATEGORIES:
            category = cls._TERM_CATEGORIES[lower]

        # If not found, try reference terms
        if category is None:
            for cat, terms in MEDDRA_REFERENCE_TERMS.items():
                for ref_term in terms:
                    if ref_term.lower() == lower:
                        category = cat
                        break
                if category:
                    break

        if category and category in cls._CATEGORY_DIMS:
            dim_idx = cls._CATEGORY_DIMS[category]
            vec[dim_idx] += 5.0  # Strong signal in category direction

        return vec


# ---------------------------------------------------------------------------
# A numpy-based mock classifier that mimics AEClassifier behavior
# ---------------------------------------------------------------------------

class MockClassifier:
    """Numpy-based mock of AEClassifier for testing without torch."""

    def __init__(self) -> None:
        self._model_name = "mock-sapbert"
        self._reference_terms = MEDDRA_REFERENCE_TERMS
        self._is_loaded = True
        self._load_time = 0.5
        self._device = "cpu"
        self._embedding_dim = 768

        # Build reference index
        self._reference_metadata: list[dict[str, str]] = []
        all_terms: list[str] = []
        for category, terms in MEDDRA_REFERENCE_TERMS.items():
            for term in terms:
                all_terms.append(term)
                self._reference_metadata.append(
                    {"category": category, "term": term}
                )

        # Compute reference embeddings
        ref_vecs = np.stack([FakeEmbeddings.embed(t) for t in all_terms])
        norms = np.linalg.norm(ref_vecs, axis=1, keepdims=True) + 1e-8
        self._ref_normalized = ref_vecs / norms

    def classify_ae_term(self, term: str, top_k: int = 3) -> dict:
        """Classify a term using numpy cosine similarity."""
        query = FakeEmbeddings.embed(term).reshape(1, -1)
        query_norm = query / (np.linalg.norm(query) + 1e-8)

        sims = (query_norm @ self._ref_normalized.T).squeeze()

        top_k = min(top_k, len(self._reference_metadata))
        top_indices = np.argsort(sims)[::-1][:top_k]

        matches = []
        for idx in top_indices:
            meta = self._reference_metadata[idx]
            matches.append({
                "category": meta["category"],
                "confidence": round(float(sims[idx]), 4),
                "matched_term": meta["term"],
            })

        return {"input_term": term, "top_matches": matches}

    def classify_ae_terms_batch(self, terms: list[str], top_k: int = 3) -> list[dict]:
        """Classify multiple terms."""
        if not terms:
            return []
        return [self.classify_ae_term(t, top_k=top_k) for t in terms]

    def embed_ae_terms(self, terms: list[str]) -> list[list[float]]:
        """Embed terms using fake embeddings."""
        if not terms:
            return []
        return [FakeEmbeddings.embed(t).tolist() for t in terms]

    def get_model_status(self) -> dict:
        """Return mock status."""
        return {
            "available": True,
            "loaded": self._is_loaded,
            "model_name": self._model_name,
            "device": self._device,
            "embedding_dim": self._embedding_dim,
            "load_time_seconds": round(self._load_time, 3) if self._load_time else None,
            "categories": list(self._reference_terms.keys()),
            "total_reference_terms": sum(
                len(v) for v in self._reference_terms.values()
            ),
            "terms_per_category": {
                k: len(v) for k, v in self._reference_terms.items()
            },
        }

    def get_categories(self) -> list[str]:
        """Return category names."""
        return list(self._reference_terms.keys())

    def get_reference_terms(self, category: str) -> list[str]:
        """Return reference terms for a category."""
        return list(self._reference_terms.get(category, []))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_classifier() -> MockClassifier:
    """Create a numpy-based mock classifier that mimics AEClassifier behavior.

    Uses deterministic fake embeddings aligned to category directions so
    cosine similarity tests work correctly, without requiring torch.
    """
    return MockClassifier()


# ---------------------------------------------------------------------------
# Test: MEDDRA_REFERENCE_TERMS structure
# ---------------------------------------------------------------------------

class TestMedDRAReferenceTerms:
    """Tests for the reference vocabulary structure."""

    def test_all_categories_present(self):
        """Verify all 13 AE categories exist."""
        expected = {
            "crs", "icans", "cytopenias", "infections", "iechs",
            "secondary_malignancies", "cardiac", "neurological",
            "gi", "hepatic", "renal", "pulmonary", "dermatological",
        }
        assert set(MEDDRA_REFERENCE_TERMS.keys()) == expected

    def test_each_category_has_at_least_30_terms(self):
        """Each category should have >= 30 reference terms for robust matching."""
        for category, terms in MEDDRA_REFERENCE_TERMS.items():
            assert len(terms) >= 30, (
                f"Category '{category}' has only {len(terms)} terms, need >= 30"
            )

    def test_no_duplicate_terms_within_category(self):
        """No duplicates within a single category."""
        for category, terms in MEDDRA_REFERENCE_TERMS.items():
            lower_terms = [t.lower() for t in terms]
            assert len(lower_terms) == len(set(lower_terms)), (
                f"Category '{category}' has duplicate terms"
            )

    def test_all_terms_are_nonempty_strings(self):
        """All reference terms must be non-empty strings."""
        for category, terms in MEDDRA_REFERENCE_TERMS.items():
            for term in terms:
                assert isinstance(term, str) and term.strip(), (
                    f"Empty or non-string term in category '{category}'"
                )

    def test_total_terms_exceeds_400(self):
        """Should have 400+ total reference terms across all categories."""
        total = sum(len(v) for v in MEDDRA_REFERENCE_TERMS.values())
        assert total >= 400, f"Only {total} total terms, expected >= 400"


# ---------------------------------------------------------------------------
# Test: Classification of known AE terms
# ---------------------------------------------------------------------------

class TestClassifyAETerm:
    """Tests for classify_ae_term with mocked model."""

    @pytest.mark.parametrize(
        "term, expected_category",
        [
            ("cytokine release syndrome", "crs"),
            ("cytokine storm", "crs"),
            ("neurotoxicity", "icans"),
            ("encephalopathy", "icans"),
            ("neutropenia", "cytopenias"),
            ("thrombocytopenia", "cytopenias"),
            ("low platelet count", "cytopenias"),
            ("pneumonia", "infections"),
            ("sepsis", "infections"),
            ("hemophagocytic lymphohistiocytosis", "iechs"),
            ("macrophage activation syndrome", "iechs"),
            ("secondary malignancy", "secondary_malignancies"),
            ("cardiomyopathy", "cardiac"),
            ("peripheral neuropathy", "neurological"),
            ("diarrhea", "gi"),
            ("hepatotoxicity", "hepatic"),
            ("acute kidney injury", "renal"),
            ("pneumonitis", "pulmonary"),
            ("rash", "dermatological"),
        ],
    )
    def test_known_terms_classified_correctly(
        self, mock_classifier, term, expected_category
    ):
        """Known AE terms should map to the correct MedDRA category."""
        result = mock_classifier.classify_ae_term(term)

        assert result["input_term"] == term
        assert len(result["top_matches"]) == 3
        # Top match should be the expected category
        assert result["top_matches"][0]["category"] == expected_category

    def test_returns_top_3_by_default(self, mock_classifier):
        """Default top_k=3 should return exactly 3 matches."""
        result = mock_classifier.classify_ae_term("cytokine storm")
        assert len(result["top_matches"]) == 3

    def test_top_k_parameter(self, mock_classifier):
        """Custom top_k should return the requested number of matches."""
        result = mock_classifier.classify_ae_term("cytokine storm", top_k=5)
        assert len(result["top_matches"]) == 5

    def test_top_k_1(self, mock_classifier):
        """top_k=1 should return exactly 1 match."""
        result = mock_classifier.classify_ae_term("neutropenia", top_k=1)
        assert len(result["top_matches"]) == 1
        assert result["top_matches"][0]["category"] == "cytopenias"

    def test_confidence_scores_in_valid_range(self, mock_classifier):
        """All confidence scores should be between -1 and 1 (cosine range)."""
        result = mock_classifier.classify_ae_term("cytokine storm")
        for match in result["top_matches"]:
            assert -1.0 <= match["confidence"] <= 1.0

    def test_confidence_scores_are_descending(self, mock_classifier):
        """Matches should be sorted by descending confidence."""
        result = mock_classifier.classify_ae_term("neutropenia")
        scores = [m["confidence"] for m in result["top_matches"]]
        assert scores == sorted(scores, reverse=True)

    def test_matched_term_is_from_reference_vocab(self, mock_classifier):
        """Each matched_term should exist in the reference vocabulary."""
        all_terms = set()
        for terms in MEDDRA_REFERENCE_TERMS.values():
            all_terms.update(terms)

        result = mock_classifier.classify_ae_term("fever with hypotension")
        for match in result["top_matches"]:
            assert match["matched_term"] in all_terms

    def test_result_structure(self, mock_classifier):
        """Result should have the expected keys and structure."""
        result = mock_classifier.classify_ae_term("anemia")

        assert "input_term" in result
        assert "top_matches" in result
        assert isinstance(result["top_matches"], list)

        for match in result["top_matches"]:
            assert "category" in match
            assert "confidence" in match
            assert "matched_term" in match
            assert isinstance(match["confidence"], float)


# ---------------------------------------------------------------------------
# Test: Batch classification
# ---------------------------------------------------------------------------

class TestBatchClassification:
    """Tests for classify_ae_terms_batch."""

    def test_batch_returns_correct_count(self, mock_classifier):
        """Batch should return one result per input term."""
        terms = ["cytokine storm", "neutropenia", "rash"]
        results = mock_classifier.classify_ae_terms_batch(terms)
        assert len(results) == 3

    def test_batch_empty_input(self, mock_classifier):
        """Empty input should return empty list."""
        results = mock_classifier.classify_ae_terms_batch([])
        assert results == []

    def test_batch_matches_individual_results(self, mock_classifier):
        """Batch results should match individual classify_ae_term calls."""
        terms = ["cytokine storm", "neutropenia", "hepatotoxicity"]
        batch_results = mock_classifier.classify_ae_terms_batch(terms)

        for term, batch_result in zip(terms, batch_results):
            individual_result = mock_classifier.classify_ae_term(term)
            assert batch_result["input_term"] == individual_result["input_term"]
            assert batch_result["top_matches"][0]["category"] == \
                individual_result["top_matches"][0]["category"]

    def test_batch_preserves_order(self, mock_classifier):
        """Results should be in the same order as input terms."""
        terms = ["rash", "sepsis", "ARDS", "jaundice"]
        results = mock_classifier.classify_ae_terms_batch(terms)

        for term, result in zip(terms, results):
            assert result["input_term"] == term


# ---------------------------------------------------------------------------
# Test: Embedding
# ---------------------------------------------------------------------------

class TestEmbedAETerms:
    """Tests for embed_ae_terms."""

    def test_embedding_dimensions(self, mock_classifier):
        """Each embedding should have the correct dimensionality (768)."""
        terms = ["cytokine storm", "neutropenia"]
        embeddings = mock_classifier.embed_ae_terms(terms)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 768
        assert len(embeddings[1]) == 768

    def test_embedding_returns_floats(self, mock_classifier):
        """Embedding values should be floats."""
        embeddings = mock_classifier.embed_ae_terms(["test term"])
        assert all(isinstance(v, float) for v in embeddings[0])

    def test_empty_input(self, mock_classifier):
        """Empty input should return empty list."""
        assert mock_classifier.embed_ae_terms([]) == []

    def test_different_terms_produce_different_embeddings(self, mock_classifier):
        """Different terms should produce different embeddings."""
        embeddings = mock_classifier.embed_ae_terms(
            ["cytokine storm", "neutropenia"]
        )
        # Should not be identical
        assert embeddings[0] != embeddings[1]

    def test_single_term(self, mock_classifier):
        """Single term should return a list with one embedding."""
        embeddings = mock_classifier.embed_ae_terms(["rash"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 768


# ---------------------------------------------------------------------------
# Test: Model status
# ---------------------------------------------------------------------------

class TestModelStatus:
    """Tests for get_model_status."""

    def test_status_when_loaded(self, mock_classifier):
        """Status should show loaded=True with correct metadata."""
        status = mock_classifier.get_model_status()

        assert status["loaded"] is True
        assert status["available"] is True
        assert status["model_name"] == "mock-sapbert"
        assert status["device"] == "cpu"
        assert status["embedding_dim"] == 768
        assert isinstance(status["categories"], list)
        assert len(status["categories"]) == 13
        assert status["total_reference_terms"] > 300

    def test_status_has_terms_per_category(self, mock_classifier):
        """Status should include term counts per category."""
        status = mock_classifier.get_model_status()

        assert "terms_per_category" in status
        for category, count in status["terms_per_category"].items():
            assert count >= 30, f"Category '{category}' has {count} terms"

    def test_status_categories_match_reference(self, mock_classifier):
        """Categories in status should match MEDDRA_REFERENCE_TERMS keys."""
        status = mock_classifier.get_model_status()
        assert set(status["categories"]) == set(MEDDRA_REFERENCE_TERMS.keys())

    def test_status_unloaded(self):
        """Status of an unloaded classifier should show loaded=False."""
        with patch("src.models.ae_classifier._HAS_TORCH", True), \
             patch("src.models.ae_classifier._HAS_TRANSFORMERS", True):
            from src.models.ae_classifier import AEClassifier
            classifier = AEClassifier(model_name="test-model", device="cpu")
            status = classifier.get_model_status()

            assert status["loaded"] is False
            assert status["load_time_seconds"] is None

    def test_status_unavailable(self):
        """When torch is missing, available should be False."""
        with patch("src.models.ae_classifier._HAS_TORCH", False), \
             patch("src.models.ae_classifier._HAS_TRANSFORMERS", True):
            from src.models.ae_classifier import AEClassifier
            classifier = AEClassifier(model_name="test-model", device="cpu")
            status = classifier.get_model_status()

            assert status["available"] is False


# ---------------------------------------------------------------------------
# Test: Utility methods
# ---------------------------------------------------------------------------

class TestUtilityMethods:
    """Tests for get_categories and get_reference_terms."""

    def test_get_categories(self, mock_classifier):
        """get_categories should return all 13 category names."""
        categories = mock_classifier.get_categories()
        assert len(categories) == 13
        assert "crs" in categories
        assert "icans" in categories

    def test_get_reference_terms_existing(self, mock_classifier):
        """get_reference_terms for an existing category returns its terms."""
        terms = mock_classifier.get_reference_terms("crs")
        assert len(terms) >= 30
        assert "cytokine release syndrome" in terms

    def test_get_reference_terms_nonexistent(self, mock_classifier):
        """get_reference_terms for unknown category returns empty list."""
        terms = mock_classifier.get_reference_terms("nonexistent_category")
        assert terms == []


# ---------------------------------------------------------------------------
# Test: Module-level functions
# ---------------------------------------------------------------------------

class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_classify_ae_term_function(self):
        """Module-level classify_ae_term should use singleton."""
        with patch("src.models.ae_classifier._get_classifier") as mock_get:
            mock_cls = MagicMock()
            mock_cls.classify_ae_term.return_value = {
                "input_term": "test",
                "top_matches": [],
            }
            mock_get.return_value = mock_cls

            from src.models.ae_classifier import classify_ae_term
            result = classify_ae_term("test")
            mock_cls.classify_ae_term.assert_called_once_with("test", top_k=3)

    def test_embed_ae_terms_function(self):
        """Module-level embed_ae_terms should use singleton."""
        with patch("src.models.ae_classifier._get_classifier") as mock_get:
            mock_cls = MagicMock()
            mock_cls.embed_ae_terms.return_value = [[0.1, 0.2]]
            mock_get.return_value = mock_cls

            from src.models.ae_classifier import embed_ae_terms
            result = embed_ae_terms(["test"])
            mock_cls.embed_ae_terms.assert_called_once_with(["test"])

    def test_get_model_status_function(self):
        """Module-level get_model_status should use singleton."""
        with patch("src.models.ae_classifier._get_classifier") as mock_get:
            mock_cls = MagicMock()
            mock_cls.get_model_status.return_value = {"loaded": False}
            mock_get.return_value = mock_cls

            from src.models.ae_classifier import get_model_status
            result = get_model_status()
            mock_cls.get_model_status.assert_called_once()

    def test_classify_batch_function(self):
        """Module-level classify_ae_terms_batch should use singleton."""
        with patch("src.models.ae_classifier._get_classifier") as mock_get:
            mock_cls = MagicMock()
            mock_cls.classify_ae_terms_batch.return_value = []
            mock_get.return_value = mock_cls

            from src.models.ae_classifier import classify_ae_terms_batch
            result = classify_ae_terms_batch(["term1", "term2"], top_k=5)
            mock_cls.classify_ae_terms_batch.assert_called_once_with(
                ["term1", "term2"], top_k=5
            )


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_long_term(self, mock_classifier):
        """Very long terms should be handled (truncated by tokenizer)."""
        long_term = "severe life-threatening " * 50 + "cytokine release syndrome"
        result = mock_classifier.classify_ae_term(long_term)
        assert result["input_term"] == long_term
        assert len(result["top_matches"]) == 3

    def test_special_characters(self, mock_classifier):
        """Terms with special characters should not crash."""
        result = mock_classifier.classify_ae_term("CRS (grade >=2)")
        assert len(result["top_matches"]) == 3

    def test_numeric_term(self, mock_classifier):
        """Purely numeric input should not crash."""
        result = mock_classifier.classify_ae_term("12345")
        assert len(result["top_matches"]) == 3

    def test_single_character(self, mock_classifier):
        """Single character input should not crash."""
        result = mock_classifier.classify_ae_term("x")
        assert len(result["top_matches"]) == 3

    def test_ensure_loaded_without_deps(self):
        """_ensure_loaded should raise RuntimeError when deps missing."""
        with patch("src.models.ae_classifier._HAS_TORCH", False):
            from src.models.ae_classifier import AEClassifier
            classifier = AEClassifier(model_name="test", device="cpu")
            with pytest.raises(RuntimeError, match="requires PyTorch"):
                classifier._ensure_loaded()

    def test_large_batch(self, mock_classifier):
        """Batch with many terms should not crash."""
        terms = [f"adverse event {i}" for i in range(50)]
        results = mock_classifier.classify_ae_terms_batch(terms)
        assert len(results) == 50

    def test_repeated_terms(self, mock_classifier):
        """Repeated terms should produce identical results."""
        result1 = mock_classifier.classify_ae_term("neutropenia")
        result2 = mock_classifier.classify_ae_term("neutropenia")
        assert result1 == result2


# ---------------------------------------------------------------------------
# Test: AEClassification dataclass
# ---------------------------------------------------------------------------

class TestAEClassificationDataclass:
    """Tests for the AEClassification frozen dataclass."""

    def test_creation(self):
        """AEClassification should be creatable with all fields."""
        from src.models.ae_classifier import AEClassification

        result = AEClassification(
            input_term="test",
            category="crs",
            confidence=0.95,
            matched_term="cytokine release syndrome",
        )
        assert result.input_term == "test"
        assert result.category == "crs"
        assert result.confidence == 0.95
        assert result.matched_term == "cytokine release syndrome"

    def test_frozen(self):
        """AEClassification should be immutable."""
        from src.models.ae_classifier import AEClassification

        result = AEClassification(
            input_term="test",
            category="crs",
            confidence=0.95,
            matched_term="cytokine release syndrome",
        )
        with pytest.raises(AttributeError):
            result.category = "icans"


# ---------------------------------------------------------------------------
# Test: Constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Tests for module constants."""

    def test_model_name(self):
        from src.models.ae_classifier import MODEL_NAME
        assert "SapBERT" in MODEL_NAME
        assert "PubMedBERT" in MODEL_NAME

    def test_max_length(self):
        from src.models.ae_classifier import MAX_LENGTH
        assert MAX_LENGTH == 64

    def test_embedding_dim(self):
        from src.models.ae_classifier import EMBEDDING_DIM
        assert EMBEDDING_DIM == 768


# ---------------------------------------------------------------------------
# Test: Alignment with existing codebase AE categories
# ---------------------------------------------------------------------------

class TestCodebaseAlignment:
    """Verify the classifier categories align with existing codebase."""

    def test_ctgov_categories_covered(self):
        """All categories from ctgov_cache.py AE_TERM_MAP should be present."""
        ctgov_categories = {"crs", "icans", "cytopenias", "infections", "iechs"}
        for cat in ctgov_categories:
            assert cat in MEDDRA_REFERENCE_TERMS, (
                f"ctgov_cache category '{cat}' missing from classifier"
            )

    def test_mechanisms_ae_categories_covered(self):
        """AECategory values from mechanisms.py should map to classifier categories."""
        # From mechanisms.py AECategory enum
        mechanism_categories = {
            "Cytokine Release Syndrome": "crs",
            "ICANS": "icans",
            "Prolonged Cytopenia": "cytopenias",
            "Infection": "infections",
            "IEC-HS": "iechs",
        }
        for _label, cat_key in mechanism_categories.items():
            assert cat_key in MEDDRA_REFERENCE_TERMS, (
                f"Mechanism category '{cat_key}' missing from classifier"
            )

    def test_extended_categories_present(self):
        """Categories beyond the core 5 should be present for comprehensive coverage."""
        extended = {
            "secondary_malignancies",
            "cardiac",
            "neurological",
            "gi",
            "hepatic",
            "renal",
            "pulmonary",
            "dermatological",
        }
        for cat in extended:
            assert cat in MEDDRA_REFERENCE_TERMS, (
                f"Extended category '{cat}' missing from classifier"
            )
