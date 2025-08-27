"""Email nurturing service for trial account conversion."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

from ..core.config import settings

logger = logging.getLogger(__name__)

class NurturingStage(Enum):
    """Email nurturing stages for trial users."""
    WELCOME = "welcome"
    VALUE_DEMO = "value_demo"
    FEATURE_INTRO = "feature_intro"
    SUCCESS_STORIES = "success_stories"
    ROI_FOCUS = "roi_focus"
    URGENCY_CONVERSION = "urgency_conversion"
    LAST_CHANCE = "last_chance"

class EmailNurturingService:
    """Service for managing automated email sequences for trial users."""
    
    def __init__(self):
        """Initialize the email nurturing service."""
        self.email_sequences = self._define_email_sequences()
    
    def _define_email_sequences(self) -> Dict[str, Dict[str, Any]]:
        """Define the complete email nurturing sequences."""
        
        return {
            NurturingStage.WELCOME.value: {
                "subject": "🎯 Welcome to MapMyStandards A³E - Your Accreditation Success Begins Now",
                "delay_hours": 1,  # Send 1 hour after signup
                "template": "welcome_sequence",
                "personalization": {
                    "requires_institution_name": True,
                    "requires_goals": True,
                    "requires_accreditor": True
                },
                "content_blocks": [
                    {
                        "type": "hero",
                        "title": "Welcome {institution_name}!",
                        "subtitle": "Your AI-powered accreditation platform is ready"
                    },
                    {
                        "type": "quick_start",
                        "steps": [
                            "Complete your guided tutorial (5 minutes)",
                            "Upload your first document for analysis",
                            "Review AI-generated standards mapping",
                            "Generate your first compliance report"
                        ]
                    },
                    {
                        "type": "cta",
                        "primary": "Start Your Tutorial",
                        "secondary": "Explore Quick Wins Dashboard"
                    }
                ],
                "success_metrics": [
                    "tutorial_completion",
                    "first_document_upload", 
                    "dashboard_visit"
                ]
            },
            
            NurturingStage.VALUE_DEMO.value: {
                "subject": "⚡ See How A³E Saves {institution_type}s 40+ Hours Monthly",
                "delay_hours": 24,  # Day 2
                "template": "value_demonstration",
                "personalization": {
                    "requires_institution_size": True,
                    "requires_institution_type": True
                },
                "content_blocks": [
                    {
                        "type": "social_proof",
                        "headline": "Institutions like yours are seeing incredible results",
                        "stats": [
                            "87% average compliance score improvement",
                            "16.8x return on investment",
                            "40+ hours saved monthly on accreditation work",
                            "94% of users see value within first week"
                        ]
                    },
                    {
                        "type": "feature_showcase",
                        "features": [
                            {
                                "icon": "🎯",
                                "title": "AI Standards Mapping",
                                "description": "Instantly map documents to {accreditor} standards",
                                "time_saved": "12 hours/month"
                            },
                            {
                                "icon": "📊", 
                                "title": "Automated Compliance Tracking",
                                "description": "Real-time compliance monitoring and gap analysis",
                                "time_saved": "15 hours/month"
                            },
                            {
                                "icon": "📈",
                                "title": "Professional Report Generation",
                                "description": "Executive-ready reports in minutes, not weeks",
                                "time_saved": "20 hours/month"
                            }
                        ]
                    },
                    {
                        "type": "cta",
                        "primary": "See Your ROI Calculation",
                        "secondary": "Watch Demo Video"
                    }
                ]
            },
            
            NurturingStage.FEATURE_INTRO.value: {
                "subject": "🚀 Hidden A³E Features That Will Transform Your {accreditor} Process",
                "delay_hours": 72,  # Day 4
                "template": "feature_deep_dive",
                "content_blocks": [
                    {
                        "type": "feature_spotlight",
                        "title": "Advanced Features You May Have Missed",
                        "features": [
                            {
                                "name": "Multi-Document Analysis",
                                "description": "Upload multiple documents and see cross-references automatically",
                                "use_case": "Perfect for comprehensive self-study preparation"
                            },
                            {
                                "name": "Evidence Gap Detection",
                                "description": "AI identifies missing evidence before accreditors do",
                                "use_case": "Eliminates last-minute scrambling for documentation"
                            },
                            {
                                "name": "Benchmark Intelligence",
                                "description": "Compare your compliance scores to peer institutions",
                                "use_case": "Understand your competitive position"
                            },
                            {
                                "name": "API Integration Hub",
                                "description": "Connect with your LMS, SIS, and document management systems",
                                "use_case": "Seamless workflow automation"
                            }
                        ]
                    },
                    {
                        "type": "tutorial_progress",
                        "conditional": "if not tutorial_completed",
                        "message": "Complete your tutorial to unlock these advanced features"
                    }
                ]
            },
            
            NurturingStage.SUCCESS_STORIES.value: {
                "subject": "📊 How Riverside Community College Achieved 94% Compliance Score",
                "delay_hours": 120,  # Day 6
                "template": "success_case_study",
                "content_blocks": [
                    {
                        "type": "case_study",
                        "institution": "Riverside Community College",
                        "challenge": "Struggling with ACCJC self-study preparation and evidence organization",
                        "solution": "Implemented MapMyStandards A³E for comprehensive accreditation management",
                        "results": [
                            "94% compliance score (vs 73% industry average)",
                            "Saved 60 hours monthly on accreditation work",
                            "Completed self-study 3 weeks ahead of schedule",
                            "Identified and addressed 12 evidence gaps proactively"
                        ],
                        "quote": "A³E transformed our accreditation process from chaotic to confident. We caught issues months before our site visit and presented the most organized self-study in our history.",
                        "author": "Dr. Sarah Martinez, VP of Institutional Effectiveness"
                    },
                    {
                        "type": "similar_institutions",
                        "title": "Other {institution_type}s Seeing Success",
                        "examples": [
                            "Metropolitan State University: 16.8x ROI, $5,000 monthly value",
                            "Heritage Liberal Arts College: 89% compliance, 40% efficiency gain",
                            "Community colleges across CA: Average 87% compliance scores"
                        ]
                    }
                ]
            },
            
            NurturingStage.ROI_FOCUS.value: {
                "subject": "💰 Your Institution Could Save ${monthly_savings}/Month (ROI Calculator Inside)",
                "delay_hours": 168,  # Day 8  
                "template": "roi_focused",
                "personalization": {
                    "requires_roi_calculation": True
                },
                "content_blocks": [
                    {
                        "type": "personalized_roi",
                        "title": "Your Potential ROI with MapMyStandards A³E",
                        "metrics": [
                            "Monthly time savings: {time_saved} hours",
                            "Monthly cost savings: ${monthly_savings}",
                            "Annual value created: ${annual_value}",
                            "ROI multiplier: {roi_multiplier}x"
                        ],
                        "comparison": "vs ${subscription_cost}/month subscription cost"
                    },
                    {
                        "type": "cost_breakdown",
                        "traditional_method": {
                            "staff_time": "{staff_hours}h × ${hourly_rate} = ${staff_cost}",
                            "consultant_fees": "{consultant_hours}h × $200 = ${consultant_cost}",
                            "total": "${traditional_total}/month"
                        },
                        "a3e_method": {
                            "subscription": "${subscription_cost}",
                            "reduced_staff_time": "{reduced_hours}h × ${hourly_rate} = ${reduced_cost}",
                            "total": "${a3e_total}/month"
                        },
                        "savings": "${total_savings}/month"
                    },
                    {
                        "type": "urgency",
                        "message": "Trial ends in {trial_days_remaining} days",
                        "cta": "Lock in your savings now"
                    }
                ]
            },
            
            NurturingStage.URGENCY_CONVERSION.value: {
                "subject": "⏰ Only {trial_days_remaining} Days Left - Don't Lose Your A³E Progress",
                "delay_hours": 240,  # Day 11
                "template": "urgency_conversion",
                "conditional": "trial_days_remaining <= 5",
                "content_blocks": [
                    {
                        "type": "progress_summary",
                        "title": "Your A³E Journey So Far",
                        "achievements": [
                            "Documents analyzed: {documents_count}",
                            "Standards mapped: {standards_count}",
                            "Reports generated: {reports_count}",
                            "Time saved: {estimated_time_saved} hours"
                        ]
                    },
                    {
                        "type": "risk_of_loss",
                        "headline": "What happens if you don't subscribe?",
                        "consequences": [
                            "Lose all your AI-analyzed document mappings",
                            "Return to manual, time-intensive processes", 
                            "Miss evidence gaps that A³E identified",
                            "Lose institutional knowledge and progress tracking"
                        ]
                    },
                    {
                        "type": "limited_offer",
                        "offer": "Subscribe now and keep all your progress + get 1 month free",
                        "urgency": "Offer expires with your trial in {trial_days_remaining} days"
                    }
                ]
            },
            
            NurturingStage.LAST_CHANCE.value: {
                "subject": "🚨 Final Notice: Your A³E Trial Expires Tomorrow - Keep Your Progress",
                "delay_hours": 312,  # Day 14 (last day)
                "template": "last_chance",
                "conditional": "trial_days_remaining <= 1",
                "content_blocks": [
                    {
                        "type": "final_appeal",
                        "title": "Don't let your accreditation progress disappear",
                        "message": "You've built valuable institutional intelligence with A³E. Subscribing takes 30 seconds and preserves everything you've accomplished."
                    },
                    {
                        "type": "one_click_subscribe",
                        "button": "Keep My Progress - Subscribe Now",
                        "guarantee": "30-day money-back guarantee"
                    },
                    {
                        "type": "support_offer",
                        "message": "Questions? Reply to this email or call our success team directly",
                        "phone": "1-800-A3E-HELP",
                        "hours": "Available until midnight tonight"
                    }
                ]
            }
        }
    
    def get_nurturing_schedule(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized nurturing schedule for a user."""
        
        signup_date = user_data.get('signup_date', datetime.utcnow())
        if isinstance(signup_date, str):
            signup_date = datetime.fromisoformat(signup_date.replace('Z', '+00:00'))
        
        schedule = []
        
        for stage, email_config in self.email_sequences.items():
            # Check if email should be sent based on conditions
            if self._should_send_email(stage, email_config, user_data):
                send_time = signup_date + timedelta(hours=email_config['delay_hours'])
                
                schedule.append({
                    'stage': stage,
                    'send_time': send_time,
                    'email_config': email_config,
                    'personalized_content': self._personalize_content(email_config, user_data)
                })
        
        # Sort by send time
        schedule.sort(key=lambda x: x['send_time'])
        return schedule
    
    def _should_send_email(self, stage: str, config: Dict[str, Any], user_data: Dict[str, Any]) -> bool:
        """Determine if an email should be sent based on conditions."""
        
        # Check conditional logic
        if 'conditional' in config:
            condition = config['conditional']
            
            if condition == "trial_days_remaining <= 5":
                trial_days = self._calculate_trial_days_remaining(user_data)
                return trial_days <= 5
            elif condition == "trial_days_remaining <= 1":
                trial_days = self._calculate_trial_days_remaining(user_data)
                return trial_days <= 1
            elif condition == "if not tutorial_completed":
                return not user_data.get('tutorial_completed', False)
        
        # Check user activity to avoid over-emailing engaged users
        if stage == NurturingStage.URGENCY_CONVERSION.value:
            # Don't send urgency emails to highly engaged users
            if user_data.get('documents_analyzed', 0) > 5:
                return False
        
        return True
    
    def _calculate_trial_days_remaining(self, user_data: Dict[str, Any]) -> int:
        """Calculate days remaining in trial."""
        
        signup_date = user_data.get('signup_date', datetime.utcnow())
        if isinstance(signup_date, str):
            signup_date = datetime.fromisoformat(signup_date.replace('Z', '+00:00'))
        
        trial_end = signup_date + timedelta(days=14)
        days_remaining = (trial_end - datetime.utcnow()).days
        return max(0, days_remaining)
    
    def _personalize_content(self, email_config: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize email content based on user data."""
        
        personalized = email_config.copy()
        
        # Personalize subject line
        subject = personalized['subject']
        subject = subject.replace('{institution_name}', user_data.get('institution_name', 'Your Institution'))
        subject = subject.replace('{institution_type}', self._get_institution_type_display(user_data))
        subject = subject.replace('{accreditor}', user_data.get('primary_accreditor', 'your accreditor'))
        subject = subject.replace('{trial_days_remaining}', str(self._calculate_trial_days_remaining(user_data)))
        
        # Add ROI calculations if needed
        if email_config.get('personalization', {}).get('requires_roi_calculation'):
            roi_data = self._calculate_user_roi(user_data)
            subject = subject.replace('{monthly_savings}', str(roi_data['monthly_savings']))
            
            # Add ROI data to content
            personalized['roi_data'] = roi_data
        
        personalized['subject'] = subject
        
        # Personalize content blocks
        if 'content_blocks' in personalized:
            for block in personalized['content_blocks']:
                self._personalize_content_block(block, user_data)
        
        return personalized
    
    def _get_institution_type_display(self, user_data: Dict[str, Any]) -> str:
        """Get display-friendly institution type."""
        
        enrollment = user_data.get('institution_size', '5k_15k')
        type_map = {
            'under_1000': 'Small Colleges',
            '1k_5k': 'Mid-Size Institutions', 
            '5k_15k': 'Large Universities',
            '15k_plus': 'Major Universities'
        }
        return type_map.get(enrollment, 'Institutions')
    
    def _calculate_user_roi(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate personalized ROI based on user characteristics."""
        
        # Use sample data service for ROI calculation
        from .sample_data_service import SampleDataService
        sample_service = SampleDataService()
        
        institution_size = user_data.get('institution_size', '5k_15k')
        return sample_service.get_roi_calculator_data(institution_size)
    
    def _personalize_content_block(self, block: Dict[str, Any], user_data: Dict[str, Any]):
        """Personalize individual content blocks."""
        
        # This would contain logic to replace placeholders in content blocks
        # with user-specific data like institution name, goals, progress, etc.
        
        if block['type'] == 'hero' and 'title' in block:
            block['title'] = block['title'].replace(
                '{institution_name}', 
                user_data.get('institution_name', 'Your Institution')
            )
        
        # Add more personalization logic as needed
        pass
    
    def generate_email_html(self, email_data: Dict[str, Any]) -> str:
        """Generate HTML email content from email data."""
        
        # This would integrate with your email template system
        # For now, return a basic HTML structure
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{email_data['subject']}</title>
            <style>
                body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .cta-button {{ 
                    display: inline-block; 
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 8px;
                    font-weight: 600;
                }}
                .stats {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MapMyStandards A³E</h1>
                </div>
                <!-- Email content would be generated here based on content_blocks -->
                <p>This is a personalized email based on your onboarding preferences.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def track_email_engagement(self, user_email: str, email_stage: str, action: str):
        """Track email engagement for optimization."""
        
        engagement_data = {
            'user_email': user_email,
            'email_stage': email_stage,
            'action': action,  # opened, clicked, converted, unsubscribed
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Email engagement tracked: {engagement_data}")
        
        # This would integrate with your analytics system
        # Store engagement data for optimization and reporting
        
        return engagement_data
    
    def get_sequence_performance(self, date_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Get performance metrics for email sequences."""
        
        # This would query your analytics system for email performance data
        
        sample_performance = {
            'total_emails_sent': 1247,
            'overall_open_rate': 0.68,
            'overall_click_rate': 0.24,
            'conversion_rate': 0.12,
            'stage_performance': {
                NurturingStage.WELCOME.value: {
                    'open_rate': 0.78,
                    'click_rate': 0.34,
                    'conversion_rate': 0.08
                },
                NurturingStage.VALUE_DEMO.value: {
                    'open_rate': 0.71,
                    'click_rate': 0.28,
                    'conversion_rate': 0.11
                },
                NurturingStage.ROI_FOCUS.value: {
                    'open_rate': 0.65,
                    'click_rate': 0.31,
                    'conversion_rate': 0.18
                },
                NurturingStage.URGENCY_CONVERSION.value: {
                    'open_rate': 0.58,
                    'click_rate': 0.22,
                    'conversion_rate': 0.15
                }
            }
        }
        
        return sample_performance