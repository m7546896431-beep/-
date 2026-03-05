"""
Simple per-user rate limiting middleware.
Prevents spam: max 1 message per RATE_LIMIT_SECONDS seconds.
"""
import time
import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

RATE_LIMIT_SECONDS = 1.5   # min interval between messages per user

logger = logging.getLogger(__name__)
_last_seen: dict[int, float] = {}


class ThrottleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id:
            now = time.monotonic()
            last = _last_seen.get(user_id, 0)
            if now - last < RATE_LIMIT_SECONDS:
                logger.debug(f"Throttled user {user_id}")
                return   # silently ignore
            _last_seen[user_id] = now
        return await handler(event, data)
