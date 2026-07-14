from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import __version__
from .config import Settings
from .knowledge import KnowledgeBase
from .models import ChatRequest, ChatResponse, HealthResponse
from .repository import EventRepository
from .service import ConciergeService


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings.from_environment()
    logging.basicConfig(level=active_settings.log_level)
    logger = logging.getLogger("nyxora_concierge")
    repository = EventRepository(active_settings.database_path)
    knowledge_base = KnowledgeBase.from_package()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.initialize()
        app.state.service = ConciergeService(knowledge_base, repository)
        yield

    application = FastAPI(
        title="Nyxora Lead Concierge",
        version=__version__,
        description=(
            "A privacy-conscious lead qualification API with grounded answers and explicit "
            "human handoff. This educational project does not provide medical advice."
        ),
        lifespan=lifespan,
    )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled request error", extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @application.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @application.post("/v1/chat", response_model=ChatResponse, tags=["concierge"])
    async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        service: ConciergeService = request.app.state.service
        return service.respond(payload)

    return application


app = create_app()

