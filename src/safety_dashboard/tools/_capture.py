"""Side-channel ContextVar — same shape as EP02/EP03/EP04.

Currently unused inside the dashboard (no agent crew), but kept here
so a learner cloning EP05 has a working template for the
"tools-return-strings, also-write-to-contextvar" pattern.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_capture_buffer: ContextVar[list] = ContextVar("safety_dashboard_capture", default=[])


def start_capture() -> None:
    _capture_buffer.set([])


def take_capture() -> list[dict[str, Any]]:
    items = list(_capture_buffer.get())
    _capture_buffer.set([])
    return items


def capture(record: dict[str, Any]) -> None:
    buf = list(_capture_buffer.get())
    buf.append(record)
    _capture_buffer.set(buf)
