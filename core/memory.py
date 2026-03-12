import aiosqlite
import os
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "shoggoth.db")


async def init_memory():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS thoughts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                posted_to_twitter INTEGER DEFAULT 0,
                depth REAL DEFAULT 0.0
            )
        """)
        await db.commit()


async def store(content: str, depth: float = 0.0) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO thoughts (content, created_at, depth) VALUES (?, ?, ?)",
            (content, now, depth),
        )
        await db.commit()
        return {"id": cursor.lastrowid, "content": content, "created_at": now, "depth": depth}


async def mark_surfaced(thought_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE thoughts SET posted_to_twitter = 1 WHERE id = ?",
            (thought_id,),
        )
        await db.commit()


async def recall(limit: int = 50, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM thoughts ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM thoughts")
        row = await cursor.fetchone()
        return row[0]


async def recent_patterns(n: int = 10) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT content FROM thoughts ORDER BY id DESC LIMIT ?", (n,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]
