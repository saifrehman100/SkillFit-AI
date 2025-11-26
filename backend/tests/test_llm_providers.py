"""
Tests for LLM provider system.
"""
import pytest

from app.core.llm_providers import LLMFactory, LLMProvider, ClaudeClient, OpenAIClient


def test_llm_factory_create_claude():
    """Test creating Claude client via factory."""
    client = LLMFactory.create_client(
        provider=LLMProvider.CLAUDE,
        api_key="test-key"
    )

    assert isinstance(client, ClaudeClient)
    assert client.api_key == "test-key"


def test_llm_factory_create_openai():
    """Test creating OpenAI client via factory."""
    client = LLMFactory.create_client(
        provider=LLMProvider.OPENAI,
        api_key="test-key"
    )

    assert isinstance(client, OpenAIClient)
    assert client.api_key == "test-key"


def test_llm_factory_invalid_provider():
    """Test that invalid provider raises error."""
    with pytest.raises(ValueError) as exc:
        LLMFactory.create_client(
            provider="invalid_provider",
            api_key="test-key"
        )

    assert "Unsupported LLM provider" in str(exc.value)


def test_claude_default_model():
    """Test Claude default model."""
    client = ClaudeClient(api_key="test-key")
    assert client.get_default_model() == "claude-3-5-sonnet-20241022"


def test_openai_default_model():
    """Test OpenAI default model."""
    client = OpenAIClient(api_key="test-key")
    assert client.get_default_model() == "gpt-4-turbo-preview"


def test_claude_cost_estimation():
    """Test Claude cost estimation."""
    client = ClaudeClient(api_key="test-key")
    cost = client.estimate_cost(1_000_000)

    assert cost == 9.0  # $9 per million tokens


def test_openai_cost_estimation():
    """Test OpenAI cost estimation."""
    client = OpenAIClient(api_key="test-key")
    cost = client.estimate_cost(1_000_000)

    assert cost == 20.0  # $20 per million tokens
