"""Backward-compatible exports for the canonical API dependencies."""

from app.api.dependencies import get_current_admin_user, get_current_user

__all__ = ["get_current_admin_user", "get_current_user"]