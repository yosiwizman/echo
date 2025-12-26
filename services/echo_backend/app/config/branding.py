"""
Centralized white-label branding configuration for Echo backend.

This module defines all brand-specific values for the Echo API.
Modify these values to rebrand the application for different deployments.
"""

from typing import Final


class BrandingConfig:
    """White-label branding configuration."""

    # Application identity
    PRODUCT_NAME: Final[str] = "Echo"
    PRODUCT_TAGLINE: Final[str] = "AI-powered wearable companion"

    # Environment display names (for logging, monitoring, etc.)
    ENV_DISPLAY_NAME: Final[str] = "Echo API"

    # API metadata (exposed in /docs, /openapi.json)
    API_TITLE: Final[str] = f"{PRODUCT_NAME} API"
    API_DESCRIPTION: Final[str] = (
        f"{PRODUCT_TAGLINE}. "
        "Real-time transcription, AI chat, memory management, and device integration."
    )
    API_VERSION: Final[str] = "1.0.0"

    # Support/contact information
    SUPPORT_EMAIL: Final[str] = "support@echo.example.com"  # Update for production
    DOCS_URL: Final[str] = "https://docs.echo.example.com"  # Update for production

    # ==========================================
    # Usage Notes
    # ==========================================
    # 1. For simple rebrand: Update string values above
    # 2. For multi-tenant: Consider environment-based overrides
    # 3. For runtime config: Load from environment variables or config service
    # 4. API clients see these values in OpenAPI spec (/docs)


# Convenience exports
PRODUCT_NAME = BrandingConfig.PRODUCT_NAME
ENV_DISPLAY_NAME = BrandingConfig.ENV_DISPLAY_NAME
API_TITLE = BrandingConfig.API_TITLE
API_DESCRIPTION = BrandingConfig.API_DESCRIPTION
API_VERSION = BrandingConfig.API_VERSION
