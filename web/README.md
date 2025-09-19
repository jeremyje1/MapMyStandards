# Web Frontend

This folder contains static assets that are deployed by the root Vercel project.

Important:
- Deploy from the repository root, not from `/web`.
- The root `vercel.json` sets `outputDirectory: "web"` and manages redirects/headers/rewrites.
- If this folder has its own `.vercel/` directory, remove it to avoid linking a separate Vercel project:

```bash
rm -rf web/.vercel
```

Deploy (from root):

```bash
vercel deploy --prod --yes
```
