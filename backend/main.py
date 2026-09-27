"""
A2Z Nexus — Backend Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    from database.engine import init_db
    await init_db()
    yield


app = FastAPI(
    title="A2Z Nexus API",
    description="AI Multi-Agent Developer Workspace — Ask. Build. Test. Improve. Ship.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from api.health import router as health_router            # noqa: E402
from api.projects import router as projects_router        # noqa: E402
from api.chat import router as chat_router                # noqa: E402
from api.notifications import router as notif_router      # noqa: E402
from api.reminders import router as reminders_router      # noqa: E402
from api.analytics import router as analytics_router      # noqa: E402
from api.agent_stubs import router as agent_stubs_router  # noqa: E402
from api.system import router as system_router          # noqa: E402
from api.github import router as github_router            # noqa: E402
from api.workflows import router as workflows_router      # noqa: E402
from api.workspace import router as workspace_router      # noqa: E402
from api.auth import router as auth_router                # noqa: E402

app.include_router(health_router,        prefix="/api")
app.include_router(projects_router,      prefix="/api")
app.include_router(chat_router,          prefix="/api")
app.include_router(notif_router,         prefix="/api")
app.include_router(reminders_router,     prefix="/api")
app.include_router(analytics_router,     prefix="/api")
app.include_router(agent_stubs_router,   prefix="/api")
app.include_router(system_router,        prefix="/api")
app.include_router(github_router,        prefix="/api")
app.include_router(workflows_router,     prefix="/api")
app.include_router(workspace_router,      prefix="/api")
app.include_router(auth_router,            prefix="/api")
