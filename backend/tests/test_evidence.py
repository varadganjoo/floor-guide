import pytest

from app.evidence import (
    complete_passages,
    evidence_passages,
    render_review,
    section_passages,
)
from app.schemas import EvidenceReview


def source(text, passages):
    return {
        "source_id": "test:hash:1",
        "document_id": "test",
        "document_hash": "hash",
        "topic_id": "dynamic-topic",
        "title": "Test",
        "revision": "0",
        "heading": "Procedure",
        "demonstration": True,
        "excerpt": text,
        "passages": passages,
    }


def test_complete_numbered_sequence_keeps_preconditions_with_next_step():
    blocks = [
        "Isolation",
        "1. Prevent reaccumulation.",
        "2. Verify isolation.",
        "3. Return test controls to safe state.",
        "Report faults.",
    ]
    units = complete_passages(blocks)
    assert units[1] == "\n".join(blocks[1:4])
    item = source("\n".join(blocks), units)
    passages = evidence_passages({item["source_id"]: item})
    review = EvidenceReview(
        short_answer="Verify isolation before servicing.",
        passage_ids=["test:hash:1/p1"],
        information_missing=False,
        missing_information="",
    )
    result = render_review(review, passages)
    assert all(step in result["answer"] for step in blocks[1:4])
    assert result["references"][0]["quote"] == "\n".join(blocks[1:4])


def test_table_row_keeps_checks_record_and_reaction_in_answer():
    row = (
        "Stage: Receipt; Checks: identity and supplier evidence; "
        "Reaction: hold material."
    )
    item = source(row, complete_passages(["Table columns: Stage | Checks", row]))
    passages = evidence_passages({item["source_id"]: item})
    review = EvidenceReview(
        short_answer="Hold the material.",
        passage_ids=list(passages),
        information_missing=False,
        missing_information="",
    )
    result = render_review(review, passages)
    assert row in result["answer"]
    assert result["references"][0]["quote"] == row
    assert result["selected_topic_ids"] == ["dynamic-topic"]


def test_named_release_checklist_and_record_form_remain_complete():
    blocks = [
        "Asset ____",
        "Record: First piece and held product",
        "Approval ____",
        "Release criteria",
        "Inspections pass.",
        "Labels and packaging comply.",
        "Quality signs and dates release.",
    ]
    passages = section_passages(blocks, [3])
    assert passages == ["\n".join(blocks[:3]), "\n".join(blocks[3:])]
    assert section_passages(["A standalone paragraph."], []) == [
        "A standalone paragraph."
    ]


def test_nonexistent_passage_cannot_create_citation():
    review = EvidenceReview(
        short_answer="Unsupported.",
        passage_ids=["invented"],
        information_missing=False,
        missing_information="",
    )
    with pytest.raises(ValueError, match="unknown passage"):
        render_review(review, {})


def test_missing_information_has_explicit_notice_and_no_fabricated_quote():
    review = EvidenceReview(
        short_answer="The location field is blank.",
        passage_ids=[],
        information_missing=True,
        missing_information="Approved site emergency plan.",
    )
    result = render_review(review, {})
    assert result["answer"].startswith("I don't have enough information")
    assert result["references"] == []
    assert result["evidence_status"] == "insufficient_evidence"
