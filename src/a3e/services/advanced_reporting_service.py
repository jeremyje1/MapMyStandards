"""
Advanced Reporting Service
Provides comprehensive reporting capabilities for enterprise users
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import json
from io import BytesIO
import xlsxwriter

from src.a3e.database.models import (
    User, Team, Organization, Standard, Evidence, 
    StandardRequirement, ComplianceAssessment
)
from src.a3e.database.enterprise_models import (
    AuditLog, TeamMember, Department, ComplianceScore
)
from src.a3e.services.analytics_service import AnalyticsService
from src.a3e.core.config import get_settings

settings = get_settings()


class AdvancedReportingService:
    """Handles advanced reporting and analytics"""
    
    def __init__(self):
        self.analytics_service = AnalyticsService()
        
    async def generate_executive_report(
        self,
        db: AsyncSession,
        team_id: int,
        date_range: Tuple[datetime, datetime],
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive executive report"""
        start_date, end_date = date_range
        
        # Gather all report components
        report_data = await asyncio.gather(
            self._get_compliance_overview(db, team_id, date_range),
            self._get_department_performance(db, team_id, date_range),
            self._get_risk_analysis(db, team_id, date_range),
            self._get_evidence_statistics(db, team_id, date_range),
            self._get_user_activity(db, team_id, date_range),
            self._get_cost_savings(db, team_id, date_range)
        )
        
        compliance_overview, dept_performance, risk_analysis, evidence_stats, user_activity, cost_savings = report_data
        
        # Get predictions if requested
        predictions = {}
        if include_predictions:
            predictions = await self._get_compliance_predictions(db, team_id)
            
        return {
            'report_date': datetime.utcnow().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'executive_summary': await self._generate_executive_summary(
                compliance_overview,
                risk_analysis,
                cost_savings
            ),
            'compliance_overview': compliance_overview,
            'department_performance': dept_performance,
            'risk_analysis': risk_analysis,
            'evidence_statistics': evidence_stats,
            'user_activity': user_activity,
            'cost_savings': cost_savings,
            'predictions': predictions,
            'recommendations': await self._generate_recommendations(
                compliance_overview,
                risk_analysis,
                dept_performance
            )
        }
        
    async def generate_compliance_report(
        self,
        db: AsyncSession,
        team_id: int,
        standard_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Generate detailed compliance report"""
        # Build filters
        filters = [Team.id == team_id]
        if standard_ids:
            filters.append(Standard.id.in_(standard_ids))
        if department_ids:
            filters.append(Department.id.in_(department_ids))
            
        # Get compliance assessments
        assessments = await self._get_compliance_assessments(db, filters, date_range)
        
        # Calculate compliance metrics
        metrics = await self._calculate_compliance_metrics(assessments)
        
        # Get gap analysis
        gap_analysis = await self._perform_gap_analysis(db, team_id, standard_ids)
        
        # Get evidence coverage
        evidence_coverage = await self._analyze_evidence_coverage(
            db, team_id, standard_ids
        )
        
        return {
            'summary': {
                'overall_score': metrics['overall_score'],
                'standards_covered': metrics['standards_count'],
                'requirements_total': metrics['requirements_total'],
                'requirements_met': metrics['requirements_met'],
                'critical_gaps': metrics['critical_gaps']
            },
            'by_standard': metrics['by_standard'],
            'by_department': metrics['by_department'],
            'gap_analysis': gap_analysis,
            'evidence_coverage': evidence_coverage,
            'timeline': await self._build_compliance_timeline(assessments),
            'action_items': await self._generate_action_items(gap_analysis)
        }
        
    async def generate_risk_report(
        self,
        db: AsyncSession,
        team_id: int,
        risk_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment report"""
        # Get all risk factors
        risk_factors = await asyncio.gather(
            self._assess_compliance_risks(db, team_id),
            self._assess_evidence_risks(db, team_id),
            self._assess_operational_risks(db, team_id),
            self._assess_timeline_risks(db, team_id)
        )
        
        compliance_risks, evidence_risks, operational_risks, timeline_risks = risk_factors
        
        # Calculate overall risk score
        overall_risk = self._calculate_weighted_risk_score(risk_factors)
        
        # Identify high-risk areas
        high_risk_areas = await self._identify_high_risk_areas(
            db, team_id, risk_threshold
        )
        
        # Generate mitigation strategies
        mitigation_strategies = await self._generate_mitigation_strategies(
            high_risk_areas
        )
        
        return {
            'risk_score': overall_risk,
            'risk_level': self._get_risk_level(overall_risk),
            'risk_factors': {
                'compliance': compliance_risks,
                'evidence': evidence_risks,
                'operational': operational_risks,
                'timeline': timeline_risks
            },
            'high_risk_areas': high_risk_areas,
            'mitigation_strategies': mitigation_strategies,
            'risk_trends': await self._calculate_risk_trends(db, team_id),
            'recommendations': await self._generate_risk_recommendations(
                overall_risk,
                high_risk_areas
            )
        }
        
    async def generate_department_report(
        self,
        db: AsyncSession,
        team_id: int,
        department_id: int,
        include_benchmarks: bool = True
    ) -> Dict[str, Any]:
        """Generate detailed department-specific report"""
        # Get department details
        dept_result = await db.execute(
            select(Department).where(
                Department.id == department_id,
                Department.team_id == team_id
            )
        )
        department = dept_result.scalar_one_or_none()
        
        if not department:
            raise ValueError("Department not found")
            
        # Gather department metrics
        metrics = await asyncio.gather(
            self._get_department_compliance_score(db, department_id),
            self._get_department_evidence_stats(db, department_id),
            self._get_department_user_activity(db, department_id),
            self._get_department_timeline_adherence(db, department_id)
        )
        
        compliance_score, evidence_stats, user_activity, timeline_adherence = metrics
        
        # Get benchmarks if requested
        benchmarks = {}
        if include_benchmarks:
            benchmarks = await self._get_department_benchmarks(db, team_id, department_id)
            
        return {
            'department': {
                'id': department.id,
                'name': department.name,
                'manager': department.manager_name
            },
            'compliance_score': compliance_score,
            'evidence_statistics': evidence_stats,
            'user_activity': user_activity,
            'timeline_adherence': timeline_adherence,
            'benchmarks': benchmarks,
            'strengths': await self._identify_department_strengths(metrics),
            'improvement_areas': await self._identify_improvement_areas(metrics),
            'recommendations': await self._generate_department_recommendations(
                department,
                metrics
            )
        }
        
    async def generate_custom_report(
        self,
        db: AsyncSession,
        team_id: int,
        report_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate custom report based on configuration"""
        sections = report_config.get('sections', [])
        filters = report_config.get('filters', {})
        format_type = report_config.get('format', 'json')
        
        report_data = {}
        
        # Generate requested sections
        for section in sections:
            if section == 'compliance':
                report_data['compliance'] = await self.generate_compliance_report(
                    db, team_id,
                    filters.get('standard_ids'),
                    filters.get('department_ids'),
                    filters.get('date_range')
                )
            elif section == 'risk':
                report_data['risk'] = await self.generate_risk_report(
                    db, team_id,
                    filters.get('risk_threshold', 0.7)
                )
            elif section == 'evidence':
                report_data['evidence'] = await self._generate_evidence_report(
                    db, team_id, filters
                )
            elif section == 'users':
                report_data['users'] = await self._generate_user_report(
                    db, team_id, filters
                )
            elif section == 'timeline':
                report_data['timeline'] = await self._generate_timeline_report(
                    db, team_id, filters
                )
                
        # Apply custom calculations if specified
        if 'calculations' in report_config:
            report_data['custom_metrics'] = await self._apply_custom_calculations(
                report_data,
                report_config['calculations']
            )
            
        return report_data
        
    async def export_report(
        self,
        report_data: Dict[str, Any],
        format_type: str = 'xlsx',
        template: Optional[str] = None
    ) -> BytesIO:
        """Export report in specified format"""
        if format_type == 'xlsx':
            return await self._export_to_excel(report_data, template)
        elif format_type == 'pdf':
            return await self._export_to_pdf(report_data, template)
        elif format_type == 'csv':
            return await self._export_to_csv(report_data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
            
    async def schedule_report(
        self,
        db: AsyncSession,
        team_id: int,
        report_type: str,
        schedule: Dict[str, Any],
        recipients: List[str]
    ) -> Dict[str, Any]:
        """Schedule automated report generation"""
        # Create scheduled report configuration
        scheduled_report = {
            'team_id': team_id,
            'report_type': report_type,
            'schedule': schedule,
            'recipients': recipients,
            'created_at': datetime.utcnow(),
            'next_run': self._calculate_next_run(schedule),
            'is_active': True
        }
        
        # Store in database (would need a ScheduledReport model)
        # For now, return the configuration
        return scheduled_report
        
    async def _get_compliance_overview(
        self,
        db: AsyncSession,
        team_id: int,
        date_range: Tuple[datetime, datetime]
    ) -> Dict[str, Any]:
        """Get compliance overview statistics"""
        # Get overall compliance score
        score_result = await db.execute(
            select(func.avg(ComplianceScore.score)).where(
                ComplianceScore.team_id == team_id,
                ComplianceScore.calculated_at.between(*date_range)
            )
        )
        overall_score = score_result.scalar() or 0.0
        
        # Get compliance by standard
        standards_result = await db.execute(
            select(
                Standard.name,
                Standard.acronym,
                func.avg(ComplianceScore.score).label('avg_score'),
                func.count(ComplianceAssessment.id).label('assessments')
            ).join(
                ComplianceAssessment,
                Standard.id == ComplianceAssessment.standard_id
            ).join(
                ComplianceScore,
                ComplianceScore.assessment_id == ComplianceAssessment.id
            ).where(
                ComplianceAssessment.team_id == team_id,
                ComplianceScore.calculated_at.between(*date_range)
            ).group_by(Standard.id)
        )
        
        by_standard = [
            {
                'name': row.name,
                'acronym': row.acronym,
                'score': float(row.avg_score or 0),
                'assessments': row.assessments
            }
            for row in standards_result
        ]
        
        return {
            'overall_score': float(overall_score),
            'score_trend': await self._calculate_score_trend(db, team_id, date_range),
            'by_standard': by_standard,
            'total_standards': len(by_standard),
            'fully_compliant': len([s for s in by_standard if s['score'] >= 95]),
            'at_risk': len([s for s in by_standard if s['score'] < 70])
        }
        
    async def _export_to_excel(
        self,
        report_data: Dict[str, Any],
        template: Optional[str] = None
    ) -> BytesIO:
        """Export report data to Excel format"""
        output = BytesIO()
        
        with xlsxwriter.Workbook(output, {'in_memory': True}) as workbook:
            # Add summary worksheet
            summary_sheet = workbook.add_worksheet('Executive Summary')
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4B5563',
                'font_color': 'white',
                'border': 1
            })
            
            metric_format = workbook.add_format({
                'num_format': '0.00%',
                'border': 1
            })
            
            # Write summary data
            summary_sheet.write('A1', 'MapMyStandards Compliance Report', header_format)
            summary_sheet.write('A3', 'Report Date:', header_format)
            summary_sheet.write('B3', report_data.get('report_date', ''))
            
            # Add compliance metrics
            if 'compliance_overview' in report_data:
                compliance = report_data['compliance_overview']
                summary_sheet.write('A5', 'Overall Compliance Score', header_format)
                summary_sheet.write('B5', compliance.get('overall_score', 0) / 100, metric_format)
                
            # Add additional sheets for detailed data
            if 'by_standard' in report_data.get('compliance_overview', {}):
                standards_sheet = workbook.add_worksheet('Standards Detail')
                self._write_standards_detail(
                    standards_sheet,
                    report_data['compliance_overview']['by_standard'],
                    header_format
                )
                
        output.seek(0)
        return output
        
    def _calculate_weighted_risk_score(
        self,
        risk_factors: List[Dict[str, float]]
    ) -> float:
        """Calculate weighted overall risk score"""
        weights = {
            'compliance': 0.4,
            'evidence': 0.3,
            'operational': 0.2,
            'timeline': 0.1
        }
        
        total_score = 0.0
        for i, (factor_type, weight) in enumerate(weights.items()):
            if i < len(risk_factors) and 'score' in risk_factors[i]:
                total_score += risk_factors[i]['score'] * weight
                
        return round(total_score, 2)
        
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < 0.3:
            return 'Low'
        elif risk_score < 0.5:
            return 'Moderate'
        elif risk_score < 0.7:
            return 'High'
        else:
            return 'Critical'
            
    async def _generate_executive_summary(
        self,
        compliance_overview: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        cost_savings: Dict[str, Any]
    ) -> str:
        """Generate executive summary text"""
        overall_score = compliance_overview.get('overall_score', 0)
        risk_level = risk_analysis.get('level', 'Unknown')
        savings = cost_savings.get('total_saved', 0)
        
        summary = f"""
        Your organization maintains a {overall_score:.1f}% compliance score across 
        {compliance_overview.get('total_standards', 0)} standards. 
        
        Current risk level is assessed as {risk_level}, with 
        {risk_analysis.get('high_risk_count', 0)} areas requiring immediate attention.
        
        MapMyStandards has saved your organization ${savings:,.0f} through 
        automated evidence mapping and streamlined compliance processes.
        """
        
        return summary.strip()
        
    def _calculate_next_run(self, schedule: Dict[str, Any]) -> datetime:
        """Calculate next run time for scheduled report"""
        frequency = schedule.get('frequency', 'weekly')
        time_of_day = schedule.get('time', '09:00')
        
        now = datetime.utcnow()
        
        if frequency == 'daily':
            next_run = now + timedelta(days=1)
        elif frequency == 'weekly':
            days_ahead = schedule.get('day_of_week', 1) - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
        elif frequency == 'monthly':
            # First day of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_run = now.replace(month=now.month + 1, day=1)
        else:
            next_run = now + timedelta(days=7)  # Default to weekly
            
        # Set time
        hour, minute = map(int, time_of_day.split(':'))
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_run
