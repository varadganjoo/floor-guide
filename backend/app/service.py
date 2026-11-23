import json
import threading
from datetime import datetime
from time import monotonic, perf_counter

import langsmith as ls
from langgraph.types import Command
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    RateLimitError,
)

from app.agent import AgentEngine, AgentFailure
from app.database import Conflict, Database, NotFound, now, uid
from app.documents import DocumentCatalog, import_manifest
from app.observability import (
    Observer,
    clean,
    configure_logging,
    execution_context,
    logger,
)


def public_error(error: Exception) -> str:
    if isinstance(error, AgentFailure):
        return str(error)
    if isinstance(error, AuthenticationError):
        return "OpenAI rejected the API key. Check OPENAI_API_KEY in the root .env."
    if isinstance(error, RateLimitError):
        return "OpenAI rate or quota limit reached. Check billing and retry later."
    if isinstance(error, APIConnectionError):
        return "Could not connect to OpenAI. Your question is saved; please retry."
    if isinstance(error, APIStatusError):
        return (
            f"OpenAI returned HTTP {error.status_code}. Check model access and "
            "API configuration. Your question is saved."
        )
    return (
        "This turn failed unexpectedly. Your question is saved. Inspect its run for"
        " the error category and retry."
    )


class ChatService:
    def __init__(self, settings, *, model=None, decisions=None):
        self.settings = settings
        self.db = Database(settings.data_dir / "application.sqlite3")
        configure_logging(settings.data_dir / "logs")
        if not self.db.rows("SELECT id FROM topics LIMIT 1"):
            import_manifest(self.db, settings.document_manifest)
        self.catalog = DocumentCatalog(self.db)
        self.engine = AgentEngine(
            self.db, self.catalog, settings, model=model, decisions=decisions
        )
        self.observer = Observer(self.db)
        self.locks: dict[str, threading.Lock] = {}
        self.lock_guard = threading.Lock()
        self.trace_client = None
        if settings.langsmith_tracing and settings.langsmith_api_key:
            try:
                self.trace_client = ls.Client(
                    api_key=settings.langsmith_api_key.get_secret_value(),
                    hide_inputs=clean if settings.trace_content else True,
                    hide_outputs=clean if settings.trace_content else True,
                    hide_metadata=lambda metadata: clean(
                        {
                            k: v
                            for k, v in metadata.items()
                            if k
                            in {
                                "thread_id",
                                "conversation_id",
                                "turn_id",
                                "execution_id",
                                "model",
                                "reasoning_effort",
                                "prompt_version",
                            }
                        }
                    ),
                )
            except Exception:
                logger.warning("trace_client_unavailable")
        self.recover()
        logger.info(
            "documents_loaded",
            extra={
                "fields": {
                    "sections": len(self.catalog.sources),
                    "unavailable": self.catalog.errors,
                }
            },
        )

    def lock(self, conversation_id: str):
        with self.lock_guard:
            return self.locks.setdefault(conversation_id, threading.Lock())

    def close(self):
        from app.observability import close_logging

        self.engine.close()
        if self.trace_client:
            try:
                self.trace_client.flush()
            except Exception:
                logger.warning("trace_flush_failed")
        close_logging(self.settings.data_dir / "logs")

    def graph_config(
        self,
        conversation_id: str,
        execution_id: str | None = None,
        run_id: str | None = None,
    ):
        return {
            "configurable": {"thread_id": conversation_id},
            "recursion_limit": 40,
            "metadata": {
                "thread_id": conversation_id,
                "conversation_id": conversation_id,
                "turn_id": run_id,
                "execution_id": execution_id,
                "model": "gpt-6-luna",
                "reasoning_effort": "none",
            },
        }

    def recover(self):
        for record in self.db.rows(
            "SELECT data FROM conversation_runs WHERE status='running'"
        ):
            run = json.loads(record["data"])
            snapshot = self.engine.graph.get_state(
                self.graph_config(run["conversation_id"])
            )
            values = snapshot.values or {}
            if values.get("run_id") == run["id"] and snapshot.interrupts:
                self.project(run, values, snapshot.interrupts)
            elif values.get("run_id") == run["id"] and values.get("answer"):
                self.project(run, values, ())
            else:
                run.update(
                    status="failed",
                    error=(
                        "Execution was interrupted by a restart. Retry the saved "
                        "question."
                    ),
                    version=run["version"] + 1,
                )
                with self.db.connect() as db:
                    self.db.save_run(run, db)

    def response(self, run: dict) -> dict:
        return {
            "run": run,
            "messages": self.db.messages(run["conversation_id"], limit=10000),
        }

    def send(self, conversation_id: str, content: str, operation_id: str):
        lock = self.lock(conversation_id)
        if not lock.acquire(blocking=False):
            raise Conflict("This conversation is processing a request")
        try:
            run, execute = self.db.start_turn(conversation_id, content, operation_id)
            if execute:
                snapshot = self.engine.graph.get_state(
                    self.graph_config(conversation_id)
                )
                graph_input = self.engine.initial(run)
                if snapshot.values.get("run_id") == run["id"]:
                    # Explicit retries retain already completed searches, counters
                    # and human context instead of replaying the original question.
                    graph_input = None
                run = self.execute(run, graph_input)
            return self.response(run)
        finally:
            lock.release()

    def resume(self, conversation_id: str, payload):
        lock = self.lock(conversation_id)
        if not lock.acquire(blocking=False):
            raise Conflict("This conversation is processing a request")
        try:
            run_id = str(payload.turn_id)
            run = self.db.run(run_id)
            if run["conversation_id"] != conversation_id:
                raise NotFound("Run not found in this conversation")
            operation_id = str(payload.operation_id)
            fingerprint = json.dumps(
                payload.model_dump(mode="json", exclude={"operation_id"}),
                sort_keys=True,
            )
            graph_input = Command(resume={"content": payload.content})
            with self.db.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                previous = db.execute(
                    "SELECT * FROM operations WHERE id=?", (operation_id,)
                ).fetchone()
                if previous:
                    if (
                        previous["run_id"] != run_id
                        or previous["kind"] != "resume"
                        or previous["payload"] != fingerprint
                    ):
                        raise Conflict("Operation ID belongs to another request")
                    snapshot = self.engine.graph.get_state(
                        self.graph_config(conversation_id)
                    )
                    pending_matches = any(
                        item.id == payload.interrupt_id for item in snapshot.interrupts
                    )
                    if run["status"] != "failed" and not (
                        run["status"] == "awaiting_clarification" and pending_matches
                    ):
                        return self.response(run)
                    if snapshot.values.get("run_id") != run_id:
                        raise Conflict("A newer turn has replaced this checkpoint")
                    # Retry completed nodes from their saved checkpoint. Only deliver
                    # the human answer again when a crash left the interrupt pending.
                    graph_input = graph_input if pending_matches else None
                else:
                    if (
                        run["status"] != "awaiting_clarification"
                        or run["interrupt_id"] != payload.interrupt_id
                        or run["version"] != payload.version
                    ):
                        raise Conflict(
                            "This clarification is stale or no longer "
                            "waiting for a reply"
                        )
                    run["wait_ms"] += max(
                        0,
                        (
                            datetime.fromisoformat(now())
                            - datetime.fromisoformat(run["paused_at"])
                        ).total_seconds()
                        * 1000,
                    )
                    db.execute(
                        "INSERT INTO operations VALUES (?,?,?,?,?)",
                        (operation_id, conversation_id, run_id, "resume", fingerprint),
                    )
                    self.db.add_message(
                        db,
                        run,
                        "user",
                        "reply",
                        payload.content,
                        operation_id + ":reply",
                    )
                run.update(status="running", version=run["version"] + 1, paused_at=None)
                self.db.save_run(run, db)
            run = self.execute(run, graph_input)
            return self.response(run)
        finally:
            lock.release()

    def cancel(self, conversation_id: str, run_id: str, operation_id: str):
        with self.lock(conversation_id):
            run = self.db.run(run_id)
            if run["conversation_id"] != conversation_id:
                raise NotFound("Run not found in this conversation")
            with self.db.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                previous = db.execute(
                    "SELECT * FROM operations WHERE id=?", (operation_id,)
                ).fetchone()
                if previous:
                    if previous["run_id"] != run_id or previous["kind"] != "cancel":
                        raise Conflict("Operation ID belongs to another request")
                    return self.response(run)
                if run["status"] != "awaiting_clarification":
                    raise Conflict(
                        "Only a turn waiting for clarification can be cancelled"
                    )
                if run.get("paused_at"):
                    run["wait_ms"] += max(
                        0,
                        (
                            datetime.fromisoformat(now())
                            - datetime.fromisoformat(run["paused_at"])
                        ).total_seconds()
                        * 1000,
                    )
                run.update(
                    status="cancelled",
                    interrupt_id=None,
                    paused_at=None,
                    version=run["version"] + 1,
                )
                db.execute(
                    "INSERT INTO operations VALUES (?,?,?,?,?)",
                    (operation_id, conversation_id, run_id, "cancel", ""),
                )
                self.db.save_run(run, db)
            self.db.event(run_id, uid(), "cancelled")
            return self.response(run)

    def execute(self, run: dict, graph_input):
        from app.observability import request_context

        execution_id = uid()
        run["execution_id"] = execution_id
        parent_span_id = self.db.event(
            run["id"],
            execution_id,
            "execution_started",
            {"model": "gpt-6-luna", "reasoning_effort": "none"},
        )
        token = execution_context.set(
            {
                "run_id": run["id"],
                "conversation_id": run["conversation_id"],
                "execution_id": execution_id,
                "parent_span_id": parent_span_id,
                "deadline": monotonic() + 90,
            }
        )
        request_context.get().update(
            run_id=run["id"],
            conversation_id=run["conversation_id"],
            execution_id=execution_id,
        )
        started = perf_counter()
        previous_active_ms = run["active_ms"]
        try:
            if not self.engine.bound_model:
                raise AgentFailure(
                    "Set OPENAI_API_KEY in the root .env to enable the document agent."
                )
            config = self.graph_config(run["conversation_id"], execution_id, run["id"])
            with ls.tracing_context(
                enabled=self.trace_client is not None,
                client=self.trace_client,
                project_name=self.settings.langsmith_project,
            ):
                result = self.engine.graph.invoke(graph_input, config)
            snapshot = self.engine.graph.get_state(config)
            elapsed = (perf_counter() - started) * 1000
            run["active_ms"] = previous_active_ms + elapsed
            self.project(run, result, snapshot.interrupts)
            self.observer.emit("execution_finished", {"status": run["status"]}, elapsed)
        except Exception as error:
            elapsed = (perf_counter() - started) * 1000
            run["active_ms"] = previous_active_ms + elapsed
            run.update(
                status="failed", error=public_error(error), version=run["version"] + 1
            )
            self.observer.emit(
                "execution_failed",
                {"error_category": type(error).__name__, "message": run["error"]},
                elapsed,
            )
            self.summarize_usage(run)
            with self.db.connect() as db:
                self.db.save_run(run, db)
        finally:
            execution_context.reset(token)
        return self.db.run(run["id"])

    def summarize_usage(self, run: dict):
        events = self.db.events(run["id"])
        provider_events = [
            event
            for event in events
            if event["event"] in {"model_call", "history_selection", "answer_review"}
        ]
        for field in ("input_tokens", "output_tokens"):
            values = [event["payload"].get(field) for event in provider_events]
            run[field] = (
                sum(v for v in values if isinstance(v, int))
                if values and all(isinstance(v, int) for v in values)
                else None
            )
        run["usage_complete"] = bool(provider_events) and all(
            event["payload"].get("input_tokens") is not None
            for event in provider_events
        )

    def project(self, run: dict, state: dict, interrupts):
        self.summarize_usage(run)
        with self.db.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            run.update(error=None, version=run["version"] + 1)
            if interrupts:
                pending = interrupts[0]
                question = pending.value["question"]
                run.update(
                    status="awaiting_clarification",
                    interrupt_id=pending.id,
                    clarification_question=question,
                    paused_at=run.get("paused_at") or now(),
                )
                self.db.add_message(
                    db,
                    run,
                    "assistant",
                    "clarification",
                    question,
                    run["id"] + ":clarification:" + pending.id,
                )
            else:
                answer = state.get("answer")
                if not answer:
                    raise AgentFailure("The agent ended without a validated answer")
                run.update(
                    status="completed",
                    answer=answer["answer"],
                    selected_topic_ids=answer["selected_topic_ids"],
                    interrupt_id=None,
                    clarification_question=None,
                    paused_at=None,
                )
                self.db.add_message(
                    db,
                    run,
                    "assistant",
                    "answer",
                    answer["answer"],
                    run["id"] + ":answer",
                    answer["references"],
                )
            self.db.save_run(run, db)
