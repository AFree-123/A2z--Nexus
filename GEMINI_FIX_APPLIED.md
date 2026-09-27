# Gemini Fix Applied

The Gemini integration was updated to use Google's current `google-genai` SDK
instead of constructing the Gemini REST URL manually.

## What to do locally

From the project root:

```powershell
python -m pip install -r backend/requirements.txt
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 4000 --reload
```

Then open the frontend at:

```text
http://localhost:5173/chat
```

Keep your real API credentials only in your local `.env` file. Do not paste
API keys, OAuth secrets, or GitHub tokens into chat.

The frontend source was not modified by this fix.
