from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import threading

_LOCK = threading.Lock()
_STORE: Dict[str, List[Dict[str, Any]]] = {}
_FILE_PATH = Path(__file__).resolve().parents[3] / 'data' / 'metrics_timeseries.json'
_MAX_PER_ACCREDITOR = 365  # retain last N snapshots per accreditor


def _ensure_loaded() -> None:
    global _STORE
    if _STORE:
        return
    try:
        if _FILE_PATH.exists():
            data = json.loads(_FILE_PATH.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                _STORE = {str(k): list(v) for k, v in data.items() if isinstance(v, list)}
    except Exception:
        _STORE = {}


def _persist() -> None:
    try:
        _FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _FILE_PATH.open('w', encoding='utf-8') as f:
            json.dump(_STORE, f, ensure_ascii=False)
    except Exception:
        # Silent failure acceptable for non-critical telemetry persistence
        pass


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def maybe_snapshot(
    accreditor: str,
    payload: Dict[str, Any],
    *,
    min_interval_hours: int = 6,
    force: bool = False,
) -> Dict[str, Any]:
    """Store a metrics snapshot, throttled by min_interval_hours unless force=True.

    Payload expected keys: coverage_percentage, compliance_score, average_trust, average_risk,
    documents_analyzed, standards_mapped, total_standards. Additional keys are preserved.
    """
    _ensure_loaded()
    with _LOCK:
        key = (accreditor or 'GLOBAL').upper()
        series = _STORE.setdefault(key, [])
        if series and not force:
            last_ts = _parse_iso(series[-1].get('timestamp', '') or _now_iso())
            if last_ts and datetime.utcnow() - last_ts < timedelta(hours=min_interval_hours):
                return {"stored": False, "reason": "throttled", "last_timestamp": series[-1].get('timestamp')}
        snap = {
            "timestamp": payload.get('timestamp') or _now_iso(),
            "accreditor": key,
            "coverage_percentage": float(payload.get('coverage_percentage', 0.0)),
            "compliance_score": float(payload.get('compliance_score', 0.0)),
            "average_trust": float(payload.get('average_trust', 0.0)),
            "average_risk": float(payload.get('average_risk', 0.0)),
            "documents_analyzed": int(payload.get('documents_analyzed', 0)),
            "standards_mapped": int(payload.get('standards_mapped', 0)),
            "total_standards": int(payload.get('total_standards', 0)),
        }
        series.append(snap)
        # Enforce per-accreditor max length
        if len(series) > _MAX_PER_ACCREDITOR:
            _STORE[key] = series[-_MAX_PER_ACCREDITOR:]
        _persist()
        return {"stored": True, "snapshot": snap}


def get_series(accreditor: Optional[str] = None, days: int = 30, limit: int = 200) -> List[Dict[str, Any]]:
    """Return snapshots for an accreditor within the last N days (default 30).
    If accreditor is None, return combined series across all (tagged by accreditor).
    """
    _ensure_loaded()
    cutoff = datetime.utcnow() - timedelta(days=max(1, days))
    out: List[Dict[str, Any]] = []
    with _LOCK:
        if accreditor:
            key = accreditor.upper()
            series = _STORE.get(key, [])
            for s in series:
                ts = _parse_iso(s.get('timestamp', ''))
                if ts and ts >= cutoff:
                    out.append(s)
        else:
            for key, series in _STORE.items():
                for s in series:
                    ts = _parse_iso(s.get('timestamp', ''))
                    if ts and ts >= cutoff:
                        out.append(s)
    out.sort(key=lambda x: x.get('timestamp', ''))
    if limit and len(out) > limit:
        out = out[-limit:]
    return out


def last_snapshot(accreditor: str) -> Optional[Dict[str, Any]]:
    _ensure_loaded()
    with _LOCK:
        series = _STORE.get(accreditor.upper(), [])
        return series[-1] if series else None
