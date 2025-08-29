# Railway Project Configuration

## Project Structure

Based on your clarification:

### Frontend Service
- **Project Name**: mapmystandards-prod
- **URL**: https://platform.mapmystandards.ai
- **Description**: React frontend application

### Backend Service  
- **Project Name**: exemplary-solace
- **URL**: https://api.mapmystandards.ai
- **Description**: Python/FastAPI backend API

## How to Switch Between Projects

### To work with Frontend:
```bash
railway link --project mapmystandards-prod
railway status  # Should show: Project: mapmystandards-prod
```

### To work with Backend:
Since "exemplary-solace" appears to be a service name rather than a project name, you need to:

1. Check if backend is in a different project:
```bash
railway list  # Shows all your projects
```

2. If backend is a service within a project, first link to that project, then select the service:
```bash
railway link  # Interactive selection
railway service exemplary-solace  # Link to backend service
```

## Current Status
- Currently linked to: mapmystandards-prod (frontend)
- Need to identify which Railway project contains the exemplary-solace backend service

## Note
"exemplary-solace" appears to be a Railway-generated service name (their random name generator format).
The backend service might be within one of these projects:
- prolific-fulfillment
- beautiful-compassion  
- enormous-language

Or it might be a service within the mapmystandards-prod project itself.