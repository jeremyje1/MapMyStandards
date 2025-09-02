"""
Database initialization endpoint for seeding accreditation standards
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

# Comprehensive accreditation standards data
ACCREDITORS_DATA = [
    {
        "accreditor_id": "sacscoc",
        "name": "Southern Association of Colleges and Schools Commission on Colleges",
        "acronym": "SACSCOC",
        "description": "Regional accreditor for degree-granting institutions in the Southern states",
        "website_url": "https://sacscoc.org"
    },
    {
        "accreditor_id": "hlc",
        "name": "Higher Learning Commission",
        "acronym": "HLC",
        "description": "Regional accreditor for degree-granting institutions in the North Central region",
        "website_url": "https://www.hlcommission.org"
    },
    {
        "accreditor_id": "msche",
        "name": "Middle States Commission on Higher Education",
        "acronym": "MSCHE",
        "description": "Regional accreditor for institutions in the Middle States region",
        "website_url": "https://www.msche.org"
    },
    {
        "accreditor_id": "neasc",
        "name": "New England Association of Schools and Colleges",
        "acronym": "NEASC",
        "description": "Regional accreditor for institutions in New England",
        "website_url": "https://www.neasc.org"
    },
    {
        "accreditor_id": "wasc",
        "name": "Western Association of Schools and Colleges",
        "acronym": "WASC",
        "description": "Regional accreditor for institutions in the Western region",
        "website_url": "https://www.wscuc.org"
    },
    {
        "accreditor_id": "nwccu",
        "name": "Northwest Commission on Colleges and Universities",
        "acronym": "NWCCU",
        "description": "Regional accreditor for institutions in the Northwest",
        "website_url": "https://www.nwccu.org"
    }
]

STANDARDS_DATA = {
    "sacscoc": [
        {"standard_id": "SACSCOC_1.1", "title": "Mission", "description": "The institution has a clearly defined mission statement", "category": "Institutional Mission"},
        {"standard_id": "SACSCOC_2.1", "title": "Degree Standards", "description": "Degree programs based on appropriate credit hours", "category": "Academic Programs"},
        {"standard_id": "SACSCOC_8.1", "title": "Faculty", "description": "Sufficient qualified faculty to support the mission", "category": "Faculty"},
        {"standard_id": "SACSCOC_8.2a", "title": "Faculty Evaluation", "description": "Regular evaluation of faculty effectiveness", "category": "Faculty"},
        {"standard_id": "SACSCOC_9.1", "title": "Academic Support Services", "description": "Appropriate academic support services", "category": "Student Services"},
        {"standard_id": "SACSCOC_10.1", "title": "Financial Resources", "description": "Financial stability with capacity to support programs", "category": "Resources"},
        {"standard_id": "SACSCOC_11.1", "title": "Physical Resources", "description": "Physical resources support student learning", "category": "Resources"},
        {"standard_id": "SACSCOC_12.1", "title": "Institutional Effectiveness", "description": "Engages in ongoing evaluation and assessment", "category": "Assessment"}
    ],
    "hlc": [
        {"standard_id": "HLC_1.A", "title": "Mission", "description": "Mission is publicly articulated and operationalized", "category": "Mission"},
        {"standard_id": "HLC_1.B", "title": "Mission Articulation", "description": "Mission demonstrates commitment to public good", "category": "Mission"},
        {"standard_id": "HLC_2.A", "title": "Integrity", "description": "Operates with integrity in all relationships", "category": "Integrity"},
        {"standard_id": "HLC_3.A", "title": "Teaching and Learning Quality", "description": "Degree programs appropriate to higher education", "category": "Teaching & Learning"},
        {"standard_id": "HLC_3.B", "title": "General Education", "description": "General education imparts essential knowledge", "category": "Teaching & Learning"},
        {"standard_id": "HLC_4.A", "title": "Educational Quality", "description": "Demonstrates responsibility for quality of programs", "category": "Assessment"},
        {"standard_id": "HLC_4.B", "title": "Assessment of Student Learning", "description": "Ongoing assessment to improve student learning", "category": "Assessment"},
        {"standard_id": "HLC_5.A", "title": "Resources", "description": "Resource base supports educational programs", "category": "Resources"}
    ],
    "msche": [
        {"standard_id": "MSCHE_I", "title": "Mission and Goals", "description": "Clearly defined mission and goals", "category": "Mission"},
        {"standard_id": "MSCHE_II", "title": "Ethics and Integrity", "description": "Commitment to academic freedom and integrity", "category": "Ethics"},
        {"standard_id": "MSCHE_III", "title": "Student Learning Experience", "description": "Design and delivery of student experience", "category": "Students"},
        {"standard_id": "MSCHE_IV", "title": "Support of Student Experience", "description": "Support of the student experience", "category": "Student Support"},
        {"standard_id": "MSCHE_V", "title": "Educational Effectiveness", "description": "Assessment of educational effectiveness", "category": "Assessment"},
        {"standard_id": "MSCHE_VI", "title": "Planning and Resources", "description": "Planning, resources, and institutional improvement", "category": "Planning"},
        {"standard_id": "MSCHE_VII", "title": "Governance", "description": "Governance, leadership, and administration", "category": "Governance"}
    ],
    "neasc": [
        {"standard_id": "NEASC_1", "title": "Mission and Purposes", "description": "Clear institutional mission", "category": "Mission"},
        {"standard_id": "NEASC_2", "title": "Planning and Evaluation", "description": "Systematic planning and evaluation", "category": "Planning"},
        {"standard_id": "NEASC_3", "title": "Organization and Governance", "description": "Effective organizational structure", "category": "Governance"},
        {"standard_id": "NEASC_4", "title": "Academic Program", "description": "Quality academic programs", "category": "Academics"},
        {"standard_id": "NEASC_5", "title": "Students", "description": "Student admission and services", "category": "Students"},
        {"standard_id": "NEASC_6", "title": "Teaching and Learning", "description": "Faculty and teaching effectiveness", "category": "Teaching"},
        {"standard_id": "NEASC_7", "title": "Institutional Resources", "description": "Human, financial, and physical resources", "category": "Resources"},
        {"standard_id": "NEASC_8", "title": "Educational Effectiveness", "description": "Evidence of student learning", "category": "Assessment"}
    ],
    "wasc": [
        {"standard_id": "WASC_1", "title": "Institutional Purpose", "description": "Defining institutional purposes", "category": "Purpose"},
        {"standard_id": "WASC_2", "title": "Core Competencies", "description": "Achieving educational objectives", "category": "Education"},
        {"standard_id": "WASC_3", "title": "Resources and Structures", "description": "Developing and applying resources", "category": "Resources"},
        {"standard_id": "WASC_4", "title": "Quality Assurance", "description": "Creating organization committed to quality", "category": "Quality"}
    ],
    "nwccu": [
        {"standard_id": "NWCCU_1", "title": "Mission and Core Themes", "description": "Mission fulfillment and adaptation", "category": "Mission"},
        {"standard_id": "NWCCU_2", "title": "Resources and Capacity", "description": "Resources and organizational capacity", "category": "Resources"},
        {"standard_id": "NWCCU_3", "title": "Planning and Implementation", "description": "Institutional planning", "category": "Planning"},
        {"standard_id": "NWCCU_4", "title": "Effectiveness and Improvement", "description": "Effectiveness and improvement", "category": "Effectiveness"},
        {"standard_id": "NWCCU_5", "title": "Mission Fulfillment", "description": "Mission fulfillment and sustainability", "category": "Mission"}
    ]
}

@router.post("/init-database")
async def initialize_database(secret_key: str = None) -> Dict[str, Any]:
    """Initialize database with accreditation standards data"""
    
    # Simple security check
    expected_key = os.getenv("ADMIN_SECRET_KEY", "mapmystandards-init-2024")
    if secret_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Create tables if they don't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS accreditors (
                    accreditor_id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    acronym VARCHAR NOT NULL,
                    description TEXT,
                    website_url VARCHAR,
                    standards_version VARCHAR DEFAULT '2024',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS standards (
                    standard_id VARCHAR PRIMARY KEY,
                    accreditor_id VARCHAR REFERENCES accreditors(accreditor_id),
                    title VARCHAR NOT NULL,
                    description TEXT,
                    category VARCHAR,
                    subcategory VARCHAR,
                    version VARCHAR DEFAULT '2024',
                    effective_date DATE DEFAULT CURRENT_DATE,
                    is_required BOOLEAN DEFAULT TRUE,
                    evidence_requirements TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
            
            # Insert accreditors
            inserted_accreditors = 0
            for acc in ACCREDITORS_DATA:
                try:
                    conn.execute(text("""
                        INSERT INTO accreditors (accreditor_id, name, acronym, description, website_url)
                        VALUES (:id, :name, :acronym, :description, :url)
                        ON CONFLICT (accreditor_id) DO UPDATE
                        SET name = EXCLUDED.name,
                            acronym = EXCLUDED.acronym,
                            description = EXCLUDED.description,
                            website_url = EXCLUDED.website_url,
                            updated_at = CURRENT_TIMESTAMP
                    """), {
                        "id": acc["accreditor_id"],
                        "name": acc["name"],
                        "acronym": acc["acronym"],
                        "description": acc["description"],
                        "url": acc["website_url"]
                    })
                    inserted_accreditors += 1
                except Exception as e:
                    logger.error(f"Error inserting accreditor {acc['acronym']}: {e}")
            
            conn.commit()
            
            # Insert standards
            inserted_standards = 0
            for acc_id, standards in STANDARDS_DATA.items():
                for std in standards:
                    try:
                        conn.execute(text("""
                            INSERT INTO standards (standard_id, accreditor_id, title, description, category)
                            VALUES (:id, :acc_id, :title, :description, :category)
                            ON CONFLICT (standard_id) DO UPDATE
                            SET title = EXCLUDED.title,
                                description = EXCLUDED.description,
                                category = EXCLUDED.category,
                                updated_at = CURRENT_TIMESTAMP
                        """), {
                            "id": std["standard_id"],
                            "acc_id": acc_id,
                            "title": std["title"],
                            "description": std["description"],
                            "category": std["category"]
                        })
                        inserted_standards += 1
                    except Exception as e:
                        logger.error(f"Error inserting standard {std['standard_id']}: {e}")
            
            conn.commit()
            
            # Get counts
            result = conn.execute(text("SELECT COUNT(*) FROM accreditors"))
            total_accreditors = result.scalar()
            
            result = conn.execute(text("SELECT COUNT(*) FROM standards"))
            total_standards = result.scalar()
            
            return {
                "success": True,
                "message": "Database initialized successfully",
                "data": {
                    "accreditors_inserted": inserted_accreditors,
                    "standards_inserted": inserted_standards,
                    "total_accreditors": total_accreditors,
                    "total_standards": total_standards
                }
            }
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

@router.get("/check-database")
async def check_database_status() -> Dict[str, Any]:
    """Check database status and content"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"error": "Database not configured"}
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            # Count accreditors
            accreditor_count = 0
            if 'accreditors' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM accreditors"))
                accreditor_count = result.scalar()
            
            # Count standards
            standards_count = 0
            if 'standards' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM standards"))
                standards_count = result.scalar()
            
            # Count users
            user_count = 0
            if 'users' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
            
            return {
                "database_connected": True,
                "tables": tables,
                "counts": {
                    "accreditors": accreditor_count,
                    "standards": standards_count,
                    "users": user_count
                },
                "needs_initialization": accreditor_count == 0 or standards_count == 0
            }
            
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }