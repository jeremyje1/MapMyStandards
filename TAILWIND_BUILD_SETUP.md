# Tailwind CSS Build Setup

## Summary
I've successfully set up a Tailwind CSS build process to replace the CDN usage that was causing console warnings.

## What Was Done

1. **Created Tailwind Configuration Files**
   - `web/tailwind.config.js` - Tailwind configuration with content paths
   - `web/package.json` - NPM scripts for building CSS
   - `web/src/input.css` - Source CSS with Tailwind directives and custom components

2. **Installed Dependencies**
   - Ran `npm install` to install Tailwind CSS as a dev dependency

3. **Built CSS File**
   - Generated `web/static/css/tailwind.css` with all Tailwind utilities
   - Minified for production use

4. **Updated HTML Files**
   - Replaced `<script src="https://cdn.tailwindcss.com"></script>` with 
   - `<link rel="stylesheet" href="/web/static/css/tailwind.css">`
   - Updated files: trial-signup.html, trial-signup-old.html, trial-signup-new.html

## Build Commands

- **Build CSS**: `cd web && npm run build-css`
- **Watch Mode**: `cd web && npm run dev`

## Benefits
- Eliminates console warning about using Tailwind CDN in production
- Faster page loads (no external CDN request)
- Production-ready CSS build
- Custom component classes available (@apply directives)

## Note
The Tailwind build includes all utilities from HTML files in the web directory. The build process scans for class names and only includes the CSS that's actually used.
