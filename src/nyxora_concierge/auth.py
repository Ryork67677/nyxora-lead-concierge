from __future__ import annotations

import hashlib
import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(
    auto_error=False,
    bearerFormat="opaque API key",
    scheme_name="APIKeyBearer",
    description="Bearer API key. Production stores only configured SHA-256 key digests.",
)


class APIKeyAuthenticator:
    """Validates opaque bearer keys without retaining or logging the supplied secret."""

    def __init__(self, key_hashes: tuple[str, ...]):
        self.key_hashes = tuple(key_hash.lower() for key_hash in key_hashes)

    @property
    def enabled(self) -> bool:
        return bool(self.key_hashes)

    async def __call__(
        self,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
        ] = None,
    ) -> None:
        if not self.enabled:
            return
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise self._unauthorized()

        supplied_hash = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
        if not any(hmac.compare_digest(supplied_hash, expected) for expected in self.key_hashes):
            raise self._unauthorized()

    @staticmethod
    def _unauthorized() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid bearer credentials are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
