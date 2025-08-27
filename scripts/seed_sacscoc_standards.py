#!/usr/bin/env python3
"""
Seed SACSCOC standards data for MapMyStandards trial
Creates the minimal working standards data to unblock the trial flow
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.a3e.services.database_service import DatabaseService
from src.a3e.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SACSCOC Core Standards (simplified for trial)
SACSCOC_STANDARDS = [
    {
        "standard_id": "SACSCOC_1_1",
        "accreditor_id": "sacscoc",
        "title": "Mission",
        "description": "The institution has a clearly defined mission statement that articulates the institution's purpose, student population served, and commitment to student learning and student achievement.",
        "category": "Institutional Mission and Effectiveness",
        "subcategory": "Mission Statement",
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Mission Statement", "Board Approval Documentation", "Strategic Plan"]
    },
    {
        "standard_id": "SACSCOC_2_1", 
        "accreditor_id": "sacscoc",
        "title": "Degree Standards",
        "description": "The institution offers one or more degree programs based on at least 60 semester credit hours or the equivalent at the baccalaureate level; at least 30 semester credit hours or the equivalent at the master's level.",
        "category": "Academic and Student Affairs",
        "subcategory": "Degree Requirements",
        "version": "2024",
        "effective_date": "2024-01-01", 
        "is_required": True,
        "evidence_requirements": ["Degree Program Documentation", "Credit Hour Requirements", "Catalog Pages"]
    },
    {
        "standard_id": "SACSCOC_8_1",
        "accreditor_id": "sacscoc",
        "title": "Faculty",
        "description": "The institution employs a sufficient number of qualified faculty to support the mission of the institution and the goals of the degree programs.",
        "category": "Faculty",
        "subcategory": "Faculty Qualifications",
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Faculty CVs", "Qualification Matrix", "Teaching Load Documentation"]
    },
    {
        "standard_id": "SACSCOC_8_2_A", 
        "accreditor_id": "sacscoc",
        "title": "Faculty Evaluation",
        "description": "The institution regularly evaluates the effectiveness of each faculty member in accord with published criteria, regardless of contractual or employment terms.",
        "category": "Faculty",
        "subcategory": "Faculty Development",
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Faculty Evaluation Process", "Evaluation Criteria", "Performance Reviews"]
    },
    {
        "standard_id": "SACSCOC_9_1",
        "accreditor_id": "sacscoc", 
        "title": "Academic Support Services",
        "description": "The institution provides appropriate academic support services.",
        "category": "Academic and Student Affairs",
        "subcategory": "Student Support",
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Academic Support Services Documentation", "Tutoring Programs", "Advising Services"]
    },
    {
        "standard_id": "SACSCOC_10_1",
        "accreditor_id": "sacscoc",
        "title": "Financial Resources",  
        "description": "The institution's recent financial history demonstrates financial stability with the capacity to support its programs and services.",
        "category": "Financial Resources",
        "subcategory": "Financial Stability",
        "version": "2024", 
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Audited Financial Statements", "Budget Documentation", "Revenue Analysis"]
    },
    {
        "standard_id": "SACSCOC_11_1",
        "accreditor_id": "sacscoc",
        "title": "Physical Resources",
        "description": "The institution's physical resources support student learning and the effective delivery of programs and services.",
        "category": "Physical Resources", 
        "subcategory": "Facilities",
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Facilities Master Plan", "Campus Maps", "Safety Documentation"]
    },
    {
        "standard_id": "SACSCOC_12_1",
        "accreditor_id": "sacscoc",
        "title": "Resource Development",
        "description": "The institution has a sound financial base and demonstrated financial stability to support the mission of the institution and the scope of its programs and services.",
        "category": "Financial Resources",
        "subcategory": "Resource Development", 
        "version": "2024",
        "effective_date": "2024-01-01",
        "is_required": True,
        "evidence_requirements": ["Fundraising Documentation", "Grant Records", "Endowment Reports"]
    }
]

async def seed_standards():
    """Seed the database with SACSCOC standards"""
    try:
        # Initialize database service
        db_service = DatabaseService(settings.database_url)
        await db_service.initialize()
        
        logger.info("🌱 Starting SACSCOC standards seeding...")
        
        # Create standards table if it doesn't exist
        await db_service.create_tables()
        
        # Insert standards
        standards_created = 0
        for standard_data in SACSCOC_STANDARDS:
            try:
                # Convert date string to datetime
                standard_data_copy = standard_data.copy()
                standard_data_copy['effective_date'] = datetime.fromisoformat(standard_data['effective_date'])
                
                await db_service.create_standard(standard_data_copy)
                standards_created += 1
                logger.info(f"✅ Created standard: {standard_data['standard_id']} - {standard_data['title']}")
                
            except Exception as e:
                if "already exists" in str(e).lower() or "unique constraint" in str(e).lower():
                    logger.info(f"⏭️  Standard {standard_data['standard_id']} already exists, skipping")
                else:
                    logger.error(f"❌ Failed to create standard {standard_data['standard_id']}: {e}")
        
        logger.info(f"🎉 Seeding complete! Created {standards_created} new standards")
        
        # Verify seeding worked
        all_standards = await db_service.list_standards(accreditor_id="sacscoc", limit=100)
        logger.info(f"📊 Total SACSCOC standards in database: {len(all_standards)}")
        
        await db_service.close()
        
    except Exception as e:
        logger.error(f"💥 Seeding failed: {e}")
        raise

async def verify_seed():
    """Verify that standards were seeded correctly"""
    try:
        db_service = DatabaseService(settings.database_url) 
        await db_service.initialize()
        
        standards = await db_service.list_standards(accreditor_id="sacscoc", limit=100)
        
        print(f"\n📋 SACSCOC Standards Verification:")
        print(f"   Total Standards: {len(standards)}")
        
        for standard in standards[:5]:  # Show first 5
            print(f"   ✓ {standard.standard_id}: {standard.title}")
        
        if len(standards) > 5:
            print(f"   ... and {len(standards) - 5} more")
        
        await db_service.close()
        return len(standards) > 0
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 MapMyStandards SACSCOC Standards Seeder")
    print("=========================================")
    
    # Seed standards
    asyncio.run(seed_standards())
    
    # Verify seeding 
    print("\n🔍 Verifying seed data...")
    success = asyncio.run(verify_seed())
    
    if success:
        print("\n✅ SUCCESS: Standards seeded and verified!")
        print("👉 You can now test /api/standards?accreditor=SACSCOC")
    else:
        print("\n❌ FAILED: Standards seeding unsuccessful")
        sys.exit(1)