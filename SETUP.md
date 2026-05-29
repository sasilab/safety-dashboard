# EP05 — SETUP

Single-user local app. `uv` only — never `pip install` directly.

## Prereqs

- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) installed
  (`pip install uv` once is fine, or use the official installer)

## Install

```bash
cd safety_dashboard
uv sync
```

`uv sync` reads `pyproject.toml`, sees `agentverse-safety = { path = "../agentverse_safety", editable = true }`, and pulls in the
library as a local editable dep. Edits to either project take effect
without reinstalling.

If `uv sync` complains about the editable path, make sure you're
running from inside `safety_dashboard/` and `../agentverse_safety/`
exists as a sibling.

## Run

```bash
uv run safety-dashboard
# → "Uvicorn running on http://127.0.0.1:8000"
```

Open <http://127.0.0.1:8000> in any browser. No build step.

## Optional BYOK LLM (Layer 4 demo)

The dashboard runs **without an LLM** by default — Layers 1, 2, 3,
and 5 work on regex / static analysis. Layer 4 (output sanitiser)
can be demonstrated on canned LLM-output samples (the "Output Leak"
category).

To exercise Layer 4 against a *real* LLM response:

1. Click ⚙️ Settings → paste a key (Groq / Gemini / Sarvam / OpenAI
   / Claude) OR run Ollama locally.
2. Tick **"Call real LLM during attacks"**.
3. Fire an attack — the dashboard now actually calls the LLM with
   the (Layer 1 sanitised) payload, then sanitises the response
   through Layer 4 before rendering.

Free Groq key: <https://console.groq.com/keys>

## Run from CLI without the server

There's a smoke-test command that loops through the entire attack
catalogue and prints which layer caught each one:

```bash
uv run safety-dashboard-smoke
```

Useful for CI or for a quick "is the library still defending against
every canned attack" sanity check after a regex change.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `uv sync` fails resolving `agentverse-safety` | sibling path not found | run from `safety_dashboard/`; ensure `../agentverse_safety/` exists |
| `litellm` not installed | optional path | `uv add litellm` — or just leave `call_llm` off |
| Frontend pill says "no LLM" | no key found | paste a key in Settings, or set `GROQ_API_KEY` in `.env` |
| `data/safety_log.jsonl` filling up | safety events are append-only | rotate / delete manually — it's an audit log |
| Browser shows cached old UI after a code change | stale browser cache | hard refresh (Ctrl/Cmd-Shift-R) |
| `pip install` complaints on Windows | mixing pip + uv on the same venv | stay on `uv`; `rm -rf .venv && uv sync` |

## Folder contract recap

The dashboard endpoints are in `API_CONTRACT.md`. The episode's
architecture lives in `architecture.md`. Decisions and known issues
are in `CLAUDE_HISTORY.md` under the EP05 section.
