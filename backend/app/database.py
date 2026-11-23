"""SQLite persistence. Never hold transactions open during model calls."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4


def now() -> str:
    return datetime.now(UTC).isoformat()


def uid() -> str:
    return str(uuid4())


@contextmanager
def timed_operation(sql: str):
    from app.observability import execution_context, logger, request_context

    started = perf_counter()
    try:
        yield
    finally:
        keyword = sql.lstrip().split(maxsplit=1)[0].upper() if sql.strip() else ""
        operation = (
            keyword
            if keyword
            in {
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "WITH",
                "PRAGMA",
                "CREATE",
                "ALTER",
                "DROP",
                "BEGIN",
                "COMMIT",
                "ROLLBACK",
            }
            else "UNKNOWN"
        )
        context = {**request_context.get(), **execution_context.get()}
        identifiers = {
            name: context[name]
            for name in (
                "request_id",
                "proxy_request_id",
                "conversation_id",
                "run_id",
                "execution_id",
            )
            if name in context
        }
        logger.info(
            "db_operation",
            extra={
                "fields": {
                    **identifiers,
                    "operation": operation,
                    "duration_ms": (perf_counter() - started) * 1000,
                }
            },
        )


class Conflict(Exception):
    pass


class NotFound(Exception):
    pass


class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, topic_id TEXT NOT NULL REFERENCES topics(id),
                    path TEXT NOT NULL, title TEXT NOT NULL, revision TEXT NOT NULL,
                    content_hash TEXT NOT NULL, available INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversation_runs (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES
                    conversations(id),
                    status TEXT NOT NULL, created_at TEXT NOT NULL, data TEXT NOT NULL);
                CREATE UNIQUE INDEX IF NOT EXISTS active_run ON
                conversation_runs(conversation_id)
                    WHERE status IN ('running','awaiting_clarification');
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES
                    conversations(id),
                    run_id TEXT NOT NULL REFERENCES conversation_runs(id), sequence
                    INTEGER NOT NULL,
                    role TEXT NOT NULL, kind TEXT NOT NULL, content TEXT NOT NULL,
                    status TEXT NOT NULL, refs TEXT NOT NULL DEFAULT '[]', created_at
                    TEXT NOT NULL,
                    UNIQUE(conversation_id, sequence));
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, run_id TEXT NOT
                    NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS run_events (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES
                    conversation_runs(id),
                    execution_id TEXT NOT NULL, span_id TEXT NOT NULL, parent_span_id
                    TEXT,
                    event TEXT NOT NULL, created_at TEXT NOT NULL, duration_ms REAL,
                    payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS events_run ON run_events(run_id,created_at);
                CREATE TABLE IF NOT EXISTS request_observations (
                    id TEXT PRIMARY KEY, conversation_id TEXT, run_id TEXT, execution_id
                    TEXT,
                    proxy_id TEXT, route TEXT NOT NULL, status INTEGER NOT NULL,
                    duration_ms REAL NOT NULL, client_ms REAL, client_outcome TEXT,
                    created_at TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def rows(self, sql: str, args=()) -> list[dict]:
        with timed_operation(sql), self.connect() as db:
            return [dict(row) for row in db.execute(sql, args).fetchall()]

    def execute(self, sql: str, args=()):
        with timed_operation(sql), self.connect() as db:
            db.execute(sql, args)

    def conversation(self, conversation_id: str) -> dict:
        rows = self.rows("SELECT * FROM conversations WHERE id=?", (conversation_id,))
        if not rows:
            raise NotFound("Conversation not found")
        return rows[0]

    def create_conversation(self) -> dict:
        item = dict(
            id=uid(), title="New conversation", created_at=now(), updated_at=now()
        )
        self.execute("INSERT INTO conversations VALUES (?,?,?,?)", tuple(item.values()))
        return item

    def run(self, run_id: str) -> dict:
        rows = self.rows("SELECT data FROM conversation_runs WHERE id=?", (run_id,))
        if not rows:
            raise NotFound("Run not found")
        return json.loads(rows[0]["data"])

    def current_run(self, conversation_id: str) -> dict | None:
        self.conversation(conversation_id)
        rows = self.rows(
            (
                "SELECT data FROM conversation_runs WHERE conversation_id=? ORDER "
                "BY created_at DESC LIMIT 1"
            ),
            (conversation_id,),
        )
        return json.loads(rows[0]["data"]) if rows else None

    def save_run(self, run: dict, db):
        run["updated_at"] = now()
        db.execute(
            "UPDATE conversation_runs SET status=?,data=? WHERE id=?",
            (run["status"], json.dumps(run), run["id"]),
        )

    def add_message(
        self,
        db,
        run: dict,
        role: str,
        kind: str,
        content: str,
        message_id: str,
        refs=None,
    ):
        sequence = db.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 FROM messages WHERE conversation_id=?",
            (run["conversation_id"],),
        ).fetchone()[0]
        db.execute(
            "INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                message_id,
                run["conversation_id"],
                run["id"],
                sequence,
                role,
                kind,
                content,
                "completed",
                json.dumps(refs or []),
                now(),
            ),
        )
        db.execute(
            "UPDATE conversations SET updated_at=? WHERE id=?",
            (now(), run["conversation_id"]),
        )

    def messages(self, conversation_id: str, limit=200, offset=0) -> list[dict]:
        self.conversation(conversation_id)
        rows = self.rows(
            (
                "SELECT * FROM messages WHERE conversation_id=? ORDER BY sequence "
                "LIMIT ? OFFSET ?"
            ),
            (conversation_id, limit, offset),
        )
        for row in rows:
            row["references"] = json.loads(row.pop("refs"))
        return rows

    def start_turn(
        self, conversation_id: str, content: str, operation_id: str
    ) -> tuple[dict, bool]:
        self.conversation(conversation_id)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            operation = db.execute(
                "SELECT * FROM operations WHERE id=?", (operation_id,)
            ).fetchone()
            if operation:
                if (
                    operation["conversation_id"] != conversation_id
                    or operation["payload"] != content
                    or operation["kind"] != "send"
                ):
                    raise Conflict("Operation ID already belongs to another request")
                run = json.loads(
                    db.execute(
                        "SELECT data FROM conversation_runs WHERE id=?",
                        (operation["run_id"],),
                    ).fetchone()[0]
                )
                if run["status"] != "failed":
                    return run, False
                latest = db.execute(
                    "SELECT id FROM conversation_runs WHERE conversation_id=? "
                    "ORDER BY created_at DESC LIMIT 1",
                    (conversation_id,),
                ).fetchone()
                if latest and latest["id"] != run["id"]:
                    raise Conflict("Start a new question to retry an older failed turn")
                if db.execute(
                    (
                        "SELECT id FROM conversation_runs WHERE conversation_id=? "
                        "AND status IN ('running','awaiting_clarification')"
                    ),
                    (conversation_id,),
                ).fetchone():
                    raise Conflict("This conversation already has an active turn")
                run.update(status="running", error=None, version=run["version"] + 1)
                self.save_run(run, db)
                return run, True
            if db.execute(
                (
                    "SELECT id FROM conversation_runs WHERE conversation_id=? AND "
                    "status IN ('running','awaiting_clarification')"
                ),
                (conversation_id,),
            ).fetchone():
                raise Conflict(
                    "Reply to or cancel the current turn before starting another"
                )
            run = dict(
                id=uid(),
                conversation_id=conversation_id,
                status="running",
                question=content,
                answer=None,
                error=None,
                interrupt_id=None,
                clarification_question=None,
                version=1,
                active_ms=0.0,
                wait_ms=0.0,
                input_tokens=None,
                output_tokens=None,
                created_at=now(),
                updated_at=now(),
                paused_at=None,
                selected_topic_ids=[],
                model="gpt-6-luna",
                reasoning_effort="none",
            )
            db.execute(
                "INSERT INTO conversation_runs VALUES (?,?,?,?,?)",
                (
                    run["id"],
                    conversation_id,
                    run["status"],
                    run["created_at"],
                    json.dumps(run),
                ),
            )
            db.execute(
                "INSERT INTO operations VALUES (?,?,?,?,?)",
                (operation_id, conversation_id, run["id"], "send", content),
            )
            self.add_message(
                db, run, "user", "question", content, run["id"] + ":question"
            )
            db.execute(
                (
                    "UPDATE conversations SET title=? WHERE id=? AND title='New "
                    "conversation'"
                ),
                (content[:70], conversation_id),
            )
            return run, True

    def event(
        self,
        run_id: str,
        execution_id: str,
        event: str,
        payload=None,
        duration_ms=None,
        parent_span_id=None,
        event_id=None,
    ):
        span_id = uid()
        self.execute(
            "INSERT OR IGNORE INTO run_events VALUES (?,?,?,?,?,?,?,?,?)",
            (
                event_id or uid(),
                run_id,
                execution_id,
                span_id,
                parent_span_id,
                event,
                now(),
                duration_ms,
                json.dumps(payload or {}, ensure_ascii=False),
            ),
        )
        return span_id

    def events(self, run_id: str) -> list[dict]:
        rows = self.rows(
            "SELECT * FROM run_events WHERE run_id=? ORDER BY created_at,id", (run_id,)
        )
        for row in rows:
            row["payload"] = json.loads(row["payload"])
        return rows
