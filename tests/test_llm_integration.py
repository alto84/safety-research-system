"""Integration tests for LLM integration."""
import pytest
import os
from core.llm_integration import (
    ThoughtPipeExecutor,
    LLMProvider,
    LLMProviderFactory,
    CLAUDEMDComplianceChecker
)


def test_provider_factory_mock():
    """Test that mock provider is always available."""
    providers = LLMProviderFactory.get_available_providers()
    assert LLMProvider.MOCK in providers


def test_thought_pipe_executor_initialization():
    """Test ThoughtPipeExecutor initialization."""
    executor = ThoughtPipeExecutor()
    assert executor is not None
    assert executor.compliance_checker is not None


def test_claudemd_compliance_checker():
    """Test CLAUDE.md compliance validation."""
    checker = CLAUDEMDComplianceChecker()
    
    # Test banned phrases
    output_with_banned = {
        "summary": "This shows exceptional performance",
        "score": 75
    }
    is_valid, violations = checker.validate_output(output_with_banned, {})
    assert not is_valid
    assert any("banned phrase" in v.lower() for v in violations)
    
    # Test score fabrication
    output_with_high_score = {
        "score": 95,
        "summary": "High score without validation"
    }
    is_valid, violations = checker.validate_output(output_with_high_score, {})
    assert not is_valid
    assert any("score" in v.lower() for v in violations)


def test_thought_pipe_with_mock():
    """Test thought pipe execution with mock provider."""
    executor = ThoughtPipeExecutor(provider_preference=[LLMProvider.MOCK])
    
    result = executor.execute_thought_pipe(
        prompt="Analyze evidence quality",
        context={
            "sources": [],
            "research_question": "test question",
            "total_sources": 0
        }
    )
    
    assert result is not None
    assert "confidence" in result or "evidence_quality" in result


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
def test_anthropic_integration():
    """Test real Anthropic API integration (if API key available)."""
    executor = ThoughtPipeExecutor(provider_preference=[LLMProvider.ANTHROPIC])
    
    # This will only run if ANTHROPIC_API_KEY is set
    result = executor.execute_thought_pipe(
        prompt="What is 2+2? Return JSON with 'answer' field.",
        context={"question": "2+2"}
    )
    
    assert result is not None
