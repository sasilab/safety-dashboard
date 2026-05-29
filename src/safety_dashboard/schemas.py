"""Pydantic models for the EP05 dashboard contract."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthRulesConfig(BaseModel):
    diabetic: list[str] = Field(default_factory=list)
    high_bp: list[str] = Field(default_factory=list)
    nuts: list[str] = Field(default_factory=list)


class AttackRequest(BaseModel):
    attack_id: Optional[str] = None
    text: Optional[str] = None
    category: Optional[str] = None
    layers_enabled: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    on_topic: list[str] = Field(default_factory=list)
    health_rules: dict[str, list[str]] = Field(default_factory=dict)
    rejection_threshold: float = 0.30
    call_llm: bool = False


class AuditStep(BaseModel):
    layer: int
    action: str
    detail: dict
    label: str = ""


class AttackResponse(BaseModel):
    attack_id: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    payload: str
    expected_layer: Optional[int] = None
    result: str          # "blocked" | "sanitized" | "passed" | "override"
    caught_at_layer: Optional[int] = None
    matched_patterns: list[str] = Field(default_factory=list)
    safe_input: Optional[str] = None
    safe_output: Optional[str] = None
    fence_preview: Optional[str] = None
    swap_food: Optional[str] = None
    swap_reason: Optional[str] = None
    audit_trail: list[AuditStep] = Field(default_factory=list)
    layer_status: dict[str, str] = Field(default_factory=dict)
    llm_used: bool = False
    llm_response: Optional[str] = None
    details: str = ""


class Scoreboard(BaseModel):
    total: int = 0
    blocked: int = 0
    sanitized: int = 0
    passed: int = 0
    override: int = 0
    defense_rate: float = 0.0
    per_category: dict[str, dict[str, int]] = Field(default_factory=dict)
    per_layer: dict[str, int] = Field(default_factory=dict)
    weakest_layer: Optional[int] = None


class SettingsBody(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    layers_enabled: Optional[list[int]] = None
    on_topic: Optional[list[str]] = None
    health_rules: Optional[dict[str, list[str]]] = None
    rejection_threshold: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    llm: Optional[str] = None
    provider: Optional[str] = None
    source: Optional[str] = None
    episode: str
    layers_enabled: list[int]
    attack_count: int
