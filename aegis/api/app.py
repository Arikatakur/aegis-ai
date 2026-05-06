"""FastAPI application factory for Aegis AI REST API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aegis import __version__
from aegis.api.routes import router


def create_api_app() -> FastAPI:
    """Create and configure the Aegis AI FastAPI application."""
    api = FastAPI(
        title="Aegis AI API",
        description="REST API for Aegis AI autonomous LLM red-teaming platform",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware - restrict in production
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api.include_router(router, prefix="")

    @api.on_event("startup")
    async def on_startup() -> None:
        """Initialize database on startup."""
        from aegis.db.database import init_db

        init_db()

    @api.on_event("shutdown")
    async def on_shutdown() -> None:
        """Clean up resources on shutdown."""
        pass

    return api


app = create_api_app()
