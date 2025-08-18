#!/usr/bin/env python3
"""
A3E Data Seeding Script

Seeds the A3E database with comprehensive US accreditation data including:
- All regional accreditors and their standards
- Major national and programmatic accreditors
- Sample institutions and evidence
- Test data for development

Usage: python scripts/seed_data.py
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import uuid

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from a3e.core.config import settings
from a3e.core.accreditation_registry import ALL_ACCREDITORS, InstitutionType
from a3e.services.database_service import DatabaseService


async def seed_accreditation_data():
    """Seed comprehensive US accreditation data"""
    print("🌱 Seeding accreditation data...")
    
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    
    try:
        # Clear existing data
        await db_service.execute("DELETE FROM standards")
        await db_service.execute("DELETE FROM accreditors")
        print("✅ Cleared existing accreditation data")
        
        # Insert all accreditors and their standards
        for accreditor in ALL_ACCREDITORS.values():
            # Insert accreditor
            accreditor_data = {
                "id": accreditor.id,
                "name": accreditor.name,
                "acronym": accreditor.acronym,
                "type": accreditor.type.value,
                "recognition_authority": accreditor.recognition_authority,
                "geographic_scope": json.dumps(accreditor.geographic_scope),
                "applicable_institution_types": json.dumps([t.value for t in accreditor.applicable_institution_types]),
                "website": accreditor.website,
                "last_standards_update": datetime.utcnow(),
                "is_active": True
            }
            
            await db_service.execute("""
                INSERT INTO accreditors (id, name, acronym, type, recognition_authority, 
                                       geographic_scope, applicable_institution_types, 
                                       website, last_standards_update, is_active)
                VALUES (%(id)s, %(name)s, %(acronym)s, %(type)s, %(recognition_authority)s,
                        %(geographic_scope)s, %(applicable_institution_types)s, 
                        %(website)s, %(last_standards_update)s, %(is_active)s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    last_standards_update = EXCLUDED.last_standards_update
            """, accreditor_data)
            
            # Insert standards
            for i, standard in enumerate(accreditor.standards):
                standard_data = {
                    "id": standard.id,
                    "accreditor_id": accreditor.id,
                    "title": standard.title,
                    "description": standard.description,
                    "applicable_institution_types": json.dumps([t.value for t in standard.applicable_institution_types]),
                    "evidence_requirements": json.dumps(standard.evidence_requirements),
                    "weight": standard.weight,
                    "order_sequence": i + 1,
                    "level": 1
                }
                
                await db_service.execute("""
                    INSERT INTO standards (id, accreditor_id, title, description, 
                                         applicable_institution_types, evidence_requirements,
                                         weight, order_sequence, level)
                    VALUES (%(id)s, %(accreditor_id)s, %(title)s, %(description)s,
                            %(applicable_institution_types)s, %(evidence_requirements)s,
                            %(weight)s, %(order_sequence)s, %(level)s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description
                """, standard_data)
            
            print(f"✅ Seeded {accreditor.acronym} with {len(accreditor.standards)} standards")
        
        print(f"🎉 Successfully seeded {len(ALL_ACCREDITORS)} accreditors with comprehensive standards")
        
    finally:
        await db_service.close()


async def seed_sample_institutions():
    """Seed sample institutions for testing"""
    print("🏫 Seeding sample institutions...")
    
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    
    try:
        sample_institutions = [
            {
                "name": "Metropolitan Community College",
                "ipeds_id": "123001",
                "ope_id": "001234",
                "state": "CA",
                "city": "Los Angeles",
                "zip_code": "90001",
                "institution_types": [InstitutionType.COMMUNITY_COLLEGE.value, InstitutionType.PUBLIC.value],
                "control": "Public",
                "sector": "Public, 2-year",
                "total_enrollment": 18500,
                "undergraduate_enrollment": 18500,
                "website": "https://www.metrocc.edu",
                "primary_contact_email": "accreditation@metrocc.edu",
                "phone": "(323) 555-0100"
            },
            {
                "name": "State University of Excellence",
                "ipeds_id": "234002",
                "ope_id": "002345", 
                "state": "NY",
                "city": "Buffalo",
                "zip_code": "14260",
                "institution_types": [InstitutionType.UNIVERSITY.value, InstitutionType.RESEARCH_UNIVERSITY.value, InstitutionType.PUBLIC.value],
                "control": "Public",
                "sector": "Public, 4-year or above",
                "total_enrollment": 28750,
                "undergraduate_enrollment": 21200,
                "graduate_enrollment": 7550,
                "website": "https://www.sue.edu",
                "primary_contact_email": "accreditation@sue.edu",
                "phone": "(716) 555-0200"
            },
            {
                "name": "Liberal Arts College of Excellence",
                "ipeds_id": "345003",
                "ope_id": "003456",
                "state": "MA",
                "city": "Northampton",
                "zip_code": "01063",
                "institution_types": [InstitutionType.FOUR_YEAR_COLLEGE.value, InstitutionType.PRIVATE.value, InstitutionType.NON_PROFIT.value],
                "control": "Private non-profit",
                "sector": "Private not-for-profit, 4-year or above",
                "total_enrollment": 3250,
                "undergraduate_enrollment": 2800,
                "graduate_enrollment": 450,
                "website": "https://www.lace.edu",
                "primary_contact_email": "accreditation@lace.edu",
                "phone": "(413) 555-0300"
            },
            {
                "name": "Online University of Business",
                "ipeds_id": "456004",
                "ope_id": "004567",
                "state": "AZ",
                "city": "Phoenix",
                "zip_code": "85001",
                "institution_types": [InstitutionType.UNIVERSITY.value, InstitutionType.ONLINE_INSTITUTION.value, InstitutionType.FOR_PROFIT.value],
                "control": "Private for-profit",
                "sector": "Private for-profit, 4-year or above",
                "total_enrollment": 12500,
                "undergraduate_enrollment": 8900,
                "graduate_enrollment": 3600,
                "website": "https://www.oub.edu",
                "primary_contact_email": "accreditation@oub.edu",
                "phone": "(602) 555-0400"
            },
            {
                "name": "Seminary of Theological Studies",
                "ipeds_id": "567005",
                "ope_id": "005678",
                "state": "TX",
                "city": "Dallas",
                "zip_code": "75201",
                "institution_types": [InstitutionType.THEOLOGICAL_SEMINARY.value, InstitutionType.GRADUATE_SCHOOL.value, InstitutionType.PRIVATE.value],
                "control": "Private non-profit",
                "sector": "Private not-for-profit, 4-year or above",
                "total_enrollment": 850,
                "undergraduate_enrollment": 0,
                "graduate_enrollment": 850,
                "website": "https://www.sts.edu",
                "primary_contact_email": "accreditation@sts.edu",
                "phone": "(214) 555-0500"
            }
        ]
        
        # Clear existing sample data
        await db_service.execute("DELETE FROM institutions WHERE name LIKE '%Sample%' OR name IN (SELECT unnest(%(names)s))", 
                                {"names": [inst["name"] for inst in sample_institutions]})
        
        for institution in sample_institutions:
            institution_id = str(uuid.uuid4())
            institution["id"] = institution_id
            institution["institution_types"] = json.dumps(institution["institution_types"])
            
            await db_service.execute("""
                INSERT INTO institutions (id, name, ipeds_id, ope_id, state, city, zip_code,
                                        institution_types, control, sector, total_enrollment,
                                        undergraduate_enrollment, graduate_enrollment, website,
                                        primary_contact_email, phone, is_active)
                VALUES (%(id)s, %(name)s, %(ipeds_id)s, %(ope_id)s, %(state)s, %(city)s, %(zip_code)s,
                        %(institution_types)s, %(control)s, %(sector)s, %(total_enrollment)s,
                        %(undergraduate_enrollment)s, %(graduate_enrollment)s, %(website)s,
                        %(primary_contact_email)s, %(phone)s, true)
            """, institution)
            
            # Create sample evidence for each institution
            await create_sample_evidence(db_service, institution_id, institution["name"])
            
            print(f"✅ Seeded {institution['name']}")
        
        print(f"🎉 Successfully seeded {len(sample_institutions)} sample institutions")
        
    finally:
        await db_service.close()


async def create_sample_evidence(db_service: DatabaseService, institution_id: str, institution_name: str):
    """Create sample evidence for an institution"""
    
    evidence_items = [
        {
            "title": f"{institution_name} Strategic Plan 2024-2029",
            "description": "Five-year strategic plan outlining mission, goals, and institutional priorities",
            "evidence_type": "document",
            "source_system": "SharePoint",
            "extracted_text": f"""
            {institution_name} Strategic Plan 2024-2029
            
            MISSION STATEMENT
            {institution_name} is committed to providing high-quality education that prepares students
            for successful careers and lifelong learning. We foster innovation, critical thinking, and
            community engagement while maintaining the highest standards of academic excellence.
            
            VISION
            To be recognized as a leading institution that transforms lives through exceptional education,
            research, and community partnership.
            
            STRATEGIC GOALS
            1. Enhance Student Success and Learning Outcomes
            2. Strengthen Academic Excellence and Innovation
            3. Foster Community Engagement and Partnerships
            4. Ensure Financial Sustainability and Resource Optimization
            5. Promote Diversity, Equity, and Inclusion
            """,
            "keywords": ["mission", "strategic plan", "goals", "vision", "student success"],
            "confidence_score": 0.95
        },
        {
            "title": "Board of Trustees Meeting Minutes - Mission Approval",
            "description": "Board minutes documenting approval of institutional mission statement",
            "evidence_type": "document",
            "source_system": "BoardDocs",
            "extracted_text": f"""
            {institution_name} Board of Trustees
            Regular Meeting Minutes - March 15, 2024
            
            AGENDA ITEM 7: Mission Statement Review and Approval
            
            Motion: Trustee Johnson moved to approve the revised mission statement as presented
            by the President. The mission statement reflects our commitment to student success,
            academic excellence, and community engagement.
            
            Discussion: Trustees discussed the alignment of the mission with institutional goals
            and the importance of maintaining our commitment to quality education.
            
            Vote: Motion carried unanimously (8-0)
            
            The approved mission statement will be published in all institutional materials
            and prominently displayed on the website.
            """,
            "keywords": ["board", "trustees", "mission", "approval", "governance"],
            "confidence_score": 0.92
        },
        {
            "title": "Faculty Handbook 2024-2025",
            "description": "Comprehensive handbook outlining faculty policies, procedures, and expectations",
            "evidence_type": "policy",
            "source_system": "HR Portal",
            "extracted_text": f"""
            {institution_name} Faculty Handbook 2024-2025
            
            FACULTY QUALIFICATIONS
            All faculty members must possess appropriate credentials for their teaching assignments.
            Minimum qualifications include:
            - Master's degree in the teaching discipline or related field
            - Demonstrated teaching excellence
            - Professional experience relevant to the field
            
            TENURE AND PROMOTION
            The institution maintains a rigorous tenure and promotion process that evaluates
            faculty on teaching effectiveness, scholarly activity, and service to the institution
            and profession.
            
            PROFESSIONAL DEVELOPMENT
            The institution supports faculty development through conference attendance,
            sabbatical leave, and research support funding.
            """,
            "keywords": ["faculty", "qualifications", "tenure", "promotion", "development"],
            "confidence_score": 0.88
        },
        {
            "title": "Student Learning Assessment Report 2023-2024",
            "description": "Annual report on student learning outcomes assessment across all programs",
            "evidence_type": "assessment",
            "source_system": "Assessment Database",
            "extracted_text": f"""
            {institution_name} Student Learning Assessment Report 2023-2024
            
            EXECUTIVE SUMMARY
            This report summarizes assessment activities and results for the 2023-2024 academic year.
            Assessment data demonstrate strong student achievement across all measured learning outcomes.
            
            KEY FINDINGS
            - 89% of students met or exceeded expectations on critical thinking assessments
            - 92% demonstrated proficiency in written communication
            - 85% achieved program-specific learning outcomes
            
            AREAS FOR IMPROVEMENT
            - Quantitative reasoning skills need additional support
            - Diversity and inclusion awareness could be strengthened
            
            CONTINUOUS IMPROVEMENT ACTIONS
            - Implement supplemental math support programs
            - Enhance diversity curriculum requirements
            - Expand assessment training for faculty
            """,
            "keywords": ["assessment", "learning outcomes", "student achievement", "continuous improvement"],
            "confidence_score": 0.90
        },
        {
            "title": "Financial Audit Report 2023",
            "description": "Independent audit of institutional finances and fiscal management",
            "evidence_type": "financial",
            "source_system": "Finance Office",
            "extracted_text": f"""
            Independent Auditor's Report
            {institution_name} - Fiscal Year 2023
            
            OPINION
            In our opinion, the financial statements present fairly, in all material respects,
            the financial position of {institution_name} as of June 30, 2023.
            
            FINANCIAL HIGHLIGHTS
            - Total assets: $125.3 million
            - Net assets without donor restrictions: $78.2 million
            - Operating revenues exceeded expenses by $2.1 million
            - Debt-to-asset ratio: 0.23 (well within policy limits)
            
            MANAGEMENT RECOMMENDATIONS
            - Continue monitoring enrollment trends
            - Enhance endowment growth strategies
            - Maintain strong internal controls
            """,
            "keywords": ["financial", "audit", "assets", "revenues", "fiscal management"],
            "confidence_score": 0.87
        }
    ]
    
    for evidence in evidence_items:
        evidence_id = str(uuid.uuid4())
        evidence["id"] = evidence_id
        evidence["institution_id"] = institution_id
        evidence["processing_status"] = "completed"
        evidence["evidence_date"] = datetime.utcnow() - timedelta(days=30)
        evidence["academic_year"] = "2023-24"
        evidence["keywords"] = json.dumps(evidence["keywords"])
        
        await db_service.execute("""
            INSERT INTO evidence (id, institution_id, title, description, evidence_type,
                                source_system, extracted_text, keywords, processing_status,
                                evidence_date, academic_year, confidence_score, relevance_score)
            VALUES (%(id)s, %(institution_id)s, %(title)s, %(description)s, %(evidence_type)s,
                    %(source_system)s, %(extracted_text)s, %(keywords)s, %(processing_status)s,
                    %(evidence_date)s, %(academic_year)s, %(confidence_score)s, 0.85)
        """, evidence)


async def create_sample_workflows():
    """Create sample agent workflows for demonstration"""
    print("🤖 Creating sample agent workflows...")
    
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    
    try:
        # Get a sample institution
        institutions = await db_service.fetch_all("SELECT * FROM institutions LIMIT 1")
        if not institutions:
            print("⚠️ No institutions found. Please run seed_sample_institutions first.")
            return
        
        institution = institutions[0]
        
        # Create sample workflow
        workflow_data = {
            "id": str(uuid.uuid4()),
            "institution_id": institution["id"],
            "workflow_type": "mapping",
            "accreditor_id": "msche",
            "status": "completed",
            "current_agent": "verifier",
            "round_number": 2,
            "max_rounds": 3,
            "agent_config": json.dumps({
                "mapper": {"temperature": 0.1, "max_tokens": 4096},
                "gap_finder": {"temperature": 0.1, "max_tokens": 4096},
                "narrator": {"temperature": 0.2, "max_tokens": 4096},
                "verifier": {"temperature": 0.1, "max_tokens": 4096}
            }),
            "llm_model": "anthropic.claude-3-sonnet-20240229-v1:0",
            "temperature": 0.1,
            "output_data": json.dumps({
                "mapping": {
                    "total_evidence": 5,
                    "mapped_evidence": 4,
                    "unmapped_evidence": 1,
                    "overall_confidence": 0.87
                },
                "gap_analysis": {
                    "total_standards": 8,
                    "red_gaps": 1,
                    "amber_gaps": 2,
                    "green_compliant": 5
                },
                "narratives_generated": 5,
                "verification_passed": True
            }),
            "execution_time_seconds": 145.3,
            "token_usage": json.dumps({
                "total_tokens": 8750,
                "prompt_tokens": 6200,
                "completion_tokens": 2550
            }),
            "cost_estimate": 0.75,
            "started_at": datetime.utcnow() - timedelta(minutes=5),
            "completed_at": datetime.utcnow()
        }
        
        await db_service.execute("""
            INSERT INTO agent_workflows (id, institution_id, workflow_type, accreditor_id,
                                       status, current_agent, round_number, max_rounds,
                                       agent_config, llm_model, temperature, output_data,
                                       execution_time_seconds, token_usage, cost_estimate,
                                       started_at, completed_at)
            VALUES (%(id)s, %(institution_id)s, %(workflow_type)s, %(accreditor_id)s,
                    %(status)s, %(current_agent)s, %(round_number)s, %(max_rounds)s,
                    %(agent_config)s, %(llm_model)s, %(temperature)s, %(output_data)s,
                    %(execution_time_seconds)s, %(token_usage)s, %(cost_estimate)s,
                    %(started_at)s, %(completed_at)s)
        """, workflow_data)
        
        print("✅ Created sample agent workflow")
        
    finally:
        await db_service.close()


async def main():
    """Main seeding function"""
    print("🌱 Starting A3E database seeding...")
    print(f"Environment: {settings.environment}")
    print(f"Database: {settings.database_url}")
    
    try:
        # Seed in order of dependencies
        await seed_accreditation_data()
        await seed_sample_institutions()
        await create_sample_workflows()
        
        print("\n🎉 Database seeding completed successfully!")
        print("\nSeeded data includes:")
        print(f"• {len(ALL_ACCREDITORS)} accrediting bodies with comprehensive standards")
        print("• 5 sample institutions representing different types")
        print("• Sample evidence documents for each institution")
        print("• Sample agent workflow results")
        print("\nYou can now start the A3E application with: make dev")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
