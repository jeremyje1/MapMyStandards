# A3E — MapMyStandards VS Code Extension

- Tree view: A3E Gaps (placeholder)
- WebView: Gaps pills; will fetch `/api/v1/gaps?program_id=...`
- CodeLens (Markdown): "Insert Evidence Snippet…" under headings

Publish
```bash
npm i -g @vscode/vsce
npm i
npm run compile
vsce package
```

Settings
- `a3e.apiBase`: Backend API base (e.g., https://api.mapmystandards.ai)
