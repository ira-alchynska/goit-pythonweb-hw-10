from redis.asyncio import Redis
from typing import AsyncGenerator

async def get_redis() -> AsyncGenerator[Redis, None]:
    redis_client = Redis.from_url("redis://localhost")
    try:
        yield redis_client
    finally:
        await redis_client.close()