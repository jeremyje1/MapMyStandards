"""Lightweight evidence upload & analysis placeholder endpoints.
...existing code...
"""
from __future__ import annotations

import asyncio
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Depends
from fastapi.responses import JSONResponse

DB_PATH = Path("a3e.db")
router = APIRouter(prefix="/api/v1/upload", tags=["upload-lite"])


def _auth(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")
    return token


USE_DB = False
if DB_PATH.exists():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                filename TEXT,
                title TEXT,
                description TEXT,
                accreditor TEXT,
                status TEXT,
                progress INTEGER,
                standards_matched INTEGER,
                confidence_score REAL,
                uploaded_at TEXT
                )"""
            )
        USE_DB = True
    except Exception:
        USE_DB = False

_mem: List[Dict[str, Any]] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insert(record: Dict[str, Any]) -> None:
    if USE_DB:
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "INSERT INTO uploads VALUES (:id,:filename,:title,:description,:accreditor,:status,:progress,:standards_matched,:confidence_score,:uploaded_at)",
                record,
            )
            c.commit()
    else:
        _mem.append(record)


def _update(upload_id: str, **updates) -> None:
    if USE_DB:
        sets = ", ".join(f"{k}=:{k}" for k in updates)
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                f"UPDATE uploads SET {sets} WHERE id=:id",
                {"id": upload_id, **updates},
            )
            c.commit()
    else:
        for rec in _mem:
            if rec["id"] == upload_id:
                rec.update(updates)
                break


def _recent(limit: int) -> List[Dict[str, Any]]:
    if USE_DB:
        with sqlite3.connect(DB_PATH) as c:
            rows = c.execute(
                "SELECT id,filename,title,description,accreditor,status,progress,standards_matched,confidence_score,uploaded_at FROM uploads ORDER BY datetime(uploaded_at) DESC LIMIT ?",
                (limit,),
            ).fetchall()
        cols = [
            "id",
            "filename",
            "title",
            "description",
            "accreditor",
            "status",
            "progress",
            "standards_matched",
            "confidence_score",
            "uploaded_at",
        ]
        return [dict(zip(cols, row)) for row in rows]
    return sorted(_mem, key=lambda r: r["uploaded_at"], reverse=True)[:limit]


async def _simulate(upload_id: str) -> None:
    for pct in (15, 37, 62, 85):
        await asyncio.sleep(0.5)
        _update(upload_id, progress=pct)
    await asyncio.sleep(0.6)
    _update(
        upload_id,
        status="completed",
        progress=100,
        standards_matched=42,
        confidence_score=0.88,
    )


@router.post("/evidence")
async def upload_evidence(
    token: str = Depends(_auth),  # noqa: ARG001 - placeholder auth
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    accreditor: str = Form(...),
):
    if not accreditor:
        raise HTTPException(status_code=400, detail="Accreditor required")
    uid = str(uuid.uuid4())
    record = {
        "id": uid,
        "filename": file.filename,
        "title": title or file.filename,
        "description": description,
        "accreditor": accreditor,
        "status": "processing",
        "progress": 5,
        "standards_matched": None,
        "confidence_score": None,
        "uploaded_at": _now(),
    }
    _insert(record)
    asyncio.create_task(_simulate(uid))
    return JSONResponse({"success": True, "data": {"id": uid, "status": "processing"}})


@router.get("/list")
async def list_uploads(token: str = Depends(_auth), limit: int = 5):  # noqa: ARG001
    return {"success": True, "data": {"uploads": _recent(limit)}}
