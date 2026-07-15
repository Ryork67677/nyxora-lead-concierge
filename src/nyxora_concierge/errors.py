from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def problem_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    detail: str,
    type_uri: str = "about:blank",
    headers: dict[str, str] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    content: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "request_id": request_id,
    }
    if errors:
        content["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
        media_type="application/problem+json",
    )
