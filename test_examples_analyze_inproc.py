#!/usr/bin/env python3
"""In-process smoke test for the evidence analysis endpoint.

Builds a minimal FastAPI app with only the 'user_intelligence_simple' router
(to avoid starting the full platform), generates a JWT using the onboarding
secret, and posts a couple of small text samples to the /evidence/analyze path.
"""

import os
from datetime import datetime
from typing import List

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure src is importable if launched from repo root
import sys
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from a3e.api.routes import user_intelligence_simple as simple  # noqa: E402
import generate_dashboard_token as tokgen  # noqa: E402

EXAMPLES: List[tuple[str, bytes]] = [
    (
        "policy.txt",
        b"Our institution assesses student learning outcomes every term. Assessment reports are reviewed by the committee and actions are documented for continuous improvement.",
    ),
    (
        "governance.txt",
        b"The governance board oversees institutional integrity and compliance. Policies are updated annually and minutes are recorded.",
    ),
]


def build_app() -> FastAPI:
    app = FastAPI(title="Inproc Test App")
    app.include_router(simple.router)
    return app


def main():
    print("[inproc] starting")
    # Use a predictable onboarding secret for the token and verification
    os.environ.setdefault("ONBOARDING_SHARED_SECRET", "dev-onboarding-123")

    token = tokgen.create_dashboard_token()
    app = build_app()
    client = TestClient(app)

    headers = {"Authorization": f"Bearer {token}"}

    for name, content in EXAMPLES:
        files = {"file": (name, content, "text/plain")}
        try:
            resp = client.post(
                "/api/user/intelligence-simple/evidence/analyze",
                headers=headers,
                files=files,
                timeout=30,
            )
            print(f"\n=== {name} -> {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                mappings = data.get("analysis", {}).get("mappings", [])
                for m in mappings[:5]:
                    print(
                        f"- {m['standard_id']} | {m['title']} | conf={m['confidence']:.2f} | "
                        f"meets={m.get('meets_standard')} ({m.get('match_type')})"
                    )
                    for span in (m.get("rationale_spans") or [])[:2]:
                        print(f"  • {span}")
            else:
                try:
                    print(resp.text)
                except Exception:
                    pass
        except Exception as e:
            import traceback
            print("[inproc] request failed:", e)
            traceback.print_exc()
    print("[inproc] completed")


if __name__ == "__main__":
    main()
