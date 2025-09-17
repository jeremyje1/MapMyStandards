#!/usr/bin/env python3
"""Integration test for cross-accreditor matching functionality"""

import sys
from pathlib import Path
import unittest
from typing import List, Dict, Any

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from a3e.services.standards_loader import load_corpus
from a3e.services.standards_graph import StandardsGraph, standards_graph


class TestCrossAccreditorMatching(unittest.TestCase):
    """Test cross-accreditor matching functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize standards graph with corpus"""
        # Load corpus
        data_dir = project_root / "data" / "standards"
        corpus = load_corpus(data_dir)
        
        # Initialize a fresh standards graph for testing
        cls.test_graph = StandardsGraph()
        
        # Add all standards to the graph
        for accreditor, standards in corpus.items():
            for standard in standards:
                cls.test_graph._add_standard_hierarchy(accreditor, standard)
        
        # Also test the global instance
        cls.global_graph = standards_graph
    
    def test_find_matches_mission_standards(self):
        """Test finding matches for mission-related standards across accreditors"""
        # Test known equivalence: mission standards should match across accreditors
        test_cases = [
            ("SACSCOC", "HLC"),
            ("HLC", "MSCHE"),
            ("MSCHE", "NECHE"),
            ("WASC", "NWCCU"),
            ("NECHE", "SACSCOC")
        ]
        
        for source, target in test_cases:
            with self.subTest(source=source, target=target):
                matches = self.test_graph.find_cross_accreditor_matches(
                    source, target, threshold=0.2, top_k=5
                )
                
                # Should find at least one match
                self.assertGreater(len(matches), 0,
                    f"No matches found between {source} and {target}")
                
                # Check if mission-related standards are matched
                mission_found = False
                for match in matches:
                    if ("mission" in match["source_title"].lower() or
                            "mission" in match["target_title"].lower()):
                        mission_found = True
                        break
                
                self.assertTrue(mission_found,
                    f"No mission-related matches found between {source} and {target}")
    
    def test_match_scores_reasonable(self):
        """Test that match scores are within reasonable ranges"""
        matches = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.1, top_k=10
        )
        
        self.assertGreater(len(matches), 0, "No matches found")
        
        for match in matches:
            # Scores should be between 0 and 1
            self.assertGreaterEqual(match["score"], 0.0)
            self.assertLessEqual(match["score"], 1.0)
            
            # Higher scores should have more keyword overlap
            if match["score"] > 0.5:
                # Strong matches should have meaningful overlap
                source_words = set(match["source_title"].lower().split())
                target_words = set(match["target_title"].lower().split())
                overlap = source_words & target_words
                self.assertGreater(len(overlap), 0,
                    f"High score match has no title overlap: {match}")
    
    def test_known_equivalences(self):
        """Test specific known equivalences between accreditors"""
        known_equivalences = [
            # Mission/Purpose standards
            {
                "theme": "Mission",
                "examples": [
                    ("SACSCOC_4", "Governance"),  # SACSCOC Section 4
                    ("HLC_1", "Mission"),  # HLC Criterion 1
                    ("MSCHE_I", "Mission"),  # MSCHE Standard I
                    ("WASC_1", "Institutional Purposes"),  # WASC Standard 1
                    ("NWCCU_1.A", "Institutional Mission"),  # NWCCU 1.A
                    ("NECHE_1", "Mission")  # NECHE Standard 1
                ]
            },
            # Faculty standards
            {
                "theme": "Faculty",
                "examples": [
                    ("SACSCOC_6", "Faculty"),  # SACSCOC Section 6
                    ("HLC_3", "Teaching"),  # HLC Criterion 3 (includes faculty)
                    ("MSCHE_III", "Educational Experience"),  # MSCHE Standard III
                    ("WASC_2", "Educational Objectives"),  # WASC Standard 2
                    ("NWCCU_2.F", "Human Resources"),  # NWCCU 2.F (includes faculty)
                    ("NECHE_6", "Teaching")  # NECHE Standard 6
                ]
            },
            # Assessment/Effectiveness standards
            {
                "theme": "Assessment",
                "examples": [
                    ("SACSCOC_8", "Student Achievement"),  # SACSCOC Section 8
                    ("HLC_4", "Teaching and Learning"),  # HLC Criterion 4
                    ("MSCHE_V", "Educational Effectiveness"),  # MSCHE Standard V
                    ("WASC_4", "Quality Assurance"),  # WASC Standard 4
                    ("NWCCU_1.C", "Student Learning"),  # NWCCU 1.C
                    ("NECHE_8", "Educational Effectiveness")  # NECHE Standard 8
                ]
            }
        ]
        
        for equiv_group in known_equivalences:
            theme = equiv_group["theme"]
            examples = equiv_group["examples"]
            
            # Test that standards within each theme match with each other
            for i, (source_id, source_theme) in enumerate(examples):
                for j, (target_id, target_theme) in enumerate(examples):
                    if i >= j:  # Skip self and already-tested pairs
                        continue
                    
                    source_acc = source_id.split("_")[0]
                    target_acc = target_id.split("_")[0]
                    
                    if source_acc == target_acc:  # Skip same accreditor
                        continue
                    
                    with self.subTest(theme=theme, source=source_id, target=target_id):
                        matches = self.test_graph.find_cross_accreditor_matches(
                            source_acc, target_acc, threshold=0.15, top_k=10
                        )
                        
                        # Check if the expected standards are in the matches
                        source_matched = any(source_id in m["source_id"] for m in matches)
                        target_matched = any(target_id in m["target_id"] for m in matches)
                        
                        # At least one should be present in matches
                        self.assertTrue(source_matched or target_matched,
                            f"{theme} standards {source_id} and {target_id} not matched")
    
    def test_threshold_filtering(self):
        """Test that threshold parameter works correctly"""
        # Get matches with low threshold
        low_threshold_matches = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.1, top_k=20
        )
        
        # Get matches with high threshold
        high_threshold_matches = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.5, top_k=20
        )
        
        # High threshold should have fewer matches
        self.assertGreater(len(low_threshold_matches), len(high_threshold_matches),
            "High threshold should filter out more matches")
        
        # All high threshold matches should have score >= 0.5
        for match in high_threshold_matches:
            self.assertGreaterEqual(match["score"], 0.5,
                f"Match score {match['score']} below threshold 0.5")
    
    def test_top_k_limiting(self):
        """Test that top_k parameter limits results correctly"""
        # Get different numbers of matches
        top_3 = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.1, top_k=3
        )
        top_5 = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.1, top_k=5
        )
        top_10 = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.1, top_k=10
        )
        
        # Check counts
        self.assertLessEqual(len(top_3), 3)
        self.assertLessEqual(len(top_5), 5)
        self.assertLessEqual(len(top_10), 10)
        
        # top_3 should be subset of top_5
        top_3_ids = {(m["source_id"], m["target_id"]) for m in top_3}
        top_5_ids = {(m["source_id"], m["target_id"]) for m in top_5}
        self.assertTrue(top_3_ids.issubset(top_5_ids),
            "top_3 results should be subset of top_5")
    
    def test_reciprocal_matching(self):
        """Test that matching is reasonably reciprocal"""
        # Get matches HLC -> MSCHE
        hlc_to_msche = self.test_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.3, top_k=5
        )
        
        # Get matches MSCHE -> HLC
        msche_to_hlc = self.test_graph.find_cross_accreditor_matches(
            "MSCHE", "HLC", threshold=0.3, top_k=5
        )
        
        # Both should have matches
        self.assertGreater(len(hlc_to_msche), 0)
        self.assertGreater(len(msche_to_hlc), 0)
        
        # Check if there are reciprocal matches
        reciprocal_found = False
        for match1 in hlc_to_msche:
            for match2 in msche_to_hlc:
                if (match1["source_id"] == match2["target_id"] and
                        match1["target_id"] == match2["source_id"]):
                    reciprocal_found = True
                    break
        
        self.assertTrue(reciprocal_found,
            "No reciprocal matches found between HLC and MSCHE")
    
    def test_global_instance_initialized(self):
        """Test that the global standards_graph instance is properly initialized"""
        # Global instance should have standards loaded
        hlc_standards = self.global_graph.get_accreditor_standards("HLC")
        self.assertGreater(len(hlc_standards), 0,
            "Global standards_graph instance has no HLC standards")
        
        # Should be able to find matches
        matches = self.global_graph.find_cross_accreditor_matches(
            "HLC", "MSCHE", threshold=0.3, top_k=3
        )
        self.assertGreater(len(matches), 0,
            "Global instance cannot find cross-accreditor matches")


if __name__ == "__main__":
    # Run with higher verbosity to see test progress
    unittest.main(verbosity=2)
