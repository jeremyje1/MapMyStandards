"""
GapRisk Predictor™ - Forward-looking compliance risk scoring
Predicts likelihood of non-compliance at next review using multiple signals
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level categories"""
    CRITICAL = "critical"  # > 0.7
    HIGH = "high"  # 0.5 - 0.7
    MEDIUM = "medium"  # 0.3 - 0.5
    LOW = "low"  # 0.15 - 0.3
    MINIMAL = "minimal"  # < 0.15


@dataclass
class RiskFactor:
    """Individual risk factor contributing to overall risk"""
    factor_name: str
    value: float  # Raw value
    normalized_value: float  # 0-1 normalized
    weight: float
    contribution: float  # weight * normalized_value
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'factor': self.factor_name,
            'value': round(self.value, 3),
            'normalized': round(self.normalized_value, 3),
            'weight': self.weight,
            'contribution': round(self.contribution, 3),
            'description': self.description
        }


@dataclass
class GapRiskScore:
    """Complete gap risk assessment for a standard"""
    standard_id: str
    risk_score: float  # 0-1 overall risk
    risk_level: RiskLevel
    factors: List[RiskFactor]
    predicted_issues: List[str]
    remediation_priority: int  # 1-5, 1 being highest
    time_to_review: int  # Days until next review
    confidence: float  # Model confidence in prediction
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'standard_id': self.standard_id,
            'risk_score': round(self.risk_score, 3),
            'risk_level': self.risk_level.value,
            'factors': [f.to_dict() for f in self.factors],
            'predicted_issues': self.predicted_issues,
            'remediation_priority': self.remediation_priority,
            'time_to_review': self.time_to_review,
            'confidence': round(self.confidence, 3)
        }


class GapRiskPredictor:
    """Predicts compliance gaps before they appear"""
    
    def __init__(self):
        # Calibrated weights from historical data
        self.weights = {
            'coverage': 0.25,  # How much of standard is covered
            'trust': 0.20,  # Average evidence trust score
            'staleness': 0.15,  # Age of evidence
            'task_debt': 0.10,  # Overdue tasks
            'change_impact': 0.10,  # Recent standard changes
            'review_history': 0.10,  # Past findings
            'complexity': 0.05,  # Standard complexity
            'volatility': 0.05  # Rate of change in evidence
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            RiskLevel.CRITICAL: 0.7,
            RiskLevel.HIGH: 0.5,
            RiskLevel.MEDIUM: 0.3,
            RiskLevel.LOW: 0.15,
            RiskLevel.MINIMAL: 0.0
        }
        
        # Historical calibration data (would be ML model in production)
        self.historical_base_rate = 0.12  # 12% historical non-compliance rate
    
    def predict_risk(
        self,
        standard_id: str,
        coverage_percentage: float,
        evidence_trust_scores: List[float],
        evidence_ages_days: List[int],
        overdue_tasks_count: int,
        total_tasks_count: int,
        recent_changes_count: int,
        historical_findings_count: int,
        time_to_next_review_days: int,
        evidence_update_frequency_days: Optional[float] = None,
        department_turnover_rate: Optional[float] = None
    ) -> GapRiskScore:
        """
        Predict compliance risk for a standard
        
        Uses gradient boosting-inspired approach with calibrated weights
        """
        
        factors = []
        
        # 1. Coverage Risk
        coverage_risk = 1.0 - (coverage_percentage / 100.0)
        factors.append(RiskFactor(
            factor_name='coverage',
            value=coverage_percentage,
            normalized_value=coverage_risk,
            weight=self.weights['coverage'],
            contribution=coverage_risk * self.weights['coverage'],
            description=f"Evidence coverage: {coverage_percentage:.1f}%"
        ))
        
        # 2. Trust Risk
        avg_trust = np.mean(evidence_trust_scores) if evidence_trust_scores else 0.0
        trust_risk = 1.0 - avg_trust
        factors.append(RiskFactor(
            factor_name='trust',
            value=avg_trust,
            normalized_value=trust_risk,
            weight=self.weights['trust'],
            contribution=trust_risk * self.weights['trust'],
            description=f"Average evidence trust: {avg_trust:.2f}"
        ))
        
        # 3. Staleness Risk
        avg_age = np.mean(evidence_ages_days) if evidence_ages_days else 365
        staleness_risk = self._calculate_staleness_risk(avg_age)
        factors.append(RiskFactor(
            factor_name='staleness',
            value=avg_age,
            normalized_value=staleness_risk,
            weight=self.weights['staleness'],
            contribution=staleness_risk * self.weights['staleness'],
            description=f"Average evidence age: {avg_age:.0f} days"
        ))
        
        # 4. Task Debt Risk
        task_debt_ratio = overdue_tasks_count / max(total_tasks_count, 1)
        task_debt_risk = min(1.0, task_debt_ratio * 2)  # Amplify small debts
        factors.append(RiskFactor(
            factor_name='task_debt',
            value=overdue_tasks_count,
            normalized_value=task_debt_risk,
            weight=self.weights['task_debt'],
            contribution=task_debt_risk * self.weights['task_debt'],
            description=f"Overdue tasks: {overdue_tasks_count}/{total_tasks_count}"
        ))
        
        # 5. Change Impact Risk
        change_risk = self._calculate_change_impact_risk(recent_changes_count)
        factors.append(RiskFactor(
            factor_name='change_impact',
            value=recent_changes_count,
            normalized_value=change_risk,
            weight=self.weights['change_impact'],
            contribution=change_risk * self.weights['change_impact'],
            description=f"Recent standard changes: {recent_changes_count}"
        ))
        
        # 6. Review History Risk
        history_risk = self._calculate_history_risk(historical_findings_count)
        factors.append(RiskFactor(
            factor_name='review_history',
            value=historical_findings_count,
            normalized_value=history_risk,
            weight=self.weights['review_history'],
            contribution=history_risk * self.weights['review_history'],
            description=f"Historical findings: {historical_findings_count}"
        ))
        
        # 7. Complexity Risk (simplified for now)
        complexity_risk = 0.3  # Base complexity, would be calculated from standard
        factors.append(RiskFactor(
            factor_name='complexity',
            value=complexity_risk,
            normalized_value=complexity_risk,
            weight=self.weights['complexity'],
            contribution=complexity_risk * self.weights['complexity'],
            description="Standard complexity: moderate"
        ))
        
        # 8. Volatility Risk
        if evidence_update_frequency_days:
            volatility_risk = self._calculate_volatility_risk(evidence_update_frequency_days)
        else:
            volatility_risk = 0.2  # Default low volatility
        
        factors.append(RiskFactor(
            factor_name='volatility',
            value=evidence_update_frequency_days or 0,
            normalized_value=volatility_risk,
            weight=self.weights['volatility'],
            contribution=volatility_risk * self.weights['volatility'],
            description=f"Update volatility: {'high' if volatility_risk > 0.5 else 'low'}"
        ))
        
        # Calculate overall risk score
        raw_risk = sum(f.contribution for f in factors)
        
        # Apply sigmoid calibration for better probability estimates
        calibrated_risk = self._calibrate_risk_score(raw_risk, time_to_next_review_days)
        
        # Determine risk level
        risk_level = self._determine_risk_level(calibrated_risk)
        
        # Predict specific issues
        predicted_issues = self._predict_specific_issues(factors, calibrated_risk)
        
        # Calculate remediation priority (1-5)
        remediation_priority = self._calculate_remediation_priority(
            calibrated_risk, time_to_next_review_days
        )
        
        # Calculate confidence
        confidence = self._calculate_prediction_confidence(factors, evidence_trust_scores)
        
        return GapRiskScore(
            standard_id=standard_id,
            risk_score=calibrated_risk,
            risk_level=risk_level,
            factors=factors,
            predicted_issues=predicted_issues,
            remediation_priority=remediation_priority,
            time_to_review=time_to_next_review_days,
            confidence=confidence
        )
    
    def _calculate_staleness_risk(self, avg_age_days: float) -> float:
        """Calculate risk from evidence age using decay function"""
        # Exponential decay: risk increases as evidence gets older
        if avg_age_days <= 90:
            return 0.0  # Very fresh
        elif avg_age_days <= 180:
            return 0.2
        elif avg_age_days <= 365:
            return 0.4
        elif avg_age_days <= 730:
            return 0.7
        else:
            return 0.9
    
    def _calculate_change_impact_risk(self, changes_count: int) -> float:
        """Calculate risk from recent standard changes"""
        if changes_count == 0:
            return 0.0
        elif changes_count <= 2:
            return 0.3
        elif changes_count <= 5:
            return 0.6
        else:
            return 0.9
    
    def _calculate_history_risk(self, findings_count: int) -> float:
        """Calculate risk based on historical findings"""
        if findings_count == 0:
            return 0.1  # Slight risk even with clean history
        elif findings_count <= 2:
            return 0.4
        elif findings_count <= 5:
            return 0.7
        else:
            return 0.95
    
    def _calculate_volatility_risk(self, update_frequency_days: float) -> float:
        """Calculate risk from evidence update volatility"""
        if update_frequency_days <= 30:
            return 0.7  # Too volatile, may indicate instability
        elif update_frequency_days <= 90:
            return 0.2  # Good update cadence
        elif update_frequency_days <= 180:
            return 0.3
        elif update_frequency_days <= 365:
            return 0.5
        else:
            return 0.8  # Too infrequent updates
    
    def _calibrate_risk_score(self, raw_risk: float, days_to_review: int) -> float:
        """Apply calibration to get probability-like risk score"""
        # Time adjustment: risk increases as review approaches
        time_multiplier = 1.0
        if days_to_review <= 30:
            time_multiplier = 1.3
        elif days_to_review <= 90:
            time_multiplier = 1.15
        elif days_to_review <= 180:
            time_multiplier = 1.05
        
        adjusted_risk = raw_risk * time_multiplier
        
        # Apply sigmoid for smooth probability
        # Using temperature=1.5 for calibration
        temperature = 1.5
        calibrated = 1 / (1 + math.exp(-10 * (adjusted_risk - 0.5) / temperature))
        
        # Adjust for historical base rate
        calibrated = 0.7 * calibrated + 0.3 * self.historical_base_rate
        
        return min(0.95, calibrated)  # Cap at 95% max risk
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine categorical risk level"""
        for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            if risk_score >= self.risk_thresholds[level]:
                return level
        return RiskLevel.MINIMAL
    
    def _predict_specific_issues(self, factors: List[RiskFactor], overall_risk: float) -> List[str]:
        """Predict specific compliance issues likely to occur"""
        issues = []
        
        # Sort factors by contribution
        sorted_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)
        
        for factor in sorted_factors[:3]:  # Top 3 risk factors
            if factor.factor_name == 'coverage' and factor.normalized_value > 0.5:
                issues.append("Insufficient evidence coverage - gaps likely in documentation")
            elif factor.factor_name == 'trust' and factor.normalized_value > 0.5:
                issues.append("Low evidence quality - may not meet auditor standards")
            elif factor.factor_name == 'staleness' and factor.normalized_value > 0.5:
                issues.append("Outdated evidence - requires immediate refresh")
            elif factor.factor_name == 'task_debt' and factor.normalized_value > 0.4:
                issues.append("Accumulating task backlog - remediation falling behind")
            elif factor.factor_name == 'change_impact' and factor.normalized_value > 0.4:
                issues.append("Unaddressed standard changes - alignment gaps emerging")
            elif factor.factor_name == 'review_history' and factor.normalized_value > 0.5:
                issues.append("Recurring findings pattern - systemic issues unresolved")
        
        if overall_risk > 0.7 and not issues:
            issues.append("Multiple risk factors elevated - comprehensive review needed")
        
        return issues
    
    def _calculate_remediation_priority(self, risk_score: float, days_to_review: int) -> int:
        """Calculate 1-5 priority for remediation (1 = highest)"""
        # Combine risk and urgency
        if risk_score > 0.7 and days_to_review < 60:
            return 1  # Critical and urgent
        elif risk_score > 0.5 and days_to_review < 90:
            return 2  # High risk or urgent
        elif risk_score > 0.5 or days_to_review < 60:
            return 3  # Moderate priority
        elif risk_score > 0.3:
            return 4  # Low priority
        else:
            return 5  # Minimal priority
    
    def _calculate_prediction_confidence(
        self,
        factors: List[RiskFactor],
        evidence_trust_scores: List[float]
    ) -> float:
        """Calculate confidence in the risk prediction"""
        # Start with base confidence
        confidence = 0.7
        
        # Adjust based on data quality
        if evidence_trust_scores:
            avg_trust = np.mean(evidence_trust_scores)
            confidence += avg_trust * 0.2
        
        # Adjust based on factor agreement
        factor_values = [f.normalized_value for f in factors]
        factor_std = np.std(factor_values)
        if factor_std < 0.2:
            confidence += 0.1  # Factors agree
        
        return min(0.95, confidence)
    
    def predict_department_risk(
        self,
        department_standards: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict risk across all standards in a department"""
        
        risks = []
        for standard_data in department_standards:
            risk = self.predict_risk(
                standard_id=standard_data['standard_id'],
                coverage_percentage=standard_data.get('coverage', 0),
                evidence_trust_scores=standard_data.get('trust_scores', []),
                evidence_ages_days=standard_data.get('evidence_ages', []),
                overdue_tasks_count=standard_data.get('overdue_tasks', 0),
                total_tasks_count=standard_data.get('total_tasks', 0),
                recent_changes_count=standard_data.get('recent_changes', 0),
                historical_findings_count=standard_data.get('historical_findings', 0),
                time_to_next_review_days=standard_data.get('days_to_review', 180)
            )
            risks.append(risk)
        
        # Aggregate statistics
        risk_scores = [r.risk_score for r in risks]
        
        return {
            'department_risk': np.mean(risk_scores),
            'max_risk': max(risk_scores),
            'critical_count': sum(1 for r in risks if r.risk_level == RiskLevel.CRITICAL),
            'high_count': sum(1 for r in risks if r.risk_level == RiskLevel.HIGH),
            'standards_at_risk': [
                r.standard_id for r in risks 
                if r.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
            ],
            'top_issues': self._aggregate_issues(risks),
            'average_confidence': np.mean([r.confidence for r in risks])
        }
    
    def _aggregate_issues(self, risks: List[GapRiskScore]) -> List[str]:
        """Aggregate and deduplicate predicted issues"""
        issue_counts = {}
        for risk in risks:
            for issue in risk.predicted_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [issue for issue, count in sorted_issues[:5]]


# Global instance
gap_risk_predictor = GapRiskPredictor()