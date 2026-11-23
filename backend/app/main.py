import json
import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import UUID

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.database import Conflict, NotFound, now, uid
from app.inspection import Window, run_filter
from app.inspection import router as inspection_router
from app.observability import percentile, request_context
from app.schemas import CancelRun, ClientMeasurement, ResumeMessage, SendMessage
from app.service import ChatService


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str


def create_app(settings=None, *, model=None, decisions=None):
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application):
        service = ChatService(settings, model=model, decisions=decisions)
        application.state.service = service
        try:
            yield
        finally:
            service.close()

    application = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    application.include_router(inspection_router)

    @application.exception_handler(NotFound)
    async def not_found_handler(request, error):
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @application.exception_handler(Conflict)
    async def conflict_handler(request, error):
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @application.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = uid()
        proxy_id = request.headers.get("X-Proxy-Request-ID")
        try:
            proxy_id = str(UUID(proxy_id)) if proxy_id else None
        except ValueError:
            proxy_id = None
        started = perf_counter()
        context_token = request_context.set(
            {"request_id": request_id, "proxy_request_id": proxy_id}
        )
        try:
            try:
                response = await call_next(request)
            except Exception as error:
                logging.getLogger("floor_supervisor").error(
                    "request_failed",
                    extra={
                        "fields": {
                            "request_id": request_id,
                            "error_category": type(error).__name__,
                        }
                    },
                )
                response = JSONResponse(
                    status_code=500,
                    content={
                        ("detail"): (
                            "Application request failed. Inspect the local logs "
                            "using X-Request-ID."
                        )
                    },
                )
            duration = (perf_counter() - started) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["Server-Timing"] = f"app;dur={duration:.2f}"
            route = getattr(request.scope.get("route"), "path", "unmatched")
            service = getattr(request.app.state, "service", None)
            if service:
                try:
                    service.db.execute(
                        (
                            "INSERT INTO request_observations VALUES "
                            "(?,?,?,?,?,?,?,?,?,?,?)"
                        ),
                        (
                            request_id,
                            getattr(request.state, "conversation_id", None),
                            getattr(request.state, "run_id", None),
                            getattr(request.state, "execution_id", None),
                            proxy_id,
                            route,
                            response.status_code,
                            duration,
                            None,
                            None,
                            now(),
                        ),
                    )
                except Exception:
                    logging.getLogger("floor_supervisor").warning(
                        "request_observation_failed"
                    )
            logging.getLogger("floor_supervisor").info(
                "http_request",
                extra={
                    "fields": {
                        "request_id": request_id,
                        "route": route,
                        "status": response.status_code,
                        "duration_ms": duration,
                    }
                },
            )
            return response
        finally:
            request_context.reset(context_token)

    def service(request: Request) -> ChatService:
        return request.app.state.service

    def response(service: ChatService, run: dict):
        return {
            "run": run,
            "messages": service.db.messages(run["conversation_id"], limit=10000),
        }

    @application.get("/api/health")
    def health() -> HealthResponse:
        return HealthResponse(service=settings.app_name)

    @application.get("/api/config")
    def config(request: Request):
        svc = service(request)
        return {
            "model": "gpt-6-luna",
            "reasoning_effort": "none",
            "configured": svc.engine.model is not None,
            "tracing_enabled": svc.trace_client is not None,
            "documents_count": len(
                {source.document_id for source in svc.catalog.sources}
            ),
        }

    @application.get("/api/topics")
    def topics(request: Request):
        return {"items": service(request).catalog.topics()}

    @application.post("/api/conversations", status_code=201)
    def create_conversation(request: Request):
        return service(request).db.create_conversation()

    @application.get("/api/conversations")
    def conversations(
        request: Request,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
    ):
        return {
            "items": service(request).db.rows(
                (
                    "SELECT * FROM conversations ORDER BY updated_at DESC,id DESC "
                    "LIMIT ? OFFSET ?"
                ),
                (limit, offset),
            )
        }

    @application.get("/api/conversations/{conversation_id}/messages")
    def messages(
        conversation_id: UUID,
        request: Request,
        limit: int = Query(200, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ):
        svc, cid = service(request), str(conversation_id)
        request.state.conversation_id = cid
        return {
            "items": svc.db.messages(cid, limit, offset),
            "run": svc.db.current_run(cid),
        }

    @application.get("/api/conversations/{conversation_id}/run")
    def current_run(conversation_id: UUID, request: Request):
        return service(request).db.current_run(str(conversation_id))

    @application.post("/api/conversations/{conversation_id}/messages")
    def send(conversation_id: UUID, body: SendMessage, request: Request):
        svc, cid = service(request), str(conversation_id)
        request.state.conversation_id = cid
        result = svc.send(cid, body.content, str(body.operation_id))
        request.state.run_id = result["run"]["id"]
        request.state.execution_id = result["run"].get("execution_id")
        return result

    @application.post("/api/conversations/{conversation_id}/resume")
    def resume(conversation_id: UUID, body: ResumeMessage, request: Request):
        cid = str(conversation_id)
        request.state.conversation_id = cid
        request.state.run_id = str(body.turn_id)
        result = service(request).resume(cid, body)
        request.state.execution_id = result["run"].get("execution_id")
        return result

    @application.post("/api/conversations/{conversation_id}/runs/{turn_id}/cancel")
    def cancel(conversation_id: UUID, turn_id: UUID, body: CancelRun, request: Request):
        request.state.conversation_id, request.state.run_id = (
            str(conversation_id),
            str(turn_id),
        )
        return service(request).cancel(
            str(conversation_id), str(turn_id), str(body.operation_id)
        )

    @application.get("/api/messages/{message_id}/references/{number}")
    def reference(message_id: str, number: int, request: Request):
        rows = service(request).db.rows(
            "SELECT refs FROM messages WHERE id=?", (message_id,)
        )
        refs = json.loads(rows[0]["refs"]) if rows else []
        for ref in refs:
            if ref["number"] == number:
                return ref
        raise NotFound("Reference not found")

    @application.get("/api/observability/runs")
    def runs(
        request: Request,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        window: Window = "all",
        status: str = Query(
            "", pattern="^(|running|awaiting_clarification|completed|failed|cancelled)$"
        ),
        search: str = Query("", max_length=200),
    ):
        db = service(request).db
        where, args = run_filter(window, status, search)
        items = [
            json.loads(row["data"])
            for row in db.rows(
                (
                    "SELECT data FROM conversation_runs WHERE "
                    + where
                    + " ORDER BY created_at DESC,id DESC "
                    "LIMIT ? OFFSET ?"
                ),
                (*args, limit, offset),
            )
        ]
        # Prototype: summarize the latest 1000 runs; report the window explicitly.
        window = [
            json.loads(row["data"])
            for row in db.rows(
                "SELECT data FROM conversation_runs ORDER BY created_at DESC LIMIT 1000"
            )
        ]
        active = [r["active_ms"] for r in window if r["status"] == "completed"]
        return {
            "items": items,
            "total": db.rows(
                "SELECT count(*) AS n FROM conversation_runs WHERE " + where, args
            )[0]["n"],
            "summary": {
                "count": len(window),
                "completed": sum(r["status"] == "completed" for r in window),
                "failed": sum(r["status"] == "failed" for r in window),
                "awaiting_clarification": sum(
                    r["status"] == "awaiting_clarification" for r in window
                ),
                "p50_active_ms": percentile(active, 0.5),
                "p95_active_ms": percentile(active, 0.95),
                "latency_sample_count": len(active),
                "window": "latest_1000_runs",
            },
        }

    @application.get("/api/observability/runs/{run_id}")
    def run_detail(
        run_id: UUID,
        request: Request,
        limit: int = Query(200, ge=1, le=500),
        event_offset: int = Query(0, ge=0),
        message_offset: int = Query(0, ge=0),
        request_offset: int = Query(0, ge=0),
    ):
        db, rid = service(request).db, str(run_id)
        run = db.run(rid)
        return {
            "run": run,
            "events": [
                {**row, "payload": json.loads(row["payload"])}
                for row in db.rows(
                    "SELECT * FROM run_events WHERE run_id=? "
                    "ORDER BY created_at,id LIMIT ? OFFSET ?",
                    (rid, limit, event_offset),
                )
            ],
            "requests": db.rows(
                "SELECT * FROM request_observations WHERE run_id=? "
                "ORDER BY created_at,id LIMIT ? OFFSET ?",
                (rid, limit, request_offset),
            ),
            "messages": [
                {**row, "references": json.loads(row["refs"])}
                for row in db.rows(
                    "SELECT * FROM messages WHERE run_id=? "
                    "ORDER BY sequence LIMIT ? OFFSET ?",
                    (rid, limit, message_offset),
                )
            ],
            "totals": {
                name: db.rows(
                    f"SELECT count(*) AS n FROM {table} WHERE run_id=?", (rid,)
                )[0]["n"]
                for name, table in (
                    ("events", "run_events"),
                    ("requests", "request_observations"),
                    ("messages", "messages"),
                )
            },
        }

    @application.post("/api/observability/requests/{request_id}/client")
    def client_measurement(request_id: UUID, body: ClientMeasurement, request: Request):
        db, rid = service(request).db, str(request_id)
        if not db.rows("SELECT id FROM request_observations WHERE id=?", (rid,)):
            raise NotFound("Request observation not found")
        db.execute(
            (
                "UPDATE request_observations SET "
                "client_ms=COALESCE(client_ms,?),client_outcome=COALESCE(client_outcome,?)"
                " WHERE id=?"
            ),
            (body.duration_ms, body.outcome, rid),
        )
        return {"ok": True}

    return application


app = create_app()
