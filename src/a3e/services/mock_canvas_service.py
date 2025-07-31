"""
Mock Canvas LMS Service for A³E Development and Testing
Provides realistic Canvas data without requiring API access
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)
# settings imported from config module

class MockCanvasLMSService:
    """Mock Canvas LMS service with realistic data for testing."""
    
    def __init__(self):
        self.access_token = "mock_canvas_token_12345"
        self.api_base = "https://canvas.instructure.com/api/v1"
        self.base_url = "https://canvas.instructure.com"
        self.authenticated = False
        
        # Mock user data
        self.current_user = {
            "id": 12345,
            "name": "Dr. Jane Smith",
            "email": "jane.smith@university.edu",
            "login_id": "jsmith",
            "avatar_url": "https://canvas.instructure.com/images/messages/avatar-50.png"
        }
    
    async def authenticate(self) -> bool:
        """Mock authentication - always succeeds."""
        self.authenticated = True
        logger.info("Mock Canvas authentication successful")
        return True
    
    async def test_connection(self) -> bool:
        """Mock connection test."""
        return self.authenticated
    
    async def get_courses(self, enrollment_type: str = 'teacher') -> List[Dict[str, Any]]:
        """Get mock courses with realistic accreditation-relevant data."""
        mock_courses = [
            {
                "id": 101,
                "name": "Business Ethics and Corporate Responsibility",
                "course_code": "MGMT 485",
                "account_id": 1,
                "start_at": "2024-08-26T00:00:00Z",
                "end_at": "2024-12-15T00:00:00Z",
                "workflow_state": "available",
                "enrollment_term_id": 1,
                "total_students": 28,
                "course_image": "business_ethics.jpg",
                "syllabus_body": "<p>This course examines ethical frameworks and corporate social responsibility in modern business practices.</p>",
                "public_description": "Advanced course in business ethics with focus on real-world case studies."
            },
            {
                "id": 102,
                "name": "Principles of Accounting I",
                "course_code": "ACCT 201",
                "account_id": 1,
                "start_at": "2024-08-26T00:00:00Z",
                "end_at": "2024-12-15T00:00:00Z",
                "workflow_state": "available",
                "enrollment_term_id": 1,
                "total_students": 35,
                "course_image": "accounting.jpg",
                "syllabus_body": "<p>Introduction to fundamental accounting principles and financial statement preparation.</p>",
                "public_description": "Foundation course covering basic accounting concepts and procedures."
            },
            {
                "id": 103,
                "name": "Strategic Management Capstone",
                "course_code": "MGMT 495",
                "account_id": 1,
                "start_at": "2024-08-26T00:00:00Z",
                "end_at": "2024-12-15T00:00:00Z",
                "workflow_state": "available",
                "enrollment_term_id": 1,
                "total_students": 22,
                "course_image": "strategy.jpg",
                "syllabus_body": "<p>Capstone course integrating all business disciplines through strategic analysis and planning.</p>",
                "public_description": "Senior-level capstone course requiring comprehensive business strategy project."
            }
        ]
        
        return mock_courses
    
    async def get_course_outcomes(self, course_id: int) -> List[Dict[str, Any]]:
        """Get mock learning outcomes for courses."""
        outcomes_by_course = {
            101: [  # Business Ethics
                {
                    "id": 201,
                    "title": "Ethical Decision Making",
                    "description": "Students will analyze complex business scenarios using multiple ethical frameworks",
                    "display_name": "Ethics Analysis",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 101
                },
                {
                    "id": 202,
                    "title": "Corporate Social Responsibility",
                    "description": "Students will evaluate corporate CSR initiatives and their stakeholder impacts",
                    "display_name": "CSR Evaluation",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 101
                }
            ],
            102: [  # Accounting
                {
                    "id": 301,
                    "title": "Financial Statement Preparation",
                    "description": "Students will prepare accurate financial statements following GAAP principles",
                    "display_name": "Financial Statements",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 102
                },
                {
                    "id": 302,
                    "title": "Transaction Analysis",
                    "description": "Students will analyze business transactions and their impact on accounting equation",
                    "display_name": "Transaction Analysis",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 102
                }
            ],
            103: [  # Strategic Management
                {
                    "id": 401,
                    "title": "Strategic Analysis",
                    "description": "Students will conduct comprehensive industry and competitive analysis",
                    "display_name": "Industry Analysis",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 103
                },
                {
                    "id": 402,
                    "title": "Strategy Implementation",
                    "description": "Students will develop detailed implementation plans for strategic initiatives",
                    "display_name": "Strategy Implementation",
                    "calculation_method": "highest",
                    "mastery_points": 3,
                    "points_possible": 4,
                    "context_type": "Course",
                    "context_id": 103
                }
            ]
        }
        
        return outcomes_by_course.get(course_id, [])
    
    async def get_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Get mock assignments for courses."""
        assignments_by_course = {
            101: [  # Business Ethics
                {
                    "id": 501,
                    "name": "Stakeholder Analysis Case Study",
                    "description": "Analyze a complex business ethics case involving multiple stakeholders",
                    "due_at": "2024-10-15T23:59:00Z",
                    "points_possible": 100,
                    "course_id": 101,
                    "assignment_group_id": 1,
                    "submission_types": ["online_text_entry", "online_upload"],
                    "rubric": {
                        "criteria": [
                            {"description": "Identifies all relevant stakeholders", "points": 25},
                            {"description": "Applies appropriate ethical frameworks", "points": 25},
                            {"description": "Provides clear recommendations", "points": 25},
                            {"description": "Professional writing and presentation", "points": 25}
                        ]
                    }
                }
            ],
            102: [  # Accounting
                {
                    "id": 502,
                    "name": "Financial Statement Analysis Project",
                    "description": "Prepare complete financial statements for a small business",
                    "due_at": "2024-11-01T23:59:00Z",
                    "points_possible": 150,
                    "course_id": 102,
                    "assignment_group_id": 2,
                    "submission_types": ["online_upload"],
                    "rubric": {
                        "criteria": [
                            {"description": "Accurate balance sheet preparation", "points": 50},
                            {"description": "Correct income statement", "points": 50},
                            {"description": "Proper cash flow statement", "points": 50}
                        ]
                    }
                }
            ],
            103: [  # Strategic Management
                {
                    "id": 503,
                    "name": "Comprehensive Strategy Plan",
                    "description": "Develop a complete strategic plan for assigned company",
                    "due_at": "2024-12-10T23:59:00Z",
                    "points_possible": 200,
                    "course_id": 103,
                    "assignment_group_id": 3,
                    "submission_types": ["online_upload"],
                    "rubric": {
                        "criteria": [
                            {"description": "Thorough environmental analysis", "points": 50},
                            {"description": "Clear strategic objectives", "points": 50},
                            {"description": "Detailed implementation plan", "points": 50},
                            {"description": "Financial projections and metrics", "points": 50}
                        ]
                    }
                }
            ]
        }
        
        return assignments_by_course.get(course_id, [])
    
    async def get_student_data(self, course_id: int) -> List[Dict[str, Any]]:
        """Get mock student enrollment and performance data."""
        return [
            {
                "user_id": 1001,
                "user": {"name": "Alex Johnson", "email": "alex.j@student.edu"},
                "course_id": course_id,
                "type": "StudentEnrollment",
                "enrollment_state": "active",
                "grades": {"current_score": 87.5, "final_score": 87.5}
            },
            {
                "user_id": 1002,
                "user": {"name": "Maria Garcia", "email": "maria.g@student.edu"},
                "course_id": course_id,
                "type": "StudentEnrollment",
                "enrollment_state": "active",
                "grades": {"current_score": 92.1, "final_score": 92.1}
            },
            {
                "user_id": 1003,
                "user": {"name": "David Chen", "email": "david.c@student.edu"},
                "course_id": course_id,
                "type": "StudentEnrollment",
                "enrollment_state": "active",
                "grades": {"current_score": 85.8, "final_score": 85.8}
            }
        ]
    
    async def get_outcome_results(self, course_id: int) -> List[Dict[str, Any]]:
        """Get mock outcome assessment results for accreditation reporting."""
        return [
            {
                "outcome_id": 201,
                "user_id": 1001,
                "score": 3.2,
                "mastery": True,
                "assessed_at": "2024-10-15T14:30:00Z"
            },
            {
                "outcome_id": 201,
                "user_id": 1002,
                "score": 3.8,
                "mastery": True,
                "assessed_at": "2024-10-15T14:30:00Z"
            },
            {
                "outcome_id": 202,
                "user_id": 1001,
                "score": 2.9,
                "mastery": False,
                "assessed_at": "2024-11-01T16:45:00Z"
            }
        ]

# Mock Canvas integration for the integration manager
class MockIntegrationManager:
    """Mock integration manager with Canvas data."""
    
    def __init__(self):
        self.canvas = MockCanvasLMSService()
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test mock connections."""
        return {
            'canvas': True,
            'banner': False,  # Not mocked
            'sharepoint': False  # Not mocked
        }
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """Sync mock Canvas data."""
        sync_results = {
            'canvas': {'courses': [], 'outcomes': [], 'assignments': []},
            'banner': {'students': [], 'courses': []},
            'sharepoint': {'sites': [], 'documents': []},
            'errors': []
        }
        
        try:
            if await self.canvas.authenticate():
                # Get courses
                courses = await self.canvas.get_courses()
                sync_results['canvas']['courses'] = courses
                
                # Get outcomes and assignments for each course
                for course in courses:
                    course_id = course['id']
                    outcomes = await self.canvas.get_course_outcomes(course_id)
                    assignments = await self.canvas.get_assignments(course_id)
                    
                    sync_results['canvas']['outcomes'].extend(outcomes)
                    sync_results['canvas']['assignments'].extend(assignments)
        
        except Exception as e:
            sync_results['errors'].append(str(e))
            logger.error(f"Mock sync error: {e}")
        
        return sync_results

# Global mock instance
mock_integration_manager = MockIntegrationManager()
