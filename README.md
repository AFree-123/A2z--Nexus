# A2Z Nexus — Original Frontend + Complete Backend

This build uses the **uploaded original A2Z Nexus frontend as the visual source of truth**. The original logo, intro video, landing/auth layout, colors, components and existing styling are preserved. Only requested text changes and backend-connected functionality were added.

## Core flow
1. Start at `/intro`.
2. Login at `/auth` or continue as Guest.
3. Use the existing Chat attachment control to send a `.zip` project.
4. The backend creates a project workspace, preserves the extracted folder tree, runs static analysis, and stores the analysis.
5. Open Projects to browse the uploaded project.
6. Open Analysis to select a folder/file and view evidence-based metrics, issues and recommendations.
7. Notifications shows backend-generated project events.

## Run
### Backend terminal
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:PYTHONPATH="$PWD\backend"
& ".\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 4000
```

### Frontend terminal
```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173
Backend: http://localhost:4000
Swagger: http://localhost:4000/docs

## API credentials
See `API_KEYS_REQUIRED.md`.
- IBM watsonx.ai
- Gemini
- Google OAuth / Calendar
- Microsoft OAuth
- WhatsApp Cloud API
- GitHub token/app as needed

Never commit API keys, OAuth secrets or access tokens.
