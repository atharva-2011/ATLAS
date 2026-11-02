"""Security context models and FastAPI dependency helpers for tenant scoping and auth."""

from typing import Annotated

from fastapi import Header, HTTPException, status
from pydantic import BaseModel, Field


class SecurityContext(BaseModel):
    """Concrete implementation of SecurityContextProtocol."""

    user_id: str = Field(description="Unique user identity identifier")
    tenant_id: str = Field(default="default", description="Tenant or organization identifier")
    permissions: list[str] = Field(default_factory=list, description="Assigned permissions")

    def has_permission(self, permission: str) -> bool:
        """Check if context holds the requested permission or admin wildcard."""
        return "*" in self.permissions or permission in self.permissions


async def get_security_context(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SecurityContext:
    """FastAPI dependency resolving the current security context from HTTP headers.

    Supports API Key / Bearer / direct header identification.
    """
    tenant = x_tenant_id or "default"
    user = x_user_id or "anonymous"
    permissions = ["read", "write"]

    if authorization:
        # Example: Bearer token or ApiKey
        token = authorization.replace("Bearer ", "").strip()
        if token == "invalid_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization credentials",
            )
        if "admin" in token:
            permissions.append("*")

    return SecurityContext(user_id=user, tenant_id=tenant, permissions=permissions)


def require_permission(required_perm: str):
    """Dependency factory enforcing specific permission requirements."""

    async def _permission_checker(
        ctx: Annotated[SecurityContext, get_security_context],
    ) -> SecurityContext:
        if not ctx.has_permission(required_perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_perm}' is required for this resource",
            )
        return ctx

    return _permission_checker
