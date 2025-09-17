#!/usr/bin/env python3
"""Test script to verify all standards files load correctly"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from a3e.services.standards_loader import load_corpus, get_corpus_metadata


def test_standards_loading():
    """Test loading all standards files and display summary"""
    print("Testing standards corpus loading...\n")
    
    # Load all standards
    data_dir = project_root / "data" / "standards"
    corpus = load_corpus(data_dir)
    
    # Get metadata
    metadata = get_corpus_metadata()
    
    # Display summary
    print(f"Successfully loaded {len(corpus)} accreditors:")
    print("-" * 60)
    
    for accreditor, standards in sorted(corpus.items()):
        meta = metadata.get(accreditor, {})
        print(f"\n{accreditor}:")
        print(f"  Name: {meta.get('name', 'N/A')}")
        print(f"  Version: {meta.get('version', 'N/A')}")
        print(f"  Standards: {len(standards)}")
        print(f"  File: {meta.get('file', 'N/A')}")
        
        # Count clauses and indicators
        total_clauses = sum(len(s.get('clauses', [])) for s in standards)
        total_indicators = sum(
            sum(len(c.get('indicators', [])) for c in s.get('clauses', []))
            for s in standards
        )
        print(f"  Total Clauses: {total_clauses}")
        print(f"  Total Indicators: {total_indicators}")
        
        # Show sample standard
        if standards:
            sample = standards[0]
            print(f"  Sample: {sample.get('id')} - {sample.get('title')}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {sum(len(s) for s in corpus.values())} standards across all accreditors")
    
    # Verify all expected accreditors are present
    expected = {'SACSCOC', 'HLC', 'MSCHE', 'WASC', 'NWCCU', 'NECHE'}
    loaded = set(corpus.keys())
    missing = expected - loaded
    extra = loaded - expected
    
    if missing:
        print(f"\nWARNING: Missing expected accreditors: {missing}")
    if extra:
        print(f"\nNOTE: Extra accreditors found: {extra}")
    
    if not missing:
        print("\n✓ All expected accreditors loaded successfully!")
        return True
    else:
        print("\n✗ Some accreditors failed to load")
        return False


if __name__ == "__main__":
    success = test_standards_loading()
    sys.exit(0 if success else 1)
