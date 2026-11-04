import os

BASE_URL = os.environ.get("TELER_BACKEND_DOMAIN", "https://api.frejun.ai")

TELER_BASE_URL = f"{BASE_URL}/api/v1"
WEBHOOK_API_VERSION = "2026-06-01"
WEBHOOK_API_VERSIONS = ("2025-08-01", "2026-06-01")
AUTHENTICATION_TYPES = ("credential", "IP")
