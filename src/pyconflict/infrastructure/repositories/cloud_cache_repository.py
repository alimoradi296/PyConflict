"""Optional Redis-backed cache adapter for explicit team baselines."""

import json
from typing import Any, Optional

from pyconflict.domain.repositories import ICacheRepository

redis: Any
try:
    import redis
except ImportError:  # pragma: no cover - depends on optional extra
    redis = None


class CloudCacheRepository(ICacheRepository):
    """Redis cache with workspace-key isolation and the cache port contract."""

    def __init__(self, redis_url: str, workspace_id: str) -> None:
        if redis is None:
            raise RuntimeError(
                "Redis support is optional. From the PyConflict source checkout, run "
                '`python -m pip install ".[team]`.'
            )
        if not workspace_id.strip():
            raise ValueError("workspace_id must not be empty")
        self.workspace_id = workspace_id
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[dict]:
        value = self.redis_client.get(self._namespace_key(key))
        if value is None:
            return None
        decoded: Any = json.loads(value)
        if not isinstance(decoded, dict):
            raise ValueError(f"Cached value for {key!r} is not a JSON object")
        return decoded

    def set(self, key: str, value: dict, ttl: int) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be greater than zero")
        serialized = json.dumps(value)
        self.redis_client.set(self._namespace_key(key), serialized, ex=ttl)

    def clear(self) -> None:
        pattern = self._namespace_key("*")
        keys = list(self.redis_client.scan_iter(match=pattern))
        if keys:
            self.redis_client.delete(*keys)

    def _namespace_key(self, key: str) -> str:
        return f"pyconflict:{self.workspace_id}:{key}"
