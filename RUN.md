# A2Z Nexus — Run Guide

> The frontend is hard-coded (ChatPage.jsx) to call the backend at
> `http://localhost:4000`. Always run the backend on port 4000, matching
> `.env.example` (`BACKEND_PORT=4000`) — NOT 8000. Running on a different
> port here without also updating the frontend will make every request in
> the Chat page fail with a connection error while the app looks "broken".

## Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example ..\.env
uvicorn main:app --reload --port 4000
```

## Frontend (new terminal)
```powershell
cd frontend
npm install
npm run dev
```

Frontend API base: `http://localhost:4000/api` (override with `VITE_API_URL`,
but note ChatPage.jsx currently ignores `VITE_API_URL` and always uses 4000 —
see the "Known follow-ups" note in the top-level README).

API docs: `http://localhost:4000/docs`

### Quick diagnostic

From the `backend` folder:
```powershell
.\.venv\Scripts\python.exe check_setup.py
```
This prints only whether credentials are present; it never prints the keys.


Never commit `.env` or real API credentials.
