from __future__ import annotations

import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response

from . import __version__
from .auth import APIKeyAuthenticator
from .config import Settings
from .errors import problem_response
from .generation import OllamaGenerator
from .knowledge import KnowledgeBase
from .metrics import ServiceMetrics
from .models import ChatRequest, ChatResponse, HealthResponse, ReadinessResponse
from .observability import configure_logging, request_id_context
from .repository import EventRepository, RepositoryError
from .service import ConciergeService

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def _request_id(request: Request) -> str:
    candidate = request.headers.get("X-Request-ID", "")
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid.uuid4().hex


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = (settings or Settings.from_environment()).validate()
    configure_logging(active_settings.log_level, active_settings.log_format)
    logger = logging.getLogger("nyxora_concierge.api")
    repository = EventRepository(active_settings.database_path)
    knowledge_base = KnowledgeBase.from_package()
    metrics = ServiceMetrics()
    authenticator = APIKeyAuthenticator(active_settings.api_key_hashes)
    generator = (
        OllamaGenerator(
            base_url=active_settings.ollama_base_url,
            model=active_settings.ollama_model,
            timeout_seconds=active_settings.ollama_timeout_seconds,
        )
        if active_settings.ollama_base_url
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        repository.initialize()
        app.state.service = ConciergeService(
            knowledge_base,
            repository,
            generator,
            metrics,
        )
        logger.info(
            "application_started",
            extra={"app_env": active_settings.app_env, "request_id": "startup"},
        )
        yield
        logger.info(
            "application_stopped",
            extra={"app_env": active_settings.app_env, "request_id": "shutdown"},
        )

    application = FastAPI(
        title="Nyxora Lead Concierge",
        version=__version__,
        description=(
            "A privacy-conscious lead qualification API with grounded answers and explicit "
            "human handoff. This educational project does not provide medical advice."
        ),
        lifespan=lifespan,
        docs_url="/docs" if active_settings.docs_enabled else None,
        redoc_url="/redoc" if active_settings.docs_enabled else None,
        openapi_url="/openapi.json" if active_settings.docs_enabled else None,
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=list(active_settings.allowed_hosts),
    )
    application.state.settings = active_settings
    application.state.repository = repository
    application.state.metrics = metrics

    @application.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = _request_id(request)
        request.state.request_id = request_id
        context_token = request_id_context.set(request_id)
        started = time.perf_counter()
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration = time.perf_counter() - started
            route = _route_template(request)
            metrics.record_http(request.method, route, status_code, duration)
            logger.info(
                "http_request_completed",
                extra={
                    "duration_ms": round(duration * 1000, 2),
                    "method": request.method,
                    "path": route,
                    "status_code": status_code,
                },
            )
            request_id_context.reset(context_token)

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return problem_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Request validation failed",
            detail="One or more request fields are invalid.",
            type_uri="https://nyxora-ai.com/problems/request-validation",
            errors=errors,
        )

    @application.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        titles = {
            401: "Authentication required",
            404: "Resource not found",
        }
        return problem_response(
            request,
            status_code=exc.status_code,
            title=titles.get(exc.status_code, "Request failed"),
            detail=str(exc.detail),
            headers=exc.headers,
        )

    @application.exception_handler(RepositoryError)
    async def handle_repository_error(request: Request, exc: RepositoryError):
        logger.error(
            "repository_unavailable",
            extra={"error_type": type(exc).__name__, "path": request.url.path},
        )
        return problem_response(
            request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service temporarily unavailable",
            detail="Required application storage is unavailable. Retry later.",
            type_uri="https://nyxora-ai.com/problems/dependency-unavailable",
            headers={"Retry-After": "30"},
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception(
            "unhandled_request_error",
            extra={"error_type": type(exc).__name__, "path": request.url.path},
        )
        return problem_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal server error",
            detail="The request could not be completed.",
            type_uri="https://nyxora-ai.com/problems/internal-error",
        )

    @application.get("/livez", response_model=HealthResponse, tags=["operations"])
    async def liveness() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @application.get("/health", response_model=HealthResponse, tags=["operations"], deprecated=True)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @application.get("/readyz", response_model=ReadinessResponse, tags=["operations"])
    async def readiness() -> ReadinessResponse:
        repository.check()
        return ReadinessResponse(
            status="ready",
            version=__version__,
            database="ok",
            knowledge_base="ok",
        )

    @application.get("/metrics", tags=["operations"], include_in_schema=False)
    async def prometheus_metrics(_: None = Depends(authenticator)) -> Response:
        if not active_settings.metrics_enabled:
            raise HTTPException(status_code=404, detail="Metrics endpoint is disabled")
        return Response(
            content=metrics.render(),
            headers={"Content-Type": "text/plain; version=0.0.4; charset=utf-8"},
        )

    @application.post("/v1/chat", response_model=ChatResponse, tags=["concierge"])
    async def chat(
        payload: ChatRequest,
        request: Request,
        _: None = Depends(authenticator),
    ) -> ChatResponse:
        service: ConciergeService = request.app.state.service
        return service.respond(payload)

    return application


app = create_app()
