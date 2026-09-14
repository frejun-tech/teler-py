"""Run the real Teler API locally and drive the real SDK against it.

These are not mock tests. The backend's actual FastAPI routers are mounted and
served over a real socket, so a request from the SDK goes through genuine URL
routing, query/body validation and ``response_model`` serialization. Only the
persistence and S3 layers are stubbed, because those need Postgres and AWS.

What this catches that ``respx`` mocks cannot:
  * a wrong path (a mock asserts the path the SDK already uses)
  * query/body encoding the API's validators reject
  * response keys the SDK's dataclasses read under the wrong name

Requires the backend source and its dependencies. Set TELER_BACKEND_PATH.
"""
import os
import socket
import sys
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from types import SimpleNamespace

BACKEND_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DATABASE_ASYNC_URL": "postgresql+asyncpg://u:p@localhost:5432/d",
    "AWS_ACCESS_KEY_ID": "x",
    "AWS_SECRET_ACCESS_KEY": "x",
    "AWS_REGION": "us-east-1",
    "AWS_SES_FROM_EMAIL": "a@b.c",
    "AWS_S3_BUCKET_NAME": "test-bucket",
    "AWS_URL_EXPIRES_IN": "900",
    "SECRET_ACCESS_KEY": "x",
    "SECRET_REFRESH_KEY": "x",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "REFRESH_TOKEN_EXPIRE_MINUTES": "60",
    "CALL_CONTROL_BASE_URL": "http://localhost",
    "INTER_SERVICE_HMAC_SECRET": "x",
    # base64 of exactly 32 bytes; the backend rejects any other length
    "ENCRYPTION_KEY": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
    "API_KEY_SECRET": "x",
    "BACKEND_DOMAIN": "localhost",
    "FRONTEND_DOMAIN": "localhost",
    "ENV": "local",
    "TELER_API_KEY": "x",
    "BASE_ELEVENLABS_WEBSOCKET_URL": "wss://localhost",
    "DEFAULT_AGENT_ID": "agent_1",
    "FOLLOWUPCALL_AGENT_ID": "agent_2",
}

ACCOUNT_ID = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
NOW = datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc)


def load_backend(backend_path: str):
    """Import the backend package with settings satisfied by dummy values."""
    for key, value in BACKEND_ENV.items():
        os.environ.setdefault(key, value)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    import app  # noqa: F401  (validates the package imports)


def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_app():
    """Mount the real public v1 router with auth and the DB session overridden."""
    from fastapi import FastAPI

    from app.api.routes.public.api import external_router
    from app.db.database import get_db_session
    from app.utils.auth import verify_api_key

    api = FastAPI()
    api.include_router(external_router)

    account = SimpleNamespace(id=ACCOUNT_ID, is_active=True, key="test_api_key")
    api.dependency_overrides[verify_api_key] = lambda: account

    async def _no_db():
        yield None

    api.dependency_overrides[get_db_session] = _no_db
    return api


class LiveServer:
    """Serve an ASGI app on localhost for the duration of a test session."""

    def __init__(self, api):
        import uvicorn

        self.port = free_port()
        self._server = uvicorn.Server(
            uvicorn.Config(api, host="127.0.0.1", port=self.port, log_level="error")
        )
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/api/v1"

    def start(self, timeout: float = 30.0) -> "LiveServer":
        self._thread.start()
        deadline = threading.Event()
        waited = 0.0
        while not self._server.started and waited < timeout:
            deadline.wait(0.05)
            waited += 0.05
        if not self._server.started:
            raise RuntimeError("live server did not start")
        return self

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)


# --------------------------------------------------------------------------
# Fakes shaped to satisfy the backend's response models (from_attributes=True)
# --------------------------------------------------------------------------

SECRET_ID = uuid.UUID("00000000-0000-0000-0000-0000000000e1")


def fake_secret(name: str = "prod-secret", secret_id: uuid.UUID = None):
    return SimpleNamespace(
        id=secret_id or SECRET_ID,
        name=name,
        secret_value="whsec_abc123",
        rotated_at=None,
        created_at=NOW,
        needs_rotation=False,
        sip_trunks=[],
        voice_apps=[],
        secret=None,
    )


def fake_location():
    return SimpleNamespace(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000b1"),
        name="New York",
        region_code="NY",
        country_code="US",
        country_name="United States",
    )


def fake_vn(name: str = "Support Line", number: str = "+15550001111"):
    return SimpleNamespace(
        id=uuid.UUID("00000000-0000-0000-0000-0000000000c1"),
        account_id=ACCOUNT_ID,
        name=name,
        number=number,
        location=fake_location(),
        call_app=None,
        voice_app=None,
        sip_trunk=None,
    )


def fake_trunk(name: str = "Main Trunk"):
    return SimpleNamespace(
        uuid=uuid.UUID("00000000-0000-0000-0000-0000000000d1"),
        id=1,
        name=name,
        domain_name="trunk.example.com",
        account_id=ACCOUNT_ID,
        channel_limit=10,
        cps_limit=5,
        recording_enabled=True,
        secure=False,
        transport="tcp",
        is_active=True,
        authentication_type="credential",
        auth_ip_addresses=["10.0.0.1"],
        auth_credential_usernames=["sipuser"],
        sip_route=None,
        webhook_url=None,
        webhook_api_version="2026-06-01",
        created_at=NOW,
        updated_at=None,
        secret=None,
        secret_id=None,
        secret_name=None,
    )
