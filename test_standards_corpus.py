#!/usr/bin/env python3
"""Unit tests for standards corpus YAML parsing and structure validation"""

import sys
from pathlib import Path
import unittest

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from a3e.services.standards_loader import load_corpus, get_corpus_metadata, _ensure_prefix, _normalize_entry


class TestStandardsCorpus(unittest.TestCase):
    """Test standards corpus loading and structure"""
    
    @classmethod
    def setUpClass(cls):
        """Load corpus once for all tests"""
        cls.data_dir = project_root / "data" / "standards"
        cls.corpus = load_corpus(cls.data_dir)
        cls.metadata = get_corpus_metadata()
    
    def test_all_accreditors_loaded(self):
        """Test that all 6 regional accreditors are loaded"""
        expected = {'SACSCOC', 'HLC', 'MSCHE', 'WASC', 'NWCCU', 'NECHE'}
        loaded = set(self.corpus.keys())
        
        # Check if all expected accreditors are present
        missing = expected - loaded
        self.assertEqual(missing, set(), f"Missing accreditors: {missing}")
        
        # Verify each has standards
        for accreditor in expected:
            self.assertIn(accreditor, self.corpus)
            self.assertGreater(len(self.corpus[accreditor]), 0, 
                               f"{accreditor} has no standards")
    
    def test_metadata_structure(self):
        """Test that metadata is properly structured for each accreditor"""
        required_fields = {'accreditor', 'name', 'version', 'standard_count'}
        
        for accreditor, meta in self.metadata.items():
            with self.subTest(accreditor=accreditor):
                # Check required fields
                for field in required_fields:
                    self.assertIn(field, meta, f"{accreditor} missing {field}")
                
                # Verify counts match
                self.assertEqual(meta['standard_count'], 
                                 len(self.corpus[accreditor]),
                                 f"{accreditor} standard count mismatch")
    
    def test_standard_structure(self):
        """Test that each standard has required fields and structure"""
        required_fields = {'id', 'title', 'description', 'category'}
        
        for accreditor, standards in self.corpus.items():
            for standard in standards:
                with self.subTest(standard=standard.get('id')):
                    # Check required fields
                    for field in required_fields:
                        self.assertIn(field, standard, 
                                      f"Standard {standard.get('id')} missing {field}")
                    
                    # Verify ID has accreditor prefix
                    self.assertTrue(standard['id'].startswith(f"{accreditor}_"),
                                    f"Standard ID doesn't start with {accreditor}_")
                    
                    # Check clauses structure if present
                    if 'clauses' in standard:
                        self.assertIsInstance(standard['clauses'], list)
                        for clause in standard['clauses']:
                            self._validate_clause_structure(clause, accreditor)
    
    def _validate_clause_structure(self, clause, accreditor):
        """Helper to validate clause structure"""
        required_fields = {'id', 'title', 'description'}
        
        # Check required fields
        for field in required_fields:
            self.assertIn(field, clause, f"Clause {clause.get('id')} missing {field}")
        
        # Verify ID has accreditor prefix
        self.assertTrue(clause['id'].startswith(f"{accreditor}_"),
                        f"Clause ID doesn't start with {accreditor}_")
        
        # Check indicators if present
        if 'indicators' in clause:
            self.assertIsInstance(clause['indicators'], list)
            self.assertGreater(len(clause['indicators']), 0,
                               f"Clause {clause['id']} has empty indicators")
            # Each indicator should be a non-empty string
            for indicator in clause['indicators']:
                self.assertIsInstance(indicator, str)
                self.assertGreater(len(indicator.strip()), 0,
                                   f"Empty indicator in clause {clause['id']}")
    
    def test_ensure_prefix_function(self):
        """Test the _ensure_prefix function"""
        # Test cases
        test_cases = [
            ("SACSCOC", "1.1", "SACSCOC_1.1"),
            ("HLC", "HLC_2.A", "HLC_2.A"),  # Already prefixed
            ("MSCHE", "Standard II", "MSCHE_Standard_II"),  # Spaces replaced
            ("WASC", "1.2/3", "WASC_1.2.3"),  # Slashes replaced
        ]
        
        for accreditor, raw_id, expected in test_cases:
            with self.subTest(accreditor=accreditor, raw_id=raw_id):
                result = _ensure_prefix(accreditor, raw_id)
                self.assertEqual(result, expected)
    
    def test_normalize_entry_function(self):
        """Test the _normalize_entry function"""
        test_entry = {
            "id": "1.1",
            "title": "Test Standard",
            "description": "Test description",
            "clauses": [
                {
                    "id": "1.1.a",
                    "title": "Test Clause",
                    "indicators": ["Indicator 1", "Indicator 2"]
                }
            ]
        }
        
        defaults = {"version": "2024", "effective_date": "2024-01-01"}
        normalized = _normalize_entry("TEST", test_entry, defaults)
        
        # Check normalization
        self.assertEqual(normalized["id"], "TEST_1.1")
        self.assertEqual(normalized["version"], "2024")
        self.assertEqual(normalized["clauses"][0]["id"], "TEST_1.1.a")
        self.assertEqual(len(normalized["clauses"][0]["indicators"]), 2)
    
    def test_specific_accreditor_content(self):
        """Test specific content for each accreditor"""
        # SACSCOC - should have sections 4-14
        sacscoc_ids = {s['id'] for s in self.corpus.get('SACSCOC', [])}
        for section in range(4, 15):
            self.assertTrue(any(f"SACSCOC_{section}" in sid for sid in sacscoc_ids),
                            f"SACSCOC missing section {section}")
        
        # HLC - should have 5 main criteria
        hlc_criteria = {s['id'] for s in self.corpus.get('HLC', [])}
        for criterion in range(1, 6):
            self.assertTrue(any(f"HLC_{criterion}" in cid for cid in hlc_criteria),
                            f"HLC missing criterion {criterion}")
        
        # MSCHE - should have 7 standards
        msche_standards = self.corpus.get('MSCHE', [])
        self.assertGreaterEqual(len(msche_standards), 7,
                                "MSCHE should have at least 7 standards")
        
        # WASC - should have 4 main standards
        wasc_standards = {s['id'] for s in self.corpus.get('WASC', [])}
        for standard in range(1, 5):
            self.assertTrue(any(f"WASC_{standard}" in sid for sid in wasc_standards),
                            f"WASC missing standard {standard}")
        
        # NWCCU - should have Standard One and Standard Two
        nwccu_standards = {s['id'] for s in self.corpus.get('NWCCU', [])}
        self.assertTrue(any("NWCCU_1" in sid for sid in nwccu_standards),
                        "NWCCU missing Standard One")
        self.assertTrue(any("NWCCU_2" in sid for sid in nwccu_standards),
                        "NWCCU missing Standard Two")
        
        # NECHE - should have 9 standards
        neche_standards = [s for s in self.corpus.get('NECHE', []) 
                           if s['id'].split('_')[1].split('.')[0].isdigit()]
        standard_numbers = {int(s['id'].split('_')[1].split('.')[0]) 
                            for s in neche_standards}
        self.assertGreaterEqual(max(standard_numbers), 8,
                                "NECHE should have at least 8 main standards")
    
    def test_indicator_completeness(self):
        """Test that standards have meaningful indicators"""
        min_indicators_per_accreditor = 50  # Minimum expected
        
        for accreditor, standards in self.corpus.items():
            total_indicators = 0
            for standard in standards:
                for clause in standard.get('clauses', []):
                    total_indicators += len(clause.get('indicators', []))
            
            with self.subTest(accreditor=accreditor):
                self.assertGreaterEqual(total_indicators, min_indicators_per_accreditor,
                                        f"{accreditor} has too few indicators")
    
    def test_cross_references_potential(self):
        """Test that there are potential cross-references between accreditors"""
        # Common themes that should appear across accreditors
        common_themes = ['mission', 'governance', 'faculty', 'resources', 'assessment']
        
        for theme in common_themes:
            accreditors_with_theme = []
            for accreditor, standards in self.corpus.items():
                # Check if any standard title or description contains the theme
                for standard in standards:
                    if (theme.lower() in standard.get('title', '').lower() or
                            theme.lower() in standard.get('description', '').lower()):
                        accreditors_with_theme.append(accreditor)
                        break
            
            with self.subTest(theme=theme):
                self.assertGreaterEqual(len(accreditors_with_theme), 4,
                                        f"Theme '{theme}' should appear in most accreditors")


if __name__ == "__main__":
    unittest.main(verbosity=2)
