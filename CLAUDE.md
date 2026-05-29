# AgentVerse — Claude Code Project Memory

> Persistent instructions for any future Claude Code session working on the
> AgentVerse series. Read this first; it links to the other docs.
>
> **Canonical copy lives here, at the AgentVerse root.** Each episode folder
> also keeps an identical copy so the episode repo is self-contained when
> pushed. Edit at the root, then `cp` into each episode (or vice-versa) when
> something changes.
>
> **See [CLAUDE_HISTORY.md](./CLAUDE_HISTORY.md)** for the full decision log,
> known issues, and per-episode architecture notes from EP01-EP03. That file
> is reference-only — not auto-loaded — so this file stays light. Read it
> when touching a shipped episode or when an EP04 decision rhymes with a
> past one.

## About

**AgentVerse** is @explainpannu's (Sasi) educational series teaching AI agent
frameworks through small social-impact agents. Each **episode** = one
framework + one real-world problem. The frontend is built once and reused;
only the backend changes per episode.

## Repo shape

```
multi-agent/                       ← AgentVerse root (this folder)
├── .gitignore                     ← protects every episode subfolder
├── CLAUDE.md                      ← canonical, slim (this file)
├── CLAUDE_HISTORY.md              ← canonical, reference-only decision log
├── API_CONTRACT.md                ← canonical
├── EPISODES.md                    ← canonical
├── agentverse-frontend/           ← REUSABLE PWA (EP01-EP04)
├── social_impact_crew/            ← EP01 (CrewAI)
├── diet_memory_agent/             ← EP02 (LangGraph + Mem0)
├── rag_nutrition_agent/           ← EP03 (Custom RAG + LangGraph + Mem0)
├── kural_explainer_agent/         ← EP04 (Thirukkural · LangGraph + Mem0 + Sarvam)
├── agentverse_safety/             ← EP05 reusable Python library
└── safety_dashboard/              ← EP05 attack-testing dashboard (standalone PWA)
```

Each shipped episode folder carries its own copy of `CLAUDE.md`,
`CLAUDE_HISTORY.md`, `API_CONTRACT.md`, `EPISODES.md`, and an
episode-specific `SETUP.md` so the episode repo is publishable standalone.

## The contract

Every backend exposes the same REST surface. See **[API_CONTRACT.md](./API_CONTRACT.md)** for the full schema + compliance checklist.

```
POST /api/run  { "city": "..." }
   → { city, coords, weather, pollution, aqi_level, meme }
```

Don't break the JSON shape. Add optional fields if you need to extend.

## Episodes

| # | Name | Framework | Status |
|---|---|---|---|
| EP00 | BreezyBuddy | ReAct (custom) | 🟢 shipped (pre-contract) |
| EP01 | Social Impact Crew | CrewAI 1.x | 🟢 shipped |
| EP02 | Diet Memory Agent | LangGraph + Mem0 | 🟢 shipped |
| EP03 | PDF Nutrition RAG Agent | Custom RAG (ChromaDB + PyMuPDF) + LangGraph + Mem0 | 🟢 shipped |
| EP04 | Thirukkural Sarcastic Explainer | LangGraph + Mem0 + Sarvam AI (3-method comparison) | 🟢 shipped |
| **EP05** | **Agent Safety Harness** | Reusable `agentverse-safety` library (5 layers) + FastAPI attack-testing dashboard | 🟡 **active** |

See **[EPISODES.md](./EPISODES.md)** for what was built per episode and the
lessons learned.

## Rules for every episode

1. **`uv` only — never `pip install` directly.** Use `uv sync` / `uv add` /
   `uv run`. The lockfile is the source of truth. Mixing pip and uv on the
   same venv corrupts dependency resolution on Windows.
2. **Max 200 lines per file.** If you need more, split.
3. **BYOK LLM with auto-detect.** Free providers first (Groq / Gemini /
   Ollama / OpenAI). Centralised in `llm.py`. The user drops their key in
   `.env` OR via the Settings panel — no restart, no code edit.
4. **No paid APIs for data.** Open-Meteo, Open Food Facts, OSM Nominatim,
   etc. Only the LLM needs a key (and Ollama makes even that optional).
5. **Comments explain WHY, not WHAT.** Names should tell you what.
6. **`.env` for secrets, never committed.** Both root and episode
   `.gitignore` enforce this.
7. **Beginner-friendly first.** Production hardening is fine but not at the
   cost of clarity.
8. **Episode self-contained.** Push the episode folder; it should run with
   its README + SETUP.md alone.
9. **Match `API_CONTRACT.md` exactly.** If the JSON shape changes, the
   frontend breaks for every episode. Add optional fields rather than
   breaking existing ones; bump a `version` query param if you must break.
10. **Document every non-obvious decision in `CLAUDE_HISTORY.md`** so future
    sessions can recover the why.

## Cross-cutting architecture (applies to every episode)

- **Separate repo per episode** — each framework should stand alone so
  learners can clone just the one they're studying.
- **Frontend in its own folder, not nested in any episode** —
  `agentverse-frontend/` is reusable. Coupling it to one backend would
  force a fork per episode.
- **Stable REST contract over streaming/RPC/MCP** — anyone can ship a
  backend in 30 minutes if they only need to match a JSON shape.
- **AQI as the universal "social impact" lens** — gives every episode a
  real-world health hook beyond the toy demo.
- **Docs are duplicated, not symlinked** — symlinks are flaky on Windows
  and break when an episode is cloned standalone.
- **Rule-based safety wraps the LLM.** Life-safety decisions (extreme AQI,
  dietary conflicts, blocked-content filters, prompt-injection sanitiser)
  must NEVER depend on a model. Regex / hardcoded rules first; the LLM
  gets the decoration job. Concrete patterns:
  `safety.py::aqi_safety_override` (EP01), rule-based `nutrition_analyst`
  swap (EP02), `rag_safety.filter_chunks_for_*` (EP03). **EP05 consolidates
  all of these into the reusable `agentverse_safety` library** — new
  episodes should `from agentverse_safety import SafetyHarness` rather than
  copy-pasting the patterns again.
- **Pre-resolve external data before the LLM.** Geocoding, weather, candidate
  filtering, RAG retrieval all run deterministically in the API layer; the
  LLM receives verified inputs as kickoff / state args. Never thread data
  between tools via free-text if you can pre-compute.
- **Tool side-channel via `ContextVar`** — tools return human-readable
  strings to the LLM AND write structured dicts to a request-scoped
  contextvar. FastAPI returns typed JSON without re-parsing LLM text.
  Framework-agnostic; works for CrewAI, LangGraph, and whatever EP04 picks.
- **Per-agent temperature.** Data / analyst agents stay at 0.4 (factual),
  creative agents at 0.7-0.9 (varied). One-size-fits-all temp either
  hallucinates or bores.
- **JSON-file preferences (`data/user_preferences.json`)** — single-user
  local app, no DB needed. Async lock + atomic rename on write. Gitignored
  everywhere because it contains the BYO API key in plain text.
- **Two-layer intent classifier before any expensive call.** Regex first
  (greetings, settings, blocked-content, Tamil chitchat); LLM fallback for
  ambiguous messages (also extracts the city / food / etc.). Geocoder
  results then validated by name-similarity before reaching the agent.
- **In-tab Notification API + service worker over Web Push.** Web Push
  needs VAPID + a server endpoint; for an educational local app, the
  in-tab pattern is enough and stays cross-browser.
- **OpenLIT for observability** — one-line `openlit.init()`. Silent no-op
  without an OTLP collector.

## Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Episode folder | `snake_case`, lowercase, descriptive | `social_impact_crew/` |
| Episode repo on GitHub | matches folder name (or `PascalCase` if framework-named) | `sasilab/social-impact-crew` |
| Python package | `snake_case`, matches folder | `social_impact_crew` |
| Env vars | `UPPER_SNAKE` | `GROQ_API_KEY`, `OLLAMA_BASE_URL` |
| Frontend assets | lowercase, descriptive | `notifications.js`, `icon.svg` |
| API routes | `kebab-case` under `/api/` | `/api/run`, `/api/health` |
| JSON field names | `snake_case` | `aqi_level`, `feels_like_c` |

## Adding a new episode (EP04 and beyond)

1. Pick the closest existing episode as a template (`cp -r`). Rename
   `pyproject.toml`'s `name` and script entries.
2. Replace the framework-specific module (`crew.py` / `graph.py` / etc.)
   with the new framework's idiom. Keep `tools/`, `llm.py`, `safety.py`,
   `intent.py`, and the FastAPI surface mostly unchanged — they're
   framework-agnostic.
3. The `api.py` handler must still return the contract from
   `API_CONTRACT.md`. The `ContextVar` capture pattern (see EP01 notes in
   CLAUDE_HISTORY.md) works for any framework whose tools you can wrap.
4. Add a row to the **Episodes** table above.
5. Add a full entry to `EPISODES.md` (template at the bottom of that file).
6. **Log every non-obvious decision in `CLAUDE_HISTORY.md`** under a new
   `### Episode-internal (additions from EP04 — <name>)` section.
7. If a decision is a NEW cross-cutting pattern (not episode-specific),
   add it to the *Cross-cutting architecture* section above AND mirror it
   into CLAUDE_HISTORY.md.

## Doc sync

`CLAUDE.md`, `CLAUDE_HISTORY.md`, `API_CONTRACT.md`, `EPISODES.md` are
duplicated to each episode folder. Edit at the root, then mirror:

```powershell
foreach ($f in 'CLAUDE.md','CLAUDE_HISTORY.md','API_CONTRACT.md','EPISODES.md') {
  foreach ($ep in 'social_impact_crew','diet_memory_agent','rag_nutrition_agent','kural_explainer_agent','safety_dashboard') {
    Copy-Item $f "$ep/"
  }
}
```

```bash
# macOS / Linux / Git Bash
for f in CLAUDE.md CLAUDE_HISTORY.md API_CONTRACT.md EPISODES.md; do
  for ep in social_impact_crew diet_memory_agent rag_nutrition_agent kural_explainer_agent safety_dashboard; do
    cp "$f" "$ep/"
  done
done
```

`SETUP.md` lives only in the episode folder — don't copy it up to root.
