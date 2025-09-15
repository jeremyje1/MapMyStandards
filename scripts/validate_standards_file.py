"""Validate a standards YAML/JSON file for schema and normalization."""
from pathlib import Path
import sys
import json
from typing import Any
try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore

from src.a3e.services.standards_schema import Corpus
from src.a3e.services.standards_loader import _normalize_entry  # type: ignore


def load_any(p: Path) -> Any:
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("pyyaml not installed")
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_standards_file.py <path-to-file>")
        return 2
    path = Path(sys.argv[1]).resolve()
    data = load_any(path)
    corpus = Corpus(**data)
    # Run normalization simulation
    sample = [_normalize_entry(corpus.accreditor, s.model_dump()) for s in corpus.standards]
    print(f"Valid corpus for {corpus.accreditor}; standards: {len(sample)}; example id: {sample[0]['id'] if sample else 'N/A'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
