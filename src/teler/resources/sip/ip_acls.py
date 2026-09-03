import ipaddress
from typing import Any, Dict, List, Optional, Union, cast

from teler import exceptions
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    validate_pagination,
)
from .types import DeleteResult, IpAclResource

PATHS: Dict[str, str] = {
    "create": "/sip/ip-acls",
    "list": "/sip/ip-acls",
    "retrieve": "/sip/ip-acls/{}",
    "update": "/sip/ip-acls/{}",
    "delete": "/sip/ip-acls/{}",
}

MAX_ENTRIES_PER_IP_ACL = 50
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 255
# The API refuses anything broader, per address family.
MIN_PREFIX_LENGTHS = {4: 24, 6: 64}


def _build_list_params(
    search: Optional[str],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    """Build the query params for listing IP ACLs, dropping unset values."""
    validate_pagination(limit, cursor_after, cursor_before)
    params: Dict[str, Any] = {
        "search": search,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


IpNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]


def _parse_network(address: str) -> IpNetwork:
    """Parse an address or CIDR network, host bits stripped.

    The API stores networks canonically, so ``203.0.113.7/24`` and
    ``203.0.113.0/24`` are the same entry as far as duplicate detection goes.
    """
    return ipaddress.ip_network(address.strip(), strict=False)


def _validate_network_usable(address: str, network: IpNetwork) -> None:
    """Reject networks the API will not accept as a SIP source.

    Checked in the server's own order — the prefix cap first, then usability —
    so a value tripping both rules (``127.0.0.0/8``) reports the same reason
    the API would.
    """
    minimum = MIN_PREFIX_LENGTHS[network.version]
    if network.prefixlen < minimum:
        raise exceptions.BadParametersException(
            param="addresses",
            msg=(
                f"'{address}' covers too many addresses; "
                f"use /{minimum} or narrower."
            ),
        )
    if (
        network.network_address.is_unspecified
        or network.network_address.is_loopback
    ):
        raise exceptions.BadParametersException(
            param="addresses",
            msg=f"'{address}' is not a usable SIP source address.",
        )


def _validate_name(name: Optional[str], required: bool) -> None:
    """Names are stripped server-side and must survive as 1..64 characters."""
    if name is None:
        if required:
            raise exceptions.BadParametersException(
                param="name", msg="name is required."
            )
        return
    stripped = name.strip()
    if not stripped:
        raise exceptions.BadParametersException(
            param="name", msg="name must not be blank."
        )
    if len(stripped) > MAX_NAME_LENGTH:
        raise exceptions.BadParametersException(
            param="name",
            msg=f"name must be at most {MAX_NAME_LENGTH} characters.",
        )


def _validate_addresses(
    addresses: Optional[List[Dict[str, Any]]], required: bool
) -> None:
    """Check the address rules the API enforces but the schema does not describe.

    The schema declares only ``minItems: 1``. The API additionally caps a list at
    50 entries, rejects duplicates once networks are canonicalised, requires each
    address to parse as IPv4/IPv6 or CIDR, refuses networks broader than /24
    (IPv4) or /64 (IPv6), refuses loopback and unspecified addresses as SIP
    sources, and caps a description at 255 characters. All of them are checked
    here so a bad entry fails before the round-trip, naming the offending
    address rather than a list index.
    """
    if addresses is None:
        if required:
            raise exceptions.BadParametersException(
                param="addresses", msg="addresses is required."
            )
        return

    if not addresses:
        raise exceptions.BadParametersException(
            param="addresses", msg="Provide at least one address or CIDR network."
        )
    if len(addresses) > MAX_ENTRIES_PER_IP_ACL:
        raise exceptions.BadParametersException(
            param="addresses",
            msg=(
                f"An IP access control list may contain at most "
                f"{MAX_ENTRIES_PER_IP_ACL} addresses."
            ),
        )

    seen: Dict[str, str] = {}
    for entry in addresses:
        if not isinstance(entry, dict) or "address" not in entry:
            raise exceptions.BadParametersException(
                param="addresses",
                msg='Each address must be a dict with an "address" key.',
            )
        address = entry["address"]
        try:
            network = _parse_network(address)
        except (ValueError, AttributeError):
            raise exceptions.BadParametersException(
                param="addresses",
                msg=f"'{address}' is not a valid IPv4/IPv6 address or CIDR network.",
            )
        _validate_network_usable(address, network)
        key = str(network)
        if key in seen:
            raise exceptions.BadParametersException(
                param="addresses",
                msg=(
                    f"Duplicate address in IP access control list: {address} "
                    f"is the same network as {seen[key]}."
                ),
            )
        seen[key] = address

        description = entry.get("description")
        if description is not None and len(description) > MAX_DESCRIPTION_LENGTH:
            raise exceptions.BadParametersException(
                param="addresses",
                msg=(
                    f"description for {address} must be at most "
                    f"{MAX_DESCRIPTION_LENGTH} characters."
                ),
            )


def _build_payload(
    name: Optional[str], addresses: Optional[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Build an IP ACL create/update payload, dropping unset values."""
    payload: Dict[str, Any] = {"name": name, "addresses": addresses}
    return {k: v for k, v in payload.items() if v is not None}


def _unwrap(body: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap a ``{"data": {...}}`` envelope if present, else return body as-is."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _to_cursor_page(body: Dict[str, Any]) -> CursorPage:
    """Wrap a raw list response body into a typed CursorPage of IpAclResource."""
    return CursorPage(
        data=[IpAclResource(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class IpAclResourceManager(BaseResourceManager):
    """Synchronous manager for SIP IP access control list resources."""

    def __init__(self, client: Any):
        super().__init__(client, IpAclResource, PATHS)

    def create(
        self, name: str, addresses: List[Dict[str, Any]]
    ) -> IpAclResource:
        """
        Create a named set of source IPs or CIDR networks that SIP trunks can
        authorise against.

        Each entry in ``addresses`` is ``{"address": ..., "description": ...}``,
        where ``description`` is optional. Reference the returned ``id`` as
        ``ip_acl_id`` when creating or updating a trunk with
        ``authentication_type="IP"``.
        """
        _validate_name(name, required=True)
        _validate_addresses(addresses, required=True)
        res = self.client.request(
            "POST", self.paths["create"], json=_build_payload(name, addresses)
        )
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    def list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List the IP access control lists in your account, newest first.
        """
        params = _build_list_params(search, limit, cursor_after, cursor_before)
        res = self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    def retrieve(self, ip_acl_id: str) -> IpAclResource:
        """
        Retrieve a single IP access control list, including its addresses.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(ip_acl_id))
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    def update(
        self,
        ip_acl_id: str,
        name: Optional[str] = None,
        addresses: Optional[List[Dict[str, Any]]] = None,
    ) -> IpAclResource:
        """
        Rename an ACL and/or replace its addresses.

        Supplying ``addresses`` replaces the entire set. Changes apply to every
        trunk using this ACL.
        """
        _validate_name(name, required=False)
        _validate_addresses(addresses, required=False)
        res = self.client.request(
            "PATCH",
            self.paths["update"].format(ip_acl_id),
            json=_build_payload(name, addresses),
        )
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    def delete(self, ip_acl_id: str) -> DeleteResult:
        """
        Delete an IP access control list.

        Refused with 409 while any SIP trunk still authorises against it, so a
        trunk can never be left without an auth source.
        """
        res = self.client.request("DELETE", self.paths["delete"].format(ip_acl_id))
        return DeleteResult(_unwrap(res.json()))


class AsyncIpAclResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for SIP IP access control list resources."""

    def __init__(self, client: Any):
        super().__init__(client, IpAclResource, PATHS)

    async def create(
        self, name: str, addresses: List[Dict[str, Any]]
    ) -> IpAclResource:
        """
        Asynchronously create a named set of source IPs or CIDR networks that
        SIP trunks can authorise against.
        """
        _validate_name(name, required=True)
        _validate_addresses(addresses, required=True)
        res = await self.client.request(
            "POST", self.paths["create"], json=_build_payload(name, addresses)
        )
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    async def list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list the IP access control lists in your account.
        """
        params = _build_list_params(search, limit, cursor_after, cursor_before)
        res = await self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    async def retrieve(self, ip_acl_id: str) -> IpAclResource:
        """
        Asynchronously retrieve a single IP access control list.
        """
        res = await self.client.request(
            "GET", self.paths["retrieve"].format(ip_acl_id)
        )
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    async def update(
        self,
        ip_acl_id: str,
        name: Optional[str] = None,
        addresses: Optional[List[Dict[str, Any]]] = None,
    ) -> IpAclResource:
        """
        Asynchronously rename an ACL and/or replace its addresses.
        """
        _validate_name(name, required=False)
        _validate_addresses(addresses, required=False)
        res = await self.client.request(
            "PATCH",
            self.paths["update"].format(ip_acl_id),
            json=_build_payload(name, addresses),
        )
        return cast(IpAclResource, self.resource(_unwrap(res.json())))

    async def delete(self, ip_acl_id: str) -> DeleteResult:
        """
        Asynchronously delete an IP access control list.
        """
        res = await self.client.request(
            "DELETE", self.paths["delete"].format(ip_acl_id)
        )
        return DeleteResult(_unwrap(res.json()))
