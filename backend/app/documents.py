"""Local section catalog: parse once, return bounded, versioned evidence."""

import hashlib
import json
import re
from pathlib import Path
from zipfile import BadZipFile

import tiktoken
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from lxml.etree import XMLSyntaxError
from pydantic import Field

from app.config import PROJECT_ROOT
from app.database import Database
from app.evidence import section_passages
from app.schemas import (
    CatalogId,
    SearchDocumentsInput,
    SearchResult,
    Source,
    StrictModel,
    Text,
)

STOP_WORDS = set(
    (
        "a an the what which how is are do does can i we to of for in on and or it "
        "this that before after should please"
    ).split()
)


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w]+", text.casefold())) - STOP_WORDS


def token_count(text: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model("gpt-6-luna")
    except KeyError:
        # UTF-8 bytes conservatively bound byte-level BPE tokens for unknown models.
        return len(text.encode("utf-8"))
    return len(encoding.encode(text, disallowed_special=()))


class ManifestDocument(StrictModel):
    id: CatalogId
    path: Text
    title: str = ""
    revision: str = ""


class ManifestTopic(StrictModel):
    id: CatalogId
    name: Text
    description: Text
    documents: list[ManifestDocument]


class Manifest(StrictModel):
    topics: list[ManifestTopic] = Field(min_length=1)


def import_manifest(db: Database, manifest_path: Path):
    manifest = Manifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    if len({topic.id for topic in manifest.topics}) != len(manifest.topics):
        raise ValueError("Manifest contains duplicate topic IDs")
    document_ids = [doc.id for topic in manifest.topics for doc in topic.documents]
    if len(set(document_ids)) != len(document_ids):
        raise ValueError("Manifest contains duplicate document IDs")
    with db.connect() as conn:
        for topic in manifest.topics:
            conn.execute(
                (
                    "INSERT INTO topics VALUES (?,?,?,1) ON CONFLICT(id) DO UPDATE "
                    "SET name=excluded.name,description=excluded.description"
                ),
                (topic.id, topic.name, topic.description),
            )
            for document in topic.documents:
                path = (PROJECT_ROOT / document.path).resolve()
                if (
                    not path.is_relative_to(PROJECT_ROOT)
                    or path.suffix.lower() != ".docx"
                ):
                    raise ValueError(
                        "Document paths must identify DOCX files inside the project"
                    )
                conn.execute(
                    (
                        "INSERT INTO documents VALUES (?,?,?,?,?,?,?) ON "
                        "CONFLICT(id) DO UPDATE SET "
                        "topic_id=excluded.topic_id,path=excluded.path"
                    ),
                    (
                        document.id,
                        topic.id,
                        document.path,
                        path.stem.replace("_", " "),
                        "Unknown",
                        "",
                        int(path.is_file()),
                    ),
                )


class DocumentCatalog:
    def __init__(self, db: Database):
        self.db = db
        self.sources: list[Source] = []
        self.errors: list[dict] = []
        for record in db.rows("SELECT * FROM documents"):
            try:
                self._load(record)
            except (
                OSError,
                ValueError,
                KeyError,
                BadZipFile,
                PackageNotFoundError,
                XMLSyntaxError,
            ) as exc:
                self.errors.append(
                    {"document_id": record["id"], "error": type(exc).__name__}
                )
                db.execute(
                    "UPDATE documents SET available=0 WHERE id=?", (record["id"],)
                )

    def _load(self, record: dict):
        path = (PROJECT_ROOT / record["path"]).resolve()
        if not path.is_relative_to(PROJECT_ROOT):
            raise ValueError("Document path outside project")
        raw = path.read_bytes()
        version = hashlib.sha256(raw).hexdigest()
        doc = Document(path)
        title = next(
            (p.text for p in doc.paragraphs if p.text.strip()), record["title"]
        )
        metadata = "\n".join(p.text for p in doc.paragraphs[:8])
        revision_match = re.search(r"Revision\s+([\w.-]+)", metadata)
        revision = revision_match[1] if revision_match else "Unknown"
        heading, blocks, sections = "Document overview", [], []
        subsection_starts = []
        for block in doc.iter_inner_content():
            if isinstance(block, Table):
                rows = [[cell.text.strip() for cell in row.cells] for row in block.rows]
                if rows:
                    headers = rows[0]
                    blocks.append("Table columns: " + " | ".join(headers))
                    for row in rows[1:]:
                        blocks.append(
                            "; ".join(
                                f"{key}: {value}"
                                for key, value in zip(headers, row, strict=False)
                            )
                        )
            else:
                text = block.text.strip()
                if not text:
                    continue
                if (
                    block.style
                    and block.style.name == "Heading 1"
                    and re.match(r"^\d+(?:\s|[.)])", text)
                ):
                    if blocks:
                        sections.append(
                            (heading, blocks.copy(), subsection_starts.copy())
                        )
                    heading, blocks, subsection_starts = text, [], []
                else:
                    if block.style and block.style.name.startswith("Heading"):
                        subsection_starts.append(len(blocks))
                    blocks.append(text)
        if blocks:
            sections.append((heading, blocks.copy(), subsection_starts.copy()))
        introduction = "\n".join(sections[0][1]) if sections else ""
        for index, (heading, section_blocks, subheadings) in enumerate(sections):
            text = "\n".join(section_blocks)
            # Keep whole numbered sections, including subheadings, warnings and tables.
            excerpt = (
                text if index == 0 else introduction + "\n\n" + heading + "\n" + text
            )
            self.sources.append(
                Source(
                    source_id=f"{record['id']}:{version[:12]}:{index}",
                    document_id=record["id"],
                    document_hash=version,
                    topic_id=record["topic_id"],
                    title=title,
                    revision=revision,
                    heading=heading,
                    excerpt=excerpt,
                    score=0,
                    demonstration="EXAMPLE ONLY" in metadata,
                    passages=section_passages(section_blocks, subheadings),
                )
            )
        self.db.execute(
            (
                "UPDATE documents SET title=?,revision=?,content_hash=?,available=1"
                " WHERE id=?"
            ),
            (title, revision, version, record["id"]),
        )

    def topics(self) -> list[dict]:
        topics = self.db.rows("SELECT * FROM topics WHERE active=1 ORDER BY name")
        for topic in topics:
            topic["documents"] = self.db.rows(
                (
                    "SELECT id,title,available,revision FROM documents WHERE "
                    "topic_id=? ORDER BY title"
                ),
                (topic["id"],),
            )
        return topics

    def search(
        self,
        args: SearchDocumentsInput,
        budget: int = 6000,
        exclude: set[str] | None = None,
    ) -> SearchResult:
        active = {t["id"] for t in self.topics()}
        if not set(args.topic_ids) <= active:
            raise ValueError("Unknown or inactive topic ID. Read the topic catalog.")
        known_docs = {r["id"]: r for r in self.db.rows("SELECT * FROM documents")}
        if any(
            d not in known_docs or known_docs[d]["topic_id"] not in args.topic_ids
            for d in args.document_ids
        ):
            raise ValueError("Document IDs must belong to the selected topics")
        selected_docs = [
            r
            for r in known_docs.values()
            if r["topic_id"] in args.topic_ids
            and (not args.document_ids or r["id"] in args.document_ids)
        ]
        if any(not r["available"] for r in selected_docs):
            raise ValueError(
                "A selected document is unavailable. Check the document registry."
            )
        query = tokens(args.query)
        ranked = []
        for source in self.sources:
            if exclude and source.source_id in exclude:
                continue
            if source.topic_id not in args.topic_ids or (
                args.document_ids and source.document_id not in args.document_ids
            ):
                continue
            body_terms = tokens(source.excerpt)
            score = len(query & body_terms) + 3 * len(query & tokens(source.heading))
            if score:
                ranked.append(source.model_copy(update={"score": float(score)}))
        ranked.sort(key=lambda source: (-source.score, source.source_id))
        # Give each requested source type a turn before filling with extra hits.
        first_per_topic = [
            next((s for s in ranked if s.topic_id == topic), None)
            for topic in args.topic_ids
        ]
        first_per_topic = [s for s in first_per_topic if s is not None]
        first_ids = {s.source_id for s in first_per_topic}
        candidates = first_per_topic + [
            s for s in ranked if s.source_id not in first_ids
        ]
        results, used, truncated = [], 0, False
        for source in candidates:
            if len(results) >= args.limit:
                truncated = True
                break
            size = token_count(source.excerpt)
            if used + size > budget:
                truncated = True
                continue
            results.append(source)
            used += size
        covered_topics = {s.topic_id for s in results} | {
            s.topic_id for s in self.sources if exclude and s.source_id in exclude
        }
        return SearchResult(
            status="ok" if results else "no_results",
            sources=results,
            truncated=truncated or len(ranked) > args.limit,
            uncovered_topic_ids=[
                topic for topic in args.topic_ids if topic not in covered_topics
            ],
        )


if __name__ == "__main__":
    from app.config import get_settings

    settings = get_settings()
    database = Database(settings.data_dir / "application.sqlite3")
    import_manifest(database, settings.document_manifest)
    catalog = DocumentCatalog(database)
    print(
        json.dumps(
            {
                "topics": len(catalog.topics()),
                "sections": len(catalog.sources),
                "errors": catalog.errors,
            }
        )
    )
