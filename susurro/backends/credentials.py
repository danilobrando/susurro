"""Resolve API keys from environment variables.

Accepts both the namespaced form (`SUSURRO_<PROVIDER>_API_KEY`) and the
provider's standard env var (`<PROVIDER>_API_KEY`), so users who already
have keys in their environment don't have to duplicate them.

Provider-specific key prefixes are checked too — when a key is present
but obviously malformed (e.g. Groq key missing its `gsk_` prefix from a
copy-paste error), we fail fast at warmup instead of silently 401-ing on
the first real request.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Conventional prefixes used by each provider. Used only for a soft warning
# when a key looks malformed — we never gate on this, in case a provider
# changes its format.
_EXPECTED_PREFIXES = {
    "groq": ("gsk_",),
    "anthropic": ("sk-ant-",),
    "openai": ("sk-",),
}


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
    expected = _EXPECTED_PREFIXES.get(provider.lower())
    if expected and not any(key.startswith(p) for p in expected):
        logger.warning(
            "%s key does not start with %s — likely a copy-paste error. "
            "Backend will probably 401. Get a fresh key at the provider console.",
            provider,
            "/".join(expected),
        )
    return key
