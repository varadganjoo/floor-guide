"""Offline contract tests for retrieval, graph durability, and model requests."""

import json
import sqlite3
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command
from openai import OpenAI
from pydantic import ValidationError
from review_fakes import FakeEvidenceReviewer

from app.agent import AgentEngine, AgentFailure, TransientSearchError, make_model
from app.config import PROJECT_ROOT, Settings
from app.database import Conflict, Database
from app.documents import DocumentCatalog, import_manifest, token_count
from app.observability import execution_context, logger, request_context
from app.schemas import (
    ClarificationRequest,
    GroundedAnswer,
    ResumeMessage,
    SearchDocumentsInput,
    SendMessage,
)


class FakeModel:
    """Only the provider boundary is replaced; graph and tools remain real."""

    def __init__(self, *actions):
        self.actions = iter(actions)
        self.inputs = []
        self.binding = None

    def bind_tools(self, tools, **kwargs):
        self.binding = ([tool.name for tool in tools], kwargs)
        return self

    def with_structured_output(self, schema, **kwargs):
        return FakeEvidenceReviewer()

    def invoke(self, messages):
        self.inputs.append(messages)
        name, args = next(self.actions)
        if callable(args):
            args = args(messages)
        return AIMessage(
            content="", tool_calls=[{"id": str(uuid4()), "name": name, "args": args}]
        )


class FakeDecisions:
    def __init__(self, probability=0.0):
        self.probability = probability
        self.calls = []
        self.decisions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            answers=[
                SimpleNamespace(
                    type="predicate", name=q["name"], probability=self.probability
                )
                for q in kwargs["questions"]
            ],
            usage=None,
        )


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "application.sqlite3")


@pytest.fixture
def catalog(db):
    import_manifest(db, PROJECT_ROOT / "backend" / "documents.json")
    return DocumentCatalog(db)


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path, openai_api_key=None)


@pytest.fixture
def engine_factory(db, catalog, settings):
    engines = []

    def factory(model=None, decisions=None):
        engine = AgentEngine(
            db,
            catalog,
            settings,
            model=model or FakeModel(),
            decisions=decisions or FakeDecisions(),
        )
        engines.append(engine)
        return engine

    yield factory
    for engine in engines:
        engine.close()


def new_run(db, content="What should I inspect?"):
    conversation = db.create_conversation()
    return db.start_turn(conversation["id"], content, str(uuid4()))[0]


def search_args(**overrides):
    return {
        "query": "isolation",
        "topic_ids": ["safety"],
        "document_ids": [],
        "limit": 2,
        **overrides,
    }


def abstention():
    return {
        "evidence_status": "insufficient_evidence",
        "answer": "Evidence is missing.",
        "selected_topic_ids": [],
        "references": [],
    }


def test_import_adds_fourth_topic_without_code_changes(db, tmp_path):
    manifest = json.loads((PROJECT_ROOT / "backend/documents.json").read_text())
    fourth = {
        "id": "utilities_4",
        "name": "Utilities",
        "description": "Water systems",
        "documents": [
            {
                "id": "utilities-manual",
                ("path"): (
                    "plant_document_examples/documents/Plant_Maintenance_Manual.docx"
                ),
            }
        ],
    }
    manifest["topics"].append(fourth)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    conversation = db.create_conversation()
    import_manifest(db, path)
    import_manifest(db, path)
    catalog = DocumentCatalog(db)
    assert len(catalog.topics()) == 4
    assert (
        next(t for t in catalog.topics() if t["id"] == "utilities_4")["description"]
        == "Water systems"
    )
    result = catalog.search(
        SearchDocumentsInput(
            **search_args(
                query="maintenance",
                topic_ids=["utilities_4"],
                document_ids=["utilities-manual"],
            )
        )
    )
    assert result.status == "ok"
    assert {s.topic_id for s in result.sources} == {"utilities_4"}
    assert {s.document_id for s in result.sources} == {"utilities-manual"}
    assert db.conversation(conversation["id"])["id"] == conversation["id"]


def test_real_documents_preserve_sections_tables_and_example_status(catalog):
    safety = next(
        s
        for s in catalog.sources
        if s.document_id == "plant-safety"
        and s.heading == "3 Safe production and hazardous energy"
    )
    assert "Routine production" in safety.excerpt
    assert "Energy isolation for servicing" in safety.excerpt
    assert "EXAMPLE ONLY" in safety.excerpt
    quality = next(
        s
        for s in catalog.sources
        if s.document_id == "plant-quality"
        and s.heading == "2 Example bracket acceptance criteria"
    )
    assert "Table columns:" in quality.excerpt
    assert " | " in quality.excerpt
    assert "mm" in quality.excerpt
    assert quality.demonstration is True
    assert len(quality.document_hash) == 64
    assert quality.document_hash[:12] in quality.source_id
    assert not catalog.errors


def test_search_no_results_and_permanent_catalog_errors_are_distinct(db, catalog):
    missing = catalog.search(SearchDocumentsInput(**search_args(query="zxqv987")))
    assert missing.status == "no_results"
    assert missing.sources == []
    assert missing.truncated is False
    for args in [
        search_args(topic_ids=["unknown"]),
        search_args(document_ids=["plant-quality"]),
    ]:
        with pytest.raises(ValueError):
            catalog.search(SearchDocumentsInput(**args))
    db.execute("UPDATE topics SET active=0 WHERE id='safety'")
    with pytest.raises(ValueError, match="inactive"):
        catalog.search(SearchDocumentsInput(**search_args()))


def test_evidence_budget_omits_whole_sections(catalog):
    result = catalog.search(SearchDocumentsInput(**search_args()), budget=1)
    assert result.sources == []
    assert result.truncated is True


def test_multi_source_search_reserves_evidence_for_both_types(catalog):
    result = catalog.search(
        SearchDocumentsInput(
            **search_args(
                query=(
                    "overdue inspection gauge used on parts equipment remove from "
                    "service calibration status impact review previously "
                    "inspected product"
                ),
                topic_ids=["maintenance", "quality"],
                limit=6,
            )
        )
    )
    assert {s.topic_id for s in result.sources} == {"maintenance", "quality"}
    assert any("Identify and quarantine the gauge" in s.excerpt for s in result.sources)
    assert result.uncovered_topic_ids == []
    assert sum(token_count(s.excerpt) for s in result.sources) <= 6000


def test_multi_source_budget_shortfall_is_explicit(catalog):
    result = catalog.search(
        SearchDocumentsInput(
            **search_args(topic_ids=["maintenance", "quality"], query="inspection")
        ),
        budget=1,
    )
    assert set(result.uncovered_topic_ids) == {"maintenance", "quality"}
    assert result.truncated


def test_followup_can_narrow_topic_scope_without_losing_earlier_sources(
    db, engine_factory
):
    engine = engine_factory()
    state = engine.initial(new_run(db))
    state["action"] = {
        "id": "search-1",
        "name": "search_documents",
        "args": search_args(topic_ids=["safety", "maintenance"], query="isolation"),
    }
    state.update(engine.search(state))
    previous = set(state["sources"])
    state["action"] = {
        "id": "search-2",
        "name": "search_documents",
        "args": search_args(topic_ids=["maintenance", "quality"], query="inspection"),
    }
    state.update(engine.search(state))
    assert state["requested_topic_ids"] == ["maintenance", "quality"]
    assert previous <= set(state["sources"])


def test_topic_parameter_is_an_array_and_rejects_duplicate_ids():
    schema = SearchDocumentsInput.model_json_schema()
    assert schema["properties"]["topic_ids"]["type"] == "array"
    with pytest.raises(ValidationError):
        SearchDocumentsInput(**search_args(topic_ids="safety"))
    with pytest.raises(ValidationError):
        SearchDocumentsInput(**search_args(topic_ids=["safety", "safety"]))


def test_insufficient_evidence_explicitly_informs_user(db, engine_factory):
    engine = engine_factory()
    state = engine.initial(new_run(db))
    state["action"] = {"id": "answer", "name": "submit_answer", "args": abstention()}
    result = engine.finish(state)["answer"]
    assert result["answer"].startswith("I don't have enough information")
    assert result["evidence_status"] == "insufficient_evidence"


@pytest.mark.parametrize(
    "text",
    [
        "I don\u2019t have enough information to name the location.",
        "I do not have enough information to provide a value.",
    ],
)
def test_insufficient_information_notice_is_not_duplicated(db, engine_factory, text):
    engine = engine_factory()
    state = engine.initial(new_run(db))
    state["action"] = {
        "id": "answer",
        "name": "submit_answer",
        "args": {**abstention(), "answer": text},
    }
    assert engine.finish(state)["answer"]["answer"] == text


def test_cannot_claim_complete_answer_with_uncovered_requested_type(
    db, catalog, engine_factory
):
    engine = engine_factory()
    source = next(s for s in catalog.sources if s.topic_id == "quality")
    state = engine.initial(new_run(db))
    state.update(
        requested_topic_ids=["maintenance", "quality"],
        sources={source.source_id: source.model_dump()},
        action={
            "id": "answer",
            "name": "submit_answer",
            "args": {
                "evidence_status": "grounded",
                "answer": "Partial answer.",
                "selected_topic_ids": ["quality"],
                "references": [
                    {"source_id": source.source_id, "quote": source.excerpt[:40]}
                ],
            },
        },
    )
    correction = engine.finish(state)
    assert "answer" not in correction
    assert "maintenance" in correction["messages"][-1].content


def test_followup_search_returns_new_evidence_without_repeating_sections(catalog):
    args = SearchDocumentsInput(**search_args(query="maintenance production checks"))
    first = catalog.search(args)
    assert first.sources
    seen = {source.source_id for source in first.sources}
    second = catalog.search(args, exclude=seen)
    assert not seen.intersection(source.source_id for source in second.sources)
    assert second.sources
    assert sum(token_count(source.excerpt) for source in second.sources) <= 6000


def test_unavailable_document_is_an_explicit_error(db, catalog):
    db.execute("UPDATE documents SET available=0 WHERE id='plant-safety'")
    with pytest.raises(ValueError, match="unavailable"):
        catalog.search(SearchDocumentsInput(**search_args()))


@pytest.mark.parametrize(
    "patch",
    [
        {"query": "  "},
        {"limit": 0},
        {"limit": 7},
        {"topic_ids": []},
        {"topic_ids": ["../../secret"]},
        {"path": ".env"},
        {"query": "x" * 1001},
    ],
)
def test_search_schema_rejects_invalid_arguments(patch):
    with pytest.raises(ValidationError):
        SearchDocumentsInput(**search_args(**patch))


@pytest.mark.parametrize(
    "model,payload",
    [
        (ClarificationRequest, {"question": " "}),
        (SendMessage, {"content": "hello", "operation_id": "not-a-uuid"}),
        (
            ResumeMessage,
            {
                "content": "asset",
                "operation_id": str(uuid4()),
                "turn_id": str(uuid4()),
                "interrupt_id": "interrupt",
                "version": 0,
            },
        ),
        (GroundedAnswer, {**abstention(), "evidence_status": "guessed"}),
    ],
)
def test_request_schemas_reject_invalid_payloads(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_database_duplicate_sends_and_active_turn_exclusion(db):
    conversation = db.create_conversation()["id"]
    other = db.create_conversation()["id"]
    operation = str(uuid4())
    run, fresh = db.start_turn(conversation, "Inspect asset", operation)
    replay, replay_fresh = db.start_turn(conversation, "Inspect asset", operation)
    assert fresh is True and replay_fresh is False
    assert replay["id"] == run["id"]
    assert [m["content"] for m in db.messages(conversation)] == ["Inspect asset"]
    with pytest.raises(Conflict, match="another request"):
        db.start_turn(other, "Inspect asset", operation)
    with pytest.raises(Conflict, match="another request"):
        db.start_turn(conversation, "Changed payload", operation)
    with pytest.raises(Conflict, match="current turn"):
        db.start_turn(conversation, "Next question", str(uuid4()))
    with db.connect() as connection:
        run["status"] = "awaiting_clarification"
        db.save_run(run, connection)
    with pytest.raises(Conflict):
        db.start_turn(conversation, "Bypass clarification", str(uuid4()))
    assert len(db.messages(conversation)) == 1


def test_failed_turn_retries_reuse_question_and_increment_version(db):
    conversation = db.create_conversation()["id"]
    operation = str(uuid4())
    run, _ = db.start_turn(conversation, "Inspect CV 01", operation)
    with db.connect() as connection:
        run.update(status="failed", error="Provider unavailable")
        db.save_run(run, connection)
    retry, fresh = db.start_turn(conversation, "Inspect CV 01", operation)
    assert fresh is True
    assert retry["id"] == run["id"]
    assert retry["version"] == 2
    assert retry["status"] == "running"
    assert retry["error"] is None
    assert len(db.messages(conversation)) == 1


def test_database_timings_log_only_operation_and_correlated_ids(db, monkeypatch):
    logs = []
    monkeypatch.setattr(
        logger, "info", lambda event, **kwargs: logs.append((event, kwargs))
    )
    request_token = request_context.set({"request_id": "req-test"})
    execution_token = execution_context.set({"execution_id": "exec-test"})
    try:
        assert db.rows("SELECT ? AS value", ("private-content",)) == [
            {"value": "private-content"}
        ]
        db.execute("UPDATE conversations SET title=?", ("secret-new-title",))
        with pytest.raises(sqlite3.OperationalError):
            db.rows("SELECT * FROM absent_table")
    finally:
        execution_context.reset(execution_token)
        request_context.reset(request_token)
    assert [event for event, _ in logs] == ["db_operation"] * 3
    fields = [kwargs["extra"]["fields"] for _, kwargs in logs]
    assert [item["operation"] for item in fields] == ["SELECT", "UPDATE", "SELECT"]
    assert all(item["duration_ms"] >= 0 for item in fields)
    assert all(item["request_id"] == "req-test" for item in fields)
    assert all(item["execution_id"] == "exec-test" for item in fields)
    assert all(
        set(item)
        == {
            "operation",
            "duration_ms",
            "request_id",
            "execution_id",
        }
        for item in fields
    )
    serialized = json.dumps(logs)
    assert "private-content" not in serialized
    assert "secret-new-title" not in serialized
    assert "absent_table" not in serialized


@pytest.mark.parametrize("evidence_status", ["grounded", "insufficient_evidence"])
@pytest.mark.parametrize("invalid", ["source", "quote", "topic"])
def test_grounded_answer_rejects_invented_citations(
    db,
    catalog,
    engine_factory,
    invalid,
    evidence_status,
):
    engine = engine_factory()
    source = catalog.sources[0]
    state = engine.initial(new_run(db))
    reference = {"source_id": source.source_id, "quote": source.excerpt[:50]}
    topics = [source.topic_id]
    if invalid == "source":
        reference["source_id"] = "invented:source"
    elif invalid == "quote":
        reference["quote"] = "The plant requires a fictional 9999 mm clearance."
    else:
        topics = []
    state.update(
        sources={source.source_id: source.model_dump()},
        action={
            "id": "finish",
            "name": "submit_answer",
            "args": {
                "evidence_status": evidence_status,
                "answer": "Check the procedure.",
                "selected_topic_ids": topics,
                "references": [reference],
            },
        },
    )
    result = engine.finish(state)
    assert "answer" not in result
    assert result["correction_count"] == 1
    assert "error" in json.loads(result["messages"][-1].content)
    state["correction_count"] = 1
    with pytest.raises(AgentFailure, match="valid grounded response"):
        engine.finish(state)


@pytest.mark.parametrize("evidence_status", ["grounded", "insufficient_evidence"])
def test_grounded_answer_keeps_versioned_reference_metadata(
    db,
    catalog,
    engine_factory,
    evidence_status,
):
    source = catalog.sources[0]
    engine = engine_factory()
    state = engine.initial(new_run(db))
    state.update(
        sources={source.source_id: source.model_dump()},
        action={
            "id": "finish",
            "name": "submit_answer",
            "args": {
                "evidence_status": evidence_status,
                "answer": "Example guidance only.",
                "selected_topic_ids": [source.topic_id],
                "references": [
                    {
                        "source_id": source.source_id,
                        "quote": source.excerpt[:50].strip(),
                    }
                ],
            },
        },
    )
    reference = engine.finish(state)["answer"]["references"][0]
    assert reference["document_hash"] == source.document_hash
    assert reference["quote"] == source.passages[0]
    assert reference["quote"] in source.excerpt
    assert reference["demonstration"] is True
    assert reference["number"] == 1


@pytest.mark.parametrize("bound", [False, True])
def test_responses_serialization_always_disables_reasoning(bound):
    requests = []

    def transport(request):
        requests.append((request.url.path, json.loads(request.content)))
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "model": "gpt-6-luna",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "id": "msg_test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Test response",
                                "annotations": [],
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7},
            },
        )

    with httpx.Client(transport=httpx.MockTransport(transport)) as http:
        with OpenAI(api_key="offline-test", http_client=http) as client:
            model = make_model("offline-test")
            model.root_client = client
            runnable = (
                model.bind_tools(
                    [SearchDocumentsInput],
                    tool_choice="required",
                    strict=True,
                    parallel_tool_calls=False,
                )
                if bound
                else model
            )
            runnable.invoke([HumanMessage(content="Inspect the asset")])
    path, body = requests[0]
    assert len(requests) == 1
    assert path.endswith("/responses")
    assert body["model"] == "gpt-6-luna"
    assert body["reasoning"] == {"effort": "none"}
    assert body["store"] is False
    if bound:
        assert body["tool_choice"] == "required"
        assert body["parallel_tool_calls"] is False
        assert body["tools"][0]["strict"] is True


def test_graph_interrupt_is_durable_and_resume_keeps_same_turn(
    db,
    catalog,
    engine_factory,
):
    first_model = FakeModel(("request_clarification", {"question": "Which asset?"}))
    engine = engine_factory(first_model)
    run = new_run(db, "What before restarting it?")
    config = {"configurable": {"thread_id": run["id"]}}
    paused = engine.graph.invoke(engine.initial(run), config)
    interrupt_id = paused["__interrupt__"][0].id
    assert paused["__interrupt__"][0].value == {"question": "Which asset?"}
    assert paused["answer"] is None
    assert len(first_model.inputs) == 1
    engine.close()

    def supported_answer(messages):
        evidence = json.loads(
            next(
                m.content
                for m in reversed(messages)
                if isinstance(m, ToolMessage) and '"sources"' in m.content
            )
        )["sources"][0]
        return {
            "evidence_status": "grounded",
            "answer": "Use the example procedure.",
            "selected_topic_ids": [evidence["topic_id"]],
            "references": [
                {
                    "source_id": evidence["source_id"],
                    "quote": evidence["excerpt"][:60],
                }
            ],
        }

    resumed_model = FakeModel(
        ("search_documents", search_args()),
        ("submit_answer", supported_answer),
    )
    reopened = engine_factory(resumed_model)
    snapshot = reopened.graph.get_state(config)
    assert snapshot.tasks[0].interrupts[0].id == interrupt_id
    assert snapshot.values["run_id"] == run["id"]
    assert resumed_model.inputs == []
    completed = reopened.graph.invoke(Command(resume={"content": "CV 01"}), config)
    assert completed["run_id"] == run["id"]
    assert completed["clarification_count"] == 1
    assert completed["search_count"] == 1
    assert completed["model_count"] == 3
    assert "Supervisor clarification: CV 01" in completed["question"]
    assert completed["answer"]["references"]
    assert len(resumed_model.inputs) == 2
    assert any(
        isinstance(m, ToolMessage) and "CV 01" in m.content
        for m in resumed_model.inputs[0]
    )
    assert reopened.graph.get_state(config).next == ()
    assert len(first_model.inputs) == 1


def test_graph_retries_transient_search_errors_with_actual_policy(
    db,
    catalog,
    engine_factory,
    monkeypatch,
):
    original_search = catalog.search
    attempts = []

    def flaky_search(*args, **kwargs):
        attempts.append(True)
        if len(attempts) < 3:
            raise TransientSearchError("temporary filesystem contention")
        return original_search(*args, **kwargs)

    monkeypatch.setattr(catalog, "search", flaky_search)
    model = FakeModel(
        ("search_documents", search_args(query="zxqv987")),
        ("submit_answer", abstention()),
    )
    engine = engine_factory(model)
    run = new_run(db)
    result = engine.graph.invoke(
        engine.initial(run),
        {"configurable": {"thread_id": run["id"]}},
    )
    assert len(attempts) == 3
    assert len(model.inputs) == 2
    assert result["search_count"] == 1
    assert result["correction_count"] == 0
    assert result["answer"]["evidence_status"] == "insufficient_evidence"
    assert json.loads(result["messages"][-2].content)["status"] == "no_results"


def test_permanent_search_error_produces_correction_without_retry(
    db,
    catalog,
    engine_factory,
    monkeypatch,
):
    attempts = []
    original_search = catalog.search

    def counting_search(*args, **kwargs):
        attempts.append(True)
        return original_search(*args, **kwargs)

    monkeypatch.setattr(catalog, "search", counting_search)
    engine = engine_factory(
        FakeModel(
            ("search_documents", search_args(topic_ids=["does-not-exist"])),
            ("submit_answer", abstention()),
        )
    )
    run = new_run(db)
    result = engine.graph.invoke(
        engine.initial(run),
        {"configurable": {"thread_id": run["id"]}},
    )
    assert len(attempts) == 1
    assert result["search_count"] == 0
    assert result["correction_count"] == 1
    error = json.loads(result["messages"][-2].content)
    assert "error" in error and "status" not in error


def test_transient_search_retry_exhaustion_never_becomes_empty_evidence(
    db,
    catalog,
    engine_factory,
    monkeypatch,
):
    attempts = []

    def unavailable(*args, **kwargs):
        attempts.append(True)
        raise TransientSearchError("search resource temporarily unavailable")

    monkeypatch.setattr(catalog, "search", unavailable)
    model = FakeModel(("search_documents", search_args()))
    engine = engine_factory(model)
    run = new_run(db)
    with pytest.raises(TransientSearchError, match="temporarily unavailable"):
        engine.graph.invoke(
            engine.initial(run),
            {"configurable": {"thread_id": run["id"]}},
        )
    assert len(attempts) == 3
    assert len(model.inputs) == 1


def test_no_completed_history_skips_decisions(db, engine_factory):
    decisions = FakeDecisions()
    engine = engine_factory(decisions=decisions)
    assert engine.select_history(engine.initial(new_run(db)))["history"] == []
    assert decisions.calls == []


def completed_history(db, conversation_id, question, answer):
    run, _ = db.start_turn(conversation_id, question, str(uuid4()))
    with db.connect() as connection:
        run["status"] = "completed"
        db.save_run(run, connection)
        db.add_message(connection, run, "assistant", "answer", answer, str(uuid4()))
    return run


@pytest.mark.parametrize("probability", [0.0, 1.0])
def test_decisions_only_selects_relevant_complete_turns(
    db,
    engine_factory,
    probability,
):
    conversation = db.create_conversation()["id"]
    first = completed_history(db, conversation, "Old unrelated inspection", "old reply")
    latest = completed_history(db, conversation, "CV 01 belt repair", "CV 01 repaired")
    run, _ = db.start_turn(conversation, "Can I restart it?", str(uuid4()))
    decisions = FakeDecisions(probability=probability)
    engine = engine_factory(decisions=decisions)
    history = engine.select_history(engine.initial(run))["history"]
    assert [m.content for m in history] == (
        ["Old unrelated inspection", "old reply", "CV 01 belt repair", "CV 01 repaired"]
        if probability >= 0.55
        else []
    )
    request = decisions.calls[0]
    assert set(request) == {"model", "input", "questions"}
    assert request["model"] == "gpt-6-luna"
    payload = json.loads(request["input"])
    assert set(payload) == {"current_question", "candidate_turns"}
    assert set(payload["candidate_turns"]) == {first["id"], latest["id"]}
    assert run["id"] not in payload["candidate_turns"]
    assert all(q["type"] == "predicate" for q in request["questions"])
    assert {q["name"] for q in request["questions"]} == {
        first["id"],
        latest["id"],
    }
    assert all("candidate turn" in q["instructions"] for q in request["questions"])
    assert sum(token_count(m.content) for m in history) < 3000


@pytest.mark.parametrize("probability", [-0.1, 1.1, float("nan")])
def test_invalid_decisions_probabilities_fail_explicitly(
    db,
    engine_factory,
    probability,
):
    conversation = db.create_conversation()["id"]
    completed_history(db, conversation, "CV 01", "Repaired")
    run, _ = db.start_turn(conversation, "Restart?", str(uuid4()))
    engine = engine_factory(decisions=FakeDecisions(probability))
    with pytest.raises(AgentFailure, match="validation"):
        engine.select_history(engine.initial(run))


def test_incomplete_decisions_result_does_not_silently_drop_history(
    db,
    engine_factory,
):
    conversation = db.create_conversation()["id"]
    completed_history(db, conversation, "CV 01", "Repaired")
    run, _ = db.start_turn(conversation, "Restart?", str(uuid4()))
    decisions = SimpleNamespace(
        decisions=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(answers=[]))
    )
    engine = engine_factory(decisions=decisions)
    with pytest.raises(AgentFailure, match="incomplete"):
        engine.select_history(engine.initial(run))


def test_history_selection_bounds_candidates_and_whole_turn_memory(
    db,
    engine_factory,
):
    conversation = db.create_conversation()["id"]
    for i in range(8):
        completed_history(
            db, conversation, f"CV {i} " + "inspection " * 80, "acknowledged " * 60
        )
    run, _ = db.start_turn(conversation, "CV inspection", str(uuid4()))
    decisions = FakeDecisions(probability=1.0)
    engine = engine_factory(decisions=decisions)
    token = execution_context.set({"run_id": run["id"], "execution_id": "history"})
    try:
        history = engine.select_history(engine.initial(run))["history"]
    finally:
        execution_context.reset(token)
    candidate_turns = json.loads(decisions.calls[0]["input"])["candidate_turns"]
    assert sum(token_count(json.dumps(t)) for t in candidate_turns.values()) <= 6000
    assert history
    assert len(history) % 2 == 0
    assert all(isinstance(history[i], HumanMessage) for i in range(0, len(history), 2))
    event = next(e for e in db.events(run["id"]) if e["event"] == "history_selection")
    assert 0 < event["payload"]["selected_tokens"] <= 3000
    assert len(event["payload"]["selected_ids"]) < 8
