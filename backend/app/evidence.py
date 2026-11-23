"""Whole evidence units and server-authored, exact-text references."""

import re


def complete_passages(blocks: list[str]) -> list[str]:
    """Keep table rows and prose intact; numbered procedures stay together."""
    passages, sequence = [], []
    for block in blocks:
        if re.match(r"^\d+[.)]\s", block):
            sequence.append(block)
            continue
        if sequence:
            passages.append("\n".join(sequence))
            sequence = []
        if not block.startswith("Table columns:"):
            passages.append(block)
    if sequence:
        passages.append("\n".join(sequence))
    return passages


def section_passages(blocks: list[str], subsection_starts: list[int]) -> list[str]:
    """Subsections, bullet checklists and blank record forms are cohesive units."""
    first = subsection_starts[0] if subsection_starts else len(blocks)
    initial = blocks[:first]
    if any("____" in block for block in initial):
        passages = ["\n".join(initial)] if initial else []
    else:
        passages = complete_passages(initial)
    ends = [*subsection_starts[1:], len(blocks)] if subsection_starts else []
    for start, end in zip(subsection_starts, ends, strict=True):
        passages.append("\n".join(blocks[start:end]))
    return passages


def evidence_passages(sources: dict) -> dict:
    result = {}
    for source_id, source in sources.items():
        # Older durable checkpoints contain only the full excerpt.
        passages = source.get("passages") or [source["excerpt"]]
        for index, passage in enumerate(passages):
            if passage and passage in source["excerpt"]:
                result[f"{source_id}/p{index}"] = {
                    "source": source,
                    "text": passage,
                }
    return result


def render_review(review, passages: dict) -> dict:
    selected = list(dict.fromkeys(review.passage_ids))
    if any(passage_id not in passages for passage_id in selected):
        raise ValueError("Evidence review selected an unknown passage ID")
    if not selected and not review.information_missing:
        raise ValueError("A supported answer requires selected evidence passages")
    references, requirements, topics = [], [], []
    for passage_id in selected:
        item = passages[passage_id]
        source, text = item["source"], item["text"]
        if text not in source["excerpt"]:
            raise ValueError("Stored evidence is not an exact source excerpt")
        number = len(references) + 1
        references.append(
            {
                "number": number,
                **{
                    key: source[key]
                    for key in (
                        "source_id",
                        "document_id",
                        "document_hash",
                        "topic_id",
                        "title",
                        "revision",
                        "heading",
                        "demonstration",
                    )
                },
                "quote": text,
            }
        )
        requirements.append(f"{text} [{number}]")
        if source["topic_id"] not in topics:
            topics.append(source["topic_id"])
    answer = review.short_answer
    if review.information_missing:
        answer = (
            "I don't have enough information in the available documents to "
            "answer that fully.\n\n" + answer
        )
        if review.missing_information:
            answer += "\n\nInformation needed: " + review.missing_information
    if requirements:
        answer += "\n\nRelevant document requirements:\n\n" + "\n\n".join(requirements)
    if any(ref["demonstration"] for ref in references):
        answer += (
            "\n\nThese are example documents, not released operating instructions."
        )
    if len(answer) > 12000:
        raise ValueError("Selected evidence exceeds the answer size limit")
    return {
        "answer": answer,
        "evidence_status": (
            "insufficient_evidence" if review.information_missing else "grounded"
        ),
        "selected_topic_ids": topics,
        "references": references,
    }
