# A2Z Nexus — Credentials

## Required for the core AI workflow
- `GEMINI_API_KEY` — Gemini project analysis, explanations, recommendations, documentation and chat.
- `GITHUB_TOKEN` — GitHub repository inspection/import. A public repository can often be inspected without a token, but a token is recommended for rate limits/private repositories.
- `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` — Continue with Google and Google Calendar authorization.
- `MICROSOFT_CLIENT_ID` + `MICROSOFT_CLIENT_SECRET` + `MICROSOFT_TENANT_ID` — Continue with Microsoft.

## No longer used
- watsonx
- WhatsApp

## Important
Google OAuth and Microsoft OAuth are separate applications/credentials. Google Calendar uses the Google OAuth consent flow with the Calendar Events scope; there is no separate Google Calendar API key required for this implementation.
