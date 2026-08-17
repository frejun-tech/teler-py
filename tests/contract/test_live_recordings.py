"""Recordings, driven against the real API over a real socket.

This is the test that a mock cannot write. The SDK used to request
``/recordings/`` with a trailing slash; the API serves ``/recordings``. Starlette
normalises the slash with a redirect back to the API itself, so the SDK returned
the Teler API URL as the "signed URL" and raised nothing. A respx mock asserts
whatever path the SDK already uses, so it agreed with the bug. Real routing does
not.
"""
import uuid
from types import SimpleNamespace

import httpx
import pytest

from teler.resources.recordings import RecordingResource

ROUTE = "app.api.routes.public.v1.utilities"
SIGNED_URL = "https://s3.amazonaws.com/test-bucket/signed.mp3?X-Amz-Signature=abc"


@pytest.fixture
def stub_s3(patch_crud):
    """Make ownership pass and S3 return a known presigned URL."""
    async def _owns(db, account_id, rec_uuid):
        return SimpleNamespace(id=rec_uuid)

    patch_crud(f"{ROUTE}.verify_recording_ownership", _owns)
    patch_crud(
        f"{ROUTE}.s3_client",
        SimpleNamespace(
            generate_presigned_url=lambda **kw: SIGNED_URL,
            exceptions=SimpleNamespace(NoSuchKey=type("NoSuchKey", (Exception,), {})),
        ),
    )


def _rec_id() -> str:
    from app.utils.identifiers import recording_id_from_uuid

    return recording_id_from_uuid(uuid.UUID("00000000-0000-0000-0000-0000000000f1"))


def test_retrieve_returns_the_real_signed_url(client, stub_s3):
    rec = client.recordings.retrieve(_rec_id())

    assert isinstance(rec, RecordingResource)
    assert rec.url == SIGNED_URL, (
        "the SDK must surface the S3 signed URL, not a Teler API URL"
    )
    assert "amazonaws" in rec.url
    assert "/api/v1/recordings" not in rec.url


def test_expires_in_reaches_the_signer(client, patch_crud):
    seen = {}

    async def _owns(db, account_id, rec_uuid):
        return SimpleNamespace(id=rec_uuid)

    def _presign(**kw):
        seen["ExpiresIn"] = kw.get("ExpiresIn")
        return SIGNED_URL

    patch_crud(f"{ROUTE}.verify_recording_ownership", _owns)
    patch_crud(
        f"{ROUTE}.s3_client",
        SimpleNamespace(
            generate_presigned_url=_presign,
            exceptions=SimpleNamespace(NoSuchKey=type("NoSuchKey", (Exception,), {})),
        ),
    )

    client.recordings.retrieve(_rec_id(), expires_in=1200)

    assert seen["ExpiresIn"] == 1200


def test_trailing_slash_would_redirect_to_the_api(live_api, stub_s3):
    """Documents the original defect at the HTTP layer.

    The correct path reaches the handler and yields an S3 URL. The old
    trailing-slash path yields a redirect pointing back at the API, which is
    what the SDK used to hand back to callers.
    """
    params = {"recording_id": _rec_id()}
    with httpx.Client(
        base_url=live_api.base_url,
        headers={"x-api-key": "test_api_key"},
        follow_redirects=False,
    ) as raw:
        good = raw.get("/recordings", params=params)
        bad = raw.get("/recordings/", params=params)

    assert good.headers["location"] == SIGNED_URL
    assert "amazonaws" in good.headers["location"]

    assert bad.status_code in (301, 307, 308)
    assert "/api/v1/recordings" in bad.headers["location"]
    assert "amazonaws" not in bad.headers["location"]


def test_sdk_never_requests_the_trailing_slash_path(client, stub_s3):
    from teler.resources.recordings import PATHS

    assert PATHS["retrieve"] == "/recordings"
    assert not PATHS["retrieve"].endswith("/")


def test_unknown_recording_id_is_rejected_by_real_validation(client):
    from teler import exceptions

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.recordings.retrieve("not-a-recording-id")


@pytest.mark.asyncio
async def test_async_retrieve_returns_signed_url(async_client, stub_s3):
    rec = await async_client.recordings.retrieve(_rec_id())

    assert isinstance(rec, RecordingResource)
    assert rec.url == SIGNED_URL
