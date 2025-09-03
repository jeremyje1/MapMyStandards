"""
Custom Power BI Visuals Service
Advanced analytics custom visuals for compliance and standards mapping
Part of Phase M2: Advanced Analytics Features
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CustomVisual:
    """Custom Power BI visual configuration"""
    id: str
    name: str
    description: str
    category: str
    visual_type: str
    config: Dict[str, Any]
    data_requirements: List[str]
    style_properties: Dict[str, Any]
    interactions: Dict[str, Any]


@dataclass
class VisualDataBinding:
    """Data binding configuration for custom visuals"""
    visual_id: str
    data_source: str
    field_mappings: Dict[str, str]
    filters: List[Dict[str, Any]]
    aggregations: Dict[str, str]


class PowerBICustomVisualsService:
    """Service for managing custom Power BI visuals for compliance analytics"""
    
    def __init__(self):
        self.visuals_registry = {}
        self.data_bindings = {}
        self.visual_themes = {}
        self._initialize_default_visuals()
        
    def _initialize_default_visuals(self):
        """Initialize default custom visuals for compliance analytics"""
        
        # Compliance Heatmap Visual
        compliance_heatmap = CustomVisual(
            id="compliance_heatmap",
            name="Compliance Heatmap",
            description="Organizational compliance visualization with drill-down capabilities",
            category="compliance",
            visual_type="matrix_heatmap",
            config={
                "supports_drill_down": True,
                "supports_filtering": True,
                "supports_cross_highlight": True,
                "animation_enabled": True,
                "color_scale": "red_yellow_green",
                "cell_padding": 2,
                "show_values": True,
                "show_legend": True,
                "legend_position": "right"
            },
            data_requirements=[
                "department", "compliance_score", "employee_count", 
                "standards_count", "last_assessment_date"
            ],
            style_properties={
                "colors": {
                    "high_compliance": "#2E8B57",    # Sea Green
                    "medium_compliance": "#FFD700",   # Gold
                    "low_compliance": "#DC143C",      # Crimson
                    "no_data": "#D3D3D3"             # Light Gray
                },
                "thresholds": {
                    "high": 85,
                    "medium": 70,
                    "low": 50
                },
                "font": {
                    "family": "Segoe UI",
                    "size": 12,
                    "weight": "normal"
                }
            },
            interactions={
                "click": "drill_down_department",
                "hover": "show_details_tooltip",
                "right_click": "show_context_menu"
            }
        )
        
        # Standards Progress Wheel Visual
        progress_wheel = CustomVisual(
            id="standards_progress_wheel",
            name="Standards Progress Wheel",
            description="Circular progress visualization for standards implementation",
            category="progress",
            visual_type="radial_progress",
            config={
                "supports_animation": True,
                "supports_comparison": True,
                "show_percentage": True,
                "show_labels": True,
                "wheel_thickness": 20,
                "inner_radius": 40,
                "animation_duration": 1500,
                "segments": "auto"
            },
            data_requirements=[
                "standard_name", "completion_percent", "priority", 
                "target_date", "responsible_department"
            ],
            style_properties={
                "colors": {
                    "completed": "#228B22",      # Forest Green
                    "in_progress": "#4169E1",    # Royal Blue
                    "not_started": "#696969",    # Dim Gray
                    "overdue": "#FF4500",        # Orange Red
                    "background": "#F5F5F5"      # White Smoke
                },
                "priority_colors": {
                    "high": "#FF1744",
                    "medium": "#FF9800",
                    "low": "#4CAF50"
                },
                "font": {
                    "family": "Arial",
                    "size": 10,
                    "weight": "bold"
                }
            },
            interactions={
                "click": "view_standard_details",
                "hover": "show_progress_tooltip",
                "double_click": "edit_standard"
            }
        )
        
        # Risk Impact Matrix Visual
        risk_matrix = CustomVisual(
            id="risk_impact_matrix",
            name="Risk Impact Matrix",
            description="Interactive risk assessment visualization with quadrant analysis",
            category="risk",
            visual_type="scatter_matrix",
            config={
                "supports_quadrant_analysis": True,
                "supports_hover_details": True,
                "supports_zoom": True,
                "show_quadrant_labels": True,
                "show_trend_lines": False,
                "bubble_size_field": "affected_areas",
                "x_axis_title": "Probability",
                "y_axis_title": "Impact",
                "grid_enabled": True
            },
            data_requirements=[
                "risk_name", "impact_score", "probability_score", 
                "affected_areas", "mitigation_status", "risk_category"
            ],
            style_properties={
                "quadrants": {
                    "high_high": {"color": "#8B0000", "label": "Critical"},      # Dark Red
                    "high_low": {"color": "#FF8C00", "label": "Medium"},        # Dark Orange  
                    "low_high": {"color": "#FFD700", "label": "Medium"},        # Gold
                    "low_low": {"color": "#32CD32", "label": "Low"}             # Lime Green
                },
                "bubble_colors": {
                    "financial": "#1E90FF",
                    "operational": "#FF6347", 
                    "compliance": "#9370DB",
                    "strategic": "#20B2AA"
                },
                "axes": {
                    "min": 0,
                    "max": 10,
                    "tick_count": 5
                }
            },
            interactions={
                "click": "view_risk_details",
                "hover": "show_risk_tooltip",
                "drag": "update_risk_position"
            }
        )
        
        # Compliance Timeline Visual
        timeline_visual = CustomVisual(
            id="compliance_timeline",
            name="Compliance Timeline",
            description="Timeline visualization for compliance milestones and deadlines",
            category="timeline",
            visual_type="gantt_timeline",
            config={
                "supports_zoom": True,
                "supports_pan": True,
                "show_milestones": True,
                "show_dependencies": True,
                "show_progress_bars": True,
                "time_scale": "monthly",
                "highlight_overdue": True
            },
            data_requirements=[
                "task_name", "start_date", "end_date", "completion_percent",
                "responsible_party", "priority", "dependencies"
            ],
            style_properties={
                "colors": {
                    "completed": "#228B22",
                    "on_track": "#4169E1", 
                    "at_risk": "#FFD700",
                    "overdue": "#DC143C",
                    "milestone": "#9370DB"
                },
                "bar_height": 24,
                "font_size": 11,
                "milestone_shape": "diamond"
            },
            interactions={
                "click": "view_task_details",
                "hover": "show_timeline_tooltip",
                "drag": "reschedule_task"
            }
        )
        
        # Register all default visuals
        self.visuals_registry = {
            compliance_heatmap.id: compliance_heatmap,
            progress_wheel.id: progress_wheel,
            risk_matrix.id: risk_matrix,
            timeline_visual.id: timeline_visual
        }
        
        # Initialize default themes
        self._initialize_visual_themes()
    
    def _initialize_visual_themes(self):
        """Initialize visual themes for different institutions"""
        
        self.visual_themes = {
            "university": {
                "primary_color": "#003366",     # Navy Blue
                "secondary_color": "#4A90E2",   # Sky Blue
                "accent_color": "#F4A300",      # Orange
                "background": "#FFFFFF",
                "text_color": "#333333",
                "success_color": "#28A745",
                "warning_color": "#FFC107",
                "danger_color": "#DC3545"
            },
            "healthcare": {
                "primary_color": "#0066CC",     # Medical Blue
                "secondary_color": "#00A651",   # Medical Green
                "accent_color": "#FF6B35",      # Medical Orange
                "background": "#F8F9FA",
                "text_color": "#2C3E50",
                "success_color": "#28A745",
                "warning_color": "#F39C12",
                "danger_color": "#E74C3C"
            },
            "corporate": {
                "primary_color": "#2C3E50",     # Dark Blue-Gray
                "secondary_color": "#34495E",   # Blue-Gray
                "accent_color": "#E67E22",      # Orange
                "background": "#ECF0F1",
                "text_color": "#2C3E50",
                "success_color": "#27AE60",
                "warning_color": "#F39C12",
                "danger_color": "#C0392B"
            },
            "government": {
                "primary_color": "#1B365D",     # Navy
                "secondary_color": "#2E86AB",   # Blue
                "accent_color": "#A23B72",      # Purple
                "background": "#F7F9FC",
                "text_color": "#1A1A1A",
                "success_color": "#2ECC71",
                "warning_color": "#F1C40F",
                "danger_color": "#E74C3C"
            }
        }
    
    async def get_visual_by_id(self, visual_id: str) -> Optional[CustomVisual]:
        """Get custom visual by ID"""
        return self.visuals_registry.get(visual_id)
    
    async def get_visuals_by_category(self, category: str) -> List[CustomVisual]:
        """Get all visuals in a specific category"""
        return [
            visual for visual in self.visuals_registry.values()
            if visual.category == category
        ]
    
    async def get_all_visuals(self) -> List[CustomVisual]:
        """Get all available custom visuals"""
        return list(self.visuals_registry.values())
    
    async def create_visual_config(
        self, 
        visual_id: str, 
        theme: str = "university",
        custom_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create Power BI visual configuration"""
        
        visual = await self.get_visual_by_id(visual_id)
        if not visual:
            raise ValueError(f"Visual {visual_id} not found")
        
        theme_colors = self.visual_themes.get(theme, self.visual_themes["university"])
        
        # Merge theme colors with visual style properties
        config = {
            "visual": {
                "id": visual.id,
                "name": visual.name,
                "type": visual.visual_type,
                "version": "1.0.0"
            },
            "data": {
                "roles": [
                    {"role": field, "kind": "Grouping" if field in ["department", "category"] else "Measure"}
                    for field in visual.data_requirements
                ]
            },
            "style": {
                **visual.style_properties,
                "theme": theme_colors
            },
            "interactions": visual.interactions,
            "settings": visual.config
        }
        
        # Apply custom properties if provided
        if custom_properties:
            self._merge_custom_properties(config, custom_properties)
        
        return config
    
    def _merge_custom_properties(self, config: Dict[str, Any], custom_props: Dict[str, Any]):
        """Merge custom properties into visual configuration"""
        for key, value in custom_props.items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    
    async def create_data_binding(
        self,
        visual_id: str,
        data_source: str,
        field_mappings: Dict[str, str],
        filters: Optional[List[Dict[str, Any]]] = None,
        aggregations: Optional[Dict[str, str]] = None
    ) -> str:
        """Create data binding for a custom visual"""
        
        binding_id = f"{visual_id}_{data_source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        binding = VisualDataBinding(
            visual_id=visual_id,
            data_source=data_source,
            field_mappings=field_mappings,
            filters=filters or [],
            aggregations=aggregations or {}
        )
        
        self.data_bindings[binding_id] = binding
        return binding_id
    
    async def get_visual_data_config(self, visual_id: str, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data configuration for visual based on institution data"""
        
        visual = await self.get_visual_by_id(visual_id)
        if not visual:
            raise ValueError(f"Visual {visual_id} not found")
        
        if visual_id == "compliance_heatmap":
            return await self._generate_heatmap_data(institution_data)
        elif visual_id == "standards_progress_wheel":
            return await self._generate_progress_wheel_data(institution_data)
        elif visual_id == "risk_impact_matrix":
            return await self._generate_risk_matrix_data(institution_data)
        elif visual_id == "compliance_timeline":
            return await self._generate_timeline_data(institution_data)
        else:
            return {"error": f"Data generator not implemented for {visual_id}"}
    
    async def _generate_heatmap_data(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance heatmap data"""
        return {
            "title": "Organizational Compliance Heatmap",
            "data": [
                {
                    "department": "Engineering",
                    "compliance_score": 92,
                    "employee_count": 45,
                    "standards_count": 12,
                    "last_assessment_date": "2024-01-15"
                },
                {
                    "department": "HR",
                    "compliance_score": 88,
                    "employee_count": 23,
                    "standards_count": 8,
                    "last_assessment_date": "2024-01-10"
                },
                {
                    "department": "Finance", 
                    "compliance_score": 95,
                    "employee_count": 18,
                    "standards_count": 15,
                    "last_assessment_date": "2024-01-12"
                },
                {
                    "department": "Marketing",
                    "compliance_score": 76,
                    "employee_count": 32,
                    "standards_count": 6,
                    "last_assessment_date": "2024-01-08"
                },
                {
                    "department": "Operations",
                    "compliance_score": 82,
                    "employee_count": 56,
                    "standards_count": 10,
                    "last_assessment_date": "2024-01-14"
                }
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_departments": 5,
                "average_compliance": 86.6
            }
        }
    
    async def _generate_progress_wheel_data(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standards progress wheel data"""
        return {
            "title": "Standards Implementation Progress",
            "data": [
                {
                    "standard_name": "ISO 27001",
                    "completion_percent": 85,
                    "priority": "high",
                    "target_date": "2024-03-31",
                    "responsible_department": "IT Security"
                },
                {
                    "standard_name": "GDPR Compliance",
                    "completion_percent": 92,
                    "priority": "high", 
                    "target_date": "2024-02-28",
                    "responsible_department": "Legal"
                },
                {
                    "standard_name": "SOX Controls",
                    "completion_percent": 78,
                    "priority": "medium",
                    "target_date": "2024-04-15",
                    "responsible_department": "Finance"
                },
                {
                    "standard_name": "OSHA Safety",
                    "completion_percent": 95,
                    "priority": "high",
                    "target_date": "2024-01-31",
                    "responsible_department": "Operations"
                }
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_standards": 4,
                "average_completion": 87.5
            }
        }
    
    async def _generate_risk_matrix_data(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk impact matrix data"""
        return {
            "title": "Risk Assessment Matrix",
            "data": [
                {
                    "risk_name": "Data Breach",
                    "impact_score": 9,
                    "probability_score": 4,
                    "affected_areas": 8,
                    "mitigation_status": "in_progress",
                    "risk_category": "compliance"
                },
                {
                    "risk_name": "Regulatory Changes",
                    "impact_score": 6,
                    "probability_score": 7,
                    "affected_areas": 5,
                    "mitigation_status": "planned",
                    "risk_category": "compliance"
                },
                {
                    "risk_name": "System Downtime",
                    "impact_score": 7,
                    "probability_score": 3,
                    "affected_areas": 6,
                    "mitigation_status": "mitigated",
                    "risk_category": "operational"
                },
                {
                    "risk_name": "Budget Overrun",
                    "impact_score": 5,
                    "probability_score": 6,
                    "affected_areas": 3,
                    "mitigation_status": "monitoring",
                    "risk_category": "financial"
                }
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_risks": 4,
                "high_risk_count": 2
            }
        }
    
    async def _generate_timeline_data(self, institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance timeline data"""
        return {
            "title": "Compliance Implementation Timeline",
            "data": [
                {
                    "task_name": "Policy Review",
                    "start_date": "2024-01-01",
                    "end_date": "2024-02-15",
                    "completion_percent": 90,
                    "responsible_party": "Legal Team",
                    "priority": "high",
                    "dependencies": []
                },
                {
                    "task_name": "Staff Training",
                    "start_date": "2024-02-01",
                    "end_date": "2024-03-31",
                    "completion_percent": 65,
                    "responsible_party": "HR Department",
                    "priority": "medium",
                    "dependencies": ["Policy Review"]
                },
                {
                    "task_name": "System Audit",
                    "start_date": "2024-03-01",
                    "end_date": "2024-04-15",
                    "completion_percent": 25,
                    "responsible_party": "IT Team",
                    "priority": "high",
                    "dependencies": []
                },
                {
                    "task_name": "Documentation Update",
                    "start_date": "2024-02-15",
                    "end_date": "2024-05-01",
                    "completion_percent": 40,
                    "responsible_party": "Compliance Team",
                    "priority": "medium",
                    "dependencies": ["Policy Review", "System Audit"]
                }
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_tasks": 4,
                "on_track_count": 3,
                "at_risk_count": 1
            }
        }
    
    async def export_visual_config(self, visual_id: str, format: str = "json") -> str:
        """Export visual configuration for Power BI"""
        
        visual = await self.get_visual_by_id(visual_id)
        if not visual:
            raise ValueError(f"Visual {visual_id} not found")
        
        config = await self.create_visual_config(visual_id)
        
        if format == "json":
            return json.dumps(config, indent=2)
        elif format == "pbiviz":
            # Generate Power BI custom visual package structure
            return await self._generate_pbiviz_config(config)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _generate_pbiviz_config(self, config: Dict[str, Any]) -> str:
        """Generate Power BI custom visual package configuration"""
        
        pbiviz_config = {
            "visual": {
                "name": config["visual"]["name"],
                "displayName": config["visual"]["name"],
                "guid": f"custom{config['visual']['id'].replace('_', '')}Visual",
                "visualClassName": f"Visual{config['visual']['id'].title().replace('_', '')}",
                "version": config["visual"]["version"],
                "description": "",
                "supportUrl": "",
                "gitHubUrl": ""
            },
            "apiVersion": "2.6.0",
            "author": {
                "name": "MapMyStandards",
                "email": "support@mapmystandards.ai"
            },
            "assets": {
                "icon": "assets/icon.png"
            },
            "externalJS": [],
            "style": "style/visual.less",
            "capabilities": {
                "dataRoles": config["data"]["roles"],
                "dataViewMappings": [{
                    "conditions": [{"category": {"max": 1}, "measure": {"max": 10}}],
                    "categorical": {
                        "categories": {"for": {"in": "category"}},
                        "values": {"select": [{"for": {"in": "measure"}}]}
                    }
                }],
                "objects": {
                    "general": {
                        "displayName": "General",
                        "properties": {
                            "theme": {
                                "displayName": "Theme",
                                "type": {"enumeration": [
                                    {"displayName": "University", "value": "university"},
                                    {"displayName": "Healthcare", "value": "healthcare"},
                                    {"displayName": "Corporate", "value": "corporate"},
                                    {"displayName": "Government", "value": "government"}
                                ]}
                            }
                        }
                    }
                }
            }
        }
        
        return json.dumps(pbiviz_config, indent=2)


# Global service instance
powerbi_visuals_service = PowerBICustomVisualsService()
