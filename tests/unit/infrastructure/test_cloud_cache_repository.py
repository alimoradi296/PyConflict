"""Unit tests for Redis cache behavior without a Redis service."""

import json
from types import SimpleNamespace

import pytest

from pyconflict.infrastructure.repositories import cloud_cache_repository as module


class FakeRedisClient:
    def __init__(self):
        self.values = {}
        self.ttls = {}
        self.deleted = []

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex):
        self.values[key] = value
        self.ttls[key] = ex

    def scan_iter(self, match):
        prefix = match[:-1] if match.endswith("*") else match
        return iter(key for key in self.values if key.startswith(prefix))

    def delete(self, *keys):
        self.deleted.extend(keys)
        for key in keys:
            self.values.pop(key, None)


def make_repository(monkeypatch):
    client = FakeRedisClient()
    redis_stub = SimpleNamespace(Redis=SimpleNamespace(from_url=lambda *args, **kwargs: client))
    monkeypatch.setattr(module, "redis", redis_stub)
    return module.CloudCacheRepository("redis://example", "team-1"), client


def test_cache_uses_workspace_namespace_and_ttl(monkeypatch):
    cache, client = make_repository(monkeypatch)

    cache.set("baseline", {"requests": "2.31.0"}, ttl=90)

    assert client.values["pyconflict:team-1:baseline"] == json.dumps({"requests": "2.31.0"})
    assert client.ttls["pyconflict:team-1:baseline"] == 90
    assert cache.get("baseline") == {"requests": "2.31.0"}


def test_cache_clear_only_removes_its_workspace(monkeypatch):
    cache, client = make_repository(monkeypatch)
    client.values = {
        "pyconflict:team-1:a": "{}",
        "pyconflict:team-2:b": "{}",
    }

    cache.clear()

    assert client.values == {"pyconflict:team-2:b": "{}"}


def test_cache_rejects_non_object_json_values(monkeypatch):
    cache, client = make_repository(monkeypatch)
    client.values["pyconflict:team-1:bad"] = "[]"

    with pytest.raises(ValueError, match="not a JSON object"):
        cache.get("bad")
