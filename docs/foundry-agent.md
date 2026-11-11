# Foundry Agent Service Integration

Sage's chat, streaming, scenario analysis, Voice Live, and AI Portfolio Insight features are all backed by a
**single registered Azure AI Foundry Agent Service prompt agent**. This document explains why, how it's wired,
and how to run/debug it locally.

## Why one agent, not three integrations

Before this migration, chat/voice/insight would each have talked to Azure in a different way (a fake in-memory
"agent" for chat, a separate realtime client for voice, and a third integration for insight) — three code paths
sharing only a prompt string. That's fragile: fixes and evaluation don't propagate, and there's no single place
to reason about instructions, tools, or behavior.

Instead, `backend/foundry_agent.py` registers **one** agent in the Foundry project on startup (idempotent — it
looks up an existing agent by name before creating a new one), and every feature routes through it:

- **Chat** (`/advisor/chat`, `/chat/stream`) — conversation + run/stream via the Responses API.
- **Scenario projection** (`/api/project-scenario`) — same agent, a different per-request prompt.
- **AI Portfolio Insight** (`/api/portfolio-insight`) — same agent, a third per-request prompt.
- **Voice Live** (`backend/voice/realtime_client.py`) — the realtime WebSocket session binds to the same agent
  via `agent_name`/`project_name`, instead of carrying its own separate `instructions`.

## The "one instructions block, many prompts" pattern

`foundry_agent.SYSTEM_INSTRUCTIONS` is the agent's registered system prompt. It's written primarily for the
original scenario-analysis use case and rigidly asks for the `AnalysisOutput` JSON schema "for every scenario
request." In practice, per-request prompts **soft-override** this: a strongly worded user message like

> "Do not use the AnalysisOutput schema from your default instructions — use the schema specified below instead."

reliably produces a completely different JSON shape. This was confirmed live for all three JSON-returning
endpoints (`/api/project-scenario`, `/api/portfolio-insight`) as well as free-form markdown chat
(`/advisor/chat`), all sharing the same registered agent and conversation machinery. When adding a new
agent-backed feature with its own response shape, follow this pattern: build a per-request prompt that
explicitly overrides the schema instruction, rather than editing the shared `SYSTEM_INSTRUCTIONS`.

## Module map

| File | Responsibility |
|---|---|
| `backend/foundry_agent.py` | Registers the agent (`register_agent()`), owns conversation lifecycle (`create_conversation()`), and runs/streams the tool-call loop (`run_agent()`, `stream_agent()`). Bounded to `MAX_TOOL_ITERATIONS = 6` since Foundry runs expire 10 minutes after creation. |
| `backend/main.py` | Thin shim layer (`ThreadManager`, `_create_thread()`, `_add_message()`, `_run_assistant_sync()`, `_stream_chat_with_tools()`) that the ~16 existing call sites use, delegating to `foundry_agent`. `setup_assistant()` calls `foundry_agent.register_agent()` on startup. |
| `backend/voice/realtime_client.py` | `_split_project_endpoint()` parses `FOUNDRY_PROJECT_ENDPOINT` into a resource endpoint + project name, then `connect()` passes `agent_name=`/`project_name=` to bind the realtime session to the registered agent instead of a bare model deployment. |

## Configuration

See **[docs/environment-configuration.md](./environment-configuration.md)** for the full variable reference.
The essentials:

```bash
# backend/.env
FOUNDRY_PROJECT_ENDPOINT=https://your-resource.services.ai.azure.com/api/projects/your-project
FOUNDRY_AGENT_NAME=sage-retirement-agent
MODEL_DEPLOYMENT_NAME=gpt-4o
```

Authentication is `DefaultAzureCredential` (Azure CLI locally, Service Principal or Managed Identity in
production) — no API keys.

## Health check

```bash
curl http://localhost:8172/health
```

Returns `agent_name` and `agent_version` when the agent is registered, so you can confirm the Foundry
connection without making a chat call.

## Evaluations

Agent responses are optionally evaluated (intent resolution, tool-call accuracy, task adherence) via
`azure-ai-evaluation`. This degrades gracefully — if the package or an `AIAgentConverter` isn't available, the
app logs `[INFO] ... evaluations degraded` and falls back to mock evaluators rather than failing the request.
See `backend/tests/test_regression.py` for the module-availability checks.

## Local testing without Azure

`backend/foundry_agent.py` degrades gracefully with `FOUNDRY_PROJECT_ENDPOINT` unset: `register_agent()`
returns `None` and every downstream call returns a clear "not configured" response instead of crashing. This
means the whole frontend (mock mode) and the AI Insight feature's deterministic metrics can be exercised
without any Azure credentials at all — only the agent-authored prose (the written review, chat replies)
requires a live Foundry connection.

## Tests

- `backend/tests/test_foundry_agent.py` — tool schema/dispatch, graceful degradation when unconfigured,
  registration idempotency (mocked `AIProjectClient`), `run_agent`/`stream_agent` tool-call loops (mocked
  Responses API), bounded-loop termination.
