#!/usr/bin/env python3
"""Quick local test harness for evidence analysis endpoints.

- Reads small example text snippets or files from ./examples (if present)
- Calls /api/user/intelligence-simple/evidence/analyze
- Prints top mappings with rationale excerpts
"""

import os
import json
import requests

API_BASE = os.getenv('API_BASE', 'http://localhost:8000')
TOKEN = os.getenv('TEST_TOKEN') or os.getenv('JWT_TOKEN') or os.getenv('ACCESS_TOKEN')

EXAMPLES = [
    ("policy.txt", b"Our institution assesses student learning outcomes every term. Assessment reports are reviewed by the committee and actions are documented for continuous improvement."),
    ("handbook.txt", b"The governance board oversees institutional integrity and compliance. Policies are updated annually and minutes are recorded."),
]

def main():
    if not TOKEN:
        print("Set TEST_TOKEN (JWT) in environment.")
        return
    headers = {"Authorization": f"Bearer {TOKEN}"}

    for name, content in EXAMPLES:
        files = {"file": (name, content, "text/plain")}
        r = requests.post(f"{API_BASE}/api/user/intelligence-simple/evidence/analyze", headers=headers, files=files, timeout=30)
        print(f"\n=== {name} -> {r.status_code}")
        if r.ok:
            data = r.json()
            mappings = data.get("analysis", {}).get("mappings", [])
            for m in mappings[:5]:
                print(f"- {m['standard_id']} | {m['title']} | conf={m['confidence']:.2f} | meets={m.get('meets_standard')} ({m.get('match_type')})")
                for span in (m.get('rationale_spans') or [])[:2]:
                    print(f"  • {span}")
        else:
            try:
                print(r.text)
            except Exception:
                pass

if __name__ == "__main__":
    main()
