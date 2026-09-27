# A2Z Nexus Backend — Final Workflow

Frontend is intentionally unchanged.

## Core workflow
1. User creates/selects a project.
2. ZIP project upload or GitHub repository import.
3. Project is stored under the backend workspace and indexed in SQLite.
4. Deterministic analysis scans files, dependencies, tests, security patterns and deployment files.
5. Gemini adds project-level explanation, prioritised issues, recommendations, submission readiness and deployment readiness.
6. Analysis endpoint returns structured metrics for the existing frontend.
7. Recommendations are stored per project.
8. Reminders are stored per project.
9. Continue with Google authorizes Calendar Events; reminders can be created in the user's primary calendar.
10. Continue with Microsoft is a separate OAuth integration.

## Credentials
See `API_KEYS_REQUIRED.md` and `.env.example`.
