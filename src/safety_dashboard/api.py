"""FastAPI surface — EP05 attack dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agentverse_safety import configure_logging, drain_memory_log

from . import __episode__
from .attacks import CATEGORIES, list_attacks_for_api
from .handlers import attack_count, run_attack
from .llm import (
    clear_runtime_overrides, detect_provider, set_runtime_overrides,
    no_provider_message,
)
from .preferences import read as read_prefs
from .preferences import write_partial as write_prefs
from .schemas import (
    AttackRequest, AttackResponse, HealthResponse, Scoreboard, SettingsBody,
)
from .scoreboard import get_scoreboard

_EPISODE_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _EPISODE_ROOT / "data"
_FRONTEND_DIR = _EPISODE_ROOT / "frontend"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configure JSONL safety log for harness-internal events.
configure_logging(_DATA_DIR)


app = FastAPI(title="AgentVerse Safety Harness — EP05")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    prefs = await read_prefs()
    set_runtime_overrides(prefs)
    choice = detect_provider()
    try:
        return HealthResponse(
            status="ok",
            llm=choice.model if choice else None,
            provider=choice.provider if choice else None,
            source=choice.source if choice else None,
            episode=__episode__,
            layers_enabled=prefs.get("layers_enabled", [1, 2, 3, 4, 5]),
            attack_count=attack_count(),
        )
    finally:
        clear_runtime_overrides()


@app.get("/api/attacks")
async def list_attacks() -> dict:
    return {"categories": CATEGORIES, "attacks": list_attacks_for_api()}


@app.post("/api/attack", response_model=AttackResponse)
async def attack(req: AttackRequest) -> AttackResponse:
    prefs = await read_prefs()
    if req.call_llm:
        set_runtime_overrides(prefs)
    if not req.on_topic:
        req.on_topic = prefs.get("on_topic", [])
    if not req.health_rules:
        req.health_rules = prefs.get("health_rules", {})
    if not req.layers_enabled:
        req.layers_enabled = prefs.get("layers_enabled", [1, 2, 3, 4, 5])
    try:
        return run_attack(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if req.call_llm:
            clear_runtime_overrides()


@app.post("/api/attack/custom", response_model=AttackResponse)
async def attack_custom(req: AttackRequest) -> AttackResponse:
    # Same handler; the route exists so the frontend can use a
    # distinct path in network logs ("this was a freeform attack").
    if not req.text:
        raise HTTPException(status_code=400, detail="`text` is required for /api/attack/custom")
    req.attack_id = None
    return await attack(req)


@app.get("/api/score", response_model=Scoreboard)
async def score() -> Scoreboard:
    return Scoreboard(**get_scoreboard().to_dict())


@app.post("/api/score/reset")
async def score_reset() -> dict:
    get_scoreboard().reset()
    return {"ok": True}


@app.get("/api/events")
async def events(limit: int = 50) -> dict:
    """Latest harness audit events (in-memory ring buffer)."""
    return {"events": drain_memory_log(min(max(limit, 1), 500))}


@app.get("/api/settings")
async def settings_get() -> dict:
    prefs = await read_prefs()
    # NEVER return the api key — even on a local app, the value
    # leaking into a network log is undesirable.
    safe = {k: v for k, v in prefs.items() if k != "api_key"}
    safe["api_key_set"] = bool(prefs.get("api_key"))
    return safe


@app.post("/api/settings")
async def settings_post(body: SettingsBody) -> dict:
    patch = body.model_dump(exclude_none=True)
    updated = await write_prefs(patch)
    safe = {k: v for k, v in updated.items() if k != "api_key"}
    safe["api_key_set"] = bool(updated.get("api_key"))
    return safe


@app.get("/api/llm-status")
async def llm_status() -> dict:
    prefs = await read_prefs()
    set_runtime_overrides(prefs)
    try:
        choice = detect_provider()
        if choice is None:
            return {"available": False, "hint": no_provider_message()}
        return {"available": True, "provider": choice.provider,
                "model": choice.model, "source": choice.source}
    finally:
        clear_runtime_overrides()


# --- Frontend mount (standalone PWA in frontend/) ---

if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")

    @app.get("/")
    async def root() -> FileResponse:
        return FileResponse(_FRONTEND_DIR / "index.html")

    @app.get("/{path:path}")
    async def spa_passthrough(path: str):
        # Serve a real file when present (icon.svg, manifest.json, sw.js,
        # etc.); otherwise fall back to index.html so the SPA handles routing.
        target = _FRONTEND_DIR / path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(_FRONTEND_DIR / "index.html")
else:  # pragma: no cover - only when running before the frontend exists
    @app.get("/")
    async def root_empty() -> JSONResponse:
        return JSONResponse({"status": "ok", "note": "frontend not built"})
