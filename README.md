# Saarthi

A voice-first personal AI agent on [Bolna](https://bolna.ai). Call a number, speak Hindi, and ask for
anything. Saarthi answers on the call, remembers you, and hands real work (browsing, research,
forms, documents, code) to your own sandbox computer, then calls you back with the result.

## Run

```bash
cp .env.example .env            # fill BOLNA_API_KEY, BOLNA_TOOL_SECRET, LLM_API_KEY + OPENROUTER_API_KEY,
                                # SUPERMEMORY_API_KEY
uv run saarthi-sync --check-llm # voice model time-to-first-token, and confirms reasoning is off
docker compose --profile sandbox build sandbox   # per-user sandbox image (Chromium, agent)
docker compose up -d --build    # postgres, redis, migrate, api (:8080), worker, scheduler

# Expose the API so Bolna can reach it, then put the URL in PUBLIC_BASE_URL
docker compose --profile tunnel up tunnel     # prints https://<name>.trycloudflare.com

uv run saarthi-sync --numbers   # find your phone number id -> BOLNA_PHONE_NUMBER_ID
uv run saarthi-sync             # register the OpenRouter model, create/update agents, attach number
uv run saarthi-sync --dry-run   # print agent payloads without calling Bolna
```

## Web app

A Vite + React + Tailwind app in `frontend/`, built into the API image and served at `/app` (JSON API under
`/api/web`). Sign in with the phone number you call Saarthi from; Saarthi calls you and reads a
6-digit code (`WEB_LOGIN_DELIVERY=log` shows it on screen instead, for local dev). There you
can edit your profile and standing instructions (your UPI ID goes there), write skills
(installed as `~/.claude/skills/<name>/SKILL.md` in your sandbox before every task), connect MCP
servers (stdio ones run inside your sandbox), and see your tasks and schedule.

```bash
cd frontend && npm install
npm run dev     # http://localhost:5173/app, proxies /api to the backend on :8091
npm run build   # what FastAPI serves at /app
```

## Test

```bash
docker compose up -d postgres redis
uv run pytest
```

## Layout

| Path | What |
|---|---|
| `src/saarthi/domain/` | Business logic: users, contacts (fuzzy Hinglish name matching), ledger, tasks, routines, call sessions |
| `src/saarthi/api/` | FastAPI: Bolna caller lookup, `/tools/{name}` dispatcher, execution webhook, sandbox result callback |
| `src/saarthi/api/tools/` | One module per voice capability: onboarding, tasks, memory, schedule, khata |
| `src/saarthi/voice/` | Bolna REST client, tool specs, call context, agent definitions + prompts, sync and call CLIs |
| `src/saarthi/packs/` | Per-profession prompt add-ons injected per caller (e.g. fruit sellers) |
| `src/saarthi/sandbox/` | Starts and talks to the per-user sandbox containers |
| `sandbox/` | Sandbox image: Chromium + Playwright MCP + noVNC, and the Claude Agent SDK worker |
| `src/saarthi/memory/` | Supermemory wrapper and the profile cache used by caller lookup |
| `src/saarthi/jobs/` | arq worker jobs: run/report sandbox tasks, routines, post-call memory ingest |
| `src/saarthi/scheduler.py` | Fires due routines |

## How a call is wired

1. Bolna calls `GET /bolna/lookup` with the caller's number. We return their name, profile,
   dues and a random per-call `session` token, which Bolna merges into the prompt.
2. The LLM passes `session` on every tool call (`/tools/*`). The backend resolves the caller
   from it and never from anything the caller says.
3. After the call, Bolna posts the execution to `/webhooks/bolna`. The worker sends the
   transcript to Supermemory and refreshes the cached profile for the next lookup.
4. `do_task` queues work. The worker starts the caller's sandbox (`saarthi-sbx-<user>`, a
   long-lived container with its own home volume), where a Claude Agent SDK worker uses a real
   browser, shell and files. It posts the result back and Saarthi calls the user with it.
   Watch a sandbox's browser at `http://localhost:<port>/vnc.html` (port in the worker log).
