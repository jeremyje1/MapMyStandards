"""Legacy upload tests retired in favor of modern upload pipeline coverage."""

import pytest

pytest.skip(
    "Legacy Railway/S3 upload endpoints removed; module retained to avoid accidental import errors while CI focuses on uploads_fixed/user_intelligence_simple.",
    allow_module_level=True,
)
