"""
FastAPI dependencies for JWT authentication and RBAC.
"""
from __future__ import annotations
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_token
from app.database.session import get_db
from app.database.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedException("Missing authentication token")

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired token")

    user_id: str = payload.get("sub", "")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_roles(*roles: str):
    """Dependency factory: ensures current user has one of the given roles."""
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Role '{current_user.role}' is not authorised for this action"
            )
        return current_user
    return _check


# Convenience pre-built dependency instances
require_admin = require_roles("admin")
require_recruiter = require_roles("admin", "recruiter")
require_any_auth = require_roles("admin", "recruiter", "candidate")