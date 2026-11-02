"""Security protocols and interfaces for future auth/identity integration."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecurityContextProtocol(Protocol):
    """Protocol representing a verified security context (user, tenant, permissions)."""

    @property
    def user_id(self) -> str:
        """Unique user identity identifier."""
        ...

    @property
    def tenant_id(self) -> str:
        """Tenant or organization identifier for data isolation."""
        ...

    def has_permission(self, permission: str) -> bool:
        """Check if context holds the requested permission."""
        ...
