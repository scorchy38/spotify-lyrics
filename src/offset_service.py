import logging
import os
import redis.asyncio as redis


class OffsetService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._redis = None

    @property
    async def redis_client(self):
        if self._redis is None:
            redis_url = os.getenv("REDIS_URL")
            self._redis = redis.from_url(redis_url)
        return self._redis

    async def get_video_offset(self, video_id: str) -> int:
        client = await self.redis_client
        offset = await client.get(f"offset:{video_id}")
        return int(offset) if offset else 0

    async def set_video_offset(self, video_id: str, offset: int):
        client = await self.redis_client
        await client.set(f"offset:{video_id}", offset)
