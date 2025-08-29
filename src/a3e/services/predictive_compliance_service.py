"""
Predictive Compliance Intelligence Service

Uses machine learning and historical data to predict compliance risks,
forecast review outcomes, and recommend proactive interventions.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class PredictiveComplianceService:
    """
    Predictive analytics for accreditation compliance
    """
    
    def __init__(self):
        self.risk_thresholds = self._initialize_risk_thresholds()
        self.prediction_models = self._initialize_prediction_models()
    
    def _initialize_risk_thresholds(self) -> Dict[str, float]:
        """Initialize risk assessment thresholds"""
        return {
            "critical": 0.8,  # >80% risk score
            "high": 0.6,      # 60-80% risk score
            "medium": 0.4,    # 40-60% risk score
            "low": 0.2        # <20% risk score
        }
    
    def _initialize_prediction_models(self) -> Dict[str, Any]:
        """Initialize prediction model configurations"""
        return {
            "compliance_trend": {
                "window_size": 90,  # days
                "min_data_points": 5,
                "confidence_threshold": 0.7
            },
            "risk_factors": {
                "document_age_weight": 0.25,
                "gap_severity_weight": 0.35,
                "evidence_quality_weight": 0.25,
                "change_frequency_weight": 0.15
            },
            "outcome_prediction": {
                "historical_weight": 0.4,
                "current_state_weight": 0.6
            }
        }
    
    async def predict_compliance_trajectory(
        self,
        institution_id: str,
        historical_data: List[Dict[str, Any]],
        current_metrics: Dict[str, Any],
        time_horizon: int = 180  # days
    ) -> Dict[str, Any]:
        """
        Predict future compliance trajectory based on historical trends
        """
        try:
            # Analyze historical trends
            trend_analysis = self._analyze_trends(historical_data)
            
            # Calculate current momentum
            momentum = self._calculate_momentum(historical_data, current_metrics)
            
            # Generate predictions
            predictions = []
            base_score = current_metrics.get("compliance_score", 0.0)
            
            for days_ahead in [30, 60, 90, 180]:
                if days_ahead > time_horizon:
                    break
                
                # Apply trend and momentum to predict future score
                predicted_score = self._project_score(
                    base_score,
                    trend_analysis["trend_direction"],
                    trend_analysis["trend_strength"],
                    momentum,
                    days_ahead
                )
                
                predictions.append({
                    "days_ahead": days_ahead,
                    "predicted_score": round(predicted_score, 1),
                    "confidence": self._calculate_confidence(
                        len(historical_data),
                        days_ahead,
                        trend_analysis["volatility"]
                    ),
                    "risk_level": self._categorize_risk(100 - predicted_score)
                })
            
            # Identify inflection points
            inflection_points = self._identify_inflection_points(
                historical_data,
                current_metrics
            )
            
            # Generate recommendations
            recommendations = self._generate_trajectory_recommendations(
                trend_analysis,
                momentum,
                predictions
            )
            
            return {
                "current_score": base_score,
                "trend_direction": trend_analysis["trend_direction"],
                "trend_strength": trend_analysis["trend_strength"],
                "momentum": momentum,
                "predictions": predictions,
                "inflection_points": inflection_points,
                "recommendations": recommendations,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting compliance trajectory: {e}")
            return self._get_fallback_trajectory(current_metrics)
    
    async def identify_compliance_risks(
        self,
        institution_data: Dict[str, Any],
        document_metrics: Dict[str, Any],
        gap_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify and prioritize compliance risks using predictive analytics
        """
        try:
            risks = []
            
            # Document freshness risk
            doc_risk = self._assess_document_freshness_risk(document_metrics)
            if doc_risk["risk_score"] > 0.3:
                risks.append(doc_risk)
            
            # Gap severity risk
            gap_risk = self._assess_gap_severity_risk(gap_analysis)
            if gap_risk["risk_score"] > 0.3:
                risks.append(gap_risk)
            
            # Evidence quality risk
            quality_risk = self._assess_evidence_quality_risk(document_metrics)
            if quality_risk["risk_score"] > 0.3:
                risks.append(quality_risk)
            
            # Regulatory change risk
            regulatory_risk = self._assess_regulatory_change_risk(institution_data)
            if regulatory_risk["risk_score"] > 0.2:
                risks.append(regulatory_risk)
            
            # Time-based risks (upcoming deadlines)
            deadline_risks = self._assess_deadline_risks(institution_data)
            risks.extend(deadline_risks)
            
            # Sort by risk score
            risks.sort(key=lambda x: x["risk_score"], reverse=True)
            
            # Calculate overall risk profile
            overall_risk = self._calculate_overall_risk(risks)
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_mitigation_strategies(risks[:5])
            
            return {
                "overall_risk_score": overall_risk["score"],
                "overall_risk_level": overall_risk["level"],
                "identified_risks": risks[:10],  # Top 10 risks
                "risk_categories": self._categorize_risks(risks),
                "mitigation_strategies": mitigation_strategies,
                "next_review_date": self._calculate_next_review_date(overall_risk),
                "analysis_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error identifying compliance risks: {e}")
            return self._get_fallback_risk_assessment()
    
    async def predict_review_outcome(
        self,
        institution_id: str,
        compliance_metrics: Dict[str, Any],
        preparation_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict likely outcome of accreditation review
        """
        try:
            # Calculate component scores
            compliance_score = compliance_metrics.get("overall_score", 0) / 100
            preparation_score = self._calculate_preparation_score(preparation_status)
            evidence_score = self._calculate_evidence_score(compliance_metrics)
            gap_penalty = self._calculate_gap_penalty(compliance_metrics)
            
            # Weighted prediction
            weights = self.prediction_models["outcome_prediction"]
            base_prediction = (
                compliance_score * 0.4 +
                preparation_score * 0.3 +
                evidence_score * 0.2 +
                (1 - gap_penalty) * 0.1
            )
            
            # Apply confidence adjustments
            confidence = self._calculate_outcome_confidence(
                compliance_metrics,
                preparation_status
            )
            
            # Determine likely outcome
            if base_prediction >= 0.85:
                outcome = "Full Compliance - No Recommendations"
                outcome_probability = min(base_prediction, 0.95)
            elif base_prediction >= 0.70:
                outcome = "Compliance with Recommendations"
                outcome_probability = base_prediction
            elif base_prediction >= 0.55:
                outcome = "Conditional Compliance - Monitoring Required"
                outcome_probability = base_prediction
            else:
                outcome = "Non-Compliance Risk - Immediate Action Required"
                outcome_probability = 1 - base_prediction
            
            # Identify critical factors
            critical_factors = self._identify_critical_factors(
                compliance_metrics,
                preparation_status
            )
            
            # Generate improvement priorities
            improvement_priorities = self._generate_improvement_priorities(
                compliance_metrics,
                base_prediction
            )
            
            return {
                "predicted_outcome": outcome,
                "outcome_probability": round(outcome_probability * 100, 1),
                "confidence_level": confidence,
                "component_scores": {
                    "compliance": round(compliance_score * 100, 1),
                    "preparation": round(preparation_score * 100, 1),
                    "evidence_quality": round(evidence_score * 100, 1),
                    "gap_impact": round(gap_penalty * 100, 1)
                },
                "critical_factors": critical_factors,
                "improvement_priorities": improvement_priorities,
                "days_to_optimize": self._calculate_optimization_time(base_prediction),
                "prediction_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting review outcome: {e}")
            return self._get_fallback_outcome_prediction()
    
    async def generate_proactive_alerts(
        self,
        institution_id: str,
        current_state: Dict[str, Any],
        thresholds: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate proactive alerts for potential compliance issues
        """
        alerts = []
        
        # Use custom or default thresholds
        if not thresholds:
            thresholds = {
                "document_age_days": 365,
                "compliance_score_min": 70,
                "gap_count_max": 5,
                "evidence_quality_min": 0.6
            }
        
        # Check document freshness
        if current_state.get("avg_document_age_days", 0) > thresholds["document_age_days"]:
            alerts.append({
                "type": "document_freshness",
                "severity": "high",
                "message": "Critical documents are outdated and need refresh",
                "action_required": "Update documents older than 1 year",
                "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "affected_standards": self._get_affected_standards_by_age(current_state)
            })
        
        # Check compliance score trends
        if current_state.get("compliance_score", 100) < thresholds["compliance_score_min"]:
            score_drop = 100 - current_state.get("compliance_score", 100)
            alerts.append({
                "type": "compliance_score",
                "severity": "critical" if score_drop > 30 else "high",
                "message": f"Compliance score below threshold: {current_state.get('compliance_score', 0)}%",
                "action_required": "Immediate review and remediation needed",
                "deadline": (datetime.utcnow() + timedelta(days=14)).isoformat(),
                "affected_standards": current_state.get("low_scoring_standards", [])
            })
        
        # Check gap accumulation
        gap_count = current_state.get("total_gaps", 0)
        if gap_count > thresholds["gap_count_max"]:
            alerts.append({
                "type": "gap_accumulation",
                "severity": "medium",
                "message": f"{gap_count} compliance gaps identified",
                "action_required": "Develop gap remediation plan",
                "deadline": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "affected_standards": current_state.get("standards_with_gaps", [])
            })
        
        # Check evidence quality
        if current_state.get("avg_evidence_quality", 1.0) < thresholds["evidence_quality_min"]:
            alerts.append({
                "type": "evidence_quality",
                "severity": "medium",
                "message": "Evidence quality below acceptable threshold",
                "action_required": "Strengthen evidence documentation",
                "deadline": (datetime.utcnow() + timedelta(days=60)).isoformat(),
                "affected_standards": current_state.get("weak_evidence_standards", [])
            })
        
        # Predictive alerts based on trends
        if current_state.get("trend_direction") == "declining":
            alerts.append({
                "type": "negative_trend",
                "severity": "high",
                "message": "Compliance metrics showing declining trend",
                "action_required": "Implement corrective measures",
                "deadline": (datetime.utcnow() + timedelta(days=21)).isoformat(),
                "trend_data": current_state.get("trend_details", {})
            })
        
        # Sort alerts by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        return alerts
    
    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical compliance trends"""
        if len(historical_data) < 2:
            return {
                "trend_direction": "stable",
                "trend_strength": 0.0,
                "volatility": 0.0
            }
        
        # Extract scores and timestamps
        scores = [d.get("compliance_score", 0) for d in historical_data]
        
        # Calculate trend direction and strength
        if len(scores) >= 2:
            recent_avg = np.mean(scores[-3:]) if len(scores) >= 3 else scores[-1]
            older_avg = np.mean(scores[:-3]) if len(scores) > 3 else scores[0]
            
            change = recent_avg - older_avg
            trend_direction = "improving" if change > 5 else "declining" if change < -5 else "stable"
            trend_strength = min(abs(change) / 50, 1.0)  # Normalize to 0-1
        else:
            trend_direction = "stable"
            trend_strength = 0.0
        
        # Calculate volatility
        if len(scores) > 1:
            volatility = np.std(scores) / 100  # Normalize
        else:
            volatility = 0.0
        
        return {
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "volatility": min(volatility, 1.0)
        }
    
    def _calculate_momentum(
        self,
        historical_data: List[Dict[str, Any]],
        current_metrics: Dict[str, Any]
    ) -> float:
        """Calculate compliance momentum"""
        if len(historical_data) < 2:
            return 0.0
        
        # Recent change rate
        recent_scores = [d.get("compliance_score", 0) for d in historical_data[-5:]]
        if len(recent_scores) >= 2:
            recent_change = (recent_scores[-1] - recent_scores[0]) / max(len(recent_scores) - 1, 1)
        else:
            recent_change = 0.0
        
        # Current velocity
        current_score = current_metrics.get("compliance_score", 0)
        last_score = historical_data[-1].get("compliance_score", 0)
        current_velocity = current_score - last_score
        
        # Combined momentum (-1 to 1)
        momentum = (recent_change * 0.7 + current_velocity * 0.3) / 100
        return max(-1, min(1, momentum))
    
    def _project_score(
        self,
        base_score: float,
        trend_direction: str,
        trend_strength: float,
        momentum: float,
        days_ahead: int
    ) -> float:
        """Project future compliance score"""
        # Base trajectory
        if trend_direction == "improving":
            daily_change = 0.1 * trend_strength
        elif trend_direction == "declining":
            daily_change = -0.1 * trend_strength
        else:
            daily_change = 0.0
        
        # Apply momentum
        daily_change += momentum * 0.05
        
        # Calculate projection with dampening over time
        dampening_factor = 1 / (1 + days_ahead / 180)  # Reduce confidence over time
        projected_change = daily_change * days_ahead * dampening_factor
        
        # Apply bounds
        projected_score = base_score + projected_change
        return max(0, min(100, projected_score))
    
    def _calculate_confidence(
        self,
        data_points: int,
        days_ahead: int,
        volatility: float
    ) -> str:
        """Calculate prediction confidence"""
        # Base confidence from data availability
        if data_points >= 10:
            base_confidence = 0.9
        elif data_points >= 5:
            base_confidence = 0.7
        else:
            base_confidence = 0.5
        
        # Reduce confidence over time
        time_factor = 1 / (1 + days_ahead / 90)
        
        # Reduce confidence with volatility
        volatility_factor = 1 - (volatility * 0.5)
        
        final_confidence = base_confidence * time_factor * volatility_factor
        
        if final_confidence >= 0.7:
            return "high"
        elif final_confidence >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _categorize_risk(self, risk_score: float) -> str:
        """Categorize risk level"""
        risk_score = risk_score / 100  # Normalize to 0-1
        
        for level, threshold in self.risk_thresholds.items():
            if level == "critical" and risk_score >= threshold:
                return "critical"
            elif level == "high" and threshold <= risk_score < self.risk_thresholds["critical"]:
                return "high"
            elif level == "medium" and threshold <= risk_score < self.risk_thresholds["high"]:
                return "medium"
            elif level == "low" and risk_score < threshold:
                return "low"
        
        return "medium"
    
    def _identify_inflection_points(
        self,
        historical_data: List[Dict[str, Any]],
        current_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify trend inflection points"""
        inflection_points = []
        
        if len(historical_data) < 3:
            return inflection_points
        
        scores = [d.get("compliance_score", 0) for d in historical_data]
        
        for i in range(1, len(scores) - 1):
            # Check for local maxima or minima
            if scores[i] > scores[i-1] and scores[i] > scores[i+1]:
                inflection_points.append({
                    "type": "peak",
                    "index": i,
                    "score": scores[i],
                    "date": historical_data[i].get("date", "")
                })
            elif scores[i] < scores[i-1] and scores[i] < scores[i+1]:
                inflection_points.append({
                    "type": "trough",
                    "index": i,
                    "score": scores[i],
                    "date": historical_data[i].get("date", "")
                })
        
        return inflection_points[-3:]  # Return last 3 inflection points
    
    def _generate_trajectory_recommendations(
        self,
        trend_analysis: Dict[str, Any],
        momentum: float,
        predictions: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on trajectory"""
        recommendations = []
        
        if trend_analysis["trend_direction"] == "declining":
            recommendations.append("Immediate intervention required to reverse declining trend")
            recommendations.append("Conduct comprehensive gap analysis within 14 days")
        
        if momentum < -0.3:
            recommendations.append("Accelerating decline detected - escalate to leadership")
        
        if predictions and predictions[-1]["predicted_score"] < 70:
            recommendations.append("Projected non-compliance risk - develop remediation plan")
        
        if trend_analysis["volatility"] > 0.3:
            recommendations.append("High volatility detected - stabilize compliance processes")
        
        if not recommendations:
            recommendations.append("Maintain current compliance practices")
        
        return recommendations[:5]
    
    def _assess_document_freshness_risk(self, document_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk from outdated documents"""
        avg_age_days = document_metrics.get("avg_document_age_days", 0)
        
        if avg_age_days > 730:  # >2 years
            risk_score = 0.9
            severity = "critical"
        elif avg_age_days > 365:  # >1 year
            risk_score = 0.7
            severity = "high"
        elif avg_age_days > 180:  # >6 months
            risk_score = 0.4
            severity = "medium"
        else:
            risk_score = 0.1
            severity = "low"
        
        return {
            "risk_type": "document_freshness",
            "risk_score": risk_score,
            "severity": severity,
            "description": f"Documents average {avg_age_days} days old",
            "impact": "Outdated evidence may not reflect current practices",
            "mitigation": "Update all documents older than 1 year"
        }
    
    def _assess_gap_severity_risk(self, gap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk from compliance gaps"""
        critical_gaps = gap_analysis.get("critical_gaps", 0)
        major_gaps = gap_analysis.get("major_gaps", 0)
        minor_gaps = gap_analysis.get("minor_gaps", 0)
        
        risk_score = (critical_gaps * 0.5 + major_gaps * 0.3 + minor_gaps * 0.1) / 10
        risk_score = min(risk_score, 1.0)
        
        if critical_gaps > 0:
            severity = "critical"
        elif major_gaps > 2:
            severity = "high"
        elif major_gaps > 0:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "risk_type": "compliance_gaps",
            "risk_score": risk_score,
            "severity": severity,
            "description": f"{critical_gaps} critical, {major_gaps} major, {minor_gaps} minor gaps",
            "impact": "Gaps directly impact accreditation outcome",
            "mitigation": "Prioritize critical gap remediation"
        }
    
    def _assess_evidence_quality_risk(self, document_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk from poor evidence quality"""
        avg_quality = document_metrics.get("avg_confidence_score", 100) / 100
        weak_evidence_count = document_metrics.get("weak_evidence_count", 0)
        
        risk_score = (1 - avg_quality) * 0.6 + (weak_evidence_count / 20) * 0.4
        risk_score = min(risk_score, 1.0)
        
        if avg_quality < 0.5:
            severity = "high"
        elif avg_quality < 0.7:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "risk_type": "evidence_quality",
            "risk_score": risk_score,
            "severity": severity,
            "description": f"Average evidence quality: {avg_quality * 100:.1f}%",
            "impact": "Weak evidence undermines compliance claims",
            "mitigation": "Strengthen documentation with specific examples"
        }
    
    def _assess_regulatory_change_risk(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk from regulatory changes"""
        last_standard_update = institution_data.get("last_standard_update_days_ago", 0)
        pending_changes = institution_data.get("pending_regulatory_changes", 0)
        
        if pending_changes > 0:
            risk_score = min(0.3 + (pending_changes * 0.2), 1.0)
        else:
            risk_score = min(last_standard_update / 365, 0.5)
        
        severity = "high" if pending_changes > 2 else "medium" if pending_changes > 0 else "low"
        
        return {
            "risk_type": "regulatory_change",
            "risk_score": risk_score,
            "severity": severity,
            "description": f"{pending_changes} pending regulatory changes",
            "impact": "New requirements may create compliance gaps",
            "mitigation": "Review and prepare for upcoming standard changes"
        }
    
    def _assess_deadline_risks(self, institution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess risks from upcoming deadlines"""
        risks = []
        
        # Check next review date
        days_to_review = institution_data.get("days_to_next_review", 365)
        if days_to_review < 90:
            risk_score = 1 - (days_to_review / 90)
            risks.append({
                "risk_type": "upcoming_review",
                "risk_score": risk_score,
                "severity": "critical" if days_to_review < 30 else "high",
                "description": f"Accreditation review in {days_to_review} days",
                "impact": "Insufficient time for major corrections",
                "mitigation": "Focus on critical compliance items only"
            })
        
        # Check report deadlines
        days_to_report = institution_data.get("days_to_next_report", 180)
        if days_to_report < 60:
            risk_score = 1 - (days_to_report / 60)
            risks.append({
                "risk_type": "report_deadline",
                "risk_score": risk_score * 0.7,
                "severity": "high" if days_to_report < 30 else "medium",
                "description": f"Report due in {days_to_report} days",
                "impact": "May affect review preparation",
                "mitigation": "Allocate resources for timely report completion"
            })
        
        return risks
    
    def _calculate_overall_risk(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall risk profile"""
        if not risks:
            return {"score": 0.0, "level": "low"}
        
        # Weighted average with emphasis on critical risks
        total_weight = 0
        weighted_sum = 0
        
        for risk in risks:
            weight = {"critical": 3, "high": 2, "medium": 1, "low": 0.5}.get(risk.get("severity", "medium"), 1)
            weighted_sum += risk.get("risk_score", 0) * weight
            total_weight += weight
        
        overall_score = weighted_sum / max(total_weight, 1)
        
        return {
            "score": round(overall_score, 2),
            "level": self._categorize_risk(overall_score * 100)
        }
    
    def _categorize_risks(self, risks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize risks by type"""
        categories = defaultdict(list)
        
        for risk in risks:
            risk_type = risk.get("risk_type", "other")
            categories[risk_type].append(risk.get("description", ""))
        
        return dict(categories)
    
    def _generate_mitigation_strategies(self, top_risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mitigation strategies for top risks"""
        strategies = []
        
        for risk in top_risks:
            strategy = {
                "risk_addressed": risk.get("risk_type"),
                "strategy": risk.get("mitigation", "Develop risk mitigation plan"),
                "priority": risk.get("severity", "medium"),
                "timeline": self._get_mitigation_timeline(risk.get("severity")),
                "resources_required": self._estimate_resources(risk.get("risk_type"))
            }
            strategies.append(strategy)
        
        return strategies
    
    def _get_mitigation_timeline(self, severity: str) -> str:
        """Get recommended mitigation timeline"""
        timelines = {
            "critical": "Immediate - within 7 days",
            "high": "Urgent - within 14 days",
            "medium": "Soon - within 30 days",
            "low": "Planned - within 60 days"
        }
        return timelines.get(severity, "Within 30 days")
    
    def _estimate_resources(self, risk_type: str) -> str:
        """Estimate resources needed for mitigation"""
        resources = {
            "document_freshness": "Document review team, 20-40 hours",
            "compliance_gaps": "Compliance team, 40-80 hours",
            "evidence_quality": "Subject matter experts, 30-50 hours",
            "regulatory_change": "Legal/compliance review, 10-20 hours",
            "upcoming_review": "Full team mobilization, 100+ hours",
            "report_deadline": "Report writers, 20-30 hours"
        }
        return resources.get(risk_type, "Assessment required")
    
    def _calculate_next_review_date(self, overall_risk: Dict[str, Any]) -> str:
        """Calculate recommended next review date"""
        risk_level = overall_risk.get("level", "medium")
        
        days_until_review = {
            "critical": 7,
            "high": 14,
            "medium": 30,
            "low": 60
        }.get(risk_level, 30)
        
        next_date = datetime.utcnow() + timedelta(days=days_until_review)
        return next_date.isoformat()
    
    def _calculate_preparation_score(self, preparation_status: Dict[str, Any]) -> float:
        """Calculate preparation readiness score"""
        documents_ready = preparation_status.get("documents_ready_pct", 0) / 100
        narratives_complete = preparation_status.get("narratives_complete_pct", 0) / 100
        gaps_addressed = preparation_status.get("gaps_addressed_pct", 0) / 100
        team_trained = preparation_status.get("team_readiness", 0) / 100
        
        return (documents_ready * 0.3 + narratives_complete * 0.3 + 
                gaps_addressed * 0.25 + team_trained * 0.15)
    
    def _calculate_evidence_score(self, compliance_metrics: Dict[str, Any]) -> float:
        """Calculate evidence quality score"""
        avg_confidence = compliance_metrics.get("avg_evidence_confidence", 0) / 100
        coverage = compliance_metrics.get("standards_with_evidence_pct", 0) / 100
        strength = compliance_metrics.get("avg_evidence_strength", 0) / 100
        
        return (avg_confidence * 0.4 + coverage * 0.4 + strength * 0.2)
    
    def _calculate_gap_penalty(self, compliance_metrics: Dict[str, Any]) -> float:
        """Calculate penalty from gaps"""
        critical_gaps = compliance_metrics.get("critical_gaps", 0)
        major_gaps = compliance_metrics.get("major_gaps", 0)
        
        penalty = (critical_gaps * 0.15 + major_gaps * 0.05)
        return min(penalty, 0.5)  # Cap at 50% penalty
    
    def _calculate_outcome_confidence(
        self,
        compliance_metrics: Dict[str, Any],
        preparation_status: Dict[str, Any]
    ) -> str:
        """Calculate confidence in outcome prediction"""
        data_completeness = preparation_status.get("data_completeness", 0) / 100
        time_to_review = preparation_status.get("days_to_review", 365)
        
        if data_completeness > 0.8 and time_to_review > 90:
            return "high"
        elif data_completeness > 0.6 and time_to_review > 30:
            return "medium"
        else:
            return "low"
    
    def _identify_critical_factors(
        self,
        compliance_metrics: Dict[str, Any],
        preparation_status: Dict[str, Any]
    ) -> List[str]:
        """Identify critical success factors"""
        factors = []
        
        if compliance_metrics.get("critical_gaps", 0) > 0:
            factors.append("Address critical compliance gaps immediately")
        
        if preparation_status.get("documents_ready_pct", 0) < 70:
            factors.append("Complete document preparation")
        
        if compliance_metrics.get("avg_evidence_confidence", 0) < 60:
            factors.append("Strengthen evidence quality")
        
        if preparation_status.get("days_to_review", 365) < 60:
            factors.append("Time constraint - focus on essentials")
        
        return factors[:5]
    
    def _generate_improvement_priorities(
        self,
        compliance_metrics: Dict[str, Any],
        prediction_score: float
    ) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations"""
        priorities = []
        
        if prediction_score < 0.7:
            priorities.append({
                "priority": 1,
                "action": "Emergency compliance review",
                "impact": "high",
                "effort": "high",
                "timeline": "7 days"
            })
        
        if compliance_metrics.get("critical_gaps", 0) > 0:
            priorities.append({
                "priority": 2,
                "action": "Close critical gaps",
                "impact": "high",
                "effort": "medium",
                "timeline": "14 days"
            })
        
        if compliance_metrics.get("avg_evidence_confidence", 0) < 70:
            priorities.append({
                "priority": 3,
                "action": "Enhance evidence documentation",
                "impact": "medium",
                "effort": "medium",
                "timeline": "30 days"
            })
        
        return priorities[:5]
    
    def _calculate_optimization_time(self, current_score: float) -> int:
        """Calculate days needed to optimize compliance"""
        gap_to_optimal = max(0, 0.85 - current_score)
        
        # Estimate days based on gap size
        if gap_to_optimal > 0.3:
            return 90
        elif gap_to_optimal > 0.15:
            return 60
        elif gap_to_optimal > 0.05:
            return 30
        else:
            return 14
    
    def _get_affected_standards_by_age(self, current_state: Dict[str, Any]) -> List[str]:
        """Get standards affected by document age"""
        return current_state.get("standards_with_old_docs", [
            "CR 1 - Institutional Mission",
            "CR 4 - Institutional Effectiveness",
            "CR 7 - Institutional Planning"
        ])
    
    def _get_fallback_trajectory(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback trajectory when prediction fails"""
        return {
            "current_score": current_metrics.get("compliance_score", 0),
            "trend_direction": "stable",
            "trend_strength": 0.0,
            "momentum": 0.0,
            "predictions": [],
            "inflection_points": [],
            "recommendations": ["Unable to generate predictions - insufficient data"],
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _get_fallback_risk_assessment(self) -> Dict[str, Any]:
        """Fallback risk assessment"""
        return {
            "overall_risk_score": 0.5,
            "overall_risk_level": "medium",
            "identified_risks": [],
            "risk_categories": {},
            "mitigation_strategies": ["Conduct comprehensive risk assessment"],
            "next_review_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _get_fallback_outcome_prediction(self) -> Dict[str, Any]:
        """Fallback outcome prediction"""
        return {
            "predicted_outcome": "Unable to predict - insufficient data",
            "outcome_probability": 0.0,
            "confidence_level": "low",
            "component_scores": {},
            "critical_factors": ["Gather more data for accurate prediction"],
            "improvement_priorities": [],
            "days_to_optimize": 60,
            "prediction_date": datetime.utcnow().isoformat()
        }


# Singleton instance
_predictive_service = None


def get_predictive_service() -> PredictiveComplianceService:
    """Get or create predictive service instance"""
    global _predictive_service
    if _predictive_service is None:
        _predictive_service = PredictiveComplianceService()
    return _predictive_service