"""Dashboard queries use real SQLite fixtures and never invoke a provider."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import now, uid
from app.main import create_app


def seed(db):
    runs = []
    for status, active in (
        ("completed", 100),
        ("completed", 900),
        ("failed", 8000),
        ("awaiting_clarification", 20),
        ("cancelled", 10),
        ("running", 0),
    ):
        cid = db.create_conversation()["id"]
        run, _ = db.start_turn(cid, f"Inspect energy isolation: {status}", uid())
        run.update(status=status, active_ms=active, wait_ms=60000)
        with db.connect() as conn:
            db.save_run(run, conn)
        db.event(
            run["id"],
            "execution-one",
            "model_call",
            {"input_tokens": 100, "output_tokens": None},
            50,
        )
        db.event(
            run["id"],
            "execution-one",
            "document_search",
            {"result_count": 0 if status == "failed" else 2},
            10,
        )
        if status == "failed":
            db.event(
                run["id"],
                "execution-one",
                "execution_failed",
                {"outcome": "failed", "error_category": "Timeout"},
                8000,
            )
        if status == "awaiting_clarification":
            db.event(
                run["id"],
                "execution-one",
                "execution_finished",
                {"status": status},
                active,
            )
        runs.append(run)
    # Outside the selected time window; must not contaminate summary or logs.
    old = runs[-1].copy()
    old["created_at"] = (datetime.now(UTC) - timedelta(days=9)).isoformat()
    db.execute(
        "UPDATE conversation_runs SET created_at=?,data=? WHERE id=?",
        (old["created_at"], json.dumps(old), old["id"]),
    )
    for status, server, client, route in (
        (200, 100, 150, "/api/conversations"),
        (201, 300, None, "/api/conversations"),
        (500, 9000, None, "/api/conversations"),
        (200, 99999, 99999, "/api/observability/summary"),
    ):
        db.execute(
            "INSERT INTO request_observations VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                uid(),
                runs[0]["conversation_id"],
                runs[0]["id"],
                "execution-one",
                uid(),
                route,
                status,
                server,
                client,
                None,
                now(),
            ),
        )
    return runs


@pytest.fixture
def inspector(tmp_path):
    settings = Settings(
        _env_file=None, data_dir=tmp_path, openai_api_key=None, langsmith_tracing=False
    )
    with TestClient(create_app(settings)) as client:
        yield client, client.app.state.service.db, settings


def test_empty_summary_preserves_unknown_measurements(inspector):
    client, _, _ = inspector
    summary = client.get("/api/observability/summary").json()
    assert summary["count"] == summary["events"] == summary["provider_calls"] == 0
    assert summary["latency"]["agent"] == {"count": 0, "p50_ms": None, "p95_ms": None}
    assert summary["usage"]["input_tokens"] == {"total": None, "known": 0}
    assert len(summary["buckets"]) == 12


def test_known_metrics_exclude_wait_failed_latency_and_inspector_traffic(inspector):
    client, db, _ = inspector
    seed(db)
    response = client.get("/api/observability/summary?window=24h")
    assert response.status_code == 200
    s = response.json()
    assert s["count"] == 5 and s["sessions"] == 5
    assert s["statuses"] == {
        "completed": 2,
        "failed": 1,
        "cancelled": 1,
        "awaiting_clarification": 1,
        "running": 0,
    }
    assert s["latency"]["agent"] == {"count": 2, "p50_ms": 100, "p95_ms": 900}
    assert s["latency"]["server"] == {"count": 2, "p50_ms": 100, "p95_ms": 300}
    assert s["latency"]["client"] == {"count": 1, "p50_ms": 150, "p95_ms": 150}
    assert s["requests"] == 3 and s["http_errors"] == 1
    assert s["usage"]["input_tokens"] == {"total": 500, "known": 5}
    assert s["usage"]["output_tokens"] == {"total": None, "known": 0}
    assert s["no_results"] == s["clarified_turns"] == 1
    assert sum(b["count"] for b in s["buckets"]) == 5
    assert client.get("/api/observability/summary?window=all").json()["count"] == 6


def test_trace_filtering_and_independent_detail_pagination(inspector):
    client, db, _ = inspector
    runs = seed(db)
    result = client.get(
        "/api/observability/runs?window=24h&status=completed&limit=1"
    ).json()
    assert result["total"] == 2 and len(result["items"]) == 1
    second = client.get(
        "/api/observability/runs?window=24h&status=completed&limit=1&offset=1"
    ).json()
    assert result["items"][0]["id"] != second["items"][0]["id"]
    cid = runs[0]["conversation_id"]
    assert client.get(f"/api/observability/runs?search={cid}").json()["total"] == 1
    # Search is literal and parameterized, including SQL and wildcard characters.
    assert (
        client.get("/api/observability/runs", params={"search": "%' OR 1=1 --"}).json()[
            "total"
        ]
        == 0
    )
    rid = runs[0]["id"]
    detail = client.get(f"/api/observability/runs/{rid}?limit=1").json()
    assert detail["totals"] == {"events": 2, "messages": 1, "requests": 4}
    next_page = client.get(
        f"/api/observability/runs/{rid}?limit=1&event_offset=1"
    ).json()
    assert detail["events"][0]["id"] != next_page["events"][0]["id"]
    assert detail["messages"] == next_page["messages"]


def test_sqlite_log_classification_and_correlated_search(inspector):
    client, db, _ = inspector
    runs = seed(db)
    result = client.get("/api/observability/logs?level=error&window=24h&limit=1").json()
    assert result["total"] == 2 and len(result["items"]) == 1
    records = client.get("/api/observability/logs?level=error&window=24h").json()[
        "items"
    ]
    assert {r["source"] for r in records} == {"http", "action"}
    assert all(r["level"] == "error" for r in records)
    rid = runs[0]["id"]
    matches = client.get(f"/api/observability/logs?search={rid}").json()["items"]
    assert len(matches) == 5
    assert all(r["run_id"] == rid for r in matches)
    assert not any(r["event"].startswith("/api/observability") for r in matches)


def test_rotating_application_logs_are_bounded_and_malformed_lines_skipped(inspector):
    client, _, settings = inspector
    directory = settings.data_dir / "logs"
    (directory / "application.jsonl.1").write_text(
        json.dumps({"timestamp": now(), "level": "WARNING", "event": "older"}) + "\n",
        encoding="utf-8",
    )
    record = {
        "timestamp": now(),
        "level": "ERROR",
        "event": "provider_failed",
        "api_key": "sentinel-credential",
        "run_id": uid(),
    }
    (directory / "application.jsonl").write_text(
        "partial line\n[]\nnull\n" + json.dumps(record) + "\n", encoding="utf-8"
    )
    result = client.get("/api/observability/logs?source=application&level=error").json()
    assert result["scan_limit"] == 5000 and result["total"] == 1
    assert result["items"][0]["payload"]["api_key"] == "[REDACTED]"
    assert result["items"][0]["run_id"] == record["run_id"]


@pytest.mark.parametrize(
    "path",
    [
        "/summary?window=invalid",
        "/runs?limit=0",
        "/runs?status=invalid",
        "/logs?source=../outside",
        "/logs?level=invalid",
        "/logs?limit=201",
    ],
)
def test_invalid_filters_are_rejected(inspector, path):
    client, _, _ = inspector
    assert client.get("/api/observability" + path).status_code == 422
