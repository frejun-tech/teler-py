from dataclasses import dataclass, field
from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResource,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
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
    secret_value: Optional[str] = field(repr=False)
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
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

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
        params = build_params(
            search=search,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SecretResource)

    def retrieve(self, secret_id: str) -> SecretResource:
        """
        Retrieve a single secret by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(secret_id))
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

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
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

    def delete(self, secret_id: str) -> DeleteResult:
        """
        Delete a secret by its id.
        """
        res = self.client.request("DELETE", self.paths["delete"].format(secret_id))
        return DeleteResult(unwrap_data(res.json()))


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
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

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
        params = build_params(
            search=search,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SecretResource)

    async def retrieve(self, secret_id: str) -> SecretResource:
        """
        Asynchronously retrieve a single secret by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(secret_id))
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

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
        return cast(SecretResource, self.resource(unwrap_data(res.json())))

    async def delete(self, secret_id: str) -> DeleteResult:
        """
        Asynchronously delete a secret by its id.
        """
        res = await self.client.request("DELETE", self.paths["delete"].format(secret_id))
        return DeleteResult(unwrap_data(res.json()))
