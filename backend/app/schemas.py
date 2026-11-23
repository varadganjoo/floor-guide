from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CatalogId = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{1,80}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SendMessage(StrictModel):
    content: Text = Field(max_length=8000)
    operation_id: UUID


class ResumeMessage(SendMessage):
    turn_id: UUID
    interrupt_id: Text = Field(max_length=200)
    version: int = Field(ge=1)


class CancelRun(StrictModel):
    operation_id: UUID


class SearchDocumentsInput(StrictModel):
    query: Text = Field(
        max_length=1000,
        description="Relevant keywords, asset IDs or alternate wording.",
    )
    topic_ids: list[CatalogId] = Field(
        min_length=1,
        max_length=32,
        description=(
            "Array of one or more valid topic/source-type IDs from the live "
            "catalog. Include every type needed to answer the question. "
            "Values are validated against SQLite, not a fixed topic enum."
        ),
    )
    document_ids: list[CatalogId] = Field(
        description=(
            "Optional restriction: use an empty list for all documents in the "
            "selected topics."
        ),
        max_length=32,
    )
    limit: int = Field(ge=1, le=6)

    @field_validator("topic_ids", "document_ids")
    @classmethod
    def unique_ids(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("IDs must be unique")
        return value


class ClarificationRequest(StrictModel):
    question: Text = Field(max_length=600)


class CitationInput(StrictModel):
    source_id: Text = Field(max_length=100)
    quote: Text = Field(
        max_length=1800,
        description="An exact verbatim excerpt from this source's tool result.",
    )


class GroundedAnswer(StrictModel):
    evidence_status: Literal["grounded", "insufficient_evidence"]
    answer: Text = Field(max_length=12000)
    selected_topic_ids: list[CatalogId] = Field(max_length=32)
    references: list[CitationInput] = Field(max_length=12)


class AnswerDraft(StrictModel):
    evidence_status: Literal["grounded", "insufficient_evidence"]
    answer: Text = Field(max_length=12000)
    selected_topic_ids: list[CatalogId] = Field(max_length=32)
    source_ids: list[str] = Field(
        max_length=12,
        description=(
            "Retrieved source IDs supporting the answer; never write quotations."
        ),
    )


class EvidenceReview(StrictModel):
    short_answer: Text = Field(max_length=1800)
    passage_ids: list[str] = Field(max_length=12)
    information_missing: bool
    missing_information: str = Field(max_length=1200)


class Source(StrictModel):
    source_id: str
    document_id: str
    document_hash: str
    topic_id: str
    title: str
    revision: str
    heading: str
    excerpt: str
    score: float
    demonstration: bool = True
    passages: list[str] = Field(default_factory=list)


class SearchResult(StrictModel):
    status: str
    sources: list[Source]
    truncated: bool
    uncovered_topic_ids: list[str] = Field(default_factory=list)


class ClientMeasurement(StrictModel):
    duration_ms: float = Field(ge=0, le=3_600_000, allow_inf_nan=False)
    outcome: Text = Field(max_length=80)
