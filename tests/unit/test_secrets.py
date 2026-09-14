import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.secrets import DeleteResult, SecretResource

BASE = "https://api.frejun.ai/api/v1"

SECRET_JSON = {
    "id": "sec_123",
    "name": "prod-secret",
    "secret_value": "whsec_abc123",
    "rotated_at": None,
    "created_at": "2026-08-01T12:00:00Z",
    "needs_rotation": False,
    "sip_trunks": [{"id": "st_1", "name": "Main Trunk"}],
    "voice_apps": [{"id": "app_1", "name": "Support App"}],
}

LIST_JSON = {
    "data": [{"id": "sec_123", "name": "prod-secret"}],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}


# --- create ---
def test_secrets_create_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/secrets").mock(
            return_value=httpx.Response(201, json=SECRET_JSON)
        )
        client = Client(api_key="test_api_key")

        secret = client.secrets.create(name="prod-secret")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "prod-secret"}
        assert isinstance(secret, SecretResource)
        assert secret.id == "sec_123"
        assert secret.secret_value == "whsec_abc123"


@pytest.mark.asyncio
async def test_async_secrets_create_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/secrets").mock(
            return_value=httpx.Response(201, json=SECRET_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        secret = await client.secrets.create(name="prod-secret")

        assert route.called
        assert isinstance(secret, SecretResource)
        assert secret.id == "sec_123"


# --- list ---
def test_secrets_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/secrets").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.secrets.list(search="prod")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["search"] == "prod"
        assert params["limit"] == "10"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], SecretResource)
        assert page.data[0].id == "sec_123"


@pytest.mark.asyncio
async def test_async_secrets_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/secrets").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.secrets.list()

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], SecretResource)


# --- retrieve ---
def test_secrets_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json=SECRET_JSON)
        )
        client = Client(api_key="test_api_key")

        secret = client.secrets.retrieve("sec_123")

        assert route.called
        assert isinstance(secret, SecretResource)
        assert secret.id == "sec_123"
        assert secret.needs_rotation is False


def test_secrets_retrieve_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json={"data": SECRET_JSON})
        )
        client = Client(api_key="test_api_key")

        secret = client.secrets.retrieve("sec_123")

        assert isinstance(secret, SecretResource)
        assert secret.id == "sec_123"


@pytest.mark.asyncio
async def test_async_secrets_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json=SECRET_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        secret = await client.secrets.retrieve("sec_123")

        assert route.called
        assert isinstance(secret, SecretResource)


# --- update ---
def test_secrets_update_sends_payload_and_returns_resource():
    rotated = {**SECRET_JSON, "secret_value": "whsec_new", "rotated_at": "2026-08-13T10:00:00Z"}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json=rotated)
        )
        client = Client(api_key="test_api_key")

        secret = client.secrets.update("sec_123", rotate=True)

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"rotate": True}
        assert isinstance(secret, SecretResource)
        assert secret.secret_value == "whsec_new"
        assert secret.rotated_at == "2026-08-13T10:00:00Z"


def test_secrets_update_rename_sends_name():
    renamed = {**SECRET_JSON, "name": "staging-secret"}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json=renamed)
        )
        client = Client(api_key="test_api_key")

        secret = client.secrets.update("sec_123", name="staging-secret")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "staging-secret", "rotate": False}
        assert secret.name == "staging-secret"


@pytest.mark.asyncio
async def test_async_secrets_update_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(200, json=SECRET_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        secret = await client.secrets.update("sec_123", rotate=True)

        assert route.called
        assert isinstance(secret, SecretResource)


# --- delete ---
def test_secrets_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "Secret deleted."}
            )
        )
        client = Client(api_key="test_api_key")

        result = client.secrets.delete("sec_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


@pytest.mark.asyncio
async def test_async_secrets_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/secrets/sec_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "Secret deleted."}
            )
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.secrets.delete("sec_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


# --- repr ---
def test_secret_repr_omits_secret_value():
    """repr() hides secret_value but keeps the other fields readable."""
    secret = SecretResource(SECRET_JSON)

    text = repr(secret)

    assert "whsec_abc123" not in text
    assert "secret_value" not in text
    assert "prod-secret" in text
    assert secret.secret_value == "whsec_abc123"


def test_secret_repr_stays_clean_with_the_raw_body_attached():
    secret = SecretResource(SECRET_JSON)

    assert "whsec_abc123" not in repr(secret)
    assert secret.raw["secret_value"] == "whsec_abc123"
