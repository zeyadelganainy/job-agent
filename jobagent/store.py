"""SQLite-backed state. Tracks each job through the loop so /pick maps back correctly.

status flow: new -> scored -> sent -> picked -> generated  (or -> skipped)
"""
import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import Job

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    source      TEXT,
    title       TEXT,
    company     TEXT,
    url         TEXT,
    location    TEXT,
    description TEXT,
    posted      TEXT,
    score       INTEGER,
    reasons     TEXT,
    gaps        TEXT,
    status      TEXT DEFAULT 'new',
    docs        TEXT,                 -- json: paths of generated files
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Store:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(ROOT / db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_job(self, job: Job) -> bool:
        """Insert if new. Returns True if it was newly inserted (so we don't re-score)."""
        cur = self.conn.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job.job_id,))
        if cur.fetchone():
            return False
        self.conn.execute(
            """INSERT INTO jobs (job_id, source, title, company, url, location,
                                 description, posted)
               VALUES (?,?,?,?,?,?,?,?)""",
            (job.job_id, job.source, job.title, job.company, job.url,
             job.location, job.description, job.posted),
        )
        self.conn.commit()
        return True

    def save_score(self, job: Job):
        self.conn.execute(
            "UPDATE jobs SET score=?, reasons=?, gaps=?, status='scored' WHERE job_id=?",
            (job.score, job.reasons, job.gaps, job.job_id),
        )
        self.conn.commit()

    def get(self, job_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()

    def by_status(self, status: str) -> list[sqlite3.Row]:
        # Stable order so the digest's 1..N numbering is deterministic across calls.
        return self.conn.execute(
            "SELECT * FROM jobs WHERE status=? "
            "ORDER BY score DESC, created_at ASC, job_id ASC", (status,)
        ).fetchall()

    def top_unscored(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM jobs WHERE status='new'").fetchall()

    def set_status(self, job_id: str, status: str):
        self.conn.execute("UPDATE jobs SET status=? WHERE job_id=?", (status, job_id))
        self.conn.commit()

    def record_docs(self, job_id: str, paths: Iterable[str]):
        self.conn.execute(
            "UPDATE jobs SET docs=?, status='generated' WHERE job_id=?",
            (json.dumps(list(paths)), job_id),
        )
        self.conn.commit()
