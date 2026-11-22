"""Acceptance coverage for the Redis adapter against a live Redis service."""

import os
import uuid

import pytest

from pyconflict.infrastructure.repositories.cloud_cache_repository import CloudCacheRepository


@pytest.mark.integration
def test_cloud_cache_round_trip_isolated_and_clearable():
    redis = pytest.importorskip("redis")
    redis_url = os.environ.get("PYCONFLICT_REDIS_URL", "redis://127.0.0.1:6379/15")
    workspace = "integration-" + uuid.uuid4().hex
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    client.ping()
    cache = CloudCacheRepository(redis_url, workspace)

    try:
        assert cache.get("baseline") is None
        expected = {"requests": "2.32.0", "rich": "13.9.0"}
        cache.set("baseline", expected, ttl=60)
        assert cache.get("baseline") == expected
        assert client.ttl(f"pyconflict:{workspace}:baseline") > 0

        other_workspace = CloudCacheRepository(redis_url, workspace + "-other")
        other_workspace.set("baseline", {"django": "5.1"}, ttl=60)
        cache.clear()
        assert cache.get("baseline") is None
        assert other_workspace.get("baseline") == {"django": "5.1"}
    finally:
        cache.clear()
        client.delete(f"pyconflict:{workspace}-other:baseline")
        client.close()
