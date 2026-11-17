import random
import time
from typing import Any, Dict, Optional

import httpx

from teler import constants, exceptions
from teler._version import __version__
from teler.resources.events import (AsyncEventResourceManager, EventResourceManager)
from teler.resources.recordings import (AsyncRecordingResourceManager, RecordingResourceManager)
from teler.resources.secrets import (AsyncSecretResourceManager, SecretResourceManager)
from teler.resources.sip.sip import AsyncSipResourceManager, SipResourceManager
from teler.resources.virtual_numbers import (AsyncVirtualNumberResourceManager, VirtualNumberResourceManager)
from teler.resources.voice.voice import AsyncVoiceResourceManager, VoiceResourceManager

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


def _merge_headers(
    api_key: str, headers: Optional[Dict[str, str]]
) -> Dict[str, str]:
    """
    Merge caller headers over the SDK defaults, keyed case-insensitively.

    Caller headers take precedence over ``DEFAULT_REQUEST_HEADERS``.
    ``x-api-key`` always comes from the ``api_key`` argument.
    """
    merged = {k.lower(): v for k, v in DEFAULT_REQUEST_HEADERS.items()}
    merged.update({k.lower(): v for k, v in (headers or {}).items()})
    merged["x-api-key"] = api_key
    return merged


def _parse_retry_after(header_value: Optional[str]) -> Optional[float]:
    if not header_value:
        return None
    # Try seconds first
    try:
        # Check if it's all digits (possibly with spaces)
        seconds = float(str(header_value).strip())
        if seconds >= 0:
            return seconds * 1000.0
    except Exception:
        pass
    # Try HTTP date
    try:
        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(header_value)
        if dt is not None:
            import datetime

            now = datetime.datetime.now(datetime.timezone.utc)
            delay = (dt - now).total_seconds() * 1000.0
            return max(0.0, delay)
    except Exception:
        pass
    return None


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
            headers (Optional[Dict[str, str]]): Additional headers to include in
                requests. These take precedence over the SDK defaults
                (Content-Type, Accept, User-Agent); x-api-key is always set from
                api_key and cannot be overridden here.
            **kwargs: Additional arguments passed to httpx.Client.
        """
        if not api_key:
            raise exceptions.BadParametersException(
                param="api_key", msg="api_key is required"
            )
        self.api_key = api_key
        base_url = kwargs.pop("base_url", constants.TELER_BASE_URL)
        self.httpx_client = httpx.Client(
            base_url=base_url,
            headers=_merge_headers(self.api_key, headers),
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
        # Extract retry options
        retry = kwargs.pop("retry", None)
        base_retry_delay_ms = kwargs.pop("base_retry_delay_ms", None)
        max_retry_delay_ms = kwargs.pop("max_retry_delay_ms", None)
        timeout = kwargs.pop("timeout", None)

        method = args[0] if len(args) > 0 else kwargs.get("method", "")

        # Set defaults based on method
        if retry is None:
            if str(method).upper() == "GET":
                retry = True
                if base_retry_delay_ms is None:
                    base_retry_delay_ms = 100
            else:  # POST, PATCH, DELETE, etc.
                retry = False
                if base_retry_delay_ms is None:
                    base_retry_delay_ms = 500
        elif base_retry_delay_ms is None:
            base_retry_delay_ms = 500

        if max_retry_delay_ms is None:
            max_retry_delay_ms = getattr(constants, "MAX_RETRY_DELAY_MS", 2000)

        max_retries = getattr(constants, "RETRY_COUNT", 3) if retry else 0

        # Apply timeout if provided
        if timeout is not None:
            # Request timeouts are milliseconds; httpx expects seconds.
            kwargs["timeout"] = timeout / 1000.0

        if max_retries == 0:
            res = self.httpx_client.request(*args, **kwargs)
            _raise_for_status(res)
            return res

        for attempt in range(max_retries + 1):
            res = None
            try:
                res = self.httpx_client.request(*args, **kwargs)
                _raise_for_status(res)
                return res
            except (httpx.RequestError, exceptions.TelerException) as exc:
                # Check if retryable
                retryable = False
                if isinstance(exc, httpx.RequestError):
                    retryable = True
                elif isinstance(exc, exceptions.TelerException) and hasattr(exc, "code"):
                    if exc.code in (429, 503):
                        retryable = True
                if not retryable or attempt == max_retries:
                    raise
                # Calculate delay. Retry-After is a response header, so read it
                # from the response itself rather than from the exception body.
                retry_after_ms = None
                if res is not None:
                    retry_after_ms = _parse_retry_after(
                        res.headers.get("retry-after")
                    )
                exponential_delay = min(
                    max_retry_delay_ms, base_retry_delay_ms * (2**attempt)
                )
                delay_ms = retry_after_ms if retry_after_ms is not None else random.random() * exponential_delay
                time.sleep(delay_ms / 1000.0)

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
            headers (Optional[Dict[str, str]]): Additional headers to include in
                requests. These take precedence over the SDK defaults
                (Content-Type, Accept, User-Agent); x-api-key is always set from
                api_key and cannot be overridden here.
            **kwargs: Additional arguments passed to httpx.AsyncClient.
        """
        if not api_key:
            raise exceptions.BadParametersException(
                param="api_key", msg="api_key is required"
            )
        self.api_key = api_key
        base_url = kwargs.pop("base_url", constants.TELER_BASE_URL)
        self.httpx_client = httpx.AsyncClient(
            base_url=base_url,
            headers=_merge_headers(self.api_key, headers),
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
        retry = kwargs.pop("retry", None)
        base_retry_delay_ms = kwargs.pop("base_retry_delay_ms", None)
        max_retry_delay_ms = kwargs.pop("max_retry_delay_ms", None)
        timeout = kwargs.pop("timeout", None)

        method = args[0] if len(args) > 0 else kwargs.get("method", "")

        if retry is None:
            if str(method).upper() == "GET":
                retry = True
                if base_retry_delay_ms is None:
                    base_retry_delay_ms = 100
            else:  # POST, PATCH, DELETE, etc.
                retry = False
                if base_retry_delay_ms is None:
                    base_retry_delay_ms = 500
        elif base_retry_delay_ms is None:
            base_retry_delay_ms = 500

        if max_retry_delay_ms is None:
            max_retry_delay_ms = getattr(constants, "MAX_RETRY_DELAY_MS", 2000)

        max_retries = getattr(constants, "RETRY_COUNT", 3) if retry else 0

        if timeout is not None:
            # Request timeouts are milliseconds; httpx expects seconds.
            kwargs["timeout"] = timeout / 1000.0

        if max_retries == 0:
            res = await self.httpx_client.request(*args, **kwargs)
            _raise_for_status(res)
            return res

        for attempt in range(max_retries + 1):
            res = None
            try:
                res = await self.httpx_client.request(*args, **kwargs)
                _raise_for_status(res)
                return res
            except (httpx.RequestError, exceptions.TelerException) as exc:
                retryable = False
                if isinstance(exc, httpx.RequestError):
                    retryable = True
                elif isinstance(exc, exceptions.TelerException) and hasattr(exc, "code"):
                    if exc.code in (429, 503):
                        retryable = True
                if not retryable or attempt == max_retries:
                    raise
                # Retry-After is a response header, so read it from the response
                # itself rather than from the exception body.
                retry_after_ms = None
                if res is not None:
                    retry_after_ms = _parse_retry_after(
                        res.headers.get("retry-after")
                    )
                exponential_delay = min(
                    max_retry_delay_ms, base_retry_delay_ms * (2**attempt)
                )
                delay_ms = retry_after_ms if retry_after_ms is not None else random.random() * exponential_delay
                import asyncio

                await asyncio.sleep(delay_ms / 1000.0)

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
