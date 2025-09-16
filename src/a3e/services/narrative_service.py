"""
Lightweight Narrative HTML builder

Generates a simple HTML narrative for selected standards without invoking LLMs.
"""
from typing import List
from datetime import datetime
import html as _html

from .standards_graph import standards_graph


def generate_narrative_html(standard_ids: List[str], user_body: str = "") -> str:
    """Build a minimal narrative HTML for given standard IDs.

    - Lists each standard with title and description
    - Includes optional user-provided introductory body
    """
    safe_intro = _html.escape(user_body or "")

    sections: List[str] = []
    for sid in standard_ids or []:
        node = standards_graph.get_node(sid)
        if not node:
            continue
        title = _html.escape(node.title or sid)
        desc = _html.escape(node.description or "")
        path = standards_graph.get_path_to_root(sid)
        breadcrumb = " / ".join(_html.escape(p.title or p.node_id) for p in path) if path else title
        sections.append(
            f"<article class=\"standard\">"
            f"<h3>{_html.escape(node.node_id)} — {title}</h3>"
            f"<p class=\"breadcrumb\"><em>{breadcrumb}</em></p>"
            f"<p>{desc}</p>"
            f"</article>"
        )

    generated_at = _html.escape(datetime.utcnow().isoformat())
    body_html = f"<p>{safe_intro}</p>" if safe_intro else ""
    content = "\n".join(sections) if sections else "<p>No standards selected.</p>"
    return (
        "<section class=\"narrative\">"
        "<h2>Accreditation Narrative</h2>"
        f"<p class=\"meta\"><small>Generated at {generated_at}</small></p>"
        f"{body_html}"
        f"{content}"
        "</section>"
    )
