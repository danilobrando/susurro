"""Resolve API keys from environment variables.

Accepts both the namespaced form (`SUSURRO_<PROVIDER>_API_KEY`) and the
provider's standard env var (`<PROVIDER>_API_KEY`), so users who already
have keys in their environment don't have to duplicate them.
"""

from __future__ import annotations

import os


def get_key(provider: str) -> str | None:
    """Return the API key for `provider` (case-insensitive) or None."""
    up = provider.upper()
    return os.environ.get(f"SUSURRO_{up}_API_KEY") or os.environ.get(f"{up}_API_KEY")


def require_key(provider: str) -> str:
    """Like get_key, but raises BackendUnavailable if missing."""
    from .base import BackendUnavailable

    key = get_key(provider)
    if not key:
        raise BackendUnavailable(
            f"No API key found for {provider}. Set SUSURRO_{provider.upper()}_API_KEY "
            f"or {provider.upper()}_API_KEY in your environment."
        )
    return key
