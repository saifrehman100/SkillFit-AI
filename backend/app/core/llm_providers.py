"""
Multi-LLM provider system with support for Claude, OpenAI, Gemini, and OpenAI-compatible APIs.
Implements a modular design pattern for easy addition of new LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from enum import Enum

from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENAI_COMPATIBLE = "openai_compatible"


class LLMResponse:
    """Standardized response from LLM providers."""

    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        tokens_used: Optional[int] = None,
        cost_estimate: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost_estimate = cost_estimate
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "metadata": self.metadata
        }


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.provider_name = self.__class__.__name__

    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model name for this provider."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """Estimate the cost for the given number of tokens."""
        pass


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=self.api_key or settings.anthropic_api_key)

    def get_default_model(self) -> str:
        return "claude-sonnet-4-20250514"  # Claude Sonnet 4.5

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate response using Claude API."""
        try:
            logger.info("Generating response with Claude", model=self.model)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            cost = self.estimate_cost(total_tokens)

            logger.info(
                "Claude response generated",
                tokens=total_tokens,
                cost=cost
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=LLMProvider.CLAUDE.value,
                tokens_used=total_tokens,
                cost_estimate=cost,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )

        except Exception as e:
            logger.error("Claude API error", error=str(e))
            raise

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on Claude pricing (approximate)."""
        # Claude 3.5 Sonnet: $3/$15 per million tokens (input/output)
        # Simplified average: ~$9 per million tokens
        return (tokens / 1_000_000) * 9.0


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=self.api_key or settings.openai_api_key)

    def get_default_model(self) -> str:
        return "gpt-5.2"  # GPT-5.2 - best for coding and agentic tasks

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            logger.info("Generating response with OpenAI", model=self.model)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens

            cost = self.estimate_cost(total_tokens)

            logger.info(
                "OpenAI response generated",
                tokens=total_tokens,
                cost=cost
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=LLMProvider.OPENAI.value,
                tokens_used=total_tokens,
                cost_estimate=cost,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            )

        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on GPT-4 pricing (approximate)."""
        # GPT-4 Turbo: ~$10/$30 per million tokens (input/output)
        # Simplified average: ~$20 per million tokens
        return (tokens / 1_000_000) * 20.0


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model)
        genai.configure(api_key=self.api_key or settings.google_api_key)
        self.client = genai.GenerativeModel(self.model)

    def get_default_model(self) -> str:
        return "gemini-2.5-flash"  # Gemini 2.5 Flash - best price-performance

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate response using Gemini API."""
        try:
            logger.info("Generating response with Gemini", model=self.model)

            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            response = self.client.generate_content(
                prompt,
                generation_config=generation_config,
                **kwargs
            )

            content = response.text
            # Gemini doesn't provide token counts directly
            tokens_estimate = len(prompt.split()) + len(content.split())

            cost = self.estimate_cost(tokens_estimate)

            logger.info(
                "Gemini response generated",
                tokens_estimate=tokens_estimate,
                cost=cost
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=LLMProvider.GEMINI.value,
                tokens_used=tokens_estimate,
                cost_estimate=cost,
                metadata={"tokens_estimated": True}
            )

        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            raise

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on Gemini pricing (approximate)."""
        # Gemini Pro: Free tier available, paid ~$0.5/$1.5 per million
        # Simplified average: ~$1 per million tokens
        return (tokens / 1_000_000) * 1.0


class OpenAICompatibleClient(BaseLLMClient):
    """Client for OpenAI-compatible APIs (e.g., local models, other providers)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        super().__init__(api_key, model)
        self.base_url = base_url or settings.openai_compatible_base_url
        self.client = OpenAI(
            api_key=self.api_key or settings.openai_compatible_api_key or "dummy-key",
            base_url=self.base_url
        )

    def get_default_model(self) -> str:
        return "gpt-3.5-turbo"

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate response using OpenAI-compatible API."""
        try:
            logger.info(
                "Generating response with OpenAI-compatible API",
                model=self.model,
                base_url=self.base_url
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            total_tokens = getattr(response.usage, "total_tokens", 0) if response.usage else 0

            cost = self.estimate_cost(total_tokens)

            logger.info(
                "OpenAI-compatible response generated",
                tokens=total_tokens,
                cost=cost
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=LLMProvider.OPENAI_COMPATIBLE.value,
                tokens_used=total_tokens,
                cost_estimate=cost,
                metadata={"base_url": self.base_url}
            )

        except Exception as e:
            logger.error("OpenAI-compatible API error", error=str(e))
            raise

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost (often $0 for local or custom deployments)."""
        return 0.0


class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(
        provider: str | LLMProvider,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> BaseLLMClient:
        """Create an LLM client for the specified provider."""

        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider.lower())
            except ValueError:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        logger.info("Creating LLM client", provider=provider.value, model=model)

        clients = {
            LLMProvider.CLAUDE: ClaudeClient,
            LLMProvider.OPENAI: OpenAIClient,
            LLMProvider.GEMINI: GeminiClient,
            LLMProvider.OPENAI_COMPATIBLE: OpenAICompatibleClient,
        }

        client_class = clients.get(provider)
        if not client_class:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        return client_class(api_key=api_key, model=model, **kwargs)
