# EP05 — Architecture

```mermaid
flowchart TB
    user([User payload]) --> L1[Layer 1<br/>Input Gate]
    L1 -- blocked --> blocked([🔴 BLOCKED])
    L1 -- sanitised --> safe[safe_input]
    L1 -- passed --> safe

    safe --> L5{Layer 5<br/>Hardcoded}
    L5 -- override --> override([🟣 OVERRIDE])
    L5 -- continue --> L2[Layer 2<br/>Retrieval Gate]

    chunks([Retrieved chunks]) -.-> L2
    L2 -- batch flagged --> flagged([🔴 BATCH FLAGGED])
    L2 -- filtered --> L3[Layer 3<br/>Reasoning Fence]

    L3 --> llm[LLM]
    llm --> L4[Layer 4<br/>Output Sanitizer]
    L4 -- sanitised --> answer([🟡 SANITIZED answer])
    L4 -- passed --> green([🟢 PASSED answer])
```

## Request flow per attack

```mermaid
sequenceDiagram
    participant Frontend
    participant API as FastAPI
    participant H as SafetyHarness
    participant LLM

    Frontend->>API: POST /api/attack {attack_id, layers_enabled}
    API->>H: build harness(prefs)
    H->>H: Layer 1 — check_input(payload)
    alt blocked
        H-->>API: blocked + audit
    else sanitised / passed
        H->>H: Layer 5 — check_hardcoded(food=safe)
        H->>H: Layer 3 — fence_prompt(safe)
        opt call_llm=true
            API->>LLM: completion(safe)
            LLM-->>API: raw_response
            API->>H: Layer 4 — check_output(raw)
        end
    end
    API-->>Frontend: AttackResponse {result, caught_at_layer, audit_trail, layer_status}
    Frontend->>API: GET /api/score
```

## Two-package layout

```
multi-agent/
├── agentverse_safety/         ← reusable library
│   └── src/agentverse_safety/
│       ├── layer1_input.py
│       ├── layer2_retrieval.py
│       ├── layer3_fence.py
│       ├── layer4_output.py
│       ├── layer5_hardcoded.py
│       ├── harness.py          ← SafetyHarness
│       ├── patterns.py         ← all regex consolidated
│       └── logger.py
└── safety_dashboard/          ← EP05 web app
    ├── src/safety_dashboard/
    │   ├── api.py
    │   ├── handlers.py
    │   ├── attacks.py
    │   ├── schemas.py
    │   ├── scoreboard.py
    │   └── llm.py
    └── frontend/              ← standalone vanilla-JS PWA
```

`safety_dashboard` depends on `agentverse_safety` via `[tool.uv.sources]`
in `pyproject.toml`. Edits to either project propagate without
reinstalling.

## What about the shared frontend?

EP01-EP04 share `multi-agent/agentverse-frontend/`. EP05 is **NOT**
in that PWA — touching it risks breaking the four shipped episodes
(DO NOT TOUCH rule from the project brief). EP05 ships its own
standalone `frontend/` so the shared PWA stays frozen.
