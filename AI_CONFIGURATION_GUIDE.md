# AI Configuration Guide for MapMyStandards

## Overview

MapMyStandards platform now supports AI-enhanced analysis through integration with OpenAI. When properly configured, the platform uses a combination of proprietary algorithms and AI to provide robust analysis for accreditation directors and reviewers.

## AI-Enhanced Features

### 1. **CiteGuard™ - AI Narrative Generation**
- Generates accreditation narratives with mandatory evidence citations
- Zero hallucination guarantee - all claims backed by evidence
- Identifies gaps and provides actionable recommendations
- Available at: `/narrative.html`

### 2. **GapRisk Predictor™ - Predictive Analysis**
- 8-factor risk model with AI insights
- Forward-looking predictions for compliance challenges
- Personalized recommendations based on institution context
- Available at: `/gap-analysis.html`

### 3. **EvidenceMapper™ - Enhanced Document Analysis**
- Dual-encoder retrieval with AI reranking
- Improved accuracy (up to 95% top-3)
- Better semantic understanding of documents
- Automatic during document upload

## Configuration Steps

### 1. Set OpenAI API Key

Update your environment variables:

```bash
# In .env file or Railway environment variables
OPENAI_API_KEY=sk-YOUR-ACTUAL-OPENAI-API-KEY
```

**Important**: Replace `sk-proj-PLACEHOLDER` with your actual OpenAI API key.

### 2. Verify AI Status

Check AI integration status at:
```
https://api.mapmystandards.ai/api/user/intelligence-simple/ai/status
```

This endpoint shows:
- OpenAI configuration status
- Available AI features
- Algorithm enhancement status
- Recommendations for optimization

### 3. Feature Availability

| Feature | Without AI | With AI |
|---------|-----------|---------|
| Document Analysis | TF-IDF matching (70-80% accuracy) | AI-enhanced matching (87-95% accuracy) |
| Narrative Generation | Basic HTML formatting | Evidence-cited narratives with insights |
| Gap Analysis | Simple risk scores | Predictive analysis with AI recommendations |
| Evidence Trust | Basic scoring | Full multi-factor quality assessment |
| CrosswalkX | Not available | Coming soon |

## Fallback Behavior

The platform gracefully degrades when AI is unavailable:
- All features remain functional
- Uses algorithmic-only approach
- Reduced accuracy but maintains core functionality
- No service interruptions

## API Integration

### Narrative Generation with AI

```javascript
// POST /api/user/intelligence-simple/narratives/generate
{
  "standard_ids": ["HLC.1", "HLC.2"],
  "narrative_type": "comprehensive",  // or "concise", "executive"
  "body": "Additional context...",
  "strict_citations": true
}
```

Response includes:
- AI-generated narrative HTML
- Citations list
- Compliance score
- Gap identification
- Recommendations

### Gap Analysis with AI

```javascript
// GET /api/user/intelligence-simple/gaps/analysis
```

Response includes:
- Risk scores with AI confidence
- AI insights for each gap
- Predictive recommendations
- Next review dates
- Risk factors breakdown

## Best Practices

1. **Regular Evidence Updates**: AI predictions improve with recent evidence
2. **Complete Institution Profile**: Better context = better AI recommendations
3. **Use Narrative Types**: Choose appropriate narrative type for audience
4. **Review AI Insights**: AI provides valuable forward-looking predictions

## Troubleshooting

### AI Features Not Working

1. Check OpenAI API key is set correctly (not placeholder)
2. Verify at `/api/user/intelligence-simple/ai/status`
3. Check Railway logs for import errors
4. Ensure sufficient OpenAI API credits

### Fallback to Basic Mode

If you see `"ai_enabled": false` in responses:
- Platform is using algorithmic-only mode
- Check OpenAI configuration
- Features still work but with reduced capabilities

## Cost Considerations

AI features use OpenAI API calls:
- Document analysis: ~$0.002 per document
- Narrative generation: ~$0.005 per narrative
- Gap analysis: ~$0.01 per full analysis

Configure rate limits if needed in production.

## Support

For AI configuration support:
- Check status endpoint first
- Review Railway deployment logs
- Contact support with status endpoint output

---

Last Updated: September 2025