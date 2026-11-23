# Floor Guide

Floor supervisor document chat with FastAPI, Next.js, Astryx, LangChain and LangGraph. GPT-6 Luna answers with `reasoning.effort="none"`. OpenAI Decisions selects relevant history; the main agent selects topics and searches the local documents.

## Requirements

- Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20.19+, 22.13+, or 24+ and npm (Node.js 22 or 24 LTS recommended)

## Install

From the project root:

```sh
uv sync --directory backend --locked
npm --prefix frontend ci
```

uv creates an isolated virtual environment at `backend/.venv`. No global Python packages or manual activation are required.

## Run locally

Use two terminals from the project root:

```sh
npm run dev:backend
```

```sh
npm run dev:frontend
```

- Frontend: http://127.0.0.1:3000
- API health: http://127.0.0.1:8000/api/health
- Interactive API docs: http://127.0.0.1:8000/docs

The frontend proxies `/api/*` to FastAPI. The [observability dashboard](http://127.0.0.1:3000/observability) has Metrics, Traces and Logs views for saved questions, answers, actions, per-query token usage, timings and errors.

Create a conversation, ask a question, and open its numbered references to inspect exact supporting excerpts. Vague questions pause the graph for clarification; replying resumes the same turn, including after a backend restart. Conversations remain in SQLite. Failed sends can be retried without duplicating the question.

The supplied documents are marked **EXAMPLE ONLY — NOT RELEASED FOR OPERATION**. This is an unauthenticated local prototype, intended to bind to localhost, not a public service.

## Configuration

The root `.env` is loaded by both apps. Environment files stay local and are ignored by Git. For a new checkout, create `.env` at the project root and configure the settings below.

| Variable | Use | Default |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Optional backend credential | unset |
| `OPENAI_API_KEY` | Required for live answering and history selection | unset |
| `APP_NAME` | API title | `TechInterview API` |
| `BACKEND_URL` | Next.js proxy destination | `http://127.0.0.1:8000` |
| `LANGSMITH_TRACING` | Enable optional external agent traces | `false` |
| `LANGSMITH_API_KEY` | LangSmith credential when tracing is enabled | unset |
| `LANGSMITH_PROJECT` | Trace project | `floor-supervisor` |
| `TRACE_CONTENT` | Explicitly export sanitized trace inputs/outputs | `false` |

Python code accesses typed settings with `from app.config import get_settings`. Credentials use Pydantic `SecretStr`. All answering-agent requests use `gpt-6-luna` with reasoning effort `none`, including tool calls and resumed turns. Decisions has its own API schema and does not expose this reasoning setting.

Next.js loads the root configuration using [`@next/env`](https://nextjs.org/docs/app/guides/environment-variables). Keys stay server-side. Never prefix credentials with `NEXT_PUBLIC_`. Restart the servers after editing `.env`.

## Documents and topics

`backend/documents.json` seeds the initial SQLite topics and document registry on the first startup. Topic names and descriptions are runtime database records, not enums or topic-specific Python branches. To add or update a topic/document, edit this manifest and run:

```sh
uv run --directory backend python -m app.documents
```

Then restart the backend to rebuild its in-memory catalog. Files must be DOCX paths inside the project. Import is idempotent and does not reset conversations.

Documents are parsed once into complete numbered sections with subheadings, warnings and labelled table rows. A bounded lexical search returns excerpts; there are no embeddings, hosted file search or vector databases. Lexical search can miss paraphrases. References use document versions and section headings rather than fabricated DOCX page numbers.

The agent has three typed actions: search, request clarification, and submit a grounded answer. Pydantic validates arguments and final output. The backend checks every citation ID and verbatim quote against retrieved evidence before displaying the answer. These application references are not OpenAI hosted `file_citation` annotations.

## Storage and observability

The dashboard supports last-hour, 24-hour, 7-day and all-time windows. Metrics summarize the latest 1,000 turns accepted within the window and the latest 5,000 HTTP requests, excluding observability endpoints. Agent latency percentiles include completed turns; HTTP percentiles include successful requests. Every percentile shows its eligible sample count. The activity chart groups accepted questions by current outcome; turns/hour describes the sampled window.

Search traces by question, turn ID or conversation ID and filter by outcome. Each query shows total, input and output tokens across model/history-selection calls, including retries and clarification resumes. A total is unknown if either input or output usage is missing. Open a trace for execution waterfalls, per-call payloads, delivered transcripts with source references, and correlated server/browser timings. Each execution has its own time axis so human waiting does not inflate processing time. Lists and detail records are paginated; optional auto-refresh runs every 15 seconds while the tab is visible.

Logs has two labelled sources: SQLite action/HTTP records and rotating `backend/data/logs/application.jsonl` diagnostics. SQLite severity is classified from outcomes and HTTP status; application diagnostics retain their logged severity. The file viewer reads at most 8 MB across four rotation files and filters the latest 5,000 records. Search and severity filters locate failures, and correlated records link back to their trace. Next.js proxy logs remain in the frontend server output. External trace delivery and links are not stored, so the dashboard reports configuration without claiming successful export.

Application data, checkpoints and rotating JSON logs live under ignored `backend/data/`. Run one backend worker for this prototype. Keep both SQLite databases and use SQLite-safe backup tooling; do not copy a live database without its WAL state.

The run inspector shows the exact saved transcript, per-turn actions, history-selection probabilities, searches, reference validation, provider usage and correlated HTTP requests. Processing time and human waiting time are separate. P50/p95 active latency summarizes completed runs in the latest 1,000-run window with the sample count. Missing usage remains unknown; monetary estimates are not displayed without a verified price schedule.

FastAPI returns `X-Request-ID` and `Server-Timing`. The Next.js proxy adds its own ID/timing, and the browser records response/render elapsed time. In-process durations use monotonic clocks; stored timestamps use UTC. Ordinary JSON request logs contain IDs/outcomes/timings rather than raw message bodies. Questions and answers remain in SQLite.

Local inspection works without LangSmith. Set `LANGSMITH_TRACING=true` and its API key to export agent traces. Trace inputs/outputs, including child calls, are hidden by default. `TRACE_CONTENT=true` explicitly enables sanitized content export. Agent actions are observable; private chain-of-thought is not requested. Hosted retention and billing depend on your tracing account.

History selection and excerpts have separate token budgets. Each of at most three searches returns up to 6,000 tokens of new whole sections, excluding already retrieved sections (18,000 maximum across a turn). When the exact model tokenizer is unavailable, UTF-8 byte counts provide a conservative bound. Tools allow three attempts for explicitly transient search failures and one argument correction. Clarification is capped at two rounds. Unknown or invalid topic IDs and permanent errors are not blindly retried.

## Checks

TypeScript 6 and ESLint 9 are pinned to match the current Next.js lint plugins' supported versions. ESLint 9 currently emits an upstream end-of-support notice during installation; upgrade it when those plugins support ESLint 10.

```sh
uv run --directory backend pytest
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
npm --prefix frontend test
npm run lint
npm run typecheck
npm run build
```

## Production

```sh
uv run --directory backend fastapi run --host 127.0.0.1 --port 8000
npm run build
npm start
```

Run backend and frontend as separate services. Set `BACKEND_URL` to the backend address reachable by Next.js. Supply secrets through the deployment environment or a private root `.env`. Authentication and multi-worker deployment are outside this local prototype.

Tests replace provider boundaries with fake models or HTTP transports while exercising actual SQLite, DOCX parsing, graph interrupts, source validation and serialized non-thinking requests. They make no paid API calls. A real-model smoke test is a separate validation step; offline success does not establish live model access or answer quality.

For an opt-in paid run of the golden questions, use `uv run --directory backend python -m app.evaluate --limit 50` (use a smaller limit for a smoke test). Only the question-only dataset reaches the agent; reference answers stay outside its context. Results, retrieved sections, API traces, input fingerprints, latency, and an isolated SQLite database are saved under `backend/data/evaluations/`. The runner stops on the first failed turn unless `--keep-going` is supplied. Completed turns still need semantic review against the gold facts; completion is not an accuracy score.

The [23 November desktop UI evaluation](docs/test-results/golden-ui-20261123/report.md) covers all 50 golden questions submitted through the chat UI, with per-fact grades, first-attempt accuracy, complete answers, citation checks, and end-to-end latency. Its scores exclude the earlier interrupted API-only diagnostic run.

Acceptance requires **100% strict accuracy for safety-related scenarios** and
**at least 95% for non-safety scenarios**. Safety includes maintenance isolation,
interlocks, and emergency information, regardless of the source topic. The
evaluation-only classification is in `backend/evaluation_policy.json`; it is
never supplied to the agent. Apply gates to a semantically graded CSV with
`uv run --directory backend python -m app.evaluation --results <case-results.csv>`.
Missing/ungraded cases cannot pass a gate. These are measured evaluation gates,
not a claim that an individual generated answer has a guaranteed accuracy.

Search accepts an array of valid topic IDs from SQLite and reserves evidence for
each requested type before returning extra matches from one type. Missing source
coverage is reported to the agent and prevents a partial response from claiming
to be fully grounded. When information is insufficient, the answer explicitly
states that the available documents do not contain enough information.

Before publishing an answer, one structured GPT-6 Luna call checks the draft
against complete retrieved passages, with reasoning effort `none`. Table rows
retain all checks and reactions; numbered procedures stay together. The selected
passages appear directly in the answer so their requirements cannot be lost in
paraphrasing. Citation quotations are copied from those stored passages by the
server, rather than generated by the model. Unknown passage IDs are rejected.
This adds one model call per evidence-backed answer; measured evaluation gates
still determine acceptance.

The [latest failed-case verification](docs/test-results/failed-cases-v3-1/report.md)
passes all eight remaining regressions (four safety and four non-safety), with
22/22 required facts and 10/10 exact reference quotes. The user stopped the full
rerun and requested failed cases only, so this is a targeted result rather than
a new 50-case acceptance score.

## Layout

```text
backend/
  app/config.py       # Settings loaded from the root .env
  app/main.py         # Conversation and observability APIs
  app/agent.py        # Main agent, Decisions history filter and LangGraph
  app/documents.py    # Local document import, parsing and search
  app/database.py     # SQLite repository
  app/service.py      # Turn lifecycle and durable clarification
  app/observability.py # Structured logs and run events
  documents.json     # Data-driven topic/document manifest
  tests/              # Offline API, graph, citation and configuration checks
  pyproject.toml      # Python dependencies and tooling
  uv.lock             # Locked Python dependencies
frontend/
  src/app/            # App Router pages and styles
  src/components/     # React components
  next.config.mjs     # Shared env loading
  src/app/api/       # Correlated server-side API proxy
  src/app/observability/ # Local run inspector
  package-lock.json   # Locked frontend dependencies
package.json          # Commands for both apps
.env.example          # Configuration template
```

Design: [application plan](docs/document-chat-plan.md), [observability plan](docs/observability-plan.md). The frontend uses Astryx's prebuilt components and neutral theme; no separate UI service is required.
