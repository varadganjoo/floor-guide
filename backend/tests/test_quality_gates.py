import pytest

from app.evaluation import quality_gates

THRESHOLDS = {"safety": 1, "non_safety": 0.95}


def test_ninety_five_percent_non_safety_and_all_safety_pass():
    expected = ["safety", *[f"quality-{i}" for i in range(20)]]
    verdicts = dict.fromkeys(expected, True)
    verdicts["quality-0"] = False
    assert quality_gates(expected, ["safety"], verdicts, THRESHOLDS)["passed"]
    verdicts["safety"] = False
    result = quality_gates(expected, ["safety"], verdicts, THRESHOLDS)
    assert not result["passed"]
    assert not result["gates"]["safety"]["passed"]


def test_partial_evaluation_never_claims_to_meet_thresholds():
    result = quality_gates(
        ["s", "n", "missing"], ["s"], {"s": True, "n": True}, THRESHOLDS
    )
    assert not result["passed"]
    assert result["gates"]["non_safety"]["ungraded_cases"] == ["missing"]


@pytest.mark.parametrize("verdicts", [{"unknown": True}, {"s": "True"}])
def test_unknown_or_ungraded_results_rejected(verdicts):
    with pytest.raises(ValueError):
        quality_gates(["s", "n"], ["s"], verdicts, THRESHOLDS)
