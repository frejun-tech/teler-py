import os
from pathlib import Path

import pytest
import pytest_asyncio

BACKEND_PATH = os.environ.get("TELER_BACKEND_PATH")

CONTRACT_DIR = Path(__file__).parent


def pytest_collection_modifyitems(config, items):
    """Mark everything in this directory `contract`, so `-m` selection works.

    A module-level `pytestmark` does nothing in a conftest — pytest only honours
    it in test modules and classes — so the mark has to be applied here. The
    marker itself is registered in pyproject.toml.
    """
    for item in items:
        if CONTRACT_DIR in Path(str(item.fspath)).parents:
            item.add_marker(pytest.mark.contract)


@pytest.fixture(scope="session")
def live_api():
    """Serve the backend's real routers on localhost for the whole session."""
    if not BACKEND_PATH:
        pytest.skip("set TELER_BACKEND_PATH to run contract tests")
    if not os.path.isdir(BACKEND_PATH):
        pytest.skip(f"TELER_BACKEND_PATH does not exist: {BACKEND_PATH}")

    from .harness import LiveServer, build_app, load_backend

    try:
        load_backend(BACKEND_PATH)
    except Exception as exc:  # missing backend deps in this interpreter
        pytest.skip(f"cannot import backend: {type(exc).__name__}: {exc}")

    server = LiveServer(build_app()).start()
    yield server
    server.stop()


@pytest.fixture
def client(live_api):
    from teler import Client

    with Client(api_key="test_api_key", base_url=live_api.base_url) as c:
        yield c


@pytest_asyncio.fixture
async def async_client(live_api):
    from teler import AsyncClient

    async with AsyncClient(api_key="test_api_key", base_url=live_api.base_url) as c:
        yield c


@pytest.fixture
def patch_crud(monkeypatch):
    """Patch a route module's imported crud function by dotted path."""

    def _patch(dotted: str, replacement):
        module_path, attr = dotted.rsplit(".", 1)
        import importlib

        module = importlib.import_module(module_path)
        monkeypatch.setattr(module, attr, replacement)

    return _patch
