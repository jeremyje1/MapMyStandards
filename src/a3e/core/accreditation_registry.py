"""
Comprehensive US Accreditation Bodies and Standards Configuration

This module contains the complete mapping of US accrediting bodies,
their standards, and institution type contexts.

Sources: CHEA Database, USDE Recognition, Regional & National Accreditors
Last Updated: July 2025
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


class InstitutionType(Enum):
    """Institution types recognized by US accreditors"""
    COMMUNITY_COLLEGE = "community_college"
    FOUR_YEAR_COLLEGE = "four_year_college"
    UNIVERSITY = "university"
    RESEARCH_UNIVERSITY = "research_university"
    GRADUATE_SCHOOL = "graduate_school"
    PROFESSIONAL_SCHOOL = "professional_school"
    SPECIALIZED_INSTITUTION = "specialized_institution"
    THEOLOGICAL_SEMINARY = "theological_seminary"
    MILITARY_ACADEMY = "military_academy"
    ONLINE_INSTITUTION = "online_institution"
    FOR_PROFIT = "for_profit"
    NON_PROFIT = "non_profit"
    PUBLIC = "public"
    PRIVATE = "private"
    # K-12 institutions
    K12_SCHOOL = "k12_school"
    SCHOOL_DISTRICT = "school_district"


class AccreditorType(Enum):
    """Types of accrediting bodies"""
    REGIONAL = "regional"
    NATIONAL = "national"
    PROGRAMMATIC = "programmatic"
    SPECIALIZED = "specialized"


@dataclass
class Standard:
    """Individual accreditation standard"""
    id: str
    title: str
    description: str
    evidence_requirements: List[str]
    applicable_institution_types: Set[InstitutionType]
    weight: float = 1.0  # Relative importance
    sub_standards: Optional[List['Standard']] = None


@dataclass
class AccreditingBody:
    """US Accrediting Body with full context"""
    id: str
    name: str
    acronym: str
    type: AccreditorType
    recognition_authority: str  # USDE, CHEA, or Both
    geographic_scope: List[str]  # States or "National"
    applicable_institution_types: Set[InstitutionType]
    standards: List[Standard]
    website: str
    last_updated: str


# Regional Accreditors (The "Big 7")
REGIONAL_ACCREDITORS = {
    "neche": AccreditingBody(
        id="neche",
        name="New England Commission of Higher Education",
        acronym="NECHE",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["CT", "ME", "MA", "NH", "RI", "VT"],
        applicable_institution_types={
            InstitutionType.COMMUNITY_COLLEGE,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.UNIVERSITY,
            InstitutionType.RESEARCH_UNIVERSITY,
            InstitutionType.GRADUATE_SCHOOL,
        },
        standards=[
            Standard(
                id="neche_1",
                title="Mission and Purposes",
                description="The institution's mission and purposes are appropriate to higher education, clearly stated, and published.",
                evidence_requirements=[
                    "Mission statement",
                    "Strategic plan",
                    "Board minutes approving mission",
                    "Publication of mission in catalogs/website"
                ],
                applicable_institution_types={InstitutionType.COMMUNITY_COLLEGE, InstitutionType.FOUR_YEAR_COLLEGE}
            ),
            Standard(
                id="neche_2",
                title="Planning and Evaluation",
                description="The institution undertakes planning and evaluation to accomplish and improve the achievement of its mission and purposes.",
                evidence_requirements=[
                    "Strategic planning documents",
                    "Assessment reports",
                    "Institutional effectiveness data",
                    "Continuous improvement plans"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            # ... Additional NECHE standards would continue here
        ],
        website="https://www.neche.org",
        last_updated="2025-01-01"
    ),
    
    "msche": AccreditingBody(
        id="msche",
        name="Middle States Commission on Higher Education",
        acronym="MSCHE",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["DE", "MD", "NJ", "NY", "PA", "DC", "PR", "VI"],
        applicable_institution_types=set(InstitutionType),
        standards=[
            Standard(
                id="msche_1",
                title="Mission and Goals",
                description="The institution's mission defines its purpose within the context of higher education and indicates who the institution serves and what it intends to accomplish.",
                evidence_requirements=[
                    "Mission statement documentation",
                    "Strategic goals alignment",
                    "Stakeholder communication evidence",
                    "Mission review processes"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            Standard(
                id="msche_2", 
                title="Ethics and Integrity",
                description="Ethics and integrity are central, indispensable, and defining hallmarks of effective higher education institutions.",
                evidence_requirements=[
                    "Code of ethics/conduct",
                    "Conflict of interest policies",
                    "Academic integrity policies",
                    "Financial transparency reports"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            # ... Additional MSCHE standards
        ],
        website="https://www.msche.org",
        last_updated="2025-01-01"
    ),
    
    "sacscoc": AccreditingBody(
        id="sacscoc",
        name="Southern Association of Colleges and Schools Commission on Colleges",
        acronym="SACSCOC",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["AL", "FL", "GA", "KY", "LA", "MS", "NC", "SC", "TN", "TX", "VA"],
        applicable_institution_types=set(InstitutionType),
        standards=[
            Standard(
                id="sacscoc_1_1",
                title="Mission Statement",
                description="The institution has a clearly defined, comprehensive, and published mission statement.",
                evidence_requirements=[
                    "Published mission statement",
                    "Board approval documentation",
                    "Mission dissemination evidence",
                    "Periodic mission review records"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            # ... Additional SACSCOC Principles and Standards
        ],
        website="https://www.sacscoc.org",
        last_updated="2025-01-01"
    ),
    
    "hlc": AccreditingBody(
        id="hlc",
        name="Higher Learning Commission",
        acronym="HLC",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["AZ", "AR", "CO", "IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "NM", "ND", "OH", "OK", "SD", "WV", "WI", "WY"],
        applicable_institution_types=set(InstitutionType),
        standards=[
            Standard(
                id="hlc_1",
                title="Mission",
                description="The institution's mission is clear and articulated publicly.",
                evidence_requirements=[
                    "Mission statement",
                    "Public accessibility documentation", 
                    "Stakeholder understanding evidence",
                    "Mission-activity alignment"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            # ... Additional HLC Criteria
        ],
        website="https://www.hlcommission.org",
        last_updated="2025-01-01"
    ),
    
    "nwccu": AccreditingBody(
        id="nwccu", 
        name="Northwest Commission on Colleges and Universities",
        acronym="NWCCU",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["AK", "ID", "MT", "NV", "OR", "UT", "WA"],
        applicable_institution_types=set(InstitutionType),
        standards=[
            Standard(
                id="nwccu_1_a_1",
                title="Mission Fulfillment",
                description="The institution defines mission fulfillment in the context of its purpose, characteristics, and expectations.",
                evidence_requirements=[
                    "Mission fulfillment definition",
                    "Institutional characteristics documentation",
                    "Success indicators and metrics",
                    "Assessment methodologies"
                ],
                applicable_institution_types=set(InstitutionType)
            ),
            # ... Additional NWCCU Standards
        ],
        website="https://www.nwccu.org",
        last_updated="2025-01-01"
    ),
    
    "wscuc": AccreditingBody(
        id="wscuc",
        name="WASC Senior College and University Commission", 
        acronym="WSCUC",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE",
        geographic_scope=["CA", "HI", "Territory of Guam", "Commonwealth of the Northern Mariana Islands"],
        applicable_institution_types={
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.UNIVERSITY,
            InstitutionType.RESEARCH_UNIVERSITY,
            InstitutionType.GRADUATE_SCHOOL,
        },
        standards=[
            Standard(
                id="wscuc_1",
                title="Defining Institutional Purposes and Ensuring Educational Objectives",
                description="The institution defines its purposes and establishes educational objectives aligned with those purposes.",
                evidence_requirements=[
                    "Institutional purposes documentation",
                    "Educational objectives alignment",
                    "Stakeholder involvement evidence",
                    "Regular review processes"
                ],
                applicable_institution_types={InstitutionType.FOUR_YEAR_COLLEGE, InstitutionType.UNIVERSITY}
            ),
            # ... Additional WSCUC Standards
        ],
        website="https://www.wscuc.org",
        last_updated="2025-01-01"
    ),
    
    "accjc": AccreditingBody(
        id="accjc",
        name="Accrediting Commission for Community and Junior Colleges",
        acronym="ACCJC",
        type=AccreditorType.REGIONAL,
        recognition_authority="USDE", 
        geographic_scope=["CA", "HI", "Territory of Guam", "Commonwealth of the Northern Mariana Islands", "Republic of Palau", "Federated States of Micronesia", "Republic of the Marshall Islands", "American Samoa"],
        applicable_institution_types={InstitutionType.COMMUNITY_COLLEGE},
        standards=[
            Standard(
                id="accjc_1_a",
                title="Mission",
                description="The mission describes the institution's broad educational purposes, its intended student population, the types of degrees and other credentials it offers, and its commitment to student learning and student achievement.",
                evidence_requirements=[
                    "Published mission statement",
                    "Student population definition",
                    "Degree/credential offerings",
                    "Student learning commitment evidence"
                ],
                applicable_institution_types={InstitutionType.COMMUNITY_COLLEGE}
            ),
            # ... Additional ACCJC Standards
        ],
        website="https://www.accjc.org",
        last_updated="2025-01-01"
    )
}

# National/Faith-Based Accreditors
NATIONAL_ACCREDITORS = {
    "abhe": AccreditingBody(
        id="abhe",
        name="Association for Biblical Higher Education",
        acronym="ABHE", 
        type=AccreditorType.NATIONAL,
        recognition_authority="USDE",
        geographic_scope=["National"],
        applicable_institution_types={
            InstitutionType.THEOLOGICAL_SEMINARY,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.SPECIALIZED_INSTITUTION
        },
        standards=[
            Standard(
                id="abhe_1",
                title="Mission and Objectives",
                description="The institution has a clearly defined mission that is biblical, appropriate, and published.",
                evidence_requirements=[
                    "Biblical foundation documentation",
                    "Mission statement alignment",
                    "Educational objectives",
                    "Publication evidence"
                ],
                applicable_institution_types={InstitutionType.THEOLOGICAL_SEMINARY}
            ),
        ],
        website="https://www.abhe.org",
        last_updated="2025-01-01"
    ),
    
    "deac": AccreditingBody(
        id="deac",
        name="Distance Education Accrediting Commission",
        acronym="DEAC",
        type=AccreditorType.NATIONAL,
        recognition_authority="USDE",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.ONLINE_INSTITUTION,
            InstitutionType.SPECIALIZED_INSTITUTION,
            InstitutionType.FOR_PROFIT
        },
        standards=[
            Standard(
                id="deac_1",
                title="Mission and Objectives",
                description="The institution has a mission that is clearly defined, appropriate to distance education, and published.",
                evidence_requirements=[
                    "Distance education mission alignment",
                    "Stakeholder accessibility",
                    "Mission-practice consistency",
                    "Regular mission review"
                ],
                applicable_institution_types={InstitutionType.ONLINE_INSTITUTION}
            ),
        ],
        website="https://www.deac.org", 
        last_updated="2025-01-01"
    ),
    # K-12 accreditors
    "cognia": AccreditingBody(
        id="cognia",
        name="Cognia",
        acronym="COGNIA",
        type=AccreditorType.NATIONAL,
        recognition_authority="Independent/State Systems",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.K12_SCHOOL,
            InstitutionType.SCHOOL_DISTRICT
        },
        standards=[
            Standard(
                id="cognia_1",
                title="Leadership and Governance",
                description="School/district leadership establishes vision, ethical governance, and continuous improvement structures that advance student learning.",
                evidence_requirements=[
                    "Board policies and bylaws",
                    "Strategic/continuous improvement plans",
                    "Stakeholder engagement artifacts",
                    "Monitoring and evaluation reports"
                ],
                applicable_institution_types={InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT}
            ),
            Standard(
                id="cognia_2",
                title="Teaching and Learning",
                description="Instructional practices are coherent, standards-aligned, and supported by assessment to ensure student growth and achievement.",
                evidence_requirements=[
                    "Curriculum maps and pacing guides",
                    "Assessment frameworks and data",
                    "Instructional walkthroughs/observations",
                    "Intervention/MTSS documentation"
                ],
                applicable_institution_types={InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT}
            ),
        ],
        website="https://www.cognia.org",
        last_updated="2025-01-01"
    ),
    "sacs_casi": AccreditingBody(
        id="sacs_casi",
        name="SACS Council on Accreditation and School Improvement",
        acronym="SACS-CASI",
        type=AccreditorType.NATIONAL,
        recognition_authority="Independent/State Systems",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.K12_SCHOOL,
            InstitutionType.SCHOOL_DISTRICT
        },
        standards=[
            Standard(
                id="sacs_casi_1",
                title="Culture of Learning",
                description="The school maintains a safe, inclusive, and student-centered culture that supports learning and well-being.",
                evidence_requirements=[
                    "School climate/safety plans",
                    "Student support services documentation",
                    "Family/community engagement evidence",
                    "Equity and access initiatives"
                ],
                applicable_institution_types={InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT}
            ),
        ],
        website="https://www.cognia.org",
        last_updated="2025-01-01"
    ),
    "nca_casi": AccreditingBody(
        id="nca_casi",
        name="North Central Association Commission on Accreditation and School Improvement",
        acronym="NCA-CASI",
        type=AccreditorType.NATIONAL,
        recognition_authority="Independent/State Systems",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.K12_SCHOOL,
            InstitutionType.SCHOOL_DISTRICT
        },
        standards=[
            Standard(
                id="nca_casi_1",
                title="Improvement Planning and Results",
                description="The institution implements data-informed improvement planning and regularly evaluates impact on student outcomes.",
                evidence_requirements=[
                    "School improvement plans",
                    "Balanced assessment data reports",
                    "Program evaluation summaries",
                    "Public reporting of progress"
                ],
                applicable_institution_types={InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT}
            ),
        ],
        website="https://www.cognia.org",
        last_updated="2025-01-01"
    ),
    "msa_cess": AccreditingBody(
        id="msa_cess",
        name="Middle States Association Commissions on Elementary and Secondary Schools",
        acronym="MSA-CESS",
        type=AccreditorType.NATIONAL,
        recognition_authority="Independent/State Systems",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.K12_SCHOOL,
            InstitutionType.SCHOOL_DISTRICT
        },
        standards=[
            Standard(
                id="msa_cess_1",
                title="Governance, Leadership, and Organizational Capacity",
                description="The institution’s governance and leadership provide direction, ensure resources, and support achievement of educational goals.",
                evidence_requirements=[
                    "Governing body roles and minutes",
                    "Resource allocation and budgeting",
                    "Professional development plans",
                    "Compliance and policy frameworks"
                ],
                applicable_institution_types={InstitutionType.K12_SCHOOL, InstitutionType.SCHOOL_DISTRICT}
            ),
        ],
        website="https://www.msa-cess.org",
        last_updated="2025-01-01"
    ),
}

# Programmatic/Specialized Accreditors (Major ones)
PROGRAMMATIC_ACCREDITORS = {
    "aacsb": AccreditingBody(
        id="aacsb",
        name="Association to Advance Collegiate Schools of Business",
        acronym="AACSB",
        type=AccreditorType.PROGRAMMATIC,
        recognition_authority="CHEA",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.UNIVERSITY,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.GRADUATE_SCHOOL
        },
        standards=[
            Standard(
                id="aacsb_1",
                title="Mission, Impact, and Innovation",
                description="The business school demonstrates impact and innovation that is meaningful and sustainable for its stakeholders through teaching, research, and service.",
                evidence_requirements=[
                    "Impact measurement framework",
                    "Innovation documentation",
                    "Stakeholder engagement evidence",
                    "Sustainability planning"
                ],
                applicable_institution_types={InstitutionType.UNIVERSITY, InstitutionType.GRADUATE_SCHOOL}
            ),
            Standard(
                id="aacsb_2", 
                title="Strategic Planning",
                description="The business school demonstrates strategic thinking and planning for continuous improvement and long-term sustainability.",
                evidence_requirements=[
                    "Strategic plan documentation",
                    "Environmental scanning",
                    "Stakeholder input processes",
                    "Implementation tracking"
                ],
                applicable_institution_types={InstitutionType.UNIVERSITY, InstitutionType.GRADUATE_SCHOOL}
            ),
        ],
        website="https://www.aacsb.edu",
        last_updated="2025-01-01"
    ),
    
    "abet": AccreditingBody(
        id="abet",
        name="ABET (Accreditation Board for Engineering and Technology)",
        acronym="ABET",
        type=AccreditorType.PROGRAMMATIC,
        recognition_authority="CHEA",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.UNIVERSITY,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.COMMUNITY_COLLEGE
        },
        standards=[
            Standard(
                id="abet_1",
                title="Students",
                description="Student performance must be evaluated. Student progress must be monitored to foster success.",
                evidence_requirements=[
                    "Student performance data",
                    "Progress monitoring systems",
                    "Success metrics tracking",
                    "Intervention strategies"
                ],
                applicable_institution_types={InstitutionType.UNIVERSITY, InstitutionType.FOUR_YEAR_COLLEGE}
            ),
        ],
        website="https://www.abet.org",
        last_updated="2025-01-01"
    ),
    
    "ccne": AccreditingBody(
        id="ccne",
        name="Commission on Collegiate Nursing Education",
        acronym="CCNE",
        type=AccreditorType.PROGRAMMATIC,
        recognition_authority="CHEA",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.UNIVERSITY,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.GRADUATE_SCHOOL
        },
        standards=[
            Standard(
                id="ccne_1",
                title="Mission and Governance",
                description="The nursing program has a mission consistent with that of the parent institution and with professional nursing standards, and the governance structure supports achievement of program outcomes.",
                evidence_requirements=[
                    "Program mission and alignment",
                    "Governance policies",
                    "Faculty bylaws",
                    "Outcomes assessment reports"
                ],
                applicable_institution_types={InstitutionType.UNIVERSITY, InstitutionType.GRADUATE_SCHOOL}
            ),
        ],
        website="https://www.aacnnursing.org/CCNE",
        last_updated="2025-01-01"
    ),
    
    "caep": AccreditingBody(
        id="caep",
        name="Council for the Accreditation of Educator Preparation",
        acronym="CAEP",
        type=AccreditorType.PROGRAMMATIC,
        recognition_authority="CHEA",
        geographic_scope=["National", "International"],
        applicable_institution_types={
            InstitutionType.UNIVERSITY,
            InstitutionType.FOUR_YEAR_COLLEGE,
            InstitutionType.GRADUATE_SCHOOL
        },
        standards=[
            Standard(
                id="caep_1",
                title="Content and Pedagogical Knowledge",
                description="Provider ensures candidates develop a deep understanding of content and pedagogy to support P-12 student learning.",
                evidence_requirements=[
                    "Program curriculum maps",
                    "Candidate assessment data",
                    "P-12 partnership MOUs",
                    "Licensure pass rates"
                ],
                applicable_institution_types={InstitutionType.UNIVERSITY, InstitutionType.FOUR_YEAR_COLLEGE}
            ),
        ],
        website="https://www.caepnet.org",
        last_updated="2025-01-01"
    ),
}

# Complete registry of all US accrediting bodies
ALL_ACCREDITORS = {
    **REGIONAL_ACCREDITORS,
    **NATIONAL_ACCREDITORS, 
    **PROGRAMMATIC_ACCREDITORS
}

def get_accreditors_by_institution_type(institution_type: InstitutionType) -> List[AccreditingBody]:
    """Get all accreditors applicable to a specific institution type"""
    return [
        accreditor for accreditor in ALL_ACCREDITORS.values()
        if institution_type in accreditor.applicable_institution_types
    ]

def get_accreditors_by_state(state: str) -> List[AccreditingBody]:
    """Get all accreditors that operate in a specific state"""
    return [
        accreditor for accreditor in ALL_ACCREDITORS.values()
        if state in accreditor.geographic_scope or "National" in accreditor.geographic_scope
    ]

def get_standards_by_accreditor_and_institution_type(
    accreditor_id: str, 
    institution_type: InstitutionType
) -> List[Standard]:
    """Get applicable standards for a specific accreditor and institution type"""
    accreditor = ALL_ACCREDITORS.get(accreditor_id)
    if not accreditor:
        return []
    
    return [
        standard for standard in accreditor.standards
        if institution_type in standard.applicable_institution_types
    ]


def get_accreditor_by_id(accreditor_id: str) -> Optional[AccreditingBody]:
    """Get an accreditor by its ID"""
    return ALL_ACCREDITORS.get(accreditor_id)


def list_all_accreditors() -> List[AccreditingBody]:
    """Get a list of all accreditors"""
    return list(ALL_ACCREDITORS.values())
