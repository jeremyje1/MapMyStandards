# 05 – VS Code extension spec

Folder: `vscode-extension/`

* `/src/extension.ts` registers `A3E.showGaps` tree‑view.
* WebView fetches `/api/v1/gaps?program_id=...` and displays Red/Amber/Green pills.
* Inline `CodeLens` over markdown standards files offers **"Insert Evidence Snippet…"** which triggers Copilot suggestion seeded with A3E context.

**Publish steps:**

```bash
npm i -g @vscode/vsce
cd vscode-extension
vsce package
```

Marketplace listing links back to SaaS onboarding → lead gen.
