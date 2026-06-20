"""Provider-layer exceptions."""

from __future__ import annotations


class ProviderError(Exception):
    """Base error for model provider failures."""


class ProviderTimeoutError(ProviderError):
    """Provider call exceeded configured timeout."""


class ProviderResponseError(ProviderError):
    """Provider returned an invalid or empty response."""


class ForbiddenProviderOutputError(ProviderError):
    """Model output included verdict or decision fields."""


class ProviderSchemaValidationError(ProviderError):
    """Model JSON failed provider schema validation."""
