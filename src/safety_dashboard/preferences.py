"""JSON-file preferences (single-user local app) — slimmed EP02 pattern."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

_EPISODE_ROOT = Path(__file__).resolve().parents[2]
_PREFS_FILE = _EPISODE_ROOT / "data" / "user_preferences.json"
_PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)

_LOCK = asyncio.Lock()


DEFAULT_PREFS: dict[str, Any] = {
    "provider": "",
    "model": "",
    "api_key": "",
    "base_url": "",
    "layers_enabled": [1, 2, 3, 4, 5],
    "on_topic": ["food", "diet", "nutrition", "weather", "AQI", "health"],
    "health_rules": {
        "diabetic": ["sugar", "sweet", "jaggery", "honey", "syrup", "kheer", "halwa"],
        "high_bp": ["salt", "pickle", "papad", "instant noodle"],
        "nuts": ["almond", "cashew", "peanut", "walnut", "pistachio"],
    },
    "rejection_threshold": 0.30,
}


def _read_raw() -> dict[str, Any]:
    if not _PREFS_FILE.exists():
        return {}
    try:
        with open(_PREFS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


async def read() -> dict[str, Any]:
    async with _LOCK:
        merged = {**DEFAULT_PREFS, **_read_raw()}
        return merged


async def write_partial(patch: dict[str, Any]) -> dict[str, Any]:
    async with _LOCK:
        current = {**DEFAULT_PREFS, **_read_raw()}
        for k, v in patch.items():
            if v is None:
                continue
            current[k] = v
        # atomic write
        fd, tmp = tempfile.mkstemp(dir=str(_PREFS_FILE.parent), suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
            os.replace(tmp, _PREFS_FILE)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return current


def read_sync() -> dict[str, Any]:
    return {**DEFAULT_PREFS, **_read_raw()}
