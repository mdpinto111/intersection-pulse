import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasIngestKey(BasePermission):
    """Service-to-service auth for the ingestion endpoint (X-Ingest-Key header)."""

    message = "Missing or invalid ingest key."

    def has_permission(self, request, view) -> bool:
        provided = request.headers.get("X-Ingest-Key", "")
        # Constant-time comparison to avoid timing attacks.
        return hmac.compare_digest(provided, settings.INGEST_API_KEY)
