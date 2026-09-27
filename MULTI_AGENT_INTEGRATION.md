# A2Z Nexus — Multi-Agent Integration Map

## Core agents
1. Information — general developer Q&A
2. Code Analysis — project/code/structure analysis
3. Testing — run/generate tests and explain failures
4. Recommendation — evidence-based project improvement
5. Documentation — README/API/setup docs
6. Content — project descriptions, abstracts, presentation content
7. Narration — demo/presentation scripts
8. Reminder — deadline detection and reminder workflow
9. Submission — submission readiness
10. Release — release/deployment readiness

## Orchestrator workflows
- Project improvement: Code Analysis → Testing → Recommendation
- Submission preparation: Code Analysis → Testing → Submission
- Release check: Testing → Release

## APIs
### Required
- Groq API: primary LLM engine for classification and all AI agents.

### Optional integrations
- GitHub REST API: repository metadata/tree inspection. Works anonymously for public repositories; `GITHUB_TOKEN` can be configured for authenticated access/rate limits/private repositories.
- Google Calendar API: optional reminder/calendar integration. The reminder database workflow works without it.

### Internal APIs
- `/api/chat` — primary orchestrated chat
- `/api/analyze` — code analysis
- `/api/test/run`, `/api/test/generate` — testing
- `/api/recommendations` — project recommendations
- `/api/documentation`, `/api/content`, `/api/narration`
- `/api/submission/check`, `/api/release/check`
- `/api/workflows/project-improvement` — full improvement pipeline
- `/api/workflows/submission-prep` — full submission pipeline
- `/api/workflows/release-check` — full release pipeline
- `/api/github/inspect` — optional GitHub inspection
- `/api/system/capabilities` — safe capability/status information

No IBM watsonx API is required when `AI_PROVIDER=groq`. Existing provider adapter remains only for compatibility and is not active.
