"""BYOK LLM auto-detect — port of EP04's `llm.py`.

Only used by the dashboard when `call_llm=True`. The harness itself
doesn't need an LLM; calling a real model lets us demonstrate
Layer 4 (output sanitiser) on a genuine response.

Auto-detect order matches EP04:
  GROQ → GEMINI → SARVAM → OPENAI → ANTHROPIC → local Ollama
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

try:
    import litellm  # type: ignore
    _LITELLM_OK = True
except ImportError:  # pragma: no cover - litellm is optional
    litellm = None  # type: ignore
    _LITELLM_OK = False

try:
    import requests  # type: ignore
    _REQUESTS_OK = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS_OK = False

SARVAM_API_BASE = "https://api.sarvam.ai/v1"

DEFAULTS = {
    "groq": "groq/llama-3.3-70b-versatile",
    "gemini": "gemini/gemini-2.5-flash",
    "sarvam": "openai/sarvam-m",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-sonnet-20241022",
    "ollama": "ollama/llama3.2",
}

OLLAMA_DEFAULT_URL = "http://localhost:11434"
_runtime_overrides: ContextVar[dict] = ContextVar("llm_overrides", default={})


@dataclass
class ProviderChoice:
    provider: str
    model: str
    source: str


def set_runtime_overrides(prefs: dict) -> None:
    _runtime_overrides.set({
        "provider": (prefs.get("provider") or "").strip(),
        "model": (prefs.get("model") or "").strip(),
        "api_key": (prefs.get("api_key") or "").strip(),
        "base_url": (prefs.get("base_url") or "").strip(),
    })


def clear_runtime_overrides() -> None:
    _runtime_overrides.set({})


def _ollama_running() -> bool:
    if not _REQUESTS_OK:
        return False
    url = os.getenv("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL)
    try:
        return requests.get(url, timeout=1).ok
    except Exception:
        return False


def _normalise_model_string(provider: str, model: str) -> str:
    if not model:
        return DEFAULTS.get(provider, "")
    if "/" in model:
        return model
    if provider == "sarvam":
        return f"openai/{model}"
    if provider in ("openai", "claude"):
        return model
    return f"{provider}/{model}"


def _resolve_base_url(provider: str, base_url: str) -> str:
    if base_url:
        return base_url
    if provider == "sarvam":
        return SARVAM_API_BASE
    return ""


def detect_provider() -> Optional[ProviderChoice]:
    overrides = _runtime_overrides.get()
    if overrides.get("api_key") and overrides.get("provider"):
        return ProviderChoice(
            provider=overrides["provider"],
            model=_normalise_model_string(overrides["provider"], overrides["model"]),
            source="user settings",
        )
    explicit = os.getenv("MODEL")
    if explicit:
        provider = explicit.split("/", 1)[0] if "/" in explicit else "openai"
        return ProviderChoice(provider=provider, model=explicit, source="MODEL env var")
    if os.getenv("GROQ_API_KEY"):
        return ProviderChoice("groq", DEFAULTS["groq"], "GROQ_API_KEY")
    if os.getenv("GEMINI_API_KEY"):
        return ProviderChoice("gemini", DEFAULTS["gemini"], "GEMINI_API_KEY")
    if os.getenv("SARVAM_API_KEY"):
        return ProviderChoice("sarvam", DEFAULTS["sarvam"], "SARVAM_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        return ProviderChoice("openai", DEFAULTS["openai"], "OPENAI_API_KEY")
    if os.getenv("ANTHROPIC_API_KEY"):
        return ProviderChoice("claude", DEFAULTS["claude"], "ANTHROPIC_API_KEY")
    if os.getenv("OLLAMA_BASE_URL") or _ollama_running():
        model = os.getenv("OLLAMA_MODEL", DEFAULTS["ollama"])
        return ProviderChoice("ollama", model, "local Ollama server")
    return None


def llm_call(messages: list, temperature: float = 0.4) -> str:
    if not _LITELLM_OK:
        raise RuntimeError("litellm not installed — `uv add litellm` to enable BYOK LLM calls.")
    choice = detect_provider()
    if choice is None:
        raise RuntimeError(no_provider_message())
    kwargs: dict = {
        "model": choice.model,
        "temperature": temperature,
        "messages": messages,
    }
    overrides = _runtime_overrides.get()
    if choice.source == "user settings":
        if overrides.get("api_key"):
            kwargs["api_key"] = overrides["api_key"]
        base = _resolve_base_url(overrides.get("provider", ""),
                                 overrides.get("base_url", ""))
        if base:
            kwargs["api_base"] = base
    else:
        if choice.provider == "sarvam":
            kwargs["api_base"] = SARVAM_API_BASE
            if os.getenv("SARVAM_API_KEY"):
                kwargs["api_key"] = os.getenv("SARVAM_API_KEY")
    resp = litellm.completion(**kwargs)
    return str(resp.choices[0].message.content or "").strip()


def no_provider_message() -> str:
    return (
        "No LLM provider detected. Either:\n"
        "  - Open Settings and paste a Groq / Gemini / Sarvam / OpenAI / Claude key, OR\n"
        "  - Run Ollama locally, OR set GROQ_API_KEY in .env.\n"
        "Free Groq key: https://console.groq.com/keys\n"
    )


def llm_available() -> bool:
    return _LITELLM_OK and detect_provider() is not None
