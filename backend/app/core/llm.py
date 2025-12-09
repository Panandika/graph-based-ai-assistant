from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import LLMProvider, get_settings

SUPPORTED_MODELS: dict[LLMProvider, list[str]] = {
    LLMProvider.OPENAI: ["gpt-4o-mini", "gpt-4o"],
    LLMProvider.ANTHROPIC: ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
}


def validate_model(provider: LLMProvider, model: str) -> bool:
    """Validate that the model is supported for the given provider."""
    return model in SUPPORTED_MODELS.get(provider, [])


class LLMFactory:
    """Factory for creating LLM instances based on configuration."""

    _instances: dict[str, BaseChatModel] = {}

    @classmethod
    def get_llm(
        cls,
        provider: LLMProvider | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        Get an LLM instance for the specified provider.

        Args:
            provider: LLM provider (openai, anthropic). Defaults to settings.
            model: Model name. Defaults to settings.default_model.
            **kwargs: Additional arguments passed to the LLM constructor.

        Returns:
            A configured LLM instance.
        """
        settings = get_settings()
        provider = provider or settings.llm_provider
        model = model or settings.default_model

        cache_key = f"{provider}:{model}"
        if cache_key in cls._instances and not kwargs:
            return cls._instances[cache_key]

        llm = cls._create_llm(provider, model, **kwargs)

        if not kwargs:
            cls._instances[cache_key] = llm

        return llm

    @classmethod
    def _create_llm(
        cls,
        provider: LLMProvider,
        model: str,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a new LLM instance."""
        settings = get_settings()

        if provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=model,
                api_key=SecretStr(settings.openai_api_key),
                **kwargs,
            )
        elif provider == LLMProvider.ANTHROPIC:
            return ChatAnthropic(
                model_name=model,
                api_key=SecretStr(settings.anthropic_api_key),
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the LLM instance cache."""
        cls._instances.clear()


def get_llm(
    provider: LLMProvider | None = None,
    model: str | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """Convenience function to get an LLM instance."""
    return LLMFactory.get_llm(provider=provider, model=model, **kwargs)
