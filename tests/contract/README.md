# Live contract tests

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
SDK importable. Point these at your own checkouts:

```bash
export BACKEND=/path/to/teler-backend
export SDK=/path/to/teler-sdk-py
```

The quickest route is to add the two test packages to the backend's existing
virtualenv, which already carries FastAPI and uvicorn:

```bash
$BACKEND/.venv/bin/pip install pytest pytest-asyncio

TELER_BACKEND_PATH=$BACKEND PYTHONPATH=$SDK/src \
  $BACKEND/.venv/bin/python -m pytest tests/contract -q
```

To keep the backend's virtualenv untouched, build a dedicated one instead:

```bash
python3 -m venv ~/.venvs/teler-contract
~/.venvs/teler-contract/bin/pip install -r $BACKEND/requirements.txt
~/.venvs/teler-contract/bin/pip install pytest pytest-asyncio uvicorn

TELER_BACKEND_PATH=$BACKEND PYTHONPATH=$SDK/src \
  ~/.venvs/teler-contract/bin/python -m pytest tests/contract -q
```

`PYTHONPATH` is not optional. The backend's `requirements.txt` pins `teler`, so
both interpreters can see a *published* release that would otherwise shadow the
working tree and test the wrong code — and a later `pip install -r` silently
reinstates it. Verify with:

```bash
PYTHONPATH=$SDK/src <interpreter> -c "import teler; print(teler.__file__)"
```

It must print a path under `src/teler/`, not one under `site-packages`.

`pytest -m contract` selects the same set from anywhere in the suite, and
`pytest -m "not contract"` runs only the hermetic tests.

With `TELER_BACKEND_PATH` unset or pointing nowhere, the whole directory
**skips**, so `pytest tests/` stays green in CI and in the plain SDK virtualenv.

Setting the variable in an interpreter that lacks the backend's dependencies is a
different case: every test here **errors** rather than skips, because the fixture
only guards the backend import and FastAPI is first needed a step later, when the
app is built. This is deliberate — an error is a louder signal that the
environment is set up wrong than a silent skip would be. If you export the
variable in your shell profile, expect a plain `pytest` in the SDK virtualenv to
report those errors, and use `pytest -m "not contract"` for a clean run.

Every test here depends on the `live_api` fixture, which is what makes the skip
total. Anything that can run without the backend belongs in `tests/unit`
instead — the path well-formedness checks in `tests/unit/test_resource_paths.py`
are the hermetic counterpart to `test_live_routing.py` and share the same
`sdk_path` parametrization from `tests/conftest.py`.

## Coverage

| File | Covers |
|---|---|
| `test_live_routing.py` | every `PATHS` entry resolves on the real router, no path redirects, all appear in the served schema |
| `test_live_recordings.py` | signed-URL redirect, `expires_in`, and the trailing-slash regression at the HTTP layer |
| `test_live_events.py` | list/retrieve/redeliver, the `type` alias on the wire, 410 → `GoneException`, 409 → `ConflictException` |
| `test_live_secrets.py` | full CRUD, rotate flag, prefixed-id parsing |
| `test_live_virtual_numbers.py` | list filters as repeated query params, assign/unassign, both-targets rejection (client guard *and* real 400) |
| `test_live_sip.py` | trunk CRUD under `extra="forbid"`, SIP URL and credential validation, transport enum and the udp/credential rule (client guard *and* real 422), call list/retrieve |
| `test_live_voice.py` | transfer mode and target literals, nested transfer actions under `extra="forbid"`, the play `on_dtmf` literal and the hangup `reason` pattern |

## Adding a case

Patch the crud function *as the route module sees it* — routes import by name, so
target `app.api.routes.public.v1.<mod>.<fn>`, except `events`, which does
`from ...crud import events as crud` and so needs `app.crud.events.<fn>`. The
voice transfer and mutation routes hand their work to `run_mutation` instead of
a crud function, so that is what they patch. The
`patch_crud` fixture takes that dotted path. Fakes are `SimpleNamespace` objects
shaped for the response model's `from_attributes=True`; pass UUIDs where the
model has a prefixing validator so you exercise the real conversion.
