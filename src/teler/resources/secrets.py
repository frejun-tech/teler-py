from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResource,
    BaseResourceManager,
    CursorPage,
    validate_pagination,
)

PATHS: Dict[str, str] = {
    "create": "/secrets",
    "list": "/secrets",
    "retrieve": "/secrets/{}",
    "update": "/secrets/{}",
    "delete": "/secrets/{}",
}


@dataclass
class SecretResource(BaseResource):
    """Represents a webhook signing secret returned by the Teler API."""
    id: str
    name: Optional[str]
    secret_value: Optional[str]
    rotated_at: Optional[str]
    created_at: Optional[str]
    needs_rotation: Optional[bool]
    sip_trunks: Optional[list]
    voice_apps: Optional[list]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class DeleteResult(BaseResource):
    """Result of a secret delete request."""
    success: bool
    message: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


def _build_list_params(
    search: Optional[str],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    """Build the query params for listing secrets, dropping unset values."""
    validate_pagination(limit, cursor_after, cursor_before)
    params: Dict[str, Any] = {
        "search": search,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


def _unwrap(body: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap a ``{"data": {...}}`` envelope if present, else return body as-is."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _to_cursor_page(body: Dict[str, Any]) -> CursorPage:
    """Wrap a raw list response body into a typed CursorPage of SecretResource."""
    return CursorPage(
        data=[SecretResource(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class SecretResourceManager(BaseResourceManager):
    """Synchronous manager for secret resources."""
    def __init__(self, client: Any):
        super().__init__(client, SecretResource, PATHS)

    def create(self, name: str) -> SecretResource:
        """
        Create a webhook signing secret.
        """
        res = self.client.request(
            "POST", self.paths["create"], json={"name": name}
        )
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    def list(
        self,
        search: Optional[str] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List secrets, optionally filtered, as a cursor-paginated page.
        """
        params = _build_list_params(search, limit, cursor_after, cursor_before)
        res = self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    def retrieve(self, secret_id: str) -> SecretResource:
        """
        Retrieve a single secret by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(secret_id))
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    def update(
        self,
        secret_id: str,
        name: Optional[str] = None,
        rotate: bool = False,
    ) -> SecretResource:
        """
        Update a secret by its id; pass ``rotate=True`` to rotate its value.
        """
        payload: Dict[str, Any] = {"name": name, "rotate": rotate}
        payload = {k: v for k, v in payload.items() if v is not None}
        res = self.client.request(
            "PATCH", self.paths["update"].format(secret_id), json=payload
        )
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    def delete(self, secret_id: str) -> DeleteResult:
        """
        Delete a secret by its id.
        """
        res = self.client.request("DELETE", self.paths["delete"].format(secret_id))
        return DeleteResult(_unwrap(res.json()))


class AsyncSecretResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for secret resources."""
    def __init__(self, client: Any):
        super().__init__(client, SecretResource, PATHS)

    async def create(self, name: str) -> SecretResource:
        """
        Asynchronously create a webhook signing secret.
        """
        res = await self.client.request(
            "POST", self.paths["create"], json={"name": name}
        )
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    async def list(
        self,
        search: Optional[str] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list secrets as a cursor-paginated page.
        """
        params = _build_list_params(search, limit, cursor_after, cursor_before)
        res = await self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    async def retrieve(self, secret_id: str) -> SecretResource:
        """
        Asynchronously retrieve a single secret by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(secret_id))
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    async def update(
        self,
        secret_id: str,
        name: Optional[str] = None,
        rotate: bool = False,
    ) -> SecretResource:
        """
        Asynchronously update a secret by its id; pass ``rotate=True`` to rotate it.
        """
        payload: Dict[str, Any] = {"name": name, "rotate": rotate}
        payload = {k: v for k, v in payload.items() if v is not None}
        res = await self.client.request(
            "PATCH", self.paths["update"].format(secret_id), json=payload
        )
        return cast(SecretResource, self.resource(_unwrap(res.json())))

    async def delete(self, secret_id: str) -> DeleteResult:
        """
        Asynchronously delete a secret by its id.
        """
        res = await self.client.request("DELETE", self.paths["delete"].format(secret_id))
        return DeleteResult(_unwrap(res.json()))
