"""
Database connection and session management for Railway PostgreSQL
Production-ready async database connection with proper error handling
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncpg

from ..models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Production database manager with Railway PostgreSQL support"""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self._initialized = False
    
    def _get_database_url(self) -> tuple[str, str]:
        """Get database URLs from Railway environment"""
        # Railway provides DATABASE_URL automatically
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # Fallback for local development
            db_host = os.getenv('PGHOST', 'localhost')
            db_port = os.getenv('PGPORT', '5432')
            db_user = os.getenv('PGUSER', 'postgres')
            db_password = os.getenv('PGPASSWORD', 'postgres')
            db_name = os.getenv('PGDATABASE', 'mapmystandards')
            
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Create async URL for appropriate driver
        if database_url.startswith('postgresql://'):
            async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        elif database_url.startswith('sqlite:///'):
            async_database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        else:
            async_database_url = database_url
        
        return database_url, async_database_url
    
    async def initialize(self):
        """Initialize database connections and create tables"""
        if self._initialized:
            return
        
        try:
            sync_url, async_url = self._get_database_url()
            
            logger.info("Initializing database connections...")
            # Reduced logging - only show host info in development
            if os.getenv('DEBUG') == 'true':
                logger.info(f"Database host: {sync_url.split('@')[1].split('/')[0] if '@' in sync_url else 'unknown'}")
            
            # Synchronous engine for migrations and admin tasks
            self.engine = create_engine(
                sync_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv('DEBUG') == 'true'
            )
            
            # Async engine for FastAPI operations
            self.async_engine = create_async_engine(
                async_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv('DEBUG') == 'true'
            )
            
            # Session makers
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.AsyncSessionLocal = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            await self._create_tables()
            
            # Initialize default data
            await self._initialize_default_data()
            
            self._initialized = True
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        try:
            # Reduced logging - only log in debug mode or on first creation
            if os.getenv('DEBUG') == 'true' or not hasattr(self, '_tables_created'):
                logger.info("Creating database tables...")
            
            # Use sync engine for DDL operations (legacy tables only; AI tables managed via migrations)
            Base.metadata.create_all(bind=self.engine)
            
            if os.getenv('DEBUG') == 'true' or not hasattr(self, '_tables_created'):
                logger.info("✅ Database tables created")
                self._tables_created = True
            
        except Exception as e:
            logger.error(f"❌ Table creation failed: {e}")
            raise
    
    async def _initialize_default_data(self):
        """Initialize default accreditors and standards"""
        try:
            # Skip data initialization if already initialized to avoid recursion
            if hasattr(self, '_data_initialized') and self._data_initialized:
                return
            
            # Only log in debug mode to reduce noise
            if os.getenv('DEBUG') == 'true':
                logger.info("Initializing default data...")
            
            # Use AsyncSessionLocal directly to avoid recursion
            async with self.AsyncSessionLocal() as session:
                try:
                    # Check if SACSCOC already exists
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM accreditors WHERE accreditor_id = 'sacscoc'")
                    )
                    count = result.scalar()
                    
                    if count == 0:
                        if os.getenv('DEBUG') == 'true':
                            logger.info("Seeding SACSCOC data...")
                        await self._seed_sacscoc_data(session)
                        if os.getenv('DEBUG') == 'true':
                            logger.info("✅ SACSCOC data seeded")
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
            
            self._data_initialized = True
            
        except Exception as e:
            logger.error(f"❌ Default data initialization failed: {e}")
            # Don't raise - this is not critical for startup
    
    async def _seed_sacscoc_data(self, session: AsyncSession):
        """Seed SACSCOC accreditor and standards"""
        from ..models import Accreditor, Standard
        
        # Create SACSCOC accreditor
        accreditor = Accreditor(
            accreditor_id="sacscoc",
            name="Southern Association of Colleges and Schools Commission on Colleges",
            acronym="SACSCOC",
            description="Regional accreditor for degree-granting institutions in the Southern states",
            website_url="https://sacscoc.org",
            standards_version="2018"
        )
        session.add(accreditor)
        
        # SACSCOC Standards (from our mock data)
        standards_data = [
            {
                "standard_id": "sacscoc_1_1",
                "code": "1.1",
                "title": "Mission",
                "description": "The institution has a clearly defined mission statement that articulates the institution's purpose, student population served, and commitment to student learning and student achievement.",
                "category": "Institutional Mission and Effectiveness",
                "evidence_requirements": ["Mission Statement", "Board Approval Documentation", "Strategic Plan"],
                "weight": 100,
                "keywords": ["mission", "purpose", "student learning", "institutional effectiveness"]
            },
            {
                "standard_id": "sacscoc_2_1", 
                "code": "2.1",
                "title": "Degree Standards",
                "description": "The institution offers one or more degree programs based on at least 60 semester credit hours or the equivalent at the baccalaureate level; at least 30 semester credit hours or the equivalent at the master's level.",
                "category": "Academic and Student Affairs",
                "evidence_requirements": ["Degree Program Documentation", "Credit Hour Requirements", "Catalog Pages"],
                "weight": 100,
                "keywords": ["degree programs", "credit hours", "baccalaureate", "master's", "doctoral"]
            },
            {
                "standard_id": "sacscoc_8_1",
                "code": "8.1", 
                "title": "Faculty",
                "description": "The institution employs a sufficient number of qualified faculty to support the mission of the institution and the goals of the degree programs.",
                "category": "Faculty",
                "evidence_requirements": ["Faculty CVs", "Qualification Matrix", "Teaching Load Documentation"],
                "weight": 100,
                "keywords": ["faculty qualifications", "credentials", "teaching load", "professional experience"]
            },
            {
                "standard_id": "sacscoc_8_2_a",
                "code": "8.2.a",
                "title": "Faculty Evaluation", 
                "description": "The institution regularly evaluates the effectiveness of each faculty member in accord with published criteria, regardless of contractual or employment terms.",
                "category": "Faculty",
                "parent_id": "sacscoc_8_1",
                "evidence_requirements": ["Faculty Evaluation Process", "Evaluation Criteria", "Performance Reviews"],
                "weight": 90,
                "keywords": ["faculty evaluation", "effectiveness", "published criteria", "annual review"]
            },
            {
                "standard_id": "sacscoc_9_1",
                "code": "9.1",
                "title": "Academic Support Services", 
                "description": "The institution provides appropriate academic support services.",
                "category": "Academic and Student Affairs",
                "evidence_requirements": ["Academic Support Services Documentation", "Tutoring Programs", "Advising Services"],
                "weight": 85,
                "keywords": ["academic support", "tutoring", "writing center", "library services", "student success"]
            },
            {
                "standard_id": "sacscoc_10_1",
                "code": "10.1",
                "title": "Financial Resources",
                "description": "The institution's recent financial history demonstrates financial stability with the capacity to support its programs and services.",
                "category": "Financial Resources", 
                "evidence_requirements": ["Audited Financial Statements", "Budget Documentation", "Revenue Analysis"],
                "weight": 95,
                "keywords": ["financial stability", "audited statements", "budget", "revenue", "capacity to support programs"]
            },
            {
                "standard_id": "sacscoc_11_1",
                "code": "11.1",
                "title": "Physical Resources",
                "description": "The institution's physical resources support student learning and the effective delivery of programs and services.",
                "category": "Physical Resources",
                "evidence_requirements": ["Facilities Master Plan", "Campus Maps", "Safety Documentation"],
                "weight": 80,
                "keywords": ["physical resources", "facilities", "student learning support", "infrastructure", "safety"]
            },
            {
                "standard_id": "sacscoc_12_1",
                "code": "12.1", 
                "title": "Resource Development",
                "description": "The institution has a sound financial base and demonstrated financial stability to support the mission of the institution and the scope of its programs and services.",
                "category": "Financial Resources",
                "evidence_requirements": ["Fundraising Documentation", "Grant Records", "Endowment Reports"],
                "weight": 75,
                "keywords": ["resource development", "financial base", "stability", "mission support", "program scope"]
            }
        ]
        
        for std_data in standards_data:
            standard = Standard(
                accreditor_id="sacscoc",
                **std_data
            )
            session.add(standard)
        
        await session.commit()
        # Only log in debug mode to reduce noise
        if os.getenv('DEBUG') == 'true':
            logger.info(f"✅ Seeded {len(standards_data)} SACSCOC standards")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper cleanup"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_sync_session(self):
        """Get synchronous session for migrations and admin tasks"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_metrics(self) -> dict:
        """Get database metrics for monitoring"""
        try:
            async with self.get_session() as session:
                # Get table counts
                tables = ['users', 'files', 'jobs', 'reports', 'standards', 'standard_mappings']
                metrics = {}
                
                for table in tables:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    metrics[f"{table}_count"] = result.scalar()
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {}
    
    async def close(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.engine:
            self.engine.dispose()
        
        self._initialized = False
        logger.info("✅ Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()
