from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.auth import AuthMiddleware
from api.router import api_router
from core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Edison UI API", version="0.1.0")
    # Middleware order matters: Starlette runs middleware in LIFO order
    # (last added runs first). We want CORS to run first to add headers,
    # then Auth to check authentication. So we add Auth first, then CORS.
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
