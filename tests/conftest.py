"""Keep cache writes inside each test's temporary directory."""

import pytest


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("COSTS_CACHE_DIR", str(tmp_path / "cache"))
