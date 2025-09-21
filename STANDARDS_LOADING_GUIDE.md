# Standards Loading Guide

This guide explains how to manage and load accreditation standards in MapMyStandards.

## Overview

MapMyStandards uses a standards corpus containing accreditation standards from various accrediting bodies (SACSCOC, HLC, MSCHE, NECHE, NWCCU, WASC). The system loads these standards into an in-memory graph structure for efficient searching and mapping.

## Standards Location

Standards are stored as YAML files in the `data/standards/` directory:

```
data/standards/
├── sacscoc.yaml    # Southern Association of Colleges and Schools
├── hlc.yaml        # Higher Learning Commission
├── msche.yaml      # Middle States Commission on Higher Education  
├── neche.yaml      # New England Commission of Higher Education
├── nwccu.yaml      # Northwest Commission on Colleges and Universities
├── wasc.yaml       # Western Association of Schools and Colleges
└── README.md
```

## Loading Standards

### Method 1: Automatic Loading on Startup

The system automatically loads standards from the `data/standards/` directory when the application starts. This is handled by the startup module at `src/a3e/startup/standards_loader.py`.

### Method 2: Manual Reload Script

Use the provided script to manually reload standards:

```bash
# Load standards directly (for local development)
python3 reload_standards_corpus.py

# Load standards via API (for production)
A3E_API_KEY=your-api-key python3 reload_standards_api.py
```

### Method 3: Admin Interface

1. Navigate to `/admin-standards` in your browser
2. Click "Refresh" under "Corpus Status" to see current loaded standards
3. Use "Reload" button to reload from the corpus directory
4. For uploading new standards:
   - Enter accreditor code (e.g., SACSCOC)
   - Select YAML/JSON file
   - Click "Upload via Presigned S3" (recommended)

### Method 4: API Endpoints

Reload standards via API:

```bash
# POST method
curl -X POST https://platform.mapmystandards.ai/api/user/intelligence-simple/standards/byol/reload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"path": "data/standards", "fallback_to_seed": true}'

# GET method (if POST is blocked)
curl https://platform.mapmystandards.ai/api/user/intelligence-simple/standards/byol/reload?path=data/standards&fallback_to_seed=true \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Check corpus status:

```bash
curl https://platform.mapmystandards.ai/api/user/intelligence-simple/standards/corpus/status \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Standards File Format

Standards files use YAML format with the following structure:

```yaml
accreditor: SACSCOC
version: "2024"
effective_date: "2024-01-01"
metadata:
  name: Southern Association of Colleges and Schools Commission on Colleges
  version: "2024"
  last_updated: "2024-01-01"
  source_url: "https://sacscoc.org/"
  license: "proprietary-summary"
  disclaimer: "Paraphrased summaries for development"
  coverage_notes: "Complete principles with representative indicators"

standards:
  - id: "4.1"
    title: "Governing board characteristics"
    description: "The institution has a governing board..."
    category: "Governance"
    clauses:
      - id: "4.1.a"
        title: "Board independence"
        description: "The governing board is free from undue influence..."
        indicators:
          - "Board operates independently"
          - "No undue external influence"
```

## Troubleshooting

### Standards Not Loading

1. Check that YAML files exist in `data/standards/`
2. Verify file permissions are readable
3. Check logs for parsing errors
4. Ensure proper YAML syntax (use a YAML validator)

### API Reload Fails

1. Verify API key is valid and active
2. Check server is running and accessible
3. Try GET method if POST returns 405
4. Check network connectivity

### Admin Interface Issues

1. Ensure you're logged in with proper credentials
2. Check browser console for JavaScript errors
3. Verify file size limits (large files may timeout)
4. Use presigned upload for better reliability

## Current Standards Status

As of the latest update, the system includes:

- **SACSCOC**: 27 standards
- **HLC**: 16 standards  
- **MSCHE**: 8 standards
- **NECHE**: 63 standards
- **NWCCU**: 13 standards
- **WASC**: 8 standards
- **Total**: 1362 nodes in the standards graph

## Best Practices

1. Always backup existing standards before uploading new ones
2. Validate YAML syntax before uploading
3. Use meaningful version numbers and dates
4. Include comprehensive metadata for tracking
5. Test in development before deploying to production
6. Monitor corpus status after reloading

## Security Considerations

- API keys are required for all standards operations
- Only authenticated users can reload standards
- Standards files should not contain sensitive information
- Use proper file permissions on the server

## Support

For issues with standards loading:

1. Check this documentation first
2. Review logs for specific error messages
3. Contact technical support with:
   - Error messages
   - Steps to reproduce
   - Standards file causing issues (if applicable)