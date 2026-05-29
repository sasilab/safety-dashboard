"""Dev launcher — `uv run safety-dashboard` boots the server on :8000.

Reads `PORT` from env for one-line port overrides.
"""

from __future__ import annotations

import os
import sys

import uvicorn


def run_api() -> None:
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(
        "safety_dashboard.api:app",
        host=host,
        port=port,
        reload=False,
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )


def smoke() -> None:
    """Smoke-test the harness without booting the server."""
    from .attacks import ATTACKS
    from .handlers import run_attack
    from .schemas import AttackRequest

    ok, blocked, sanitized, passed, override = 0, 0, 0, 0, 0
    for spec in ATTACKS:
        req = AttackRequest(
            attack_id=spec.id, layers_enabled=[1, 2, 3, 4, 5],
            on_topic=["food", "diet", "nutrition"],
            health_rules={"diabetic": ["sugar", "honey"]},
        )
        res = run_attack(req)
        ok += 1
        if res.result == "blocked":
            blocked += 1
        elif res.result == "sanitized":
            sanitized += 1
        elif res.result == "override":
            override += 1
        else:
            passed += 1
        print(f"[{res.result.upper():>9}] {spec.id:<26} → "
              f"caught_at={res.caught_at_layer} expected={spec.expected_layer}")
    print(f"\n{ok} attacks: {blocked} blocked, {sanitized} sanitized, "
          f"{override} override, {passed} passed.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        smoke()
    else:
        run_api()
