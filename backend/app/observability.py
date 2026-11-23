import json
import logging
import re
from contextlib import contextmanager
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from time import perf_counter

from app.database import Database, now, uid

request_context: ContextVar[dict] = ContextVar("request_context", default={})
execution_context: ContextVar[dict] = ContextVar("execution_context", default={})
logger = logging.getLogger("floor_supervisor")


def clean(value):
    if isinstance(value, dict):
        return {
            k: (
                "[REDACTED]"
                if re.search(r"secret|password|api.?key|authorization|cookie", k, re.I)
                else clean(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value[:100]]
    if isinstance(value, str):
        return re.sub(
            r"(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+\S+)", "[REDACTED]", value, flags=re.I
        )[:4000]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": now(),
                "level": record.levelname,
                "event": record.getMessage(),
                **clean(getattr(record, "fields", {})),
            }
        )


def configure_logging(directory):
    directory.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler) and handler.baseFilename != str(
            (directory / "application.jsonl").resolve()
        ):
            logger.removeHandler(handler)
            handler.close()
    if not any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers):
        handler = RotatingFileHandler(
            directory / "application.jsonl",
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False


def close_logging(directory):
    target = str((directory / "application.jsonl").resolve())
    for handler in list(logger.handlers):
        if isinstance(handler, RotatingFileHandler) and handler.baseFilename == target:
            logger.removeHandler(handler)
            handler.close()


class Observer:
    def __init__(self, db: Database):
        self.db = db

    def emit(self, event: str, payload=None, duration_ms=None, event_id=None):
        context = execution_context.get()
        payload = clean(payload or {})
        logger.info(
            event,
            extra={
                "fields": {
                    **request_context.get(),
                    **context,
                    "duration_ms": duration_ms,
                }
            },
        )
        if context.get("run_id"):
            return self.db.event(
                context["run_id"],
                context["execution_id"],
                event,
                payload,
                duration_ms,
                context.get("parent_span_id"),
                event_id,
            )
        return None

    @contextmanager
    def span(self, event: str, payload=None):
        parent = execution_context.get()
        span_id = uid()
        token = execution_context.set({**parent, "parent_span_id": span_id})
        started = perf_counter()
        outcome = dict(payload or {})
        try:
            yield outcome
        except Exception as exc:
            outcome.update(outcome="failed", error_type=type(exc).__name__)
            raise
        finally:
            execution_context.reset(token)
            elapsed = (perf_counter() - started) * 1000
            context = execution_context.get()
            if context.get("run_id"):
                self.db.execute(
                    "INSERT OR IGNORE INTO run_events VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        span_id,
                        context["run_id"],
                        context["execution_id"],
                        span_id,
                        context.get("parent_span_id"),
                        event,
                        now(),
                        elapsed,
                        json.dumps(clean(outcome)),
                    ),
                )
            logger.info(
                event,
                extra={
                    "fields": {
                        **request_context.get(),
                        **context,
                        "duration_ms": elapsed,
                        "outcome": outcome.get("outcome", "ok"),
                    }
                },
            )


def percentile(values: list[float], fraction: float):
    import math

    if not values:
        return None
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]
