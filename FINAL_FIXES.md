# A2Z Nexus — Final Local Fixes

Applied to the supplied `A2Z-Nexus-GEMINI-FIXED(2)` base only.

## Fixed
- Removed Guest login path; protected workspace routes now require a non-guest session.
- Kept the existing Login/Register UI and fields.
- Google/Microsoft OAuth URLs now use `VITE_API_URL` instead of a hard-coded localhost URL.
- Microsoft OAuth now creates the user record when needed.
- Added top-bar notification navigation.
- Added working light/dark theme toggle with persisted preference.
- Improved chat-history flex/scroll behavior.
- Added the supplied background audio as `frontend/public/assets/a2z-background.mp3`.
- Intro audio attempts autoplay and retries on the first user interaction to respect browser autoplay policy.
- Added localhost:5174 to backend CORS.
- Updated Gemini defaults for new projects to `gemini-3.8-flash` with `gemini-3.5-flash-lite` fallback.
- Added `frontend/.env.example` for deployment.

## Important
Do not commit `.env`. It remains gitignored. Put deployment secrets in the hosting provider's environment-variable settings.

## Local frontend
Set:
`VITE_API_URL=http://localhost:4000`

## Local backend
Keep the existing backend `.env` values/credentials in your local copy.
