"""
SheldonOS — LLM Provider Abstraction Layer v2.0
A provider-agnostic interface for all LLM calls across SheldonOS.

FIXED v2.0: Previously every agent was hardcoded to Anthropic Claude with no
abstraction layer. This module provides:
  - A unified LLMClient interface that works with any provider
  - Runtime provider selection via LLM_PROVIDER env var
  - Per-agent model override via agent definition
  - Support for: Anthropic, OpenAI, Google Gemini, and any OpenAI-compatible endpoint
  - User-configurable API keys — no hardcoded credentials
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sheldon.llm")


@dataclass
class LLMMessage:
    """A single message in an LLM conversation."""
    role: str    # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"
    raw: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """
    Configuration for a single LLM call.
    All fields have sensible defaults; override per-agent as needed.
    """
    model: str = ""                  # If empty, uses provider default
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = ""
    provider: str = ""               # If empty, uses LLM_PROVIDER env var


class LLMProvider:
    """
    Provider-agnostic LLM client for SheldonOS.

    Configuration via environment variables:
      LLM_PROVIDER        = anthropic | openai | gemini | openai_compatible
      ANTHROPIC_API_KEY   = sk-ant-...
      OPENAI_API_KEY      = sk-...
      GEMINI_API_KEY      = AIza...
      LLM_BASE_URL        = https://custom-endpoint/v1  (for openai_compatible)
      LLM_DEFAULT_MODEL   = claude-3-5-sonnet-20241022  (optional override)

    Usage:
        client = LLMProvider()
        response = await client.complete(
            messages=[LLMMessage(role="user", content="Hello")],
            config=LLMConfig(model="claude-3-5-sonnet-20241022"),
        )
    """

    # Provider defaults
    PROVIDER_DEFAULTS = {
        "anthropic": "claude-3-5-sonnet-20241022",
        "openai":    "gpt-4o",
        "gemini":    "gemini-2.0-flash",
        "openai_compatible": "gpt-4o",
    }

    def __init__(self):
        self.default_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        self.default_model    = os.getenv("LLM_DEFAULT_MODEL", "")
        self._validate_config()

    def _validate_config(self):
        """Warn if required API keys are missing for the configured provider."""
        key_map = {
            "anthropic":         "ANTHROPIC_API_KEY",
            "openai":            "OPENAI_API_KEY",
            "gemini":            "GEMINI_API_KEY",
            "openai_compatible": "OPENAI_API_KEY",
        }
        required_key = key_map.get(self.default_provider)
        if required_key and not os.getenv(required_key):
            logger.warning(
                f"[LLM] {required_key} not set for provider '{self.default_provider}'. "
                f"LLM calls will fail until this is configured."
            )

    def _resolve_model(self, config: LLMConfig) -> str:
        """Resolve the model to use, with fallback chain."""
        if config.model:
            return config.model
        if self.default_model:
            return self.default_model
        provider = config.provider or self.default_provider
        return self.PROVIDER_DEFAULTS.get(provider, "gpt-4o")

    async def complete(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Send a completion request to the configured LLM provider.
        Returns a standardized LLMResponse regardless of provider.
        """
        if config is None:
            config = LLMConfig()

        provider = (config.provider or self.default_provider).lower()
        model    = self._resolve_model(config)

        logger.debug(f"[LLM] {provider}/{model} | {len(messages)} messages")

        if provider == "anthropic":
            return await self._complete_anthropic(messages, config, model)
        elif provider in ("openai", "openai_compatible"):
            return await self._complete_openai(messages, config, model)
        elif provider == "gemini":
            return await self._complete_gemini(messages, config, model)
        else:
            raise ValueError(
                f"Unknown LLM provider: '{provider}'. "
                f"Set LLM_PROVIDER to one of: anthropic, openai, gemini, openai_compatible"
            )

    async def _complete_anthropic(
        self, messages: List[LLMMessage], config: LLMConfig, model: str
    ) -> LLMResponse:
        """Call Anthropic Claude API."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        import httpx
        # Separate system message from conversation
        system = config.system_prompt or next(
            (m.content for m in messages if m.role == "system"), ""
        )
        conv_messages = [
            {"role": m.role, "content": m.content}
            for m in messages if m.role != "system"
        ]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "system": system,
                    "messages": conv_messages,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

        return LLMResponse(
            content=data["content"][0]["text"],
            model=data.get("model", model),
            provider="anthropic",
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
            stop_reason=data.get("stop_reason", "end_turn"),
            raw=data,
        )

    async def _complete_openai(
        self, messages: List[LLMMessage], config: LLMConfig, model: str
    ) -> LLMResponse:
        """Call OpenAI (or any OpenAI-compatible) API."""
        api_key  = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        import httpx
        oai_messages = []
        if config.system_prompt:
            oai_messages.append({"role": "system", "content": config.system_prompt})
        oai_messages.extend({"role": m.role, "content": m.content} for m in messages)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": oai_messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model),
            provider="openai",
            input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            output_tokens=data.get("usage", {}).get("completion_tokens", 0),
            stop_reason=choice.get("finish_reason", "stop"),
            raw=data,
        )

    async def _complete_gemini(
        self, messages: List[LLMMessage], config: LLMConfig, model: str
    ) -> LLMResponse:
        """Call Google Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")

        import httpx
        # Gemini uses "parts" format
        contents = [
            {"role": "user" if m.role == "user" else "model",
             "parts": [{"text": m.content}]}
            for m in messages if m.role != "system"
        ]
        system_instruction = config.system_prompt or next(
            (m.content for m in messages if m.role == "system"), None
        )

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": config.max_tokens,
                "temperature": config.temperature,
            },
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": api_key},
                json=body,
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()

        candidate = data["candidates"][0]
        content   = candidate["content"]["parts"][0]["text"]
        usage     = data.get("usageMetadata", {})

        return LLMResponse(
            content=content,
            model=model,
            provider="gemini",
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            stop_reason=candidate.get("finishReason", "STOP"),
            raw=data,
        )


# ─── Module-level singleton ───────────────────────────────────────────────────
_default_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Return the module-level LLMProvider singleton."""
    global _default_provider
    if _default_provider is None:
        _default_provider = LLMProvider()
    return _default_provider
