import pytest

from teler.exceptions import BadParametersException
from teler.idempotency import resolve_idempotency_key


def test_resolve_idempotency_key_generates_uuid_when_none():
    """Test that resolve_idempotency_key generates a UUID when None is provided."""
    key = resolve_idempotency_key(None)

    assert key is not None
    assert isinstance(key, str)
    assert len(key) == 36
    assert key.count("-") == 4


def test_resolve_idempotency_key_generates_different_uuids():
    """Test that resolve_idempotency_key generates different UUIDs each time."""
    key1 = resolve_idempotency_key(None)
    key2 = resolve_idempotency_key(None)

    assert key1 != key2


def test_resolve_idempotency_key_uses_provided_key():
    """Test that resolve_idempotency_key uses the provided key."""
    custom_key = "my-custom-idempotency-key-123"
    key = resolve_idempotency_key(custom_key)

    assert key == custom_key


def test_resolve_idempotency_key_rejects_empty_string():
    """Test that resolve_idempotency_key rejects empty strings."""
    with pytest.raises(BadParametersException) as exc_info:
        resolve_idempotency_key("")

    exc = exc_info.value
    assert exc.param == "Idempotency-Key"
    assert "empty" in exc.message.lower()


def test_resolve_idempotency_key_rejects_keys_exceeding_max_length():
    """Test that resolve_idempotency_key rejects keys exceeding 255 characters."""
    long_key = "a" * 256

    with pytest.raises(BadParametersException) as exc_info:
        resolve_idempotency_key(long_key)

    exc = exc_info.value
    assert exc.param == "Idempotency-Key"
    assert "255" in exc.message
    assert "exceed" in exc.message.lower()


def test_resolve_idempotency_key_accepts_max_length_key():
    """Test that resolve_idempotency_key accepts keys of exactly 255 characters."""
    max_key = "a" * 255
    key = resolve_idempotency_key(max_key)

    assert key == max_key
    assert len(key) == 255


def test_resolve_idempotency_key_accepts_various_formats():
    """Test that resolve_idempotency_key accepts various key formats."""
    test_cases = [
        "uuid-style-key-with-dashes",
        "key_with_underscores_123",
        "alphanumeric123KEY456",
        "special-chars_allowed.123",
    ]

    for test_key in test_cases:
        result = resolve_idempotency_key(test_key)
        assert result == test_key


def test_resolve_idempotency_key_validates_param_name():
    """Test that BadParametersException has correct param field."""
    with pytest.raises(BadParametersException) as exc_info:
        resolve_idempotency_key("")

    exc = exc_info.value
    assert hasattr(exc, "param")
    assert exc.param == "Idempotency-Key"


def test_resolve_idempotency_key_validates_message_field():
    """Test that BadParametersException has a message field."""
    with pytest.raises(BadParametersException) as exc_info:
        resolve_idempotency_key("")

    exc = exc_info.value
    assert hasattr(exc, "message")
    assert len(exc.message) > 0
