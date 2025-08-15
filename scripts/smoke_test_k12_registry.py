#!/usr/bin/env python3
"""
Quick smoke test to validate K-12 accreditors are resolvable in the registry.
Run: python scripts/smoke_test_k12_registry.py
"""
from src.a3e.core.accreditation_registry import (
    InstitutionType,
    get_accreditors_by_institution_type,
    get_accreditor_by_id,
    get_standards_by_accreditor_and_institution_type,
)

k12_types = [InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT]
expected_ids = {"cognia", "sacs_casi", "nca_casi", "msa_cess"}

for itype in k12_types:
    accs = get_accreditors_by_institution_type(itype)
    ids = {a.id for a in accs}
    print(f"{itype.value}: found {len(ids)} accreditors -> {sorted(ids)}")
    missing = expected_ids - ids
    assert not missing, f"Missing K-12 accreditors for {itype}: {missing}"

for aid in expected_ids:
    acc = get_accreditor_by_id(aid)
    assert acc is not None, f"accreditor {aid} not found"
    standards = get_standards_by_accreditor_and_institution_type(aid, InstitutionType.K12_SCHOOL)
    assert standards, f"no standards found for {aid}"
    print(f"{aid}: {len(standards)} standards for K12_SCHOOL")

print("K-12 registry smoke test: PASS")
