"""
GapRisk Predictor™ - AI-Enhanced Risk Prediction
Forward-looking risk scoring with 8-factor model and AI insights
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from .llm_service import LLMService
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIGapRiskPredictor:
    """Predict compliance gaps with AI-enhanced analysis"""
    
    # Risk factors with weights
    RISK_FACTORS = {
        "evidence_age": 0.20,        # How old is the evidence
        "evidence_coverage": 0.15,   # How well does evidence cover the standard
        "evidence_quality": 0.15,    # Quality/trust score of evidence
        "update_frequency": 0.10,    # How often is this updated
        "related_gaps": 0.10,        # Gaps in related standards
        "historical_issues": 0.10,   # Past compliance issues
        "upcoming_changes": 0.10,    # Known upcoming standard changes
        "institutional_risk": 0.10   # Institution-specific risk factors
    }
    
    def __init__(self):
        self.llm_service = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize LLM service"""
        if not self._initialized:
            settings = get_settings()
            self.llm_service = LLMService(settings)
            await self.llm_service.initialize()
            self._initialized = True
    
    async def predict_gap_risk(
        self,
        standard_id: str,
        evidence_data: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None,
        institution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict risk of non-compliance for a standard
        
        Args:
            standard_id: The standard to analyze
            evidence_data: Current evidence mapped to this standard
            historical_data: Past compliance history
            institution_context: Institution-specific factors
            
        Returns:
            Risk assessment with score, factors, and recommendations
        """
        if not self.llm_service:
            await self.initialize()
        
        # Calculate base risk factors
        risk_factors = self._calculate_risk_factors(
            evidence_data,
            historical_data,
            institution_context
        )
        
        # Get AI-enhanced risk assessment
        ai_assessment = await self._get_ai_risk_assessment(
            standard_id,
            risk_factors,
            evidence_data,
            institution_context
        )
        
        # Combine algorithmic and AI assessments
        final_risk_score = self._combine_assessments(risk_factors, ai_assessment)
        
        return {
            "standard_id": standard_id,
            "risk_score": final_risk_score,
            "risk_level": self._get_risk_level(final_risk_score),
            "risk_factors": risk_factors,
            "ai_insights": ai_assessment.get("insights", []),
            "predictions": ai_assessment.get("predictions", []),
            "recommended_actions": self._generate_recommendations(
                final_risk_score,
                risk_factors,
                ai_assessment
            ),
            "confidence": ai_assessment.get("confidence", 0.8),
            "next_review_date": self._calculate_next_review(final_risk_score),
            "algorithm": "GapRisk Predictor™ with AI"
        }
    
    def _calculate_risk_factors(
        self,
        evidence_data: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]],
        institution_context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate individual risk factors"""
        
        factors = {}
        
        # Evidence age factor
        if evidence_data:
            ages = []
            for evidence in evidence_data:
                upload_date = evidence.get("uploaded_at")
                if upload_date:
                    if isinstance(upload_date, str):
                        upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    age_days = (datetime.utcnow() - upload_date).days
                    ages.append(age_days)
            
            if ages:
                avg_age = sum(ages) / len(ages)
                # Risk increases with age: 0 at 0 days, 1.0 at 365 days
                factors["evidence_age"] = min(avg_age / 365, 1.0)
            else:
                factors["evidence_age"] = 1.0
        else:
            factors["evidence_age"] = 1.0
        
        # Evidence coverage factor
        factors["evidence_coverage"] = 0.0 if evidence_data else 1.0
        if evidence_data:
            # Better coverage = lower risk
            coverage_score = min(len(evidence_data) / 3, 1.0)  # Assume 3 docs is full coverage
            factors["evidence_coverage"] = 1.0 - coverage_score
        
        # Evidence quality factor
        if evidence_data:
            quality_scores = [e.get("confidence", 0.5) for e in evidence_data]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
            factors["evidence_quality"] = 1.0 - avg_quality
        else:
            factors["evidence_quality"] = 1.0
        
        # Update frequency factor
        if historical_data:
            last_update = historical_data.get("last_update_days", 365)
            factors["update_frequency"] = min(last_update / 180, 1.0)  # 6 months = high risk
        else:
            factors["update_frequency"] = 0.5
        
        # Related gaps factor
        factors["related_gaps"] = 0.3  # Default medium risk
        
        # Historical issues factor
        if historical_data:
            past_issues = historical_data.get("compliance_issues", 0)
            factors["historical_issues"] = min(past_issues / 5, 1.0)
        else:
            factors["historical_issues"] = 0.1
        
        # Upcoming changes factor
        factors["upcoming_changes"] = 0.2  # Default low risk
        
        # Institutional risk factor
        if institution_context:
            inst_risk = institution_context.get("risk_profile", 0.3)
            factors["institutional_risk"] = inst_risk
        else:
            factors["institutional_risk"] = 0.3
        
        return factors
    
    async def _get_ai_risk_assessment(
        self,
        standard_id: str,
        risk_factors: Dict[str, float],
        evidence_data: List[Dict[str, Any]],
        institution_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get AI-enhanced risk assessment"""
        
        prompt = f"""Analyze compliance risk for accreditation standard {standard_id}.

Current Risk Factors:
- Evidence Age Score: {risk_factors['evidence_age']:.2f} (0=fresh, 1=outdated)
- Evidence Coverage: {risk_factors['evidence_coverage']:.2f} (0=complete, 1=none)
- Evidence Quality: {risk_factors['evidence_quality']:.2f} (0=high, 1=low)
- Update Frequency: {risk_factors['update_frequency']:.2f}
- Historical Issues: {risk_factors['historical_issues']:.2f}

Evidence Summary:
- Number of documents: {len(evidence_data)}
- Average confidence: {sum(e.get('confidence', 0) for e in evidence_data) / len(evidence_data) if evidence_data else 0:.2f}

Institutional Context:
{json.dumps(institution_context, indent=2) if institution_context else "Not provided"}

Provide a risk assessment in JSON format:
{{
    "risk_adjustment": -0.2 to 0.2,  // Adjustment to algorithmic score
    "confidence": 0.0 to 1.0,        // Confidence in assessment
    "insights": [                    // Key risk insights
        "specific insight about this standard's compliance risk"
    ],
    "predictions": [                 // Forward-looking predictions
        "prediction about future compliance challenges"
    ],
    "critical_factors": [            // Most critical risk factors
        "factor_name"
    ]
}}
"""
        
        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                agent_name="gap_risk_predictor",
                temperature=0.2,  # Low for consistency
                max_tokens=1000
            )
            
            # Parse response
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback
            return {
                "risk_adjustment": 0,
                "confidence": 0.7,
                "insights": ["AI analysis unavailable"],
                "predictions": [],
                "critical_factors": []
            }
            
        except Exception as e:
            logger.error(f"AI risk assessment failed: {e}")
            return {
                "risk_adjustment": 0,
                "confidence": 0.5,
                "insights": ["Using algorithmic assessment only"],
                "predictions": [],
                "critical_factors": list(risk_factors.keys())[:3]
            }
    
    def _combine_assessments(
        self,
        risk_factors: Dict[str, float],
        ai_assessment: Dict[str, Any]
    ) -> float:
        """Combine algorithmic and AI risk assessments"""
        
        # Calculate weighted average of risk factors
        weighted_sum = 0
        total_weight = 0
        
        for factor, score in risk_factors.items():
            weight = self.RISK_FACTORS.get(factor, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        base_risk = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Apply AI adjustment
        ai_adjustment = ai_assessment.get("risk_adjustment", 0)
        ai_confidence = ai_assessment.get("confidence", 0.5)
        
        # Weighted combination: more confidence = more adjustment
        adjusted_risk = base_risk + (ai_adjustment * ai_confidence)
        
        # Ensure risk score is between 0 and 1
        return max(0.0, min(1.0, adjusted_risk))
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 0.8:
            return "Critical"
        elif risk_score >= 0.6:
            return "High"
        elif risk_score >= 0.4:
            return "Medium"
        elif risk_score >= 0.2:
            return "Low"
        else:
            return "Minimal"
    
    def _generate_recommendations(
        self,
        risk_score: float,
        risk_factors: Dict[str, float],
        ai_assessment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Get top risk factors
        sorted_factors = sorted(
            risk_factors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for factor, score in sorted_factors:
            if score > 0.5:
                rec = self._get_recommendation_for_factor(factor, score)
                if rec:
                    recommendations.append(rec)
        
        # Add AI insights as recommendations
        for insight in ai_assessment.get("insights", [])[:2]:
            recommendations.append({
                "priority": "High" if risk_score > 0.6 else "Medium",
                "action": insight,
                "timeline": "Within 30 days" if risk_score > 0.6 else "Within 90 days",
                "impact": "Reduces compliance risk"
            })
        
        return recommendations
    
    def _get_recommendation_for_factor(
        self,
        factor: str,
        score: float
    ) -> Optional[Dict[str, Any]]:
        """Get specific recommendation for a risk factor"""
        
        recommendations_map = {
            "evidence_age": {
                "priority": "High" if score > 0.7 else "Medium",
                "action": "Update evidence documents with recent materials",
                "timeline": f"Within {14 if score > 0.7 else 30} days",
                "impact": "Ensures evidence reflects current practices"
            },
            "evidence_coverage": {
                "priority": "Critical" if score > 0.8 else "High",
                "action": "Upload additional evidence to fully address this standard",
                "timeline": "Immediately" if score > 0.8 else "Within 14 days",
                "impact": "Improves standard coverage significantly"
            },
            "evidence_quality": {
                "priority": "High",
                "action": "Replace low-confidence evidence with authoritative documents",
                "timeline": "Within 30 days",
                "impact": "Strengthens compliance demonstration"
            },
            "update_frequency": {
                "priority": "Medium",
                "action": "Establish regular evidence review schedule",
                "timeline": "Within 60 days",
                "impact": "Maintains compliance readiness"
            }
        }
        
        return recommendations_map.get(factor)
    
    def _calculate_next_review(self, risk_score: float) -> str:
        """Calculate next review date based on risk score"""
        
        if risk_score >= 0.8:
            days = 7
        elif risk_score >= 0.6:
            days = 30
        elif risk_score >= 0.4:
            days = 90
        else:
            days = 180
        
        next_date = datetime.utcnow() + timedelta(days=days)
        return next_date.isoformat()


# Singleton instance
ai_gap_risk_predictor = AIGapRiskPredictor()
