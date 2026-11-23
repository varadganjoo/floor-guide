"""Paid, opt-in golden-question evaluation through the actual application API.

Only question-only JSONL enters the agent. Gold answers remain evaluator-only.
Each case starts a fresh conversation; results and SQLite traces are retained.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import PROJECT_ROOT, Settings
from app.main import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--keep-going", action="store_true", help="Record failures and run every case"
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or PROJECT_ROOT / "backend/data/evaluations" / stamp
    output.mkdir(parents=True, exist_ok=False)
    settings = Settings(data_dir=output / "state", langsmith_tracing=False)
    if not settings.openai_api_key:
        parser.error("Set OPENAI_API_KEY in the root .env before running")
    source = (
        PROJECT_ROOT / "plant_document_examples/rag_evaluation/test_questions.jsonl"
    )
    questions = [
        json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()
    ]
    frozen_paths = [
        *sorted((PROJECT_ROOT / "backend/app").glob("*.py")),
        PROJECT_ROOT / "backend/documents.json",
        *sorted((PROJECT_ROOT / "plant_document_examples/documents").glob("*.docx")),
        source,
    ]
    manifest = {
        str(path.relative_to(PROJECT_ROOT)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in frozen_paths
    }
    (output / "input_hashes.json").write_text(json.dumps(manifest, indent=2))
    results = []
    with TestClient(create_app(settings)) as client:
        with (output / "results.jsonl").open("w", encoding="utf-8") as stream:
            for item in questions[: args.limit]:
                cid = client.post("/api/conversations").json()["id"]
                started = perf_counter()
                response = client.post(
                    f"/api/conversations/{cid}/messages",
                    json={"content": item["question"], "operation_id": str(uuid4())},
                )
                result = {
                    **item,
                    "http_status": response.status_code,
                    "latency_ms": round((perf_counter() - started) * 1000, 2),
                    **response.json(),
                }
                run = result.get("run", {})
                if run.get("id"):
                    result["trace"] = client.get(
                        f"/api/observability/runs/{run['id']}"
                    ).json()
                    service = client.app.state.service
                    state = service.engine.graph.get_state(
                        service.graph_config(cid)
                    ).values
                    result["retrieved_sources"] = list(
                        state.get("sources", {}).values()
                    )
                stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                stream.flush()
                results.append(result)
                print(
                    f"{item['id']}: {run.get('status', 'http_error')} "
                    f"{result['latency_ms']:.0f}ms {run.get('error') or ''}",
                    flush=True,
                )
                # Stop on provider/configuration failure instead of billing for
                # fifty repetitions of the same broken request.
                if run.get("status") == "failed" and not args.keep_going:
                    break
    summary = {
        "model": "gpt-6-luna",
        "reasoning_effort": "none",
        "requested_cases": args.limit,
        "executed_cases": len(results),
        "statuses": dict(Counter(r.get("run", {}).get("status") for r in results)),
        "latency_ms_mean": sum(r["latency_ms"] for r in results) / len(results),
        "quality_grading": "Not yet graded; completion is not answer accuracy.",
        "inputs_unchanged": all(
            hashlib.sha256((PROJECT_ROOT / path).read_bytes()).hexdigest() == digest
            for path, digest in manifest.items()
        ),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Results: {output}", flush=True)


if __name__ == "__main__":
    main()
