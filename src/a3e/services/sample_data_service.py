"""Sample data service for trial accounts and guided tutorials."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import uuid

from ..core.config import settings

logger = logging.getLogger(__name__)

class SampleDataService:
    """Service for generating and managing sample data for trial accounts."""
    
    # Sample institutional profiles
    SAMPLE_INSTITUTIONS = [
        {
            "name": "Riverside Community College",
            "type": "community_college",
            "enrollment": "8,500",
            "accreditor": "ACCJC",
            "state": "CA",
            "sample_goals": ["Map standards quickly", "Prep self-study", "Track progress"],
            "sample_docs": ["Strategic Plan 2023-2028", "Student Learning Outcomes Assessment", "Faculty Qualifications Report"],
            "success_metrics": {
                "documents_analyzed": 12,
                "standards_mapped": 48,
                "compliance_score": 87,
                "reports_generated": 3
            }
        },
        {
            "name": "Metropolitan State University",
            "type": "public_university", 
            "enrollment": "15,200",
            "accreditor": "HLC",
            "state": "MN",
            "sample_goals": ["Automate evidence tagging", "Mid-cycle review", "Data for board"],
            "sample_docs": ["Annual Assessment Report", "Faculty Senate Minutes", "Student Success Dashboard"],
            "success_metrics": {
                "documents_analyzed": 24,
                "standards_mapped": 78,
                "compliance_score": 92,
                "reports_generated": 5
            }
        },
        {
            "name": "Heritage Liberal Arts College",
            "type": "private_college",
            "enrollment": "2,800", 
            "accreditor": "SACSCOC",
            "state": "GA",
            "sample_goals": ["Close assessment loop", "Accreditation visit prep", "Gap analysis"],
            "sample_docs": ["QEP Implementation Report", "Institutional Effectiveness Plan", "Board of Trustees Report"],
            "success_metrics": {
                "documents_analyzed": 18,
                "standards_mapped": 63,
                "compliance_score": 89,
                "reports_generated": 4
            }
        }
    ]
    
    # Sample analysis results for quick wins dashboard
    SAMPLE_ANALYSIS_RESULTS = {
        "quick_wins": [
            {
                "type": "gap_identified",
                "title": "Missing Evidence for Standard 8.2.c",
                "description": "AI identified potential gap in student learning outcomes documentation",
                "priority": "high",
                "action": "Upload SLO assessment reports",
                "time_saved": "4 hours"
            },
            {
                "type": "auto_mapping",
                "title": "Strategic Plan Auto-Mapped",
                "description": "Automatically mapped 23 standards across 4 accreditation categories",
                "priority": "completed",
                "action": "Review and validate mappings",
                "time_saved": "12 hours"
            },
            {
                "type": "compliance_boost",
                "title": "Compliance Score: 87%",
                "description": "Above industry average of 73% - strong institutional position",
                "priority": "positive",
                "action": "Focus on remaining 13% for excellence",
                "time_saved": "N/A"
            }
        ],
        "roi_calculation": {
            "monthly_time_saved": 40,
            "hourly_rate": 75,
            "monthly_value": 3000,
            "consultant_hours_avoided": 10,
            "consultant_rate": 200,
            "consultant_savings": 2000,
            "total_monthly_value": 5000,
            "subscription_cost": 297,
            "roi_multiplier": 16.8
        }
    }
    
    def __init__(self):
        """Initialize the sample data service."""
        pass
    
    def get_sample_institution(self, institution_type: Optional[str] = None, enrollment_range: Optional[str] = None) -> Dict[str, Any]:
        """Get appropriate sample institution data based on user characteristics."""
        
        # Filter by enrollment range if specified
        if enrollment_range:
            if enrollment_range == "under_1000":
                candidates = [inst for inst in self.SAMPLE_INSTITUTIONS if "," not in inst["enrollment"] and int(inst["enrollment"].replace(",", "")) < 1000]
            elif enrollment_range == "1k_5k":
                candidates = [inst for inst in self.SAMPLE_INSTITUTIONS if 1000 <= int(inst["enrollment"].replace(",", "")) <= 5000]
            elif enrollment_range == "5k_15k":
                candidates = [inst for inst in self.SAMPLE_INSTITUTIONS if 5000 <= int(inst["enrollment"].replace(",", "")) <= 15000]
            else:  # 15k_plus
                candidates = [inst for inst in self.SAMPLE_INSTITUTIONS if int(inst["enrollment"].replace(",", "")) > 15000]
        else:
            candidates = self.SAMPLE_INSTITUTIONS
            
        # Return first match or default to first institution
        return candidates[0] if candidates else self.SAMPLE_INSTITUTIONS[0]
    
    def generate_tutorial_data(self, user_goals: List[str], institution_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual tutorial data based on user goals and institution."""
        
        sample_inst = self.get_sample_institution()
        
        tutorial_data = {
            "institution_context": {
                "sample_name": sample_inst["name"],
                "similar_enrollment": sample_inst["enrollment"],
                "same_accreditor": sample_inst["accreditor"],
                "success_metrics": sample_inst["success_metrics"]
            },
            "guided_steps": self._generate_guided_steps(user_goals),
            "sample_documents": self._generate_sample_documents(user_goals, sample_inst),
            "expected_outcomes": self._generate_expected_outcomes(user_goals, sample_inst),
            "quick_wins": self._filter_quick_wins_by_goals(user_goals)
        }
        
        return tutorial_data
    
    def _generate_guided_steps(self, goals: List[str]) -> List[Dict[str, Any]]:
        """Generate step-by-step tutorial based on user goals."""
        
        steps = []
        
        if "Map standards quickly" in goals:
            steps.append({
                "id": "standards_mapping",
                "title": "Experience AI Standards Mapping",
                "description": "See how AI instantly maps your documents to accreditation standards",
                "estimated_time": "2 minutes",
                "demo_data": True,
                "actions": ["Upload sample strategic plan", "Watch AI analysis", "Review mappings"]
            })
        
        if "Automate evidence tagging" in goals:
            steps.append({
                "id": "evidence_tagging", 
                "title": "Automated Evidence Discovery",
                "description": "Experience intelligent evidence tagging across document types",
                "estimated_time": "3 minutes",
                "demo_data": True,
                "actions": ["Upload sample assessment report", "Review auto-tags", "Validate evidence links"]
            })
        
        if any(goal in ["Prep self-study", "Mid-cycle review", "Accreditation visit prep"] for goal in goals):
            steps.append({
                "id": "report_generation",
                "title": "Professional Report Generation",
                "description": "Generate executive-ready compliance reports with one click",
                "estimated_time": "1 minute",
                "demo_data": True,
                "actions": ["Select report type", "Generate sample report", "Download PDF"]
            })
        
        # Always include ROI demonstration
        steps.append({
            "id": "roi_demonstration",
            "title": "See Your ROI Impact", 
            "description": "Calculate time savings and cost benefits for your institution",
            "estimated_time": "1 minute",
            "demo_data": False,
            "actions": ["Review efficiency gains", "Calculate cost savings", "Compare to alternatives"]
        })
        
        return steps
    
    def _generate_sample_documents(self, goals: List[str], institution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate relevant sample documents based on goals."""
        
        all_docs = [
            {
                "name": "Strategic Plan 2023-2028",
                "type": "strategic_planning",
                "size": "2.4 MB",
                "relevance": ["Map standards quickly", "Track progress", "Data for board"],
                "mapped_standards": 23,
                "analysis_preview": "Identifies 23 accreditation standards across mission, governance, and planning categories"
            },
            {
                "name": "Student Learning Outcomes Assessment",
                "type": "assessment",
                "size": "1.8 MB", 
                "relevance": ["Close assessment loop", "Automate evidence tagging", "Gap analysis"],
                "mapped_standards": 15,
                "analysis_preview": "Strong evidence for assessment standards with minor gaps in continuous improvement"
            },
            {
                "name": "Faculty Qualifications Report",
                "type": "faculty",
                "size": "3.2 MB",
                "relevance": ["Prep self-study", "Accreditation visit prep", "Document organization"],
                "mapped_standards": 8,
                "analysis_preview": "Comprehensive faculty credentials documentation meets all qualification standards"
            }
        ]
        
        # Filter documents by user goals
        relevant_docs = [doc for doc in all_docs if any(goal in doc["relevance"] for goal in goals)]
        
        # If no matches, return first 2 documents
        if not relevant_docs:
            relevant_docs = all_docs[:2]
            
        return relevant_docs[:3]  # Limit to 3 documents
    
    def _generate_expected_outcomes(self, goals: List[str], institution: Dict[str, Any]) -> Dict[str, Any]:
        """Generate expected outcomes for user's specific goals."""
        
        outcomes = {
            "immediate_value": [],
            "30_day_goals": [],
            "roi_metrics": self.SAMPLE_ANALYSIS_RESULTS["roi_calculation"]
        }
        
        # Immediate value based on goals
        if "Map standards quickly" in goals:
            outcomes["immediate_value"].append("See 20+ standards mapped in under 3 minutes")
        if "Gap analysis" in goals:
            outcomes["immediate_value"].append("Identify 3-5 evidence gaps with specific recommendations")
        if "Automate evidence tagging" in goals:
            outcomes["immediate_value"].append("Experience 80% reduction in manual tagging time")
        
        # 30-day goals based on user intentions
        outcomes["30_day_goals"] = [
            f"Complete analysis of your initial {len(self._generate_sample_documents(goals, institution))} document types",
            "Build comprehensive evidence inventory with AI assistance", 
            "Generate first professional compliance report for leadership",
            "Establish baseline metrics for continuous improvement tracking"
        ]
        
        return outcomes
    
    def _filter_quick_wins_by_goals(self, goals: List[str]) -> List[Dict[str, Any]]:
        """Filter and customize quick wins based on user goals."""
        
        quick_wins = self.SAMPLE_ANALYSIS_RESULTS["quick_wins"].copy()
        
        # Customize messages based on goals
        for win in quick_wins:
            if win["type"] == "gap_identified" and "Gap analysis" in goals:
                win["priority"] = "high"
                win["description"] += " - directly addresses your gap analysis goals"
            elif win["type"] == "auto_mapping" and "Map standards quickly" in goals:
                win["description"] += " - demonstrating the rapid mapping you requested"
        
        return quick_wins
    
    def create_demo_account_data(self, user_email: str, institution_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive demo data for a trial account."""
        
        sample_inst = self.get_sample_institution()
        
        demo_data = {
            "account_id": str(uuid.uuid4()),
            "user_email": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "institution": {
                "name": institution_profile.get("institution_name", sample_inst["name"]),
                "type": sample_inst["type"],
                "enrollment": institution_profile.get("institution_size", sample_inst["enrollment"]),
                "accreditor": institution_profile.get("primary_accreditor", sample_inst["accreditor"]),
                "state": institution_profile.get("state", sample_inst["state"])
            },
            "demo_metrics": sample_inst["success_metrics"],
            "trial_status": {
                "days_remaining": 14,
                "trial_start": datetime.utcnow().isoformat(),
                "trial_end": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                "conversion_target": (datetime.utcnow() + timedelta(days=7)).isoformat()
            },
            "onboarding": {
                "completed_steps": [],
                "tutorial_progress": 0,
                "sample_data_loaded": True
            }
        }
        
        return demo_data
    
    def get_roi_calculator_data(self, institution_size: str = "5k_15k") -> Dict[str, Any]:
        """Get ROI calculator data customized for institution size."""
        
        base_roi = self.SAMPLE_ANALYSIS_RESULTS["roi_calculation"].copy()
        
        # Adjust metrics based on institution size
        size_multipliers = {
            "under_1000": 0.6,
            "1k_5k": 0.8, 
            "5k_15k": 1.0,
            "15k_plus": 1.4
        }
        
        multiplier = size_multipliers.get(institution_size, 1.0)
        
        base_roi["monthly_time_saved"] = int(base_roi["monthly_time_saved"] * multiplier)
        base_roi["monthly_value"] = int(base_roi["monthly_value"] * multiplier)
        base_roi["consultant_hours_avoided"] = int(base_roi["consultant_hours_avoided"] * multiplier)
        base_roi["consultant_savings"] = int(base_roi["consultant_savings"] * multiplier)
        base_roi["total_monthly_value"] = int(base_roi["total_monthly_value"] * multiplier)
        
        # Recalculate ROI
        base_roi["roi_multiplier"] = round(base_roi["total_monthly_value"] / base_roi["subscription_cost"], 1)
        
        return base_roi
    
    def generate_welcome_dashboard_data(self, user_goals: List[str], institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized welcome dashboard with sample data."""
        
        sample_inst = self.get_sample_institution(
            enrollment_range=institution_data.get("institution_size")
        )
        
        dashboard_data = {
            "personalization": {
                "institution_name": institution_data.get("institution_name", "Your Institution"),
                "primary_goals": user_goals[:3],  # Top 3 goals
                "accreditor": institution_data.get("primary_accreditor", "Your Accreditor")
            },
            "sample_metrics": sample_inst["success_metrics"],
            "quick_actions": self._generate_personalized_actions(user_goals),
            "getting_started_checklist": [
                {
                    "task": "Complete guided tutorial",
                    "completed": False,
                    "estimated_time": "5 minutes"
                },
                {
                    "task": "Upload first document",
                    "completed": False, 
                    "estimated_time": "2 minutes"
                },
                {
                    "task": "Review AI analysis results",
                    "completed": False,
                    "estimated_time": "3 minutes"
                },
                {
                    "task": "Generate sample report",
                    "completed": False,
                    "estimated_time": "1 minute"
                }
            ],
            "success_timeline": {
                "week_1": "Complete initial document analysis and evidence mapping",
                "week_2": "Generate first comprehensive compliance report",
                "month_1": "Establish full institutional baseline and improvement plan",
                "ongoing": "Continuous monitoring and automated compliance tracking"
            }
        }
        
        return dashboard_data
    
    def _generate_personalized_actions(self, goals: List[str]) -> List[Dict[str, Any]]:
        """Generate personalized quick actions based on user goals."""
        
        action_mapping = {
            "Map standards quickly": {
                "title": "🎯 Try AI Standards Mapping",
                "description": "Upload a document and watch AI map standards in real-time",
                "priority": 1
            },
            "Automate evidence tagging": {
                "title": "🏷️ Experience Smart Tagging",
                "description": "See how AI automatically tags evidence across documents",
                "priority": 2
            },
            "Prep self-study": {
                "title": "📋 Self-Study Preparation",
                "description": "Start building your comprehensive self-study documentation",
                "priority": 1
            },
            "Generate reports": {
                "title": "📊 Create Sample Report", 
                "description": "Generate a professional compliance report with demo data",
                "priority": 3
            }
        }
        
        actions = []
        for goal in goals[:4]:  # Top 4 goals
            if goal in action_mapping:
                actions.append(action_mapping[goal])
        
        # Sort by priority and return
        actions.sort(key=lambda x: x.get("priority", 99))
        return actions[:6]  # Limit to 6 actions