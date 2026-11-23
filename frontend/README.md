# Frontend implementation notes

The user confirmed Astryx (`@astryxdesign/core`). Its ChatLayout, ChatMessage, ChatComposer and Citation components adapt the REST API. The official prebuilt neutral theme needs no StyleX compiler. The CLI's Windows theme-add command failed with EISDIR, so the prebuilt theme is wired directly as documented.

Run `npm run dev` from this directory. Next.js loads the root `.env` on the server and proxies `/api/*` to `BACKEND_URL` (default `http://127.0.0.1:8000`). Model and telemetry credentials stay on the server. Logs contain route templates, identifiers, outcomes and durations, never request bodies.

The chat persists the selected conversation ID and pending idempotent operations in this browser's local storage so a transport retry or refresh can reuse the operation key. Source previews use the evidence snapshot stored with each message. The source material is demonstration content, not released operating instructions.

Checks: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`, and `npm run astryx -- doctor --built .`. State tests cover IME-safe submission and idempotency recovery. Browser and model integration checks are coordinated from the repository root.
