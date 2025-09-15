"""
Standards corpus loader

Loads accreditor standards from YAML or JSON files under data/standards/.
Normalizes IDs to include the accreditor prefix and returns a list of
standard dicts compatible with StandardsGraph._add_standard_hierarchy.
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json
import logging

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - pyyaml is in requirements
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


def _ensure_prefix(accreditor: str, raw_id: str) -> str:
    up = accreditor.upper()
    if raw_id.upper().startswith(up + "_"):
        return raw_id
    # Replace disallowed characters for node_id stability
    safe = str(raw_id).replace(" ", "_").replace("/", ".")
    return f"{up}_{safe}"


def _normalize_entry(accreditor: str, entry: Dict[str, Any], defaults: Dict[str, Any] | None = None) -> Dict[str, Any]:
    norm = dict(entry)
    norm["id"] = _ensure_prefix(accreditor, str(entry.get("id", "")))
    if defaults:
        # Attach corpus-level metadata if missing on the entry
        for k in ("version", "effective_date"):
            if k not in norm and k in defaults:
                norm[k] = defaults[k]
    clauses = []
    for cl in entry.get("clauses", []) or []:
        cln = dict(cl)
        cln["id"] = _ensure_prefix(accreditor, str(cl.get("id", "")))
        # keep indicators if present
        clauses.append(cln)
    norm["clauses"] = clauses
    return norm


def load_corpus(dir_path: str | Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load all corpus files returning {accreditor: [standards...]}

    NOTE: Extended metadata capture now also stored on a private attribute
    standards_loader._corpus_metadata for later API exposure. This preserves
    backward compatibility of the original return shape.
    """
    base = Path(dir_path)
    if not base.exists():
        logger.warning("Standards corpus directory not found: %s", base)
        return {}

    results: Dict[str, List[Dict[str, Any]]] = {}
    corpus_metadata: Dict[str, Dict[str, Any]] = {}
    for path in base.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        try:
            if path.suffix.lower() in {".yaml", ".yml"}:
                if yaml is None:
                    logger.error("pyyaml not installed; skipping %s", path.name)
                    continue
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.exception("Failed parsing %s: %s", path.name, e)
            continue

        try:
            accreditor = str((data or {}).get("accreditor", "")).strip() or path.stem.split(".")[0].upper()
            standards = (data or {}).get("standards", []) or []
            meta_block = (data or {}).get("metadata", {}) or {}
            # Backwards compatibility: allow top-level version/effective_date
            defaults = {"version": meta_block.get("version") or (data or {}).get("version"),
                        "effective_date": meta_block.get("effective_date") or (data or {}).get("effective_date")}
            normalized = [_normalize_entry(accreditor, s, defaults) for s in standards]
            results.setdefault(accreditor, []).extend(normalized)
            corpus_metadata[accreditor] = {
                "accreditor": accreditor,
                "name": meta_block.get("name"),
                "version": defaults.get("version"),
                "effective_date": defaults.get("effective_date"),
                "last_updated": meta_block.get("last_updated"),
                "source_url": meta_block.get("source_url"),
                "license": meta_block.get("license"),
                "disclaimer": meta_block.get("disclaimer"),
                "coverage_notes": meta_block.get("coverage_notes"),
                "standard_count": len(standards),
                "file": path.name,
            }
            logger.info("Loaded %d standards for %s from %s", len(standards), accreditor, path.name)
        except Exception as e:
            logger.exception("Failed normalizing %s: %s", path.name, e)
            continue
    # Store for later external access (e.g., API endpoint) without changing signature
    try:
        globals()["_corpus_metadata_cache"] = corpus_metadata
    except Exception:  # pragma: no cover
        pass
    return results


def get_corpus_metadata() -> Dict[str, Dict[str, Any]]:
    """Return cached corpus metadata collected during the last load_corpus call.

    If no metadata is cached yet, returns an empty dict. This avoids triggering a filesystem
    load inside an API request; callers can force reload explicitly by calling load_corpus.
    """
    return globals().get("_corpus_metadata_cache", {})  # type: ignore
