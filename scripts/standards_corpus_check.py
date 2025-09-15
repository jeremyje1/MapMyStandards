"""Quick check script to load the standards corpus and print summary stats."""
from pathlib import Path
from src.a3e.services.standards_loader import load_corpus


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    corpus_dir = repo_root / "data" / "standards"
    corpus = load_corpus(corpus_dir)
    total = sum(len(v) for v in corpus.values())
    print(f"Loaded accreditors: {list(corpus.keys())}")
    print(f"Total standards: {total}")
    for acc, items in corpus.items():
        print(f" - {acc}: {len(items)} standards")


if __name__ == "__main__":
    main()
