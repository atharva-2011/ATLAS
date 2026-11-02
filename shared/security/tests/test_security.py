"""Tests for atlas_security package."""

from atlas_security import SecurityContextProtocol


class DummyContext:
    def __init__(self, user_id: str, tenant_id: str) -> None:
        self._user_id = user_id
        self._tenant_id = tenant_id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    def has_permission(self, permission: str) -> bool:
        return permission == "read"


def test_security_context_protocol():
    ctx = DummyContext(user_id="user-1", tenant_id="tenant-1")
    assert isinstance(ctx, SecurityContextProtocol)
    assert ctx.user_id == "user-1"
    assert ctx.tenant_id == "tenant-1"
    assert ctx.has_permission("read") is True
    assert ctx.has_permission("admin") is False
