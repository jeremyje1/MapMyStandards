"""
Database-backed Report Generation API

Generates real reports based on evidence mappings from the database.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..dependencies import get_current_user, get_async_db
from ...models.database_schema import (
    StandardMapping, Document, AccreditationStandard, User,
    StandardComplianceStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

async def get_user_evidence_data(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Get all evidence mapping data for a user"""
    # Get all documents
    docs_result = await db.execute(
        select(Document).where(Document.owner_id == user_id)
    )
    documents = docs_result.scalars().all()
    
    # Get all mappings with standards
    mappings_result = await db.execute(
        select(StandardMapping, Document, AccreditationStandard)
        .join(Document, StandardMapping.document_id == Document.id)
        .join(AccreditationStandard, StandardMapping.standard_id == AccreditationStandard.id)
        .where(Document.owner_id == user_id)
    )
    mappings_data = mappings_result.all()
    
    # Get compliance statuses
    compliance_result = await db.execute(
        select(StandardComplianceStatus, AccreditationStandard)
        .join(AccreditationStandard, StandardComplianceStatus.standard_id == AccreditationStandard.id)
        .where(StandardComplianceStatus.user_id == user_id)
    )
    compliance_data = compliance_result.all()
    
    return {
        "documents": documents,
        "mappings": mappings_data,
        "compliance": compliance_data
    }

def generate_html_report(
    report_type: str,
    data: Dict[str, Any],
    user_info: Dict[str, Any]
) -> str:
    """Generate HTML report content"""
    
    documents = data.get("documents", [])
    mappings = data.get("mappings", [])
    compliance = data.get("compliance", [])
    
    # Count statistics
    total_docs = len(documents)
    total_mappings = len(mappings)
    unique_standards = len(set(m[2].code for m in mappings))  # m[2] is AccreditationStandard
    verified_mappings = sum(1 for m in mappings if m[0].is_verified)  # m[0] is StandardMapping
    
    # Group mappings by standard
    standards_map = {}
    for mapping, document, standard in mappings:
        if standard.code not in standards_map:
            standards_map[standard.code] = {
                "standard": standard,
                "evidence": []
            }
        standards_map[standard.code]["evidence"].append({
            "document": document,
            "mapping": mapping
        })
    
    # Start HTML generation
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{report_type} Report - {user_info.get('name', 'User')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ background: #1e40af; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
            .metrics {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .metric-card {{ background: #f3f4f6; padding: 20px; border-radius: 8px; flex: 1; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #1e40af; }}
            .section {{ margin-bottom: 40px; }}
            .section h2 {{ color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
            .standard-block {{ background: #f9fafb; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; }}
            .evidence-item {{ background: white; padding: 15px; margin: 10px 0; border-radius: 6px; border: 1px solid #e5e7eb; }}
            .confidence-high {{ color: #059669; }}
            .confidence-medium {{ color: #f59e0b; }}
            .confidence-low {{ color: #dc2626; }}
            .verified-badge {{ background: #059669; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; }}
            .gap {{ background: #fef2f2; border-left-color: #dc2626; }}
            .recommendation {{ background: #fffbeb; padding: 15px; border-radius: 6px; margin-top: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
            th {{ background: #f3f4f6; font-weight: bold; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.9em; }}
        </style>
    </head>
    <body>
    """
    
    # Header
    html += f"""
        <div class="header">
            <h1>{report_type} Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p>Institution: {user_info.get('institution_name', user_info.get('name', 'N/A'))}</p>
        </div>
    """
    
    # Metrics Summary
    html += """
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div>Documents Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div>Standards Mapped</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div>Evidence Mappings</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{}%</div>
                <div>Verified Evidence</div>
            </div>
        </div>
    """.format(
        total_docs,
        unique_standards,
        total_mappings,
        int((verified_mappings / total_mappings * 100) if total_mappings > 0 else 0)
    )
    
    if report_type == "Comprehensive Compliance":
        html += generate_comprehensive_sections(standards_map, compliance)
    elif report_type == "QEP Impact Assessment":
        html += generate_qep_sections(standards_map, documents)
    elif report_type == "Evidence Mapping Summary":
        html += generate_evidence_sections(standards_map, documents)
    elif report_type == "Gap Analysis":
        html += generate_gap_sections(standards_map, compliance)
    
    # Footer
    html += """
        <div class="footer">
            <p>This report was generated automatically by MapMyStandards.ai based on your uploaded evidence and mapped standards.</p>
            <p>© 2025 MapMyStandards.ai - Proprietary and Confidential</p>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_comprehensive_sections(standards_map: Dict, compliance: List) -> str:
    """Generate comprehensive report sections"""
    html = '<div class="section"><h2>Standards Compliance Overview</h2>'
    
    for std_code, data in sorted(standards_map.items()):
        standard = data["standard"]
        evidence_list = data["evidence"]
        
        html += f'<div class="standard-block">'
        html += f'<h3>{std_code}: {standard.title}</h3>'
        html += f'<p><strong>Accreditor:</strong> {standard.accreditor}</p>'
        html += f'<p><strong>Evidence Count:</strong> {len(evidence_list)}</p>'
        
        # Evidence items
        for item in evidence_list:
            doc = item["document"]
            mapping = item["mapping"]
            confidence_class = (
                "confidence-high" if mapping.confidence_score >= 80 else
                "confidence-medium" if mapping.confidence_score >= 60 else
                "confidence-low"
            )
            
            html += f'<div class="evidence-item">'
            html += f'<strong>{doc.filename}</strong> '
            if mapping.is_verified:
                html += '<span class="verified-badge">Verified</span>'
            html += f'<div class="{confidence_class}">Confidence: {mapping.confidence_score}%</div>'
            if mapping.mapped_text:
                html += f'<p style="margin-top: 10px; color: #6b7280;">{mapping.mapped_text[:200]}...</p>'
            html += '</div>'
        
        html += '</div>'
    
    html += '</div>'
    return html

def generate_qep_sections(standards_map: Dict, documents: List) -> str:
    """Generate QEP report sections"""
    html = '<div class="section"><h2>Quality Enhancement Plan Impact</h2>'
    html += '<p>This assessment evaluates how your evidence supports QEP initiatives and measurable outcomes.</p>'
    
    # QEP-related standards (simplified - in reality would filter by QEP tags)
    qep_standards = [code for code in standards_map.keys() if any(
        keyword in standards_map[code]["standard"].title.lower() 
        for keyword in ["quality", "improvement", "assessment", "outcome"]
    )]
    
    html += f'<h3>QEP-Relevant Standards: {len(qep_standards)}</h3>'
    
    for std_code in qep_standards:
        data = standards_map[std_code]
        standard = data["standard"]
        evidence_list = data["evidence"]
        
        html += f'<div class="standard-block">'
        html += f'<h4>{std_code}: {standard.title}</h4>'
        html += '<div class="recommendation">'
        html += '<strong>QEP Alignment:</strong> '
        html += f'This standard has {len(evidence_list)} supporting documents. '
        html += 'Consider developing specific metrics to track improvement in this area.'
        html += '</div>'
        html += '</div>'
    
    html += '</div>'
    return html

def generate_evidence_sections(standards_map: Dict, documents: List) -> str:
    """Generate evidence mapping sections"""
    html = '<div class="section"><h2>Evidence Mapping Details</h2>'
    
    # Document-centric view
    html += '<h3>Documents and Their Mappings</h3>'
    html += '<table>'
    html += '<tr><th>Document</th><th>Type</th><th>Standards Mapped</th><th>Avg Confidence</th></tr>'
    
    # Aggregate by document
    doc_mappings = {}
    for std_code, data in standards_map.items():
        for item in data["evidence"]:
            doc = item["document"]
            mapping = item["mapping"]
            if doc.id not in doc_mappings:
                doc_mappings[doc.id] = {
                    "document": doc,
                    "standards": [],
                    "confidences": []
                }
            doc_mappings[doc.id]["standards"].append(std_code)
            doc_mappings[doc.id]["confidences"].append(mapping.confidence_score)
    
    for doc_id, data in doc_mappings.items():
        doc = data["document"]
        avg_confidence = sum(data["confidences"]) / len(data["confidences"])
        html += f'<tr>'
        html += f'<td>{doc.filename}</td>'
        html += f'<td>{doc.doc_type or "General"}</td>'
        html += f'<td>{len(data["standards"])}</td>'
        html += f'<td>{avg_confidence:.0f}%</td>'
        html += f'</tr>'
    
    html += '</table>'
    html += '</div>'
    return html

def generate_gap_sections(standards_map: Dict, compliance: List) -> str:
    """Generate gap analysis sections"""
    html = '<div class="section"><h2>Compliance Gap Analysis</h2>'
    
    # Find standards with no or low evidence
    html += '<h3>Critical Gaps Identified</h3>'
    
    gaps_found = False
    for std_code, data in sorted(standards_map.items()):
        evidence_list = data["evidence"]
        if len(evidence_list) == 0:
            gaps_found = True
            standard = data["standard"]
            html += f'<div class="standard-block gap">'
            html += f'<h4>⚠️ {std_code}: {standard.title}</h4>'
            html += '<p><strong>Gap Type:</strong> No evidence mapped</p>'
            html += '<div class="recommendation">'
            html += '<strong>Recommendation:</strong> Urgent action required. '
            html += 'Identify and upload relevant documentation for this standard.'
            html += '</div>'
            html += '</div>'
    
    # Low confidence mappings
    for std_code, data in sorted(standards_map.items()):
        evidence_list = data["evidence"]
        low_confidence = [e for e in evidence_list if e["mapping"].confidence_score < 60]
        if low_confidence:
            gaps_found = True
            standard = data["standard"]
            html += f'<div class="standard-block gap">'
            html += f'<h4>⚠️ {std_code}: {standard.title}</h4>'
            html += f'<p><strong>Gap Type:</strong> Low confidence evidence ({len(low_confidence)} documents)</p>'
            html += '<div class="recommendation">'
            html += '<strong>Recommendation:</strong> Review and strengthen evidence. '
            html += 'Consider uploading more specific documentation.'
            html += '</div>'
            html += '</div>'
    
    if not gaps_found:
        html += '<p style="color: #059669;">✅ No critical gaps identified. Continue monitoring and updating evidence.</p>'
    
    html += '</div>'
    return html

@router.post("/comprehensive")
async def generate_comprehensive_report(
    selected_standards: Optional[List[str]] = Query(None, description="Selected standard codes"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> HTMLResponse:
    """Generate a comprehensive compliance report"""
    try:
        data = await get_user_evidence_data(current_user.id, db)
        
        # Filter by selected standards if provided
        if selected_standards:
            data["mappings"] = [
                m for m in data["mappings"] 
                if m[2].code in selected_standards  # m[2] is AccreditationStandard
            ]
        
        html_content = generate_html_report(
            "Comprehensive Compliance",
            data,
            {
                "name": current_user.name or current_user.email,
                "institution_name": getattr(current_user, 'institution_name', None)
            }
        )
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/qep")
async def generate_qep_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> HTMLResponse:
    """Generate a QEP impact assessment report"""
    try:
        data = await get_user_evidence_data(current_user.id, db)
        
        html_content = generate_html_report(
            "QEP Impact Assessment",
            data,
            {
                "name": current_user.name or current_user.email,
                "institution_name": getattr(current_user, 'institution_name', None)
            }
        )
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating QEP report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/evidence")
async def generate_evidence_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> HTMLResponse:
    """Generate an evidence mapping summary report"""
    try:
        data = await get_user_evidence_data(current_user.id, db)
        
        html_content = generate_html_report(
            "Evidence Mapping Summary",
            data,
            {
                "name": current_user.name or current_user.email,
                "institution_name": getattr(current_user, 'institution_name', None)
            }
        )
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating evidence report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.post("/gaps")
async def generate_gap_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> HTMLResponse:
    """Generate a gap analysis report"""
    try:
        data = await get_user_evidence_data(current_user.id, db)
        
        html_content = generate_html_report(
            "Gap Analysis",
            data,
            {
                "name": current_user.name or current_user.email,
                "institution_name": getattr(current_user, 'institution_name', None)
            }
        )
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error generating gap report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
