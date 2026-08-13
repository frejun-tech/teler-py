from importlib import metadata
from typing import Dict, Optional

import httpx

from teler import constants, exceptions
from teler.resources.events import (AsyncEventResourceManager, EventResourceManager)
from teler.resources.recordings import (AsyncRecordingResourceManager, RecordingResourceManager)
from teler.resources.secrets import (AsyncSecretResourceManager, SecretResourceManager)
from teler.resources.sip.sip import AsyncSipResourceManager, SipResourceManager
from teler.resources.virtual_numbers import (AsyncVirtualNumberResourceManager, VirtualNumberResourceManager)
from teler.resources.voice.voice import AsyncVoiceResourceManager, VoiceResourceManager

try:
    __version__ = metadata.version("teler")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

DEFAULT_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": f"teler/{__version__} (python-sdk)",
}

STATUS_EXCEPTIONS = {
    400: exceptions.BadParametersException,
    401: exceptions.UnauthorizedException,
    403: exceptions.ForbiddenException,
    404: exceptions.NotFoundException,
    409: exceptions.ConflictException,
    410: exceptions.GoneException,
    422: exceptions.UnprocessableRequestException,
    429: exceptions.RateLimitException,
    500: exceptions.InternalServerErrorException,
    501: exceptions.NotImplementedException,
}


def _raise_for_status(res: httpx.Response) -> None:
    """
    Map a non-2xx/3xx HTTP response to an SDK exception.

    Only raises for status codes >= 400; redirects (3xx) pass through
    untouched so recording downloads (302 + Location) keep working.
    """
    if res.status_code < 400:
        return

    try:
        body = res.json()
    except (ValueError, TypeError):
        body = {}

    message = (
        body.get("message")
        if isinstance(body, dict)
        else None
    ) or f"Request failed with status {res.status_code}."

    details = (
        body.get("errors")
        if isinstance(body, dict)
        else None
    )

    exc = STATUS_EXCEPTIONS.get(
        res.status_code,
        exceptions.TelerException,
    )

    raise exc(
        msg=message,
        details=details,
        code=res.status_code,
    )


class Client:
    """
    Synchronous HTTP Client for the Teler API.

    Usage:
        with Client(api_key="...") as client:
            ...
    """
    def __init__(self, api_key: str = "", headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Initialize the synchronous Teler API client.

        Args:
            api_key (str): The API key for authentication.
            headers (Optional[Dict[str, str]]): Additional headers to include in requests.
            **kwargs: Additional arguments passed to httpx.Client.
        """
        if not api_key:
            raise exceptions.BadParametersException("api_key is required")
        self.api_key = api_key
        merged_headers = {
            **(headers or {}),
            **DEFAULT_REQUEST_HEADERS,
            "X-Api-Key": self.api_key,
        }
        base_url = kwargs.pop("base_url", constants.TELER_BASE_URL)
        self.httpx_client = httpx.Client(
            base_url=base_url,
            headers={
                k.lower(): v
                for k, v in merged_headers.items()
            },
            **kwargs,
        )
        self.voice = VoiceResourceManager(self)
        self.events = EventResourceManager(self)
        self.recordings = RecordingResourceManager(self)
        self.virtual_numbers = VirtualNumberResourceManager(self)
        self.sip = SipResourceManager(self)
        self.secrets = SecretResourceManager(self)

    def request(self, *args, **kwargs) -> httpx.Response:
        """
        Make a synchronous HTTP request using the underlying httpx.Client.
        """
        res = self.httpx_client.request(*args, **kwargs)
        _raise_for_status(res)
        return res

    def close(self):
        """
        Close the underlying httpx.Client.
        """
        self.httpx_client.close()

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context and close the client.
        """
        self.close()


class AsyncClient:
    """
    Asynchronous HTTP Client for the Teler API.

    Usage:
        async with AsyncClient(api_key="...") as client:
            ...
    """
    def __init__(self, api_key: str = "", headers: Optional[Dict[str, str]] = None, **kwargs):
        """
        Initialize the asynchronous Teler API client.

        Args:
            api_key (str): The API key for authentication.
            headers (Optional[Dict[str, str]]): Additional headers to include in requests.
            **kwargs: Additional arguments passed to httpx.AsyncClient.
        """
        if not api_key:
            raise exceptions.BadParametersException("api_key is required")
        self.api_key = api_key
        merged_headers = {
            **(headers or {}),
            **DEFAULT_REQUEST_HEADERS,
            "X-Api-Key": self.api_key,
        }
        base_url = kwargs.pop("base_url", constants.TELER_BASE_URL)
        self.httpx_client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                k.lower(): v
                for k, v in merged_headers.items()
            },
            **kwargs,
        )
        self.voice = AsyncVoiceResourceManager(self)
        self.events = AsyncEventResourceManager(self)
        self.recordings = AsyncRecordingResourceManager(self)
        self.virtual_numbers = AsyncVirtualNumberResourceManager(self)
        self.sip = AsyncSipResourceManager(self)
        self.secrets = AsyncSecretResourceManager(self)

    async def request(self, *args, **kwargs) -> httpx.Response:
        """
        Make an asynchronous HTTP request using the underlying httpx.AsyncClient.
        """
        res = await self.httpx_client.request(*args, **kwargs)
        _raise_for_status(res)
        return res

    async def aclose(self):
        """
        Close the underlying httpx.AsyncClient.
        """
        await self.httpx_client.aclose()

    async def __aenter__(self):
        """
        Enter the async runtime context related to this object.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the async runtime context and close the client.
        """
        await self.aclose()
