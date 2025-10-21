"""
Unit tests for Source Authenticity Verification Skill
"""

import pytest
from pathlib import Path
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from skills.audit.source_authenticity_verification.scripts.verify import (
    SourceAuthenticityVerification,
    verify_source_authenticity
)


class TestSourceAuthenticityVerification:
    """Test suite for SourceAuthenticityVerification skill."""

    def setup_method(self):
        """Set up test fixtures."""
        self.skill = SourceAuthenticityVerification()

    def test_metadata(self):
        """Test skill metadata is correct."""
        metadata = self.skill.metadata
        assert metadata.name == "source_authenticity_verification"
        assert metadata.version == "1.0.0"
        assert metadata.category.value == "audit"
        assert metadata.skill_type.value == "deterministic"

    def test_input_validation_missing_sources(self):
        """Test input validation fails without sources."""
        with pytest.raises(ValueError, match="Required input 'sources' not provided"):
            self.skill.validate_inputs({})

    def test_input_validation_invalid_type(self):
        """Test input validation fails with non-list sources."""
        with pytest.raises(ValueError, match="Input 'sources' must be a list"):
            self.skill.validate_inputs({"sources": "not a list"})

    def test_input_validation_invalid_source_type(self):
        """Test input validation fails with non-dict source."""
        with pytest.raises(ValueError, match="Source at index 0 must be a dictionary"):
            self.skill.validate_inputs({"sources": ["not a dict"]})

    def test_input_validation_success(self):
        """Test input validation succeeds with valid inputs."""
        assert self.skill.validate_inputs({"sources": [{"pmid": "12345"}]})

    def test_authentic_source(self):
        """Test authentic source passes validation."""
        result = self.skill.execute({
            "sources": [
                {
                    "pmid": "31415927",  # Realistic PMID (no sequential patterns)
                    "title": "Real Study on ADC-ILD",
                    "authors": ["Johnson A", "Smith B"],
                    "doi": "10.1234/example"
                }
            ]
        })

        # Should be authentic (PMID has no sequential pattern, title/authors are real)
        assert len(result["authentic_sources"]) == 1
        assert len(result["fabricated_sources"]) == 0
        # No critical issues from PMID/title/authors
        critical_issues = [i for i in result["issues"] if i["category"] in ["fabricated_pmid", "fabricated_source"]]
        assert len(critical_issues) == 0

    def test_fabricated_pmid_sequential_pattern(self):
        """Test detection of fabricated PMID with sequential pattern."""
        result = self.skill.execute({
            "sources": [{"pmid": "12345678"}]
        })

        assert len(result["authentic_sources"]) == 0
        assert len(result["fabricated_sources"]) == 1
        # May have multiple issues (known fake + sequential pattern)
        assert len(result["issues"]) >= 1

        # At least one issue should be fabricated_pmid
        pmid_issues = [i for i in result["issues"] if i["category"] == "fabricated_pmid"]
        assert len(pmid_issues) >= 1
        assert pmid_issues[0]["severity"] == "critical"

    def test_fabricated_pmid_known_fake(self):
        """Test detection of known fake PMIDs."""
        fake_pmids = ["12345678", "87654321", "11111111", "22222222"]

        for pmid in fake_pmids:
            result = self.skill.execute({"sources": [{"pmid": pmid}]})
            assert len(result["fabricated_sources"]) == 1
            assert any(i["category"] == "fabricated_pmid" for i in result["issues"])

    def test_invalid_pmid_format(self):
        """Test detection of invalid PMID format."""
        result = self.skill.execute({
            "sources": [{"pmid": "abc123"}]  # Not all digits
        })

        assert len(result["fabricated_sources"]) == 1
        issue = result["issues"][0]
        assert issue["category"] == "invalid_pmid_format"
        assert issue["severity"] == "critical"

    def test_pmid_too_long(self):
        """Test detection of PMID with >8 digits."""
        result = self.skill.execute({
            "sources": [{"pmid": "123456789"}]  # 9 digits
        })

        assert len(result["fabricated_sources"]) == 1
        assert any(i["category"] == "invalid_pmid_format" for i in result["issues"])

    def test_sequential_pattern_detection(self):
        """Test _is_sequential_pattern method."""
        # Ascending patterns
        assert self.skill._is_sequential_pattern("12345678")
        assert self.skill._is_sequential_pattern("23456789")
        assert self.skill._is_sequential_pattern("34567890")

        # Descending patterns
        assert self.skill._is_sequential_pattern("98765432")
        assert self.skill._is_sequential_pattern("87654321")

        # Contains sequential substring (3456)
        assert self.skill._is_sequential_pattern("34567801")

        # Truly non-sequential
        assert not self.skill._is_sequential_pattern("31415926")
        assert not self.skill._is_sequential_pattern("27182818")

    def test_placeholder_title_detection(self):
        """Test detection of placeholder titles."""
        placeholder_titles = [
            "Example Study",
            "Sample Research on ADC",
            "Test Paper",
            "Placeholder Title",
            "Lorem Ipsum Content",
            "To Be Determined",
            "TBD Study"
        ]

        for title in placeholder_titles:
            result = self.skill.execute({
                "sources": [{"title": title}]
            })

            assert len(result["fabricated_sources"]) == 1
            assert any(
                i["category"] == "fabricated_source" and "title" in i["location"]
                for i in result["issues"]
            ), f"Failed to detect placeholder title: {title}"

    def test_placeholder_authors_detection(self):
        """Test detection of placeholder author names."""
        placeholder_authors = [
            "Smith et al.",
            "Jones et al.",
            "Doe et al.",
            "Author Name",
            "et al."
        ]

        for authors in placeholder_authors:
            result = self.skill.execute({
                "sources": [{"authors": authors}]
            })

            assert len(result["fabricated_sources"]) == 1
            assert any(
                i["category"] == "fabricated_source" and "authors" in i["location"]
                for i in result["issues"]
            ), f"Failed to detect placeholder authors: {authors}"

    def test_authors_as_list(self):
        """Test handling of authors as list."""
        result = self.skill.execute({
            "sources": [{"authors": ["Smith", "Jones"]}]
        })

        # Real names, should pass
        assert len(result["authentic_sources"]) == 1

        # Placeholder in list
        result = self.skill.execute({
            "sources": [{"authors": ["Smith et al."]}]
        })

        assert len(result["fabricated_sources"]) == 1

    def test_invalid_url_format(self):
        """Test detection of invalid URL format."""
        invalid_urls = [
            "not-a-url",
            "missing-scheme.com",
        ]

        for url in invalid_urls:
            result = self.skill.execute({
                "sources": [{"url": url}]
            })

            assert len(result["fabricated_sources"]) >= 1
            assert any(i["category"] == "invalid_url_format" for i in result["issues"]), \
                f"Failed to detect invalid URL: {url}"

    def test_placeholder_url_detection(self):
        """Test detection of placeholder URLs."""
        placeholder_urls = [
            "https://example.com/study",
            "http://example.org/paper",
            "https://test.com/data",
            "http://fake.com/source",
            "http://dummy.com/placeholder",
            "http://localhost/test",
            "http://127.0.0.1/data"
        ]

        for url in placeholder_urls:
            result = self.skill.execute({
                "sources": [{"url": url}]
            })

            assert len(result["fabricated_sources"]) == 1
            assert any(i["category"] == "fabricated_url" for i in result["issues"]), \
                f"Failed to detect placeholder URL: {url}"

    def test_valid_url_format(self):
        """Test that valid URL format passes (accessibility may fail)."""
        result = self.skill.execute({
            "sources": [{"url": "https://pubmed.ncbi.nlm.nih.gov/34567890/"}]
        })

        # Should not have invalid_url_format or fabricated_url issues
        invalid_format_issues = [
            i for i in result["issues"]
            if i["category"] in ["invalid_url_format", "fabricated_url"]
        ]
        assert len(invalid_format_issues) == 0

    def test_doi_validation(self):
        """Test DOI format validation."""
        # Valid DOI
        result = self.skill.execute({
            "sources": [{"doi": "10.1234/example.2023"}]
        })
        assert len([i for i in result["issues"] if i["category"] == "invalid_doi_format"]) == 0

        # Invalid DOI
        result = self.skill.execute({
            "sources": [{"doi": "invalid-doi"}]
        })
        assert any(i["category"] == "invalid_doi_format" for i in result["issues"])

    def test_doi_none_value(self):
        """Test handling of None DOI value."""
        result = self.skill.execute({
            "sources": [{"doi": None}]
        })
        # Should not raise error, should skip validation
        assert True

    def test_multiple_sources(self):
        """Test handling of multiple sources."""
        result = self.skill.execute({
            "sources": [
                {"pmid": "34567890", "title": "Real Study"},  # Authentic
                {"pmid": "12345678", "title": "Example Study"},  # Fabricated
                {"url": "https://pubmed.ncbi.nlm.nih.gov/34567890/"},  # Authentic (format)
                {"url": "https://example.com/fake"}  # Fabricated
            ]
        })

        assert result["summary"]["total_sources"] == 4
        # Note: Exact counts depend on URL accessibility checks
        assert result["summary"]["fabricated_count"] >= 2  # At least the 2 obvious fakes

    def test_multiple_issues_per_source(self):
        """Test source with multiple issues."""
        result = self.skill.execute({
            "sources": [
                {
                    "pmid": "12345678",  # Fabricated
                    "title": "Example Study",  # Placeholder
                    "authors": "Smith et al.",  # Placeholder
                    "url": "https://example.com/fake"  # Placeholder
                }
            ]
        })

        assert len(result["fabricated_sources"]) == 1
        assert len(result["issues"]) >= 3  # Multiple issues for this source

    def test_execute_with_validation(self):
        """Test execute_with_validation wrapper."""
        result = self.skill.execute_with_validation({
            "sources": [{"pmid": "34567890"}]
        })

        assert result.success
        assert result.skill_name == "source_authenticity_verification"
        assert result.execution_time_ms > 0
        assert "authentic_sources" in result.output

    def test_execute_with_validation_error(self):
        """Test execute_with_validation with invalid input."""
        result = self.skill.execute_with_validation({
            "sources": "invalid"  # Not a list
        })

        assert not result.success
        assert "Input validation failed" in result.error

    def test_get_schema(self):
        """Test get_schema method."""
        schema = self.skill.get_schema()

        assert schema["metadata"]["name"] == "source_authenticity_verification"
        assert schema["metadata"]["type"] == "deterministic"
        assert len(schema["inputs"]) > 0
        assert len(schema["outputs"]) > 0

    def test_convenience_function(self):
        """Test convenience function verify_source_authenticity."""
        result = verify_source_authenticity([
            {"pmid": "34567890"},
            {"pmid": "12345678"}
        ])

        assert "authentic_sources" in result
        assert "fabricated_sources" in result
        assert "issues" in result
        assert result["summary"]["total_sources"] == 2

    def test_empty_sources(self):
        """Test handling of empty sources list."""
        result = self.skill.execute({"sources": []})

        assert result["summary"]["total_sources"] == 0
        assert len(result["authentic_sources"]) == 0
        assert len(result["fabricated_sources"]) == 0
        assert len(result["issues"]) == 0

    def test_source_without_identifiers(self):
        """Test source with only title/authors, no PMID/URL."""
        result = self.skill.execute({
            "sources": [
                {
                    "title": "Real Research Study",
                    "authors": ["Johnson A", "Smith B", "Lee C"],
                    "year": 2023
                }
            ]
        })

        # Should pass - no PMIDs/URLs to validate
        assert len(result["authentic_sources"]) == 1
        assert len(result["issues"]) == 0

    def test_issue_structure(self):
        """Test that issues have correct structure."""
        result = self.skill.execute({
            "sources": [{"pmid": "12345678"}]
        })

        issue = result["issues"][0]
        required_fields = ["category", "severity", "description", "location", "suggested_fix"]

        for field in required_fields:
            assert field in issue, f"Issue missing required field: {field}"

        assert issue["severity"] in ["critical", "warning"]

    def test_location_field_accuracy(self):
        """Test that location field accurately identifies issue location."""
        result = self.skill.execute({
            "sources": [
                {"pmid": "12345678"},  # Source 0
                {"url": "https://example.com/fake"}  # Source 1
            ]
        })

        # Check location fields reference correct source indices
        pmid_issue = [i for i in result["issues"] if "pmid" in i["location"]][0]
        assert "sources[0]" in pmid_issue["location"]

        url_issue = [i for i in result["issues"] if "url" in i["location"]][0]
        assert "sources[1]" in url_issue["location"]

    def test_summary_accuracy(self):
        """Test that summary statistics are accurate."""
        sources = [
            {"pmid": "34567890"},  # Authentic
            {"pmid": "12345678"},  # Fabricated
            {"title": "Example Study"}  # Fabricated
        ]

        result = self.skill.execute({"sources": sources})

        summary = result["summary"]
        assert summary["total_sources"] == 3
        assert summary["authentic_count"] == len(result["authentic_sources"])
        assert summary["fabricated_count"] == len(result["fabricated_sources"])
        assert summary["total_issues"] == len(result["issues"])

    def test_verification_issues_field(self):
        """Test that fabricated sources include _verification_issues field."""
        result = self.skill.execute({
            "sources": [{"pmid": "12345678"}]
        })

        assert len(result["fabricated_sources"]) == 1
        fabricated = result["fabricated_sources"][0]
        assert "_verification_issues" in fabricated
        assert len(fabricated["_verification_issues"]) > 0

    def test_performance_metrics(self):
        """Test that execution tracks performance metrics."""
        sources = [{"pmid": f"{i:08d}"} for i in range(10)]
        result = self.skill.execute_with_validation({"sources": sources})

        assert result.metadata["execution_count"] == 1
        assert result.metadata["avg_execution_time_ms"] > 0

        # Execute again to update stats
        result2 = self.skill.execute_with_validation({"sources": sources})
        assert result2.metadata["execution_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=skills.audit.source_authenticity_verification", "--cov-report=html"])
