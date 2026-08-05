import json
from typing import Any

import redis


class RedisCache:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(
            redis_url,
            decode_responses=True,
        )

    def get_json(self, key: str) -> Any | None:
        value = self.client.get(key)
        if not value:
            return None

        try:
            return json.loads(value)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        self.client.setex(
            key,
            ttl_seconds,
            json.dumps(value, default=str),
        )

    def delete(self, key: str) -> None:
        self.client.delete(key)
