"""Read-only, bounded queries for the local observability dashboard."""

import json
from collections import Counter, deque
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.observability import clean, percentile

router = APIRouter(prefix="/api/observability")
Window = Literal["1h", "24h", "7d", "all"]


def cutoff(window: Window):
    hours = {"1h": 1, "24h": 24, "7d": 168}
    return (
        (datetime.now(UTC) - timedelta(hours=hours[window])).isoformat()
        if window in hours
        else ""
    )


def run_filter(window="all", status="", search=""):
    return (
        "created_at >= ? AND (? = '' OR status = ?) AND "
        "(? = '' OR instr(lower(data), lower(?)) > 0)",
        (cutoff(window), status, status, search, search),
    )


def latency(values):
    values = [v for v in values if v is not None and v >= 0]
    return {
        "count": len(values),
        "p50_ms": percentile(values, 0.5),
        "p95_ms": percentile(values, 0.95),
    }


@router.get("/summary")
def summary(request: Request, window: Window = "24h"):
    db = request.app.state.service.db
    since = cutoff(window)
    rows = db.rows(
        "SELECT data FROM conversation_runs WHERE created_at >= ? "
        "ORDER BY created_at DESC,id DESC LIMIT 1000",
        (since,),
    )
    runs = [json.loads(row["data"]) for row in rows]
    counts = Counter(run["status"] for run in runs)
    requests = db.rows(
        "SELECT status,duration_ms,client_ms FROM request_observations "
        "WHERE created_at >= ? AND route NOT LIKE '/api/observability/%' "
        "ORDER BY created_at DESC,id DESC LIMIT 5000",
        (since,),
    )
    # Scope action/usage metrics to the exact same latest-1000-turn cohort.
    events = db.rows(
        "SELECT event,payload,duration_ms,run_id FROM run_events WHERE run_id IN "
        "(SELECT id FROM conversation_runs WHERE created_at >= ? "
        "ORDER BY created_at DESC,id DESC LIMIT 1000)",
        (since,),
    )
    providers, searches, retries, clarified = [], [], 0, set()
    stages = {}
    for event in events:
        payload = json.loads(event["payload"])
        name = event["event"]
        if name in {"model_call", "history_selection"}:
            providers.append({"event": name, **payload})
        if name == "document_search":
            searches.append(payload)
        if "retry" in name or name == "argument_correction":
            retries += 1
        if (
            name == "execution_finished"
            and payload.get("status") == "awaiting_clarification"
        ):
            clarified.add(event["run_id"])
        if name in {"model_call", "history_selection", "document_search"}:
            stages.setdefault(name, []).append(event["duration_ms"])
    end = datetime.now(UTC)
    start = (
        datetime.fromisoformat(since)
        if since
        else min(
            (datetime.fromisoformat(run["created_at"]) for run in runs),
            default=end - timedelta(hours=24),
        )
    )
    # An all-time cohort can be very recent; keep a readable minimum chart width.
    start = min(start, end - timedelta(minutes=1))
    width = (end - start).total_seconds() / 12
    buckets = [
        {
            "at": (start + timedelta(seconds=i * width)).isoformat(),
            "count": 0,
            "completed": 0,
            "failed": 0,
        }
        for i in range(12)
    ]
    for run in runs:
        index = max(
            0,
            min(
                11,
                int(
                    (datetime.fromisoformat(run["created_at"]) - start).total_seconds()
                    / width
                ),
            ),
        )
        buckets[index]["count"] += 1
        if run["status"] in {"completed", "failed"}:
            buckets[index][run["status"]] += 1
    usage = {}
    for field in (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "reasoning_tokens",
    ):
        values = [p.get(field) for p in providers]
        known = [v for v in values if isinstance(v, (int, float))]
        usage[field] = {"total": sum(known) if known else None, "known": len(known)}
    successful = [r for r in requests if 200 <= r["status"] < 300]
    return {
        "window": window,
        "since": start.isoformat(),
        "until": end.isoformat(),
        "run_limit": 1000,
        "request_limit": 5000,
        "count": len(runs),
        "statuses": {
            s: counts[s]
            for s in (
                "completed",
                "failed",
                "running",
                "awaiting_clarification",
                "cancelled",
            )
        },
        "sessions": len({r["conversation_id"] for r in runs}),
        "latency": {
            "agent": latency(
                [r.get("active_ms") for r in runs if r["status"] == "completed"]
            ),
            "server": latency([r["duration_ms"] for r in successful]),
            "client": latency([r["client_ms"] for r in successful]),
        },
        "requests": len(requests),
        "http_errors": sum(r["status"] >= 400 for r in requests),
        "events": len(events),
        "provider_calls": len(providers),
        "usage": usage,
        "searches": len(searches),
        "no_results": sum(p.get("result_count") == 0 for p in searches),
        "clarified_turns": len(clarified),
        "corrections_and_retries": retries,
        "stages": [{"name": k, **latency(v)} for k, v in stages.items()],
        "buckets": buckets,
    }


# SQLite records have outcomes, not logger severity. Classify explicitly for triage.
LOG_CTE = """
WITH records AS (
    SELECT e.id,e.created_at,e.event,e.run_id,r.conversation_id,e.execution_id,
        e.duration_ms,e.payload,'action' AS source,
        CASE WHEN json_extract(e.payload,'$.outcome') = 'failed'
              OR json_extract(e.payload,'$.status') = 'failed'
              OR e.event LIKE '%failed%' THEN 'error'
             WHEN e.event LIKE '%retry%' OR e.event = 'argument_correction'
              THEN 'warning' ELSE 'info' END AS level
    FROM run_events e JOIN conversation_runs r ON r.id = e.run_id
    UNION ALL
    SELECT id,created_at,route,run_id,conversation_id,execution_id,duration_ms,
        json_object('request_id',id,'proxy_id',proxy_id,'status',status,
                    'client_ms',client_ms,'client_outcome',client_outcome),
        'http',CASE WHEN status >= 500 THEN 'error'
                    WHEN status >= 400 THEN 'warning' ELSE 'info' END
    FROM request_observations WHERE route NOT LIKE '/api/observability/%'
)
"""


@router.get("/logs")
def logs(
    request: Request,
    window: Window = "24h",
    source: Literal["sqlite", "application"] = "sqlite",
    level: Literal["all", "info", "warning", "error"] = "all",
    search: str = Query("", max_length=200),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    svc = request.app.state.service
    since = cutoff(window)
    if source == "application":
        # Fixed files only. Rotation bounds disk reads to 8 MB; retain at most 5000.
        records = deque(maxlen=5000)
        for suffix in (".3", ".2", ".1", ""):
            path = svc.settings.data_dir / "logs" / f"application.jsonl{suffix}"
            try:
                with path.open("rb") as stream:
                    stream.seek(0, 2)
                    start = max(0, stream.tell() - 2_000_000)
                    stream.seek(start)
                    if start:
                        stream.readline()  # Discard a potentially partial first line.
                    lines = (
                        stream.read(2_000_000)
                        .decode("utf-8", errors="replace")
                        .splitlines()
                    )
                for line in lines:
                    try:
                        item = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    if isinstance(item, dict) and isinstance(
                        item.get("timestamp"), str
                    ):
                        records.append(clean(item))
            except FileNotFoundError:
                continue  # A concurrent rotation may remove a backup between reads.
        items = []
        for item in reversed(records):
            severity = item.get("level", "INFO").lower()
            severity = "error" if severity == "critical" else severity
            if item.get("timestamp", "") < since:
                continue
            if level != "all" and severity != level:
                continue
            if search.lower() not in json.dumps(item).lower():
                continue
            items.append(
                {
                    "id": sha256(json.dumps(item, sort_keys=True).encode()).hexdigest(),
                    "created_at": item.get("timestamp"),
                    "event": item.get("event", "log"),
                    "level": severity,
                    "run_id": item.get("run_id"),
                    "conversation_id": item.get("conversation_id"),
                    "execution_id": item.get("execution_id"),
                    "duration_ms": item.get("duration_ms"),
                    "source": "application",
                    "payload": clean(item),
                }
            )
        return {
            "items": items[offset : offset + limit],
            "total": len(items),
            "source": source,
            "scan_limit": 5000,
        }
    where = (
        "created_at >= ? AND (? = 'all' OR level = ?) AND "
        "(? = '' OR instr(lower(event || ' ' || id || ' ' || coalesce(run_id,'') "
        "|| ' ' || coalesce(conversation_id,'') || ' ' || coalesce(execution_id,'') "
        "|| ' ' || payload),lower(?)) > 0)"
    )
    args = (since, level, level, search, search)
    total = svc.db.rows(
        LOG_CTE + "SELECT count(*) AS n FROM records WHERE " + where, args
    )[0]["n"]
    items = svc.db.rows(
        LOG_CTE
        + "SELECT * FROM records WHERE "
        + where
        + " ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?",
        (*args, limit, offset),
    )
    for item in items:
        item["payload"] = json.loads(item["payload"])
    return {"items": items, "total": total, "source": source, "scan_limit": None}
