"""Evaluate already graded results; never infer quality from run completion."""

import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path

from app.config import PROJECT_ROOT


def quality_gates(expected_ids, safety_ids, verdicts, thresholds):
    expected, safety = set(expected_ids), set(safety_ids)
    if not safety <= expected or not set(verdicts) <= expected:
        raise ValueError("Evaluation contains unknown case IDs")
    if not all(type(value) is bool for value in verdicts.values()):
        raise ValueError("Every verdict must be a graded boolean")
    gates = {}
    for name, cases in {"safety": safety, "non_safety": expected - safety}.items():
        threshold = Decimal(str(thresholds[name]))
        if not 0 <= threshold <= 1:
            raise ValueError("Thresholds must be between zero and one")
        passed = sum(verdicts.get(case, False) for case in cases)
        missing = sorted(cases - verdicts.keys())
        gates[name] = {
            "passed_cases": passed,
            "total_cases": len(cases),
            "accuracy": passed / len(cases) if cases else None,
            "threshold": float(threshold),
            "ungraded_cases": missing,
            "passed": bool(cases)
            and not missing
            and Decimal(passed) >= threshold * len(cases),
        }
    return {"passed": all(g["passed"] for g in gates.values()), "gates": gates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    policy = json.loads(
        (PROJECT_ROOT / "backend/evaluation_policy.json").read_text(encoding="utf-8")
    )
    questions = (
        PROJECT_ROOT / "plant_document_examples/rag_evaluation/test_questions.jsonl"
    )
    expected = [
        json.loads(line)["id"]
        for line in questions.read_text(encoding="utf-8").splitlines()
    ]
    verdicts = {}
    with args.results.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            if row["id"] in verdicts or row["strict_pass"] not in {"True", "False"}:
                raise ValueError("Results contain duplicate IDs or ungraded verdicts")
            verdicts[row["id"]] = row["strict_pass"] == "True"
    result = quality_gates(
        expected, policy["safety_case_ids"], verdicts, policy["thresholds"]
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
