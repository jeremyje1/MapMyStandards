from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

_LOCK = threading.Lock()
_STORE: Dict[str, List[Dict[str, Any]]] = {}
_FILE_PATH = Path(__file__).resolve().parents[3] / "data" / "telemetry_standards_explorer.json"
_MAX_EVENTS_PER_USER = 200
_MAX_TOTAL_EVENTS = 2000


def _ensure_loaded() -> None:
    global _STORE
    if _STORE:
        return
    try:
        if _FILE_PATH.exists():
            raw = json.loads(_FILE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _STORE = {str(k): list(v) for k, v in raw.items() if isinstance(v, list)}
    except Exception:
        _STORE = {}


def _persist() -> None:
    try:
        _FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _FILE_PATH.open("w", encoding="utf-8") as handle:
            json.dump(_STORE, handle, ensure_ascii=False)
    except Exception:
        # Telemetry should never block core flows. Fail silently.
        pass


def _hash_user(user_key: str) -> str:
    digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()
    return digest[:16]


def record_event(user_key: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Append an explorer telemetry event for the given user.

    The payload is truncated to keep storage bounded. Returns the stored event for inspection.
    """
    _ensure_loaded()
    event = dict(event)
    event.setdefault("timestamp", datetime.utcnow().isoformat())
    payload = event.get("payload")
    if isinstance(payload, dict):
        # Prevent runaway payload growth by trimming nested values to primitives where possible
        event["payload"] = {str(k)[:50]: payload[k] for k in list(payload.keys())[:15]}

    hashed_user = _hash_user(user_key or "anonymous")
    with _LOCK:
        series = _STORE.setdefault(hashed_user, [])
        series.append(event)
        if len(series) > _MAX_EVENTS_PER_USER:
            _STORE[hashed_user] = series[-_MAX_EVENTS_PER_USER:]
        # Enforce global ceiling
        total_events = sum(len(v) for v in _STORE.values())
        if total_events > _MAX_TOTAL_EVENTS:
            # Drop oldest events across users by trimming each list proportionally
            for key in list(_STORE.keys()):
                entries = _STORE[key]
                if len(entries) > 10:
                    _STORE[key] = entries[-min(len(entries), _MAX_EVENTS_PER_USER // 2 or 1):]
        _persist()
        return event
