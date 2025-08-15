# MapMyStandards Demo Evidence & Standards Pack

Educational demo assets you can import into a fresh MapMyStandards instance to explore workflows end‑to‑end (standards import, evidence upload, mapping, gap analysis, narratives).

## Contents

Standards templates (JSON):
* `standards_SACSCOC_template.json`
* `standards_NWCCU_template.json`

Evidence & context data:
* `positions.csv` – Staffing positions (demo data)
* `org_units.csv` – Organizational units hierarchy
* `evidence_snippets.csv` – Small textual evidence excerpts with an optional hint column
* `program_review_template.csv` – Sample outcomes assessment snapshot

Regeneration script:
* `../../scripts/generate_demo_pack.py` – (Re)builds fresh JSON (with current timestamp) and a distributable zip.

## Usage Workflow
1. (Optional) Regenerate to get current timestamps: `python scripts/generate_demo_pack.py`
2. Use the platform UI or POST to `/api/standards/import` with one of the JSON template files (repeat for both if desired).
3. Upload CSV evidence sources (or load them via any bulk evidence ingestion endpoint you have enabled).
4. Run automated mapping (`/api/map` or UI action) to link evidence to standards.
5. Execute gap analysis (`/api/gaps/run`) and fetch results.
6. Generate narratives (`/api/narratives`).

## JSON Template Schema (simplified)
```
metadata: { key, name, version, publisher, importedAt (nullable), notes }
items: [
  { code, title, description, level, parent (nullable), weight, evidenceExamples?, rubric? }
]
```
`rubric` (optional):
```
{
  "levels": ["Insufficient", "Developing", "Meets", "Exceeds"],
  "anchors": [ ... optional descriptive anchors aligned to levels ... ]
}
```

## Disclaimers
* All standard titles & descriptions are paraphrased demo snippets – NOT official or complete texts.
* Provided solely for functional testing & demonstration.
* Do not distribute as authoritative accreditation material.

## Creating the Zip (Distribution)
Running the generation script produces `examples/demo_pack/mms_demo_evidence_pack.zip` containing:
```
positions.csv
org_units.csv
evidence_snippets.csv
program_review_template.csv
standards_SACSCOC_template.json
standards_NWCCU_template.json
README_MMS_DEMO.txt
```

## License
Demo data released under the project license. Paraphrased standards text remains non-official.
