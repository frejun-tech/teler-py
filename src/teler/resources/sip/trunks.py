from typing import Any, Dict, List, Optional, cast

from teler import exceptions
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
)
from teler.resources.virtual_numbers import VirtualNumberResource
from .types import DeleteResult, SipTrunkResource

PATHS: Dict[str, str] = {
    "create": "/sip/trunks",
    "list": "/sip/trunks",
    "retrieve": "/sip/trunks/{}",
    "update": "/sip/trunks/{}",
    "delete": "/sip/trunks/{}",
    "virtual_numbers": "/sip/trunks/{}/virtual-numbers",
}

MAX_AUTH_ADDRESSES = 5


def _validate_auth_fields(
    authentication_type: Optional[str],
    auth_credential: Optional[Dict[str, str]],
    auth_addresses: Optional[List[Dict[str, str]]],
    ip_acl_id: Optional[str] = None,
) -> None:
    """Check the auth pairing the API enforces but the schema does not describe.

    ``credential`` requires auth_credential and forbids both IP auth sources.
    ``IP`` takes exactly one of ``auth_addresses`` (up to five inline entries) or
    ``ip_acl_id`` (a shared, reusable list) — supplying both or neither is
    rejected.
    """
    if authentication_type == "credential":
        if not auth_credential:
            raise exceptions.BadParametersException(
                param="auth_credential",
                msg="auth_credential is required when authentication_type is 'credential'.",
            )
        if auth_addresses:
            raise exceptions.BadParametersException(
                param="auth_addresses",
                msg="auth_addresses cannot be used when authentication_type is 'credential'.",
            )
        if ip_acl_id is not None:
            raise exceptions.BadParametersException(
                param="ip_acl_id",
                msg="ip_acl_id cannot be used when authentication_type is 'credential'.",
            )
    elif authentication_type == "IP":
        if auth_addresses and ip_acl_id is not None:
            raise exceptions.BadParametersException(
                param="ip_acl_id",
                msg="Provide either auth_addresses or ip_acl_id, not both.",
            )
        if not auth_addresses and ip_acl_id is None:
            raise exceptions.BadParametersException(
                param="auth_addresses",
                msg=(
                    "auth_addresses or ip_acl_id is required when "
                    "authentication_type is 'IP'."
                ),
            )

    if auth_addresses is not None and len(auth_addresses) > MAX_AUTH_ADDRESSES:
        raise exceptions.BadParametersException(
            param="auth_addresses",
            msg=f"A maximum of {MAX_AUTH_ADDRESSES} authentication addresses are allowed.",
        )


def _build_trunk_payload(
    *,
    name: Optional[str] = None,
    domain_name: Optional[str] = None,
    authentication_type: Optional[str] = None,
    channel_limit: Optional[int] = None,
    recording: Optional[bool] = None,
    secure: Optional[bool] = None,
    transport: Optional[str] = None,
    is_active: Optional[bool] = None,
    webhook_url: Optional[str] = None,
    auth_credential: Optional[Dict[str, str]] = None,
    auth_addresses: Optional[List[Dict[str, str]]] = None,
    ip_acl_id: Optional[str] = None,
    inbound_route: Optional[Dict[str, Any]] = None,
    secret_id: Optional[str] = None,
    webhook_api_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a SIP trunk create/update payload, dropping unset values."""
    payload: Dict[str, Any] = {
        "name": name,
        "domain_name": domain_name,
        "authentication_type": authentication_type,
        "channel_limit": channel_limit,
        "recording": recording,
        "secure": secure,
        "transport": transport,
        "is_active": is_active,
        "webhook_url": webhook_url,
        "auth_credential": auth_credential,
        "auth_addresses": auth_addresses,
        "ip_acl_id": ip_acl_id,
        "inbound_route": inbound_route,
        "secret_id": secret_id,
        "webhook_api_version": webhook_api_version,
    }
    return {k: v for k, v in payload.items() if v is not None}


class SipTrunkResourceManager(BaseResourceManager):
    """Synchronous manager for SIP trunk resources."""
    def __init__(self, client: Any):
        super().__init__(client, SipTrunkResource, PATHS)

    def create(
        self,
        name: str,
        domain_name: str,
        authentication_type: str,
        channel_limit: Optional[int] = None,
        recording: Optional[bool] = None,
        secure: Optional[bool] = None,
        transport: Optional[str] = None,
        webhook_url: Optional[str] = None,
        auth_credential: Optional[Dict[str, str]] = None,
        auth_addresses: Optional[List[Dict[str, str]]] = None,
        ip_acl_id: Optional[str] = None,
        inbound_route: Optional[Dict[str, Any]] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
    ) -> SipTrunkResource:
        """
        Create a SIP trunk.

        ``authentication_type`` is either ``"credential"`` or ``"IP"``.
        ``auth_credential`` is ``{"username": ..., "password": ...}``;
        ``auth_addresses`` is a list of ``{"name": ..., "address": ...}``;
        ``inbound_route`` is ``{"name": ..., "sip_url": ..., "sip_user": ...}``.

        With ``"IP"``, authorise against exactly one of ``auth_addresses``
        (inline, up to five) or ``ip_acl_id`` (a reusable list from
        ``client.sip.ip_acls``).

        ``transport`` is ``"tls"``, ``"tcp"`` or ``"udp"``. Pass ``transport``
        or ``secure``, never both — the API rejects a payload carrying both, as
        ``transport`` supersedes ``secure``. When only ``secure`` is given the
        API derives the transport from it (``True`` → ``"tls"``, else
        ``"tcp"``). ``"udp"`` is only accepted with credential authentication.
        """
        _validate_auth_fields(
            authentication_type, auth_credential, auth_addresses, ip_acl_id
        )
        payload = _build_trunk_payload(
            name=name,
            domain_name=domain_name,
            authentication_type=authentication_type,
            channel_limit=channel_limit,
            recording=recording,
            secure=secure,
            transport=transport,
            webhook_url=webhook_url,
            auth_credential=auth_credential,
            auth_addresses=auth_addresses,
            ip_acl_id=ip_acl_id,
            inbound_route=inbound_route,
            secret_id=secret_id,
            webhook_api_version=webhook_api_version,
        )
        res = self.client.request("POST", self.paths["create"], json=payload)
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List SIP trunks, optionally filtered, as a cursor-paginated page.
        """
        params = build_params(
            search=search,
            status=status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SipTrunkResource)

    def retrieve(self, trunk_id: str) -> SipTrunkResource:
        """
        Retrieve a single SIP trunk by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(trunk_id))
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    def update(
        self,
        trunk_id: str,
        name: Optional[str] = None,
        channel_limit: Optional[int] = None,
        recording: Optional[bool] = None,
        secure: Optional[bool] = None,
        transport: Optional[str] = None,
        is_active: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        authentication_type: Optional[str] = None,
        auth_credential: Optional[Dict[str, str]] = None,
        auth_addresses: Optional[List[Dict[str, str]]] = None,
        ip_acl_id: Optional[str] = None,
        inbound_route: Optional[Dict[str, Any]] = None,
        secret_id: Optional[str] = None,
    ) -> SipTrunkResource:
        """
        Update a SIP trunk by its id.

        Pass ``transport`` or ``secure``, never both — the API rejects both
        together. Changing the authentication of a trunk requires
        ``authentication_type`` alongside whichever of ``auth_credential``,
        ``auth_addresses`` or ``ip_acl_id`` you supply.
        """
        _validate_auth_fields(
            authentication_type, auth_credential, auth_addresses, ip_acl_id
        )
        payload = _build_trunk_payload(
            name=name,
            authentication_type=authentication_type,
            channel_limit=channel_limit,
            recording=recording,
            secure=secure,
            transport=transport,
            is_active=is_active,
            webhook_url=webhook_url,
            auth_credential=auth_credential,
            auth_addresses=auth_addresses,
            ip_acl_id=ip_acl_id,
            inbound_route=inbound_route,
            secret_id=secret_id,
            webhook_api_version=webhook_api_version,
        )
        res = self.client.request(
            "PATCH", self.paths["update"].format(trunk_id), json=payload
        )
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    def delete(self, trunk_id: str) -> DeleteResult:
        """
        Delete a SIP trunk by its id.
        """
        res = self.client.request("DELETE", self.paths["delete"].format(trunk_id))
        return DeleteResult(unwrap_data(res.json()))

    def list_virtual_numbers(
        self,
        trunk_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List the virtual numbers assigned to a SIP trunk.
        """
        params = build_params(
            search=search,
            location=location,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(trunk_id),
            params=params,
        )
        return to_cursor_page(res.json(), VirtualNumberResource)


class AsyncSipTrunkResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for SIP trunk resources."""
    def __init__(self, client: Any):
        super().__init__(client, SipTrunkResource, PATHS)

    async def create(
        self,
        name: str,
        domain_name: str,
        authentication_type: str,
        channel_limit: Optional[int] = None,
        recording: Optional[bool] = None,
        secure: Optional[bool] = None,
        transport: Optional[str] = None,
        webhook_url: Optional[str] = None,
        auth_credential: Optional[Dict[str, str]] = None,
        auth_addresses: Optional[List[Dict[str, str]]] = None,
        ip_acl_id: Optional[str] = None,
        inbound_route: Optional[Dict[str, Any]] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
    ) -> SipTrunkResource:
        """
        Asynchronously create a SIP trunk.

        ``transport`` is ``"tls"``, ``"tcp"`` or ``"udp"``. Pass ``transport``
        or ``secure``, never both — the API rejects both together. ``"udp"``
        is only accepted with credential authentication.
        """
        _validate_auth_fields(
            authentication_type, auth_credential, auth_addresses, ip_acl_id
        )
        payload = _build_trunk_payload(
            name=name,
            domain_name=domain_name,
            authentication_type=authentication_type,
            channel_limit=channel_limit,
            recording=recording,
            secure=secure,
            transport=transport,
            webhook_url=webhook_url,
            auth_credential=auth_credential,
            auth_addresses=auth_addresses,
            ip_acl_id=ip_acl_id,
            inbound_route=inbound_route,
            secret_id=secret_id,
            webhook_api_version=webhook_api_version,
        )
        res = await self.client.request("POST", self.paths["create"], json=payload)
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    async def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list SIP trunks as a cursor-paginated page.
        """
        params = build_params(
            search=search,
            status=status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SipTrunkResource)

    async def retrieve(self, trunk_id: str) -> SipTrunkResource:
        """
        Asynchronously retrieve a single SIP trunk by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(trunk_id))
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    async def update(
        self,
        trunk_id: str,
        name: Optional[str] = None,
        channel_limit: Optional[int] = None,
        recording: Optional[bool] = None,
        secure: Optional[bool] = None,
        transport: Optional[str] = None,
        is_active: Optional[bool] = None,
        webhook_url: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        authentication_type: Optional[str] = None,
        auth_credential: Optional[Dict[str, str]] = None,
        auth_addresses: Optional[List[Dict[str, str]]] = None,
        ip_acl_id: Optional[str] = None,
        inbound_route: Optional[Dict[str, Any]] = None,
        secret_id: Optional[str] = None,
    ) -> SipTrunkResource:
        """
        Asynchronously update a SIP trunk by its id.

        Pass ``transport`` or ``secure``, never both. Changing authentication
        requires ``authentication_type`` alongside the auth material.
        """
        _validate_auth_fields(
            authentication_type, auth_credential, auth_addresses, ip_acl_id
        )
        payload = _build_trunk_payload(
            name=name,
            authentication_type=authentication_type,
            channel_limit=channel_limit,
            recording=recording,
            secure=secure,
            transport=transport,
            is_active=is_active,
            webhook_url=webhook_url,
            auth_credential=auth_credential,
            auth_addresses=auth_addresses,
            ip_acl_id=ip_acl_id,
            inbound_route=inbound_route,
            secret_id=secret_id,
            webhook_api_version=webhook_api_version,
        )
        res = await self.client.request(
            "PATCH", self.paths["update"].format(trunk_id), json=payload
        )
        return cast(SipTrunkResource, self.resource(unwrap_data(res.json())))

    async def delete(self, trunk_id: str) -> DeleteResult:
        """
        Asynchronously delete a SIP trunk by its id.
        """
        res = await self.client.request("DELETE", self.paths["delete"].format(trunk_id))
        return DeleteResult(unwrap_data(res.json()))

    async def list_virtual_numbers(
        self,
        trunk_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list the virtual numbers assigned to a SIP trunk.
        """
        params = build_params(
            search=search,
            location=location,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(trunk_id),
            params=params,
        )
        return to_cursor_page(res.json(), VirtualNumberResource)
