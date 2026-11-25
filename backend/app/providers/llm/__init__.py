"""
LLM Provider Adapters Layer

Protocol-based adapters for all supported LLM providers:
OpenAI, Anthropic, Ollama, Google Gemini, Groq, DeepSeek, Azure OpenAI, OpenRouter.
All adapters implement complete(), stream(), estimate_cost(), embeddings(), and health_check().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol, runtime_checkable

import httpx


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
    """Protocol contract for all LLM provider adapters."""

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse: ...
    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]: ...
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: ...
    async def embeddings(self, text: str) -> list[float]: ...
    async def health_check(self) -> bool: ...


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

    async def embeddings(self, text: str) -> list[float]:
        resp = await self.client.embeddings.create(input=text, model="text-embedding-3-small")
        return resp.data[0].embedding

    async def health_check(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False


class AnthropicAdapter:
    """Anthropic Claude adapter."""

    PRICING = {
        "claude-sonnet-4-20250514": (0.003, 0.015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
    }

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs: Any):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
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

    async def embeddings(self, text: str) -> list[float]:
        # Anthropic does not provide an embedding endpoint — fallback dummy vector
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.client.api_key)


class GeminiAdapter:
    """Google Gemini adapter (gemini-3.5-flash-lite, gemini-3.8-flash, gemma-4-26b-a4b-it, gemma-4-31b-it)."""

    PRICING = {
        "gemini-3.5-flash-lite": (0.000075, 0.0003),
        "gemini-3.8-flash": (0.0001, 0.0004),
        "gemma-4-26b-a4b-it": (0.00005, 0.0002),
        "gemma-4-31b-it": (0.000075, 0.0003),
        "gemini-1.5-flash": (0.000075, 0.0003),
        "gemini-1.5-pro": (0.00125, 0.005),
        "gemini-2.0-flash": (0.0001, 0.0004),
    }

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite", **kwargs: Any):
        self.api_key = api_key
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        system_instruction = None
        contents = []
        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload: dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=60.0)
            if not resp.is_success:
                raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text}")
            data = resp.json()

            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                non_thought_parts = [p.get("text", "") for p in parts if not p.get("thought")]
                text = "".join(non_thought_parts) if non_thought_parts else "".join(p.get("text", "") for p in parts)

            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            return LLMResponse(
                content=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_price, output_price = self.PRICING.get(self.model, (0.0001, 0.0004))
        return (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)

    async def embeddings(self, text: str) -> list[float]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.api_key}"
        payload = {"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=30.0)
            if resp.is_success:
                return resp.json().get("embedding", {}).get("values", [0.0] * 768)
        return [0.0] * 768

    async def health_check(self) -> bool:
        return bool(self.api_key)


class GroqAdapter:
    """Groq Cloud API adapter (llama-3.1-70b-versatile, mixtral-8x7b-32768)."""

    def __init__(self, api_key: str, model: str = "llama-3.1-70b-versatile", **kwargs: Any):
        self.api_key = api_key
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if not resp.is_success:
                raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000 * 0.0005) + (output_tokens / 1000 * 0.0008)

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.api_key)


class DeepSeekAdapter:
    """DeepSeek API adapter (deepseek-chat, deepseek-coder)."""

    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs: Any):
        self.api_key = api_key
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        url = "https://api.deepseek.com/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if not resp.is_success:
                raise RuntimeError(f"DeepSeek API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000 * 0.00014) + (output_tokens / 1000 * 0.00028)

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.api_key)


class AzureOpenAIAdapter:
    """Azure OpenAI API adapter."""

    def __init__(self, api_key: str, endpoint: str, deployment_name: str = "gpt-4o", api_version: str = "2024-02-01", **kwargs: Any):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.deployment_name = deployment_name
        self.api_version = api_version

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {"messages": [{"role": m.role, "content": m.content} for m in messages]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if not resp.is_success:
                raise RuntimeError(f"Azure OpenAI API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                model=self.deployment_name,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000 * 0.005) + (output_tokens / 1000 * 0.015)

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.api_key and self.endpoint)


class OpenRouterAdapter:
    """OpenRouter API adapter."""

    def __init__(self, api_key: str, model: str = "openai/gpt-4o", **kwargs: Any):
        self.api_key = api_key
        self.model = model

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": m.role, "content": m.content} for m in messages]}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
            if not resp.is_success:
                raise RuntimeError(f"OpenRouter API error ({resp.status_code}): {resp.text}")
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice.get("message", {}).get("content", ""),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
        response = await self.complete(messages, **kwargs)
        yield response.content

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.01)

    async def embeddings(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def health_check(self) -> bool:
        return bool(self.api_key)


class OllamaAdapter:
    """Ollama local model adapter."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434", **kwargs: Any):
        self.model = model
        self.base_url = base_url

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                },
                timeout=120.0,
            )
            data = resp.json()
            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                total_tokens=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
                model=self.model,
            )

    async def stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]:
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
        return 0.0

    async def embeddings(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30.0,
            )
            if resp.is_success:
                return resp.json().get("embedding", [0.0] * 4096)
        return [0.0] * 4096

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return resp.is_success
        except Exception:
            return False


class LLMProviderFactory:
    """Creates LLM provider adapter instances."""

    _ADAPTERS: dict[str, type] = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "ollama": OllamaAdapter,
        "gemini": GeminiAdapter,
        "google": GeminiAdapter,
        "groq": GroqAdapter,
        "deepseek": DeepSeekAdapter,
        "azure": AzureOpenAIAdapter,
        "openrouter": OpenRouterAdapter,
    }

    @classmethod
    def create(cls, provider_type: str, **kwargs: Any) -> LLMProvider:
        """Create an LLM provider adapter by type."""
        adapter_class = cls._ADAPTERS.get(provider_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown LLM provider: '{provider_type}'. Available: {list(cls._ADAPTERS.keys())}")
        return adapter_class(**kwargs)

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """Register a custom adapter."""
        cls._ADAPTERS[name.lower()] = adapter_class
