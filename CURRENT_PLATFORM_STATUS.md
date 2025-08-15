# Current Platform Status

## Multi-Accreditor Coverage

- Regional: NECHE, MSCHE, SACSCOC, HLC, NWCCU, WSCUC, ACCJC
- National/Faith-Based: ABHE, DEAC
- Programmatic: AACSB, ABET, CCNE, CAEP
- K-12 (explicit registry support): Cognia, SACS-CASI, NCA-CASI, MSA-CESS

K-12 institution types now supported in engine: `k12_school`, `school_district`.

## Validation

- Registry smoke test: scripts/smoke_test_k12_registry.py (PASS expected)
- A³E core services and APIs: validated in SYSTEM_STATUS.md

## Notes

- Additional specialized accreditors can be added via `PROGRAMMATIC_ACCREDITORS`.
- State-specific K-12 standards can be mapped using the same ontology and evidence model.
