# 02 – One‑command local dev

## Prerequisites
* Docker ≥ 26
* Python 3.12 + poetry
* Node 20 (for VS Code extension sandbox)

```bash
# clone & spin everything
git clone https://github.com/YOURORG/a3e.git
cd a3e
make dev         # builds containers & seeds sample data
```

`make dev` runs:

1. `docker compose up` (Postgres, Milvus, FastAPI).
2. `poetry install` + pre‑commit.
3. Seeds 10 public accreditation artefacts into Milvus.

**Copilot/Sonnet notes**: code comments are "prompt‑rich" so the pair‑programming models infer typings & docstrings automatically.
