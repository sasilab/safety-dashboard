# EP05 — AgentVerse Safety Harness

Teach the **5-layer defence model** for AI agents by attacking your own
agent live. Two things in one episode:

1. **`agentverse_safety/`** — a reusable Python library every agent
   builder can wrap their agent with. Five layers, one harness.
2. **`safety_dashboard/`** (this folder) — a FastAPI + vanilla-JS
   dashboard that fires pre-written attacks at the harness so the
   audience SEES each layer catch each attack in real time.

## The 5-layer model

| # | Layer | What it does |
|---|---|---|
| 1 | **Input Gate** | Blocks unsafe / off-topic; sanitises injection phrases inline |
| 2 | **Retrieval Gate** | Drops poisoned RAG / Mem0 chunks before they enter the prompt |
| 3 | **Reasoning Fence** | Wraps context as `DATA, not INSTRUCTIONS` |
| 4 | **Output Sanitizer** | Strips tool-call JSON / code fences / system-prompt leaks from the LLM response |
| 5 | **Hardcoded Safety** | Deterministic AQI / diet / emotion / keyword gates that bypass the LLM |

## What you'll see

- A **grid of attack categories**: prompt injection, content safety,
  PDF poisoning, memory poisoning, output leak, off-topic bypass.
- Click a category → see the canned attacks for it.
- Click **🔥 Fire** → the dashboard routes the payload through the
  `SafetyHarness`, returns a structured result, and renders:
  - 🔴 / 🟡 / 🟣 / 🟢 status pill per attack
  - Which layer caught it
  - The neutralised / sanitised text (when applicable)
  - A per-layer status strip (each layer's outcome)
  - The full audit trail
- A **live scoreboard**: total fired, defenses by type, defense rate,
  weakest layer.
- A **Settings panel**: toggle individual layers on/off, change the
  on-topic keywords, tune the Layer 2 rejection threshold, paste a
  BYOK LLM key (Groq / Gemini / Sarvam / OpenAI / Claude / Ollama).

## Run it

See `SETUP.md` for the full setup. TL;DR:

```bash
cd safety_dashboard
uv sync
uv run safety-dashboard
# open http://127.0.0.1:8000
```

## Folder shape

```
safety_dashboard/
├── pyproject.toml
├── README.md           ← you are here
├── SETUP.md            ← uv + run instructions
├── CLAUDE.md           ← project memory for Claude Code
├── CLAUDE_HISTORY.md   ← decision log
├── API_CONTRACT.md     ← endpoints exposed by this episode
├── EPISODES.md         ← AgentVerse episode index
├── architecture.md     ← Mermaid pipeline diagram
├── .env.example
├── .gitignore
├── src/safety_dashboard/
│   ├── api.py          ← FastAPI routes
│   ├── handlers.py     ← routes attacks through the harness
│   ├── attacks.py      ← 26 canned educational attacks
│   ├── schemas.py
│   ├── llm.py          ← optional BYOK
│   ├── preferences.py
│   ├── scoreboard.py
│   ├── main.py         ← `uv run safety-dashboard` entry
│   └── tools/          ← capture + open-meteo helpers
└── frontend/           ← standalone vanilla-JS PWA
    ├── index.html
    ├── style.css
    ├── app.js
    ├── icon.svg
    └── manifest.json
```

## Why standalone frontend?

EP01-EP04 share `multi-agent/agentverse-frontend/`. EP05's UI is a
different beast (live attack log, per-layer indicators, score
sidebar), so it ships its own standalone PWA in `frontend/`.
Touching the shared frontend would risk breaking the four shipped
episodes — frozen by design.

## What's NOT here

- **No real agent.** EP05 is a *defence* episode, not a *task*
  episode. The harness defends against payloads; there's no chat
  bot to "win" the game with. Optional BYOK LLM lets you exercise
  Layer 4 against a real response.
- **No persistence.** The scoreboard resets on restart by design —
  running the dashboard for a live demo shouldn't show yesterday's
  bad score on stage.

## Library usage outside this episode

The `agentverse_safety` library lives in
`../agentverse_safety/`. Drop it into ANY agent (CrewAI / LangGraph
/ LlamaIndex / raw OpenAI) and get the same 5 layers for free. See
that folder's `README.md` for the library API.
