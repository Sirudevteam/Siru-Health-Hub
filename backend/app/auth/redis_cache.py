import redis.asyncio as redis
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
            return None
    return _redis_client


async def revoke_token(token: str, expires_in_seconds: int = 3600) -> bool:
    """Store revoked token in Redis blacklist with TTL."""
    client = get_redis_client()
    if not client:
        return False
    try:
        key = f"token_blacklist:{token}"
        await client.setex(key, expires_in_seconds, "revoked")
        return True
    except Exception as e:
        logger.warning(f"Error revoking token in Redis: {e}")
        return False


async def is_token_revoked(token: str) -> bool:
    """Check if token is in Redis blacklist."""
    client = get_redis_client()
    if not client:
        return False
    try:
        key = f"token_blacklist:{token}"
        result = await client.get(key)
        return result is not None
    except Exception as e:
        logger.warning(f"Error checking token blacklist in Redis: {e}")
        return False

