from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from teler import exceptions
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResource,
    BaseResourceManager,
    CursorPage,
    validate_pagination,
)

PATHS: Dict[str, str] = {
    "list": "/virtual-numbers",
    "assign": "/virtual-numbers/assign",
    "unassign": "/virtual-numbers/unassign",
    "update": "/virtual-numbers/{}",
}


@dataclass
class VirtualNumberResource(BaseResource):
    """Represents a virtual number returned by the Teler API."""
    id: str
    account_id: Optional[str]
    name: Optional[str]
    number: Optional[str]
    location: Optional[Dict[str, Any]]
    voice_app: Optional[Dict[str, Any]]
    sip_trunk: Optional[Dict[str, Any]]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class VNActionResult(BaseResource):
    """Result of a virtual number assign/unassign request."""
    success: bool
    message: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


def _build_filter_params(
    search: Optional[str],
    location: Optional[List[str]],
    voice_app: Optional[List[str]],
    sip_trunk: Optional[List[str]],
    limit: Optional[int] = None,
    cursor_after: Optional[str] = None,
    cursor_before: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the query params for virtual number endpoints, dropping unset values."""
    validate_pagination(limit, cursor_after, cursor_before)
    params: Dict[str, Any] = {
        "search": search,
        "location": location,
        "voice_app": voice_app,
        "sip_trunk": sip_trunk,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


def _validate_selection(
    vn_ids: Optional[List[str]], apply_to_all: Optional[bool]
) -> None:
    """The API requires either explicit vn_ids or apply_to_all."""
    if not vn_ids and not apply_to_all:
        raise exceptions.BadParametersException(
            param="vn_ids",
            msg="Provide vn_ids or set apply_to_all=True.",
        )


def _validate_assign_target(
    voice_app_id: Optional[str], sip_trunk_id: Optional[str]
) -> None:
    """A virtual number is assigned to exactly one of a voice app or SIP trunk."""
    if not voice_app_id and not sip_trunk_id:
        raise exceptions.BadParametersException(
            param="voice_app_id",
            msg="Provide either voice_app_id or sip_trunk_id.",
        )
    if voice_app_id and sip_trunk_id:
        raise exceptions.BadParametersException(
            param="voice_app_id",
            msg="A virtual number cannot be assigned to both a voice app and a SIP trunk.",
        )


def _build_assign_payload(
    vn_ids: Optional[List[str]],
    apply_to_all: Optional[bool],
    voice_app_id: Optional[str],
    sip_trunk_id: Optional[str],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "vn_ids": vn_ids,
        "apply_to_all": apply_to_all,
        "voice_app_id": voice_app_id,
        "sip_trunk_id": sip_trunk_id,
    }
    return {k: v for k, v in payload.items() if v is not None}


def _unwrap(body: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap a ``{"data": {...}}`` envelope if present, else return body as-is."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _to_cursor_page(body: Dict[str, Any]) -> CursorPage:
    """Wrap a raw list response body into a typed CursorPage of VirtualNumberResource."""
    return CursorPage(
        data=[VirtualNumberResource(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class VirtualNumberResourceManager(BaseResourceManager):
    """Synchronous manager for virtual number resources."""
    def __init__(self, client: Any):
        super().__init__(client, VirtualNumberResource, PATHS)

    def list(
        self,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List virtual numbers, optionally filtered, as a cursor-paginated page.
        """
        params = _build_filter_params(
            search, location, voice_app, sip_trunk,
            limit, cursor_after, cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    def assign(
        self,
        vn_ids: Optional[List[str]] = None,
        apply_to_all: bool = False,
        voice_app_id: Optional[str] = None,
        sip_trunk_id: Optional[str] = None,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
    ) -> VNActionResult:
        """
        Assign virtual numbers to a voice app or SIP trunk.

        Pass explicit ``vn_ids``, or ``apply_to_all=True`` combined with the
        filter query params (``search``, ``location``, ``voice_app``,
        ``sip_trunk``) to assign every matching number.
        """
        _validate_selection(vn_ids, apply_to_all)
        _validate_assign_target(voice_app_id, sip_trunk_id)
        params = _build_filter_params(search, location, voice_app, sip_trunk)
        payload = _build_assign_payload(
            vn_ids, apply_to_all, voice_app_id, sip_trunk_id
        )
        res = self.client.request(
            "POST", self.paths["assign"], params=params, json=payload
        )
        return VNActionResult(_unwrap(res.json()))

    def unassign(
        self,
        vn_ids: Optional[List[str]] = None,
        apply_to_all: bool = False,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
    ) -> VNActionResult:
        """
        Unassign virtual numbers from their voice app or SIP trunk.

        Pass explicit ``vn_ids``, or ``apply_to_all=True`` combined with the
        filter query params to unassign every matching number.
        """
        _validate_selection(vn_ids, apply_to_all)
        params = _build_filter_params(search, location, voice_app, sip_trunk)
        payload = _build_assign_payload(vn_ids, apply_to_all, None, None)
        res = self.client.request(
            "POST", self.paths["unassign"], params=params, json=payload
        )
        return VNActionResult(_unwrap(res.json()))

    def update(
        self,
        vn_id: str,
        name: Optional[str] = None,
    ) -> VirtualNumberResource:
        """
        Update a virtual number by its id.
        """
        payload: Dict[str, Any] = {"name": name}
        payload = {k: v for k, v in payload.items() if v is not None}
        res = self.client.request(
            "PATCH", self.paths["update"].format(vn_id), json=payload
        )
        return cast(VirtualNumberResource, self.resource(_unwrap(res.json())))


class AsyncVirtualNumberResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for virtual number resources."""
    def __init__(self, client: Any):
        super().__init__(client, VirtualNumberResource, PATHS)

    async def list(
        self,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list virtual numbers as a cursor-paginated page.
        """
        params = _build_filter_params(
            search, location, voice_app, sip_trunk,
            limit, cursor_after, cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    async def assign(
        self,
        vn_ids: Optional[List[str]] = None,
        apply_to_all: bool = False,
        voice_app_id: Optional[str] = None,
        sip_trunk_id: Optional[str] = None,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
    ) -> VNActionResult:
        """
        Asynchronously assign virtual numbers to a voice app or SIP trunk.
        """
        _validate_selection(vn_ids, apply_to_all)
        _validate_assign_target(voice_app_id, sip_trunk_id)
        params = _build_filter_params(search, location, voice_app, sip_trunk)
        payload = _build_assign_payload(
            vn_ids, apply_to_all, voice_app_id, sip_trunk_id
        )
        res = await self.client.request(
            "POST", self.paths["assign"], params=params, json=payload
        )
        return VNActionResult(_unwrap(res.json()))

    async def unassign(
        self,
        vn_ids: Optional[List[str]] = None,
        apply_to_all: bool = False,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        voice_app: Optional[List[str]] = None,
        sip_trunk: Optional[List[str]] = None,
    ) -> VNActionResult:
        """
        Asynchronously unassign virtual numbers from their voice app or SIP trunk.
        """
        _validate_selection(vn_ids, apply_to_all)
        params = _build_filter_params(search, location, voice_app, sip_trunk)
        payload = _build_assign_payload(vn_ids, apply_to_all, None, None)
        res = await self.client.request(
            "POST", self.paths["unassign"], params=params, json=payload
        )
        return VNActionResult(_unwrap(res.json()))

    async def update(
        self,
        vn_id: str,
        name: Optional[str] = None,
    ) -> VirtualNumberResource:
        """
        Asynchronously update a virtual number by its id.
        """
        payload: Dict[str, Any] = {"name": name}
        payload = {k: v for k, v in payload.items() if v is not None}
        res = await self.client.request(
            "PATCH", self.paths["update"].format(vn_id), json=payload
        )
        return cast(VirtualNumberResource, self.resource(_unwrap(res.json())))
