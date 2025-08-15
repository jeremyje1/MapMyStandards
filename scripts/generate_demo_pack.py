"""Generate MapMyStandards demo standards templates & evidence pack.

Creates JSON templates (with fresh importedAt timestamp), CSV demo data, and a zip
archive for quick import testing. Safe to run multiple times.
"""
from __future__ import annotations

import datetime as dt
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "examples" / "demo_pack"
DEMO_DIR.mkdir(parents=True, exist_ok=True)

timestamp = dt.datetime.now(dt.timezone.utc).isoformat()

def build_standards():
    sacs = {
        "metadata": {
            "key": "SACSCOC_2024_DEMO",
            "name": "SACSCOC Principles of Accreditation (Demo Subset)",
            "version": "2024.demo",
            "publisher": "SACSCOC (Demo subset for testing)",
            "importedAt": timestamp,
            "notes": "Paraphrased demo subset for testing MapMyStandards import. NOT official text."
        },
        "items": [
            {
                "code": "CR 1.1",
                "title": "Institutional Integrity (Core Requirement)",
                "description": "The institution operates with integrity and consistent ethical standards across governance, academics, and operations. (Paraphrased demo text)",
                "level": 1,
                "parent": None,
                "weight": 1.0,
                "evidenceExamples": [
                    "Board minutes referencing ethics policy review",
                    "Annual compliance attestation documents"
                ],
                "rubric": {
                    "levels": ["Insufficient", "Developing", "Meets", "Exceeds"],
                    "anchors": [
                        "Policies absent or not applied",
                        "Policies exist with inconsistent application",
                        "Policies exist and are consistently applied",
                        "Policies are exemplary and externally benchmarked"
                    ]
                }
            },
            {
                "code": "7.1",
                "title": "Institutional Planning",
                "description": "The institution engages in ongoing, comprehensive, and integrated planning processes. (Paraphrased demo text)",
                "level": 1,
                "parent": None,
                "weight": 1.0,
                "evidenceExamples": [
                    "Strategic plan with KPIs",
                    "Annual planning cycle calendar"
                ],
                "rubric": {"levels": ["Insufficient", "Developing", "Meets", "Exceeds"]}
            },
            {
                "code": "8.2.a",
                "title": "Student Achievement",
                "description": "The institution identifies, evaluates, and publishes goals and outcomes for student achievement. (Paraphrased demo text)",
                "level": 2,
                "parent": "7.1",
                "weight": 1.0,
                "evidenceExamples": [
                    "Student achievement dashboard or fact book",
                    "Program-level outcomes with thresholds"
                ],
                "rubric": {"levels": ["Insufficient", "Developing", "Meets", "Exceeds"]}
            },
            {
                "code": "9.1",
                "title": "Program Length",
                "description": "The institution ensures program length is appropriate to the degree level. (Paraphrased demo text)",
                "level": 1,
                "parent": None,
                "weight": 1.0
            },
            {
                "code": "10.4",
                "title": "Academic Governance",
                "description": "The institution demonstrates effective academic governance and faculty role in curriculum and assessment. (Paraphrased demo text)",
                "level": 1,
                "parent": None,
                "weight": 1.0
            }
        ]
    }
    nw = {
        "metadata": {
            "key": "NWCCU_2024_DEMO",
            "name": "NWCCU Standards (Demo Subset)",
            "version": "2024.demo",
            "publisher": "NWCCU (Demo subset for testing)",
            "importedAt": timestamp,
            "notes": "Paraphrased demo subset for testing MapMyStandards import. NOT official text."
        },
        "items": [
            {"code": "1.A", "title": "Mission", "description": "The institution articulates a clear mission and widely communicates it. (Paraphrased demo text)", "level": 1, "parent": None, "weight": 1.0},
            {"code": "1.B", "title": "Enhancement of Student Learning", "description": "The institution engages in ongoing planning and resource allocation to support learning. (Paraphrased demo text)", "level": 1, "parent": None, "weight": 1.0},
            {"code": "2.C", "title": "Educational Resources", "description": "Programs are supported by adequate faculty, facilities, and learning resources. (Paraphrased demo text)", "level": 1, "parent": None, "weight": 1.0},
            {"code": "2.C.1", "title": "Faculty Qualifications", "description": "Faculty are qualified to deliver and assess the curriculum. (Paraphrased demo text)", "level": 2, "parent": "2.C", "weight": 1.0}
        ]
    }
    (DEMO_DIR / "standards_SACSCOC_template.json").write_text(json.dumps(sacs, indent=2))
    (DEMO_DIR / "standards_NWCCU_template.json").write_text(json.dumps(nw, indent=2))

def ensure_csvs():
    positions = pd.DataFrame(
        [
            {
                "Position_ID": "P001",
                "Unit_ID": "U001",
                "Title": "Director of Accreditation",
                "FTE": 1.0,
                "Salary": 95000,
                "Benefits_%": 25,
                "Vacant_YN": "N",
            },
            {
                "Position_ID": "P002",
                "Unit_ID": "U001",
                "Title": "Assessment Coordinator",
                "FTE": 1.0,
                "Salary": 72000,
                "Benefits_%": 25,
                "Vacant_YN": "N",
            },
            {
                "Position_ID": "P003",
                "Unit_ID": "U002",
                "Title": "Institutional Research Analyst",
                "FTE": 1.0,
                "Salary": 78000,
                "Benefits_%": 25,
                "Vacant_YN": "N",
            },
            {
                "Position_ID": "P004",
                "Unit_ID": "U003",
                "Title": "Faculty Chair - General Education",
                "FTE": 0.5,
                "Salary": 60000,
                "Benefits_%": 25,
                "Vacant_YN": "N",
            },
            {
                "Position_ID": "P005",
                "Unit_ID": "U004",
                "Title": "Student Success Advisor",
                "FTE": 1.0,
                "Salary": 56000,
                "Benefits_%": 25,
                "Vacant_YN": "Y",
            },
        ]
    )
    org_units = pd.DataFrame(
        [
            {
                "Unit_ID": "U001",
                "Parent_ID": "",
                "Name": "Accreditation Office",
                "Type": "Department",
                "Location": "Main Campus",
            },
            {
                "Unit_ID": "U002",
                "Parent_ID": "U001",
                "Name": "Institutional Research",
                "Type": "Team",
                "Location": "Main Campus",
            },
            {
                "Unit_ID": "U003",
                "Parent_ID": "",
                "Name": "Academic Affairs",
                "Type": "Division",
                "Location": "Main Campus",
            },
            {
                "Unit_ID": "U004",
                "Parent_ID": "U003",
                "Name": "Student Success",
                "Type": "Department",
                "Location": "Main Campus",
            },
            {
                "Unit_ID": "U005",
                "Parent_ID": "U003",
                "Name": "Gen Ed Programs",
                "Type": "Department",
                "Location": "Main Campus",
            },
        ]
    )
    evidence = pd.DataFrame(
        [
            {
                "DocumentTitle": "Strategic Plan 2024-2027",
                "Section": "Priority 1",
                "Text": "We commit to transparent governance and ethical conduct across all operations.",
                "HintStandard": "CR 1.1",
            },
            {
                "DocumentTitle": "Institutional Planning Calendar",
                "Section": "Annual Cycle",
                "Text": "Planning occurs on a rolling annual cycle with mid-year reviews and KPI tracking.",
                "HintStandard": "7.1",
            },
            {
                "DocumentTitle": "Student Achievement Report",
                "Section": "KPIs",
                "Text": "Undergraduate retention improved from 62% to 68% over two years.",
                "HintStandard": "8.2.a",
            },
            {
                "DocumentTitle": "Faculty Handbook",
                "Section": "Governance",
                "Text": "Curriculum changes require majority vote of the faculty senate.",
                "HintStandard": "10.4",
            },
            {
                "DocumentTitle": "Program Catalog",
                "Section": "Degree Requirements",
                "Text": "Associate degree programs require a minimum of 60 semester credits.",
                "HintStandard": "9.1",
            },
        ]
    )
    outcomes = pd.DataFrame(
        {
            "Program": ["AA General Studies", "AS Biology"],
            "LearningOutcome": [
                "Students communicate effectively",
                "Students apply scientific methods",
            ],
            "AssessmentMethod": ["Capstone rubric", "Lab practical"],
            "Target": ["80% meet/exceed", "85% meet/exceed"],
            "Result": ["78%", "83%"],
            "ActionPlan": ["Revise writing module", "Add methods workshop"],
        }
    )
    positions.to_csv(DEMO_DIR / "positions.csv", index=False)
    org_units.to_csv(DEMO_DIR / "org_units.csv", index=False)
    evidence.to_csv(DEMO_DIR / "evidence_snippets.csv", index=False)
    outcomes.to_csv(DEMO_DIR / "program_review_template.csv", index=False)

def write_readme_txt():
    txt = (
        "MapMyStandards Demo Evidence Pack (Paraphrased / Non-Official)\n\n"
        "Files in this archive:\n"
        "- positions.csv\n- org_units.csv\n- evidence_snippets.csv\n- program_review_template.csv\n"
        "- standards_SACSCOC_template.json\n- standards_NWCCU_template.json\n\n"
        "Usage Summary:\n"
        "1) Import one or both standards via /api/standards/import\n"
        "2) Upload CSV evidence files\n"
        "3) Run mapping, gap analysis, and narrative generation\n\n"
        "Disclaimer: Paraphrased demo subset – NOT official standards text."
    )
    (DEMO_DIR / "README_MMS_DEMO.txt").write_text(txt)

def build_zip():
    zip_path = DEMO_DIR / "mms_demo_evidence_pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname in [
            "positions.csv", "org_units.csv", "evidence_snippets.csv", "program_review_template.csv",
            "standards_SACSCOC_template.json", "standards_NWCCU_template.json", "README_MMS_DEMO.txt",
        ]:
            z.write(DEMO_DIR / fname, arcname=fname)
    return zip_path

def main():
    build_standards()
    ensure_csvs()
    write_readme_txt()
    zip_path = build_zip()
    print(f"✅ Demo pack generated at: {zip_path}")

if __name__ == "__main__":
    main()
