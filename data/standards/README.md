# Standards Corpus

This folder holds accreditor standards in a portable, editable format. Files can be YAML or JSON.

Schema (minimal, flexible):
- accreditor: short code (e.g., SACSCOC)
- version: string (e.g., "2024")
- effective_date: ISO date (e.g., "2024-01-01")
- standards: array of standards
  - id: standard identifier (will be prefixed with accreditor if not already)
  - title: string
  - description: string (optional)
  - clauses: array
    - id: clause identifier (will be prefixed if not already)
    - title: string
    - description: string (optional)
    - indicators: array of strings (optional)

Notes:
- IDs are auto-normalized to include the accreditor prefix to ensure global uniqueness.
- Additional metadata fields are allowed and ignored by the loader if unknown.
- Add more accreditors by dropping new files here (e.g., `hlc.yaml`, `msche.json`).
