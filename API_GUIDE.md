# A2Z Nexus — API setup

The frontend is kept unchanged. This build uses a FastAPI backend on port **4000** and a React/Vite frontend on port **5173**.

## External services used by the complete build

| Service | Required for | Environment variables |
|---|---|---|
| Google Gemini | AI chat, project intelligence, recommendations, documentation and readiness guidance | `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL` |
| GitHub | Private/public repository inspect and import | `GITHUB_TOKEN` |
| Google OAuth + Calendar | Continue with Google and creating Google Calendar submission reminders | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` |
| Microsoft Entra OAuth | Continue with Microsoft | `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID`, `MICROSOFT_REDIRECT_URI` |

**IBM watsonx.ai is intentionally not included in this build.** Gemini is the AI provider.

Google Calendar does not need a separate API key in this build; the Calendar API is accessed using the Google OAuth access token after the user signs in with Google and grants Calendar permission.

## Required redirect URIs

Google:
```text
JavaScript origin: http://localhost:4000
Redirect URI:      http://localhost:4000/api/auth/google/callback
```

Microsoft:
```text
Web redirect URI: http://localhost:4000/api/auth/microsoft/callback
```

## `.env`

Copy `.env.example` to `.env`, then paste your own credentials locally. Never paste API keys or client secrets into chat or commit them to Git.

Core values:
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
GITHUB_TOKEN=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:4000/api/auth/google/callback
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:4000/api/auth/microsoft/callback
BACKEND_PORT=4000
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite+aiosqlite:///./a2z_nexus.db
```

## Internal API flow

1. Upload a project ZIP from Chat.
2. Backend stores/extracts it under `backend/data/projects/<project_id>`.
3. Deterministic static analysis scans the actual files.
4. The Analysis page can select a folder or file and request fresh analysis.
5. Gemini adds evidence-based summaries, recommendations, submission readiness and deployment guidance when configured.
6. GitHub import can inspect/import a repository using the GitHub token.
7. Google Calendar reminders use the signed-in Google OAuth credential.

## Startup

```powershell
# terminal 1
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
# fill .env first
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 4000
```

Second terminal:
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://localhost:4000/docs`.
