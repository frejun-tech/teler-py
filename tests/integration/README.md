# Live integration tests

These drive the **real SDK** against the **real Teler API**. The backend's actual
FastAPI routers are mounted and served over a real localhost socket, so every
request goes through genuine URL routing, query/body validation and
`response_model` serialization. Nothing is mocked at the HTTP layer.

Only two layers are stubbed, because they need infrastructure this machine does
not have: the database (Postgres — the models use `ENUM`, `INET` and partial
indexes, so SQLite is not an option) and S3.

## Why these exist

`respx` mocks assert the request the SDK *already makes*, so they agree with the
SDK even when it is wrong. That is exactly how the recordings bug survived: the
SDK asked for `/recordings/`, the API serves `/recordings`, and the mock was
written against the trailing-slash path. Real routing catches that class of bug,
plus anything the API's validators reject and any response key the SDK's
dataclasses fail to declare (`BaseResource` raises `TypeError` on unknown keys).

## Running them

They need one interpreter that has **both** the backend's dependencies and this
SDK importable. The backend's own virtualenv has a *published* `teler` release
installed, which would shadow the working tree, so put `src` on `PYTHONPATH`
explicitly:

```bash
# one-time: an interpreter with the backend's dependencies
python3 -m venv /tmp/teler-itest
/tmp/teler-itest/bin/pip install -r /home/sahil/Work/teler-backend/requirements.txt
/tmp/teler-itest/bin/pip install pytest pytest-asyncio uvicorn

# run
TELER_BACKEND_PATH=/home/sahil/Work/teler-backend \
PYTHONPATH=/path/to/teler-sdk-py/src \
/tmp/teler-itest/bin/python -m pytest tests/integration -q
```

Without `TELER_BACKEND_PATH`, or when the backend cannot be imported, the whole
directory **skips** rather than fails, so `pytest tests/` stays green in CI and
in the plain SDK virtualenv.

## Coverage

| File | Covers |
|---|---|
| `test_live_recordings.py` | signed-URL redirect, `expires_in`, and the trailing-slash regression at the HTTP layer |
| `test_live_events.py` | list/retrieve/redeliver, the `type` alias on the wire, 410 → `GoneException`, 409 → `ConflictException` |
| `test_live_secrets.py` | full CRUD, rotate flag, prefixed-id parsing |
| `test_live_virtual_numbers.py` | list filters as repeated query params, assign/unassign, both-targets rejection (client guard *and* real 400) |
| `test_live_sip.py` | trunk CRUD under `extra="forbid"`, SIP URL and credential validation, call list/retrieve |

## Adding a case

Patch the crud function *as the route module sees it* — routes import by name, so
target `app.api.routes.public.v1.<mod>.<fn>`, except `events`, which does
`from ...crud import events as crud` and so needs `app.crud.events.<fn>`. The
`patch_crud` fixture takes that dotted path. Fakes are `SimpleNamespace` objects
shaped for the response model's `from_attributes=True`; pass UUIDs where the
model has a prefixing validator so you exercise the real conversion.
