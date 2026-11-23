import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage
from review_fakes import FakeEvidenceReviewer

from app.config import Settings
from app.main import create_app
from app.observability import clean


class ScriptedModel:
    def __init__(self, clarify=False, fail=False):
        self.clarify = clarify
        self.fail = fail

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        return FakeEvidenceReviewer()

    def invoke(self, messages):
        if self.fail:
            raise RuntimeError("internal failure with sk-test-secret-should-not-leak")
        last = messages[-1]
        if self.clarify:
            self.clarify = False
            name, args = (
                "request_clarification",
                {"question": "Which machine and task?"},
            )
        elif isinstance(last, ToolMessage) and '"sources"' in last.content:
            source = json.loads(last.content)["sources"][0]
            name = "submit_answer"
            args = {
                ("answer"): (
                    "This demonstration document requires approved task instructions."
                ),
                "evidence_status": "grounded",
                "selected_topic_ids": [source["topic_id"]],
                "source_ids": [source["source_id"]],
            }
        else:
            name, args = (
                "search_documents",
                {
                    "query": "energy isolation servicing guards",
                    "topic_ids": ["safety"],
                    "document_ids": [],
                    "limit": 1,
                },
            )
        return AIMessage(
            content="",
            tool_calls=[{"id": str(uuid4()), "name": name, "args": args}],
            usage_metadata={
                "input_tokens": 100,
                "output_tokens": 30,
                "total_tokens": 130,
            },
        )


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None, data_dir=tmp_path, openai_api_key=None, langsmith_tracing=False
    )


def conversation(client):
    return client.post("/api/conversations", json={}).json()["id"]


def test_answer_history_citations_and_observability(settings):
    with TestClient(create_app(settings, model=ScriptedModel())) as client:
        cid = conversation(client)
        payload = {
            "content": "What are the energy isolation requirements?",
            "operation_id": str(uuid4()),
        }
        result = client.post(f"/api/conversations/{cid}/messages", json=payload)
        assert result.status_code == 200
        data = result.json()
        assert data["run"]["status"] == "completed", data
        assert data["run"]["reasoning_effort"] == "none"
        assert data["run"]["input_tokens"] == 300
        assert len(data["messages"]) == 2
        assert data["messages"][-1]["references"][0]["quote"]
        request_id = result.headers["X-Request-ID"]
        assert "app;dur=" in result.headers["Server-Timing"]
        assert (
            client.post(
                f"/api/observability/requests/{request_id}/client",
                json={"duration_ms": 123, "outcome": "completed"},
            ).status_code
            == 200
        )
        detail = client.get(f"/api/observability/runs/{data['run']['id']}").json()
        assert {"model_call", "document_search", "answer_validated"} <= {
            e["event"] for e in detail["events"]
        }
        assert detail["requests"][0]["client_ms"] == 123
        assert all(e["execution_id"] for e in detail["events"])
        assert (
            client.post(f"/api/conversations/{cid}/messages", json=payload).json()[
                "messages"
            ]
            == data["messages"]
        )
        summary = client.get("/api/observability/runs").json()["summary"]
        assert summary["completed"] == 1
        assert summary["latency_sample_count"] == 1


def test_pause_restart_resume_and_duplicate_reply(settings):
    with TestClient(create_app(settings, model=ScriptedModel(clarify=True))) as client:
        cid = conversation(client)
        result = client.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "What should I check?", "operation_id": str(uuid4())},
        ).json()
        run = result["run"]
        assert run["status"] == "awaiting_clarification"
        assert len(result["messages"]) == 2
    with TestClient(create_app(settings, model=ScriptedModel())) as client:
        waiting = client.get(f"/api/conversations/{cid}/run").json()
        assert waiting["interrupt_id"] == run["interrupt_id"]
        payload = {
            "turn_id": run["id"],
            "interrupt_id": run["interrupt_id"],
            "version": waiting["version"],
            "content": "CV 01 after servicing",
            "operation_id": str(uuid4()),
        }
        reply = client.post(f"/api/conversations/{cid}/resume", json=payload)
        assert reply.status_code == 200, reply.text
        assert reply.json()["run"]["status"] == "completed", reply.json()
        assert len(reply.json()["messages"]) == 4
        again = client.post(f"/api/conversations/{cid}/resume", json=payload)
        assert len(again.json()["messages"]) == 4
        payload["operation_id"] = str(uuid4())
        assert (
            client.post(f"/api/conversations/{cid}/resume", json=payload).status_code
            == 409
        )


def test_cancel_and_new_turn(settings):
    with TestClient(create_app(settings, model=ScriptedModel(clarify=True))) as client:
        cid = conversation(client)
        result = client.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "Check what?", "operation_id": str(uuid4())},
        ).json()
        run = result["run"]
        cancel = client.post(
            f"/api/conversations/{cid}/runs/{run['id']}/cancel",
            json={"operation_id": str(uuid4())},
        )
        assert cancel.json()["run"]["status"] == "cancelled"
        answer = client.post(
            f"/api/conversations/{cid}/messages",
            json={
                "content": "What are energy isolation requirements?",
                "operation_id": str(uuid4()),
            },
        )
        assert answer.json()["run"]["status"] == "completed", answer.json()


def test_retry_failed_resume_preserves_clarification(settings):
    model = ScriptedModel(clarify=True)
    with TestClient(create_app(settings, model=model)) as client:
        cid = conversation(client)
        waiting = client.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "What should I check?", "operation_id": str(uuid4())},
        ).json()["run"]
        reply = {
            "turn_id": waiting["id"],
            "interrupt_id": waiting["interrupt_id"],
            "version": waiting["version"],
            "content": "CV 01 after servicing",
            "operation_id": str(uuid4()),
        }
        model.fail = True
        failed = client.post(f"/api/conversations/{cid}/resume", json=reply).json()
        assert failed["run"]["status"] == "failed"
        assert len(failed["messages"]) == 3
        model.fail = False
        retried = client.post(f"/api/conversations/{cid}/resume", json=reply).json()
        assert retried["run"]["status"] == "completed", retried
        assert [m["kind"] for m in retried["messages"]] == [
            "question",
            "clarification",
            "reply",
            "answer",
        ]


def test_failure_saved_and_retry_no_duplicate(settings):
    model = ScriptedModel(fail=True)
    with TestClient(create_app(settings, model=model)) as client:
        cid = conversation(client)
        payload = {"content": "Energy isolation?", "operation_id": str(uuid4())}
        failed = client.post(f"/api/conversations/{cid}/messages", json=payload).json()
        assert failed["run"]["status"] == "failed"
        assert "sk-test" not in failed["run"]["error"]
        assert len(failed["messages"]) == 1
        model.fail = False
        completed = client.post(
            f"/api/conversations/{cid}/messages", json=payload
        ).json()
        assert completed["run"]["id"] == failed["run"]["id"]
        assert len(completed["messages"]) == 2
        assert completed["run"]["status"] == "completed"


def test_request_validation_and_missing_ids(settings):
    with TestClient(create_app(settings, model=ScriptedModel())) as client:
        cid = conversation(client)
        assert (
            client.post(
                f"/api/conversations/{cid}/messages",
                json={"content": " ", "operation_id": str(uuid4())},
            ).status_code
            == 422
        )
        assert client.get(f"/api/conversations/{uuid4()}/messages").status_code == 404
        assert client.get("/api/conversations?limit=9999").status_code == 422
        result = client.get("/api/config")
        assert result.json()["documents_count"] == 3
        assert result.json()["reasoning_effort"] == "none"


def test_sanitization_and_no_key(settings, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert clean(
        {"Authorization": "Bearer something", "query": "sk-12345678901234"}
    ) == {"Authorization": "[REDACTED]", "query": "[REDACTED]"}
    with TestClient(create_app(settings)) as client:
        cid = conversation(client)
        result = client.post(
            f"/api/conversations/{cid}/messages",
            json={"content": "How?", "operation_id": str(uuid4())},
        ).json()
        assert result["run"]["status"] == "failed"
        assert "OPENAI_API_KEY" in result["run"]["error"]
