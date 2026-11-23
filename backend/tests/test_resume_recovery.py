from uuid import uuid4

from fastapi.testclient import TestClient
from test_api import ScriptedModel, conversation

from app.config import Settings
from app.main import create_app


def waiting_turn(client):
    cid = conversation(client)
    send = {"content": "What should I check?", "operation_id": str(uuid4())}
    data = client.post(f"/api/conversations/{cid}/messages", json=send).json()
    run = data["run"]
    reply = {
        "turn_id": run["id"],
        "interrupt_id": run["interrupt_id"],
        "version": run["version"],
        "content": "CV 01 after servicing",
        "operation_id": str(uuid4()),
    }
    return cid, send, reply


def test_original_send_retry_retains_clarification(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path, openai_api_key=None)
    model = ScriptedModel(clarify=True)
    with TestClient(create_app(settings, model=model)) as client:
        cid, send, reply = waiting_turn(client)
        model.fail = True
        failed = client.post(f"/api/conversations/{cid}/resume", json=reply).json()
        assert failed["run"]["status"] == "failed"
        model.fail = False
        result = client.post(f"/api/conversations/{cid}/messages", json=send).json()
        assert result["run"]["status"] == "completed", result
        assert [m["kind"] for m in result["messages"]] == [
            "question",
            "clarification",
            "reply",
            "answer",
        ]


def test_crash_after_accepting_reply_can_resume_once(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, data_dir=tmp_path, openai_api_key=None)
    with TestClient(create_app(settings, model=ScriptedModel(clarify=True))) as client:
        cid, _, reply = waiting_turn(client)

        def crash(*args):
            raise RuntimeError("Simulated crash after reply transaction")

        monkeypatch.setattr(client.app.state.service, "execute", crash)
        response = client.post(f"/api/conversations/{cid}/resume", json=reply)
        assert response.status_code == 500
    with TestClient(create_app(settings, model=ScriptedModel())) as client:
        restored = client.get(f"/api/conversations/{cid}/run").json()
        assert restored["status"] == "awaiting_clarification"
        response = client.post(f"/api/conversations/{cid}/resume", json=reply)
        assert response.json()["run"]["status"] == "completed", response.json()
        kinds = [m["kind"] for m in response.json()["messages"]]
        assert kinds == ["question", "clarification", "reply", "answer"]
