"""Secrets, driven against the real API over a real socket."""
import pytest

from teler.resources.base import CursorPage
from teler.resources.secrets import DeleteResult, SecretResource

from .harness import SECRET_ID, fake_secret

ROUTE = "app.api.routes.public.v1.secrets"


def test_create_secret(client, patch_crud):
    captured = {}

    async def _create(db, secret_in, account_id, is_private=True):
        captured["name"] = secret_in.name
        captured["is_private"] = is_private
        return fake_secret(name=secret_in.name)

    patch_crud(f"{ROUTE}.create_secret", _create)

    secret = client.secrets.create(name="prod-secret")

    # The SDK's body satisfied the real SecretCreate model.
    assert captured["name"] == "prod-secret"
    assert captured["is_private"] is False
    # The real SecretResponse serialization parsed into the SDK dataclass.
    assert isinstance(secret, SecretResource)
    assert secret.name == "prod-secret"
    assert secret.secret_value == "whsec_abc123"
    assert secret.id.startswith("sk_"), secret.id
    assert secret.needs_rotation is False


def test_list_secrets_passes_filters_through_real_validation(client, patch_crud):
    captured = {}

    async def _list(db, account_id, filters):
        captured["limit"] = filters.limit
        captured["search"] = filters.search
        captured["cursor_after"] = filters.cursor_after
        return [fake_secret()], "cur_next", None, True

    patch_crud(f"{ROUTE}.list_secrets_by_account", _list)

    page = client.secrets.list(search="prod", limit=25, cursor_after="cur_a")

    assert captured == {"limit": 25, "search": "prod", "cursor_after": "cur_a"}
    assert isinstance(page, CursorPage)
    assert page.has_more is True
    assert page.next_cursor == "cur_next"
    assert isinstance(page.data[0], SecretResource)
    assert page.data[0].id.startswith("sk_")


def test_retrieve_secret(client, patch_crud):
    async def _get(db, account_id, secret_id, is_private=True):
        assert secret_id == SECRET_ID
        return fake_secret()

    patch_crud(f"{ROUTE}.get_secret", _get)

    from app.utils.identifiers import secret_key_id_from_uuid

    secret = client.secrets.retrieve(secret_key_id_from_uuid(SECRET_ID))

    assert isinstance(secret, SecretResource)
    assert secret.name == "prod-secret"


def test_update_secret_sends_rotate_flag(client, patch_crud):
    captured = {}

    async def _update(db, secret_id, secret_in, account_id, is_private=True):
        captured["rotate"] = secret_in.rotate
        captured["name"] = secret_in.name
        return fake_secret(name=secret_in.name or "prod-secret")

    patch_crud(f"{ROUTE}.update_secret", _update)

    from app.utils.identifiers import secret_key_id_from_uuid

    secret = client.secrets.update(
        secret_key_id_from_uuid(SECRET_ID), name="renamed", rotate=True
    )

    assert captured == {"rotate": True, "name": "renamed"}
    assert isinstance(secret, SecretResource)
    assert secret.name == "renamed"


def test_delete_secret(client, patch_crud):
    async def _delete(db, secret_id, account_id):
        return True

    patch_crud(f"{ROUTE}.delete_secret", _delete)

    from app.utils.identifiers import secret_key_id_from_uuid

    result = client.secrets.delete(secret_key_id_from_uuid(SECRET_ID))

    assert isinstance(result, DeleteResult)
    assert result.success is True
    assert "deleted" in result.message.lower()


def test_malformed_secret_id_raises_not_found(client):
    from teler import exceptions

    with pytest.raises(exceptions.NotFoundException):
        client.secrets.retrieve("not-a-secret-id")


@pytest.mark.asyncio
async def test_async_list_secrets(async_client, patch_crud):
    async def _list(db, account_id, filters):
        return [fake_secret()], None, None, False

    patch_crud(f"{ROUTE}.list_secrets_by_account", _list)

    page = await async_client.secrets.list()

    assert isinstance(page, CursorPage)
    assert isinstance(page.data[0], SecretResource)
