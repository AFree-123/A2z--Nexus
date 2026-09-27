# A2Z Nexus — Backend Repair Notes

This repair pass changes **backend/configuration only**. The existing frontend files are unchanged.

## Fixed

1. **Project-root `.env` loading**
   - Backend settings now resolve the project-root `.env` from the file location, so starting Uvicorn from `backend/` does not make environment loading depend on the current working directory.
   - A `backend/.env` is also accepted if present.

2. **Gemini configuration**
   - Gemini remains the primary provider.
   - Primary model: `gemini-2.5-flash`.
   - Fallback model: `gemini-2.5-flash-lite`.
   - Gemini errors are logged without exposing credentials.

3. **No silent AI failure for ambiguous chat**
   - If the Gemini provider is unavailable during intent classification, the backend now returns a clear configuration message instead of failing the chat request with no useful response.

4. **`hi` / basic greetings**
   - Basic greetings are handled locally by the orchestrator. This lets you verify that the frontend → backend chat path works before configuring an AI key.

5. **System capabilities endpoint**
   - Removed stale references to nonexistent GROQ settings.

6. **Setup diagnostic**
   - Added `backend/check_setup.py`.
   - It reports whether credentials are present without printing their values.

## Database

SQLite is already wired into the backend. On backend startup, SQLAlchemy creates the required tables automatically with `Base.metadata.create_all` when they do not exist.

For local development, no separate database installation is required.

## Frontend

The frontend directory and its source files were not changed in this repair pass.
