from abc import ABC
from dataclasses import dataclass, field
from dataclasses import fields as dataclass_fields
from typing import Any, Dict, List, Optional, Type

from .. import exceptions


@dataclass
class BaseResource(ABC):
    """Base class for all resource objects."""

    def __init__(self, data: Dict[str, Any]):
        # Match only declared fields; raise on extra keys
        names = {f.name for f in dataclass_fields(self)}
        unknown = set(data) - names
        if unknown:
            raise TypeError(f"Unknown fields: {unknown}")
        for name in names:
            setattr(self, name, data.get(name))


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
    """Validate cursor pagination arguments before issuing a request.

    The API rejects a limit outside 1..max_limit and rejects both cursors being
    sent together. Neither rule appears in the OpenAPI schema, so both are
    checked here to fail fast instead of round-tripping to a 422.
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
        self, client: Any, resource: type[BaseResource], paths: Dict[str, str]
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
