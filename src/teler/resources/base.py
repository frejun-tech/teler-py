from abc import ABC
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from typing import Any, Dict, List, Optional, Type

from .. import exceptions


@dataclass
class BaseResource(ABC):
    """Base class for all resource objects.

    Declared fields are set from ``data``; undeclared keys are ignored.
    ``raw`` holds the full body.
    """

    def __init__(self, data: Dict[str, Any]):
        names = {f.name for f in dataclass_fields(self)}
        for name in names:
            setattr(self, name, data.get(name))
        # Not a dataclass field: absent from __repr__ and __eq__.
        self.raw = data


@dataclass
class CursorPage:
    """A single page of cursor-paginated results.

    Attributes:
        data (List[Any]): The resource objects on this page.
        next_cursor (Optional[str]): Cursor for the next page, if any.
        previous_cursor (Optional[str]): Cursor for the previous page, if any.
        has_more (bool): Whether more pages are available after this one.
    """

    data: List[Any] = field(default_factory=list)
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    has_more: bool = False


def validate_pagination(
    limit: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
    max_limit: int = 100,
) -> None:
    """Validate cursor pagination arguments.

    Raises ``BadParametersException`` if ``limit`` falls outside 1..max_limit
    or if both cursors are supplied.
    """
    if limit is not None and not 1 <= limit <= max_limit:
        raise exceptions.BadParametersException(
            param="limit",
            msg=f"limit must be between 1 and {max_limit}.",
        )
    if cursor_after is not None and cursor_before is not None:
        raise exceptions.BadParametersException(
            param="cursor_after",
            msg="cursor_after and cursor_before are mutually exclusive.",
        )


def unwrap_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap a ``{"data": {...}}`` envelope if present, else return body as-is."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def to_cursor_page(
    body: Dict[str, Any], resource_cls: Type[BaseResource]
) -> CursorPage:
    """Wrap a raw list response body into a typed CursorPage of ``resource_cls``."""
    return CursorPage(
        data=[resource_cls(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


def build_params(
    limit: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
    max_limit: int = 100,
    **filters: Any,
) -> Dict[str, Any]:
    """Build query params for a cursor-paginated endpoint, dropping unset values.

    Validates pagination against ``max_limit``.
    """
    validate_pagination(limit, cursor_after, cursor_before, max_limit)
    params: Dict[str, Any] = {
        **filters,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


class BaseResourceManager(ABC):
    """Base class for all resource managers."""

    def __init__(
        self, client: Any, resource: Type[BaseResource], paths: Dict[str, str]
    ):
        self.client = client
        self.resource = resource
        self.paths = paths

    def create(self, *args, **kwargs) -> BaseResource:
        raise exceptions.NotImplementedException(
            msg="Method 'create()' is not implemented."
        )

    def list(self) -> List[BaseResource]:
        if self.paths.get("list", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'list()' is not implemented."
            )
        res = self.client.request("GET", self.paths["list"])
        return [self.resource(item) for item in res.json()]

    def retrieve(self, id) -> BaseResource:
        if self.paths.get("retrieve", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'retrieve()' is not implemented."
            )
        res = self.client.request("GET", self.paths["retrieve"].format(id))
        return self.resource(res.json())

    def update(self, id) -> BaseResource:
        if self.paths.get("update", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'update()' is not implemented."
            )
        res = self.client.request("PATCH", self.paths["update"].format(id))
        return self.resource(res.json())

    def delete(self, id) -> None:
        if self.paths.get("delete", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'delete()' is not implemented."
            )
        _ = self.client.request("DELETE", self.paths["delete"].format(id))
        return None


class AsyncBaseResourceManager(ABC):
    """Base class for all async resource managers."""

    def __init__(
        self, client: Any, resource: Type[BaseResource], paths: Dict[str, str]
    ):
        self.client = client
        self.resource = resource
        self.paths = paths

    async def create(self, *args, **kwargs) -> BaseResource:
        raise exceptions.NotImplementedException(
            msg="Method 'create()' is not implemented."
        )

    async def list(self) -> List[BaseResource]:
        if self.paths.get("list", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'list()' is not implemented."
            )
        res = await self.client.request("GET", self.paths["list"])
        return [self.resource(item) for item in res.json()]

    async def retrieve(self, id) -> BaseResource:
        if self.paths.get("retrieve", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'retrieve()' is not implemented."
            )
        res = await self.client.request("GET", self.paths["retrieve"].format(id))
        return self.resource(res.json())

    async def update(self, id) -> BaseResource:
        if self.paths.get("update", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'update()' is not implemented."
            )
        res = await self.client.request("PATCH", self.paths["update"].format(id))
        return self.resource(res.json())

    async def delete(self, id) -> None:
        if self.paths.get("delete", None) is None:
            raise exceptions.NotImplementedException(
                msg="Method 'delete()' is not implemented."
            )
        _ = await self.client.request("DELETE", self.paths["delete"].format(id))
        return None
