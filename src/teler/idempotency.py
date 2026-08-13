import uuid
from typing import Optional

from teler.exceptions import UnprocessableRequestException

IDEMPOTENCY_KEY_MAX_LEN = 255


def resolve_idempotency_key(key: Optional[str] = None) -> str:
    """
    Resolves the idempotency key: uses the caller-supplied value if provided,
    otherwise auto-generates a UUID v4. User-supplied keys are validated
    (non-empty, <= 255 characters).
    """
    if key is None:
        return str(uuid.uuid4())
    if len(key) == 0:
        raise UnprocessableRequestException(
            "Idempotency-Key must not be empty. A UUID is recommended."
        )
    if len(key) > IDEMPOTENCY_KEY_MAX_LEN:
        raise UnprocessableRequestException(
            f"Idempotency-Key must not exceed {IDEMPOTENCY_KEY_MAX_LEN} characters "
            f"(got {len(key)})."
        )
    return key