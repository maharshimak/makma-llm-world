"""SQLite persistence. Private context queries require the owning agent ID."""
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .schemas import Agent, MemoryWrite, now, uid


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id), kind TEXT NOT NULL, content TEXT NOT NULL, importance REAL NOT NULL, confidence REAL NOT NULL, sources TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_memories_agent_time ON memories(agent_id, created_at);
                CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL REFERENCES agents(id), kind TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL, read INTEGER NOT NULL DEFAULT 0);
                CREATE INDEX IF NOT EXISTS idx_messages_recipient_read ON messages(recipient, read);
                CREATE TABLE IF NOT EXISTS records(collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, PRIMARY KEY(collection,id));
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, entity_id TEXT NOT NULL, summary TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'immutable event'); END;
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id), project_id TEXT, kind TEXT NOT NULL, payload TEXT NOT NULL, priority REAL NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority DESC, created_at);
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                PRAGMA user_version=1;
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def event(self, kind: str, entity: str, summary: str):
        with self.connect() as db:
            db.execute("INSERT INTO events(type,entity_id,summary,created_at) VALUES(?,?,?,?)", (kind, entity, summary[:500], now()))

    def events(self, after=0, limit=100):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?", (after, limit))]

    def save_agent(self, agent: Agent):
        with self.connect() as db:
            db.execute("INSERT INTO agents VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data", (agent.id, agent.model_dump_json()))

    def agent(self, agent_id: str) -> Agent:
        with self.connect() as db:
            row = db.execute("SELECT data FROM agents WHERE id=?", (agent_id,)).fetchone()
        if row is None:
            raise KeyError(agent_id)
        return Agent.model_validate_json(row[0])

    def agents(self) -> list[Agent]:
        with self.connect() as db:
            return [Agent.model_validate_json(r[0]) for r in db.execute("SELECT data FROM agents ORDER BY id")]

    def remember(self, agent_id: str, memory: MemoryWrite) -> str:
        self.agent(agent_id)
        mid = uid("mem")
        with self.connect() as db:
            db.execute("INSERT INTO memories VALUES(?,?,?,?,?,?,?,?)", (mid, agent_id, memory.kind, memory.content, memory.importance, memory.confidence, json.dumps(memory.sources), now()))
        self.event("MEMORY_CREATED", agent_id, f"Stored private {memory.kind} memory")
        return mid

    def memories(self, agent_id: str, query="", goal="", limit=20, weights=(.35,.20,.20,.15,.10)):
        self.agent(agent_id)
        with self.connect() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM memories WHERE agent_id=? ORDER BY created_at DESC LIMIT 1000", (agent_id,))]
        terms = lambda s: set(re.findall(r"\w+", s.lower()))
        q, g = terms(query), terms(goal)
        for r in rows:
            t = terms(r["content"])
            sim = len(q & t) / max(1, math.sqrt(len(q)*len(t)))
            relevance = len(g & t) / max(1, len(g))
            age = (datetime.now(timezone.utc)-datetime.fromisoformat(r["created_at"])).total_seconds()/86400
            r["score"] = sum(w*v for w,v in zip(weights, (sim,r["importance"],relevance,math.exp(-age/30),r["confidence"])))
            r["sources"] = json.loads(r["sources"])
        return sorted(rows, key=lambda r:r["score"], reverse=True)[:limit]

    def send(self, sender: str, recipient: str, content: str, kind="message"):
        self.agent(recipient)
        if sender != "human":
            self.agent(sender)
        mid = uid("msg")
        with self.connect() as db:
            db.execute("INSERT INTO messages(id,sender,recipient,kind,content,created_at) VALUES(?,?,?,?,?,?)", (mid,sender,recipient,kind,content,now()))
        self.event("MESSAGE_SENT", recipient, f"{kind} delivered from {sender}")
        return mid

    def inbox(self, agent_id: str, unread=False):
        self.agent(agent_id)
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM messages WHERE recipient=? AND (?=0 OR read=0) ORDER BY created_at DESC LIMIT 50", (agent_id,int(unread)))]

    def mark_read(self, agent_id: str, ids: list[str]):
        with self.connect() as db:
            db.executemany("UPDATE messages SET read=1 WHERE recipient=? AND id=?", [(agent_id,i) for i in ids])

    def put(self, collection: str, value: dict[str, Any]):
        with self.connect() as db:
            db.execute("INSERT INTO records VALUES(?,?,?) ON CONFLICT(collection,id) DO UPDATE SET data=excluded.data", (collection,value["id"],json.dumps(value,allow_nan=False)))
        return value

    def get(self, collection: str, rid: str):
        with self.connect() as db:
            r = db.execute("SELECT data FROM records WHERE collection=? AND id=?", (collection,rid)).fetchone()
        if r is None:
            raise KeyError(rid)
        return json.loads(r[0])

    def records(self, collection: str):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT data FROM records WHERE collection=? ORDER BY rowid DESC", (collection,))]

    def setting(self, key: str, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self, key: str, value):
        with self.connect() as db:
            db.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key,json.dumps(value)))

    def enqueue(self, agent_id, kind, payload, project_id=None, priority=1):
        jid = uid("job")
        with self.connect() as db:
            db.execute("INSERT INTO jobs(id,agent_id,project_id,kind,payload,priority,status,created_at,updated_at) VALUES(?,?,?,?,?,?,'queued',?,?)", (jid,agent_id,project_id,kind,json.dumps(payload),priority,now(),now()))
        self.event("JOB_QUEUED", jid, f"{kind} assigned to {agent_id}")
        return jid

    def claim_job(self, project_id=None):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT * FROM jobs WHERE status='queued'
                AND agent_id NOT IN (SELECT agent_id FROM jobs WHERE status='running')
                AND (project_id IS NULL OR project_id IN
                    (SELECT id FROM records WHERE collection='projects' AND json_extract(data,'$.status')='running'))
                AND (project_id IS NULL OR project_id NOT IN
                    (SELECT project_id FROM jobs WHERE status='running' AND project_id IS NOT NULL))
                AND (? IS NULL OR project_id=?)
                ORDER BY priority DESC,created_at LIMIT 1""", (project_id, project_id)).fetchone()
            if not row:
                return None
            db.execute("UPDATE jobs SET status='running',attempts=attempts+1,updated_at=? WHERE id=?", (now(),row["id"]))
            result = dict(row)
            result["payload"] = json.loads(result["payload"])
            return result

    def finish_job(self, jid, status, error=None):
        with self.connect() as db:
            db.execute("UPDATE jobs SET status=?,error=?,updated_at=? WHERE id=?", (status,error,now(),jid))

    def jobs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 200")]

    def recover(self):
        # Do not replay experiments after an uncertain process crash.
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='blocked',error='Interrupted by restart; inspect artifacts before retry',updated_at=? WHERE status='running'", (now(),))
        for agent in self.agents():
            if agent.state == "thinking":
                agent.state = "idle"
                self.save_agent(agent)
