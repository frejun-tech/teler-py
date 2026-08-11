from dataclasses import dataclass
from typing import Any, Dict, Optional

from teler import exceptions
from teler.resources.base import (AsyncBaseResourceManager, BaseResource,
                                  BaseResourceManager)

PATHS: Dict[str, str] = {
    "retrieve": "/recordings/",
}


@dataclass
class RecordingResource(BaseResource):
    """Represents a signed URL for downloading a call recording."""
    url: Optional[str]
    recording_id: str
    expires_in: int

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


def _validate_recording_id(recording_id: str) -> None:
    if not recording_id:
        raise exceptions.BadParametersException(
            param="recording_id", msg="recording_id is a required parameter."
        )


def _to_recording(res, recording_id: str, expires_in: int) -> RecordingResource:
    """Build a RecordingResource from a 302 Location header or a JSON body.

    Prefers the ``Location`` header (302 redirect); falls back to a JSON body
    carrying ``url``/``expires_in`` (optionally wrapped in a ``data`` envelope).
    """
    url = res.headers.get("location")
    if not url and res.headers.get("content-type", "").startswith("application/json"):
        body = res.json()
        if isinstance(body, dict):
            body = body.get("data", body)
            url = body.get("url")
            expires_in = body.get("expires_in", expires_in)
    if not url:
        raise exceptions.TelerException(
            msg="Recording response did not include a signed URL."
        )
    return RecordingResource(
        {"url": url, "recording_id": recording_id, "expires_in": expires_in}
    )


class RecordingResourceManager(BaseResourceManager):
    """Synchronous manager for recording resources."""
    def __init__(self, client: Any):
        super().__init__(client, RecordingResource, PATHS)

    def retrieve(
        self, recording_id: str, expires_in: int = 900
    ) -> RecordingResource:
        """
        Retrieve a short-lived signed download URL for a call recording.
        """
        _validate_recording_id(recording_id)
        res = self.client.request(
            "GET",
            self.paths["retrieve"],
            params={"recording_id": recording_id, "expires_in": expires_in},
            follow_redirects=False,
        )
        return _to_recording(res, recording_id, expires_in)


class AsyncRecordingResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for recording resources."""
    def __init__(self, client: Any):
        super().__init__(client, RecordingResource, PATHS)

    async def retrieve(
        self, recording_id: str, expires_in: int = 900
    ) -> RecordingResource:
        """
        Asynchronously retrieve a short-lived signed download URL for a recording.
        """
        _validate_recording_id(recording_id)
        res = await self.client.request(
            "GET",
            self.paths["retrieve"],
            params={"recording_id": recording_id, "expires_in": expires_in},
            follow_redirects=False,
        )
        return _to_recording(res, recording_id, expires_in)
