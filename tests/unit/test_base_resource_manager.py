from dataclasses import dataclass
from typing import Any, Dict

import httpx
import pytest
import respx

from teler import AsyncClient, Client, exceptions
from teler.resources.base import (AsyncBaseResourceManager, BaseResource,
                                   BaseResourceManager, validate_pagination)

BASE = "https://api.frejun.ai/api/v1"

PATHS: Dict[str, str] = {
    "list": "/widgets",
    "retrieve": "/widgets/{}",
    "update": "/widgets/{}",
    "delete": "/widgets/{}",
}

WIDGET_JSON = {"id": "w_1", "name": "Widget"}


@dataclass
class WidgetResource(BaseResource):
    id: str
    name: str

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


class WidgetManager(BaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, WidgetResource, PATHS)


class AsyncWidgetManager(AsyncBaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, WidgetResource, PATHS)


# --- base-class update: the async path must await the request ---
def test_base_update_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/widgets/w_1").mock(
            return_value=httpx.Response(200, json=WIDGET_JSON)
        )
        manager = WidgetManager(Client(api_key="test_api_key"))

        widget = manager.update("w_1")

        assert route.called
        assert isinstance(widget, WidgetResource)
        assert widget.id == "w_1"


@pytest.mark.asyncio
async def test_async_base_update_awaits_request_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/widgets/w_1").mock(
            return_value=httpx.Response(200, json=WIDGET_JSON)
        )
        manager = AsyncWidgetManager(AsyncClient(api_key="test_api_key"))

        widget = await manager.update("w_1")

        assert route.called
        assert isinstance(widget, WidgetResource)
        assert widget.id == "w_1"


@pytest.mark.asyncio
async def test_async_base_list_and_retrieve_and_delete():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/widgets").mock(
            return_value=httpx.Response(200, json=[WIDGET_JSON])
        )
        respx_mock.get(f"{BASE}/widgets/w_1").mock(
            return_value=httpx.Response(200, json=WIDGET_JSON)
        )
        respx_mock.delete(f"{BASE}/widgets/w_1").mock(
            return_value=httpx.Response(204)
        )
        manager = AsyncWidgetManager(AsyncClient(api_key="test_api_key"))

        widgets = await manager.list()
        widget = await manager.retrieve("w_1")

        assert isinstance(widgets[0], WidgetResource)
        assert isinstance(widget, WidgetResource)
        assert await manager.delete("w_1") is None


def test_unimplemented_methods_raise():
    manager = WidgetManager(Client(api_key="test_api_key"))
    manager.paths = {}

    for call in (manager.list, lambda: manager.retrieve("w_1"),
                 lambda: manager.update("w_1"), lambda: manager.delete("w_1")):
        with pytest.raises(exceptions.NotImplementedException):
            call()


# --- shared pagination validator ---
@pytest.mark.parametrize("limit", [0, -1, 101])
def test_validate_pagination_rejects_out_of_range_limit(limit):
    with pytest.raises(exceptions.BadParametersException):
        validate_pagination(limit=limit)


@pytest.mark.parametrize("limit", [1, 50, 100])
def test_validate_pagination_accepts_in_range_limit(limit):
    validate_pagination(limit=limit)


def test_validate_pagination_respects_custom_max_limit():
    validate_pagination(limit=50, max_limit=50)
    with pytest.raises(exceptions.BadParametersException):
        validate_pagination(limit=51, max_limit=50)


def test_validate_pagination_rejects_both_cursors():
    with pytest.raises(exceptions.BadParametersException):
        validate_pagination(cursor_after="a", cursor_before="b")


def test_validate_pagination_allows_single_cursor_and_no_limit():
    validate_pagination(cursor_after="a")
    validate_pagination(cursor_before="b")
    validate_pagination()
