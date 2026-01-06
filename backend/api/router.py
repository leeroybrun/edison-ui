from __future__ import annotations

from fastapi import APIRouter

from .routes.activity import router as activity_router
from .routes.health import router as health_router
from .routes.pairing import router as pairing_router
from .routes.projects import router as projects_router
from .routes.qa import router as qa_router
from .routes.realtime import router as realtime_router
from .routes.sessions import router as sessions_router
from .routes.settings import router as settings_router
from .routes.tasks import router as tasks_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(activity_router)
api_router.include_router(health_router)
api_router.include_router(pairing_router)
api_router.include_router(projects_router)
api_router.include_router(qa_router)
api_router.include_router(realtime_router)
api_router.include_router(sessions_router)
api_router.include_router(settings_router)
api_router.include_router(tasks_router)
