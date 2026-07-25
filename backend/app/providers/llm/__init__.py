"""
LLM Provider Adapters

Protocol-based adapters for all supported LLM providers.
The factory creates the correct adapter based on provider_type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol, runtime_checkable


@dataclass
class Message:
    """Chat message."""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    finish_reason: str = ""
    raw_response: dict | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM provider adapters."""

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse: ...
    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]: ...
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: ...


class OpenAIAdapter:
    """OpenAI GPT adapter (GPT-4o, GPT-4, GPT-3.5-turbo)."""

    PRICING = {
        "gpt-4o": (0.005, 0.015),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0005, 0.0015),
    }

    def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs: Any):
        import openai
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            **kwargs,
        )
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            model=response.model,
            finish_reason=choice.finish_reason or "",
        )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_price, output_price = self.PRICING.get(self.model, (0.01, 0.03))
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)


class AnthropicAdapter:
    """Anthropic Claude adapter."""

    PRICING = {
        "claude-sonnet-4-20250514": (0.003, 0.015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
    }

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs: Any):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        # Separate system message
        system = ""
        user_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system,
            messages=user_messages,
        )
        return LLMResponse(
            content=response.content[0].text if response.content else "",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            model=response.model,
            finish_reason=response.stop_reason or "",
        )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        system = ""
        user_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system,
            messages=user_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_price, output_price = self.PRICING.get(self.model, (0.003, 0.015))
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)


class OllamaAdapter:
    """Ollama local model adapter."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434", **kwargs: Any):
        self.model = model
        self.base_url = base_url

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                },
                timeout=120.0,
            )
            data = response.json()
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                total_tokens=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        import httpx
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": True,
                },
                timeout=120.0,
            ) as response:
                import json
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0  # Local models are free


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------

class LLMProviderFactory:
    """Creates LLM provider adapter instances."""

    _ADAPTERS: dict[str, type] = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "ollama": OllamaAdapter,
    }

    @classmethod
    def create(cls, provider_type: str, **kwargs: Any) -> LLMProvider:
        """Create an LLM provider adapter by type."""
        adapter_class = cls._ADAPTERS.get(provider_type)
        if not adapter_class:
            raise ValueError(f"Unknown LLM provider: '{provider_type}'. Available: {list(cls._ADAPTERS.keys())}")
        return adapter_class(**kwargs)

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """Register a custom adapter."""
        cls._ADAPTERS[name] = adapter_class
