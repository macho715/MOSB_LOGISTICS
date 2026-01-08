from __future__ import annotations

import hashlib
import inspect
from functools import wraps
from typing import Callable

from cachetools import TTLCache

class CacheManager:
    def __init__(self):
        self.locations = TTLCache(maxsize=1024, ttl=300)
        self.shipments = TTLCache(maxsize=1024, ttl=300)
        self.legs = TTLCache(maxsize=1024, ttl=300)
        self.events = TTLCache(maxsize=4096, ttl=60)

    def invalidate_locations(self): self.locations.clear()
    def invalidate_shipments(self): self.shipments.clear()
    def invalidate_legs(self): self.legs.clear()
    def invalidate_events(self): self.events.clear()

def _key(func_name: str, args: tuple, kwargs: dict) -> str:
    raw = f"{func_name}|{args}|{sorted(kwargs.items())}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()

def cache_response(cache: TTLCache) -> Callable:
    def deco(fn: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(fn)

        if is_async:
            @wraps(fn)
            async def aw(*args, **kwargs):
                k = _key(fn.__name__, args, kwargs)
                if k in cache:
                    return cache[k]
                val = await fn(*args, **kwargs)
                cache[k] = val
                return val
            return aw

        @wraps(fn)
        def sw(*args, **kwargs):
            k = _key(fn.__name__, args, kwargs)
            if k in cache:
                return cache[k]
            val = fn(*args, **kwargs)
            cache[k] = val
            return val
        return sw

    return deco
