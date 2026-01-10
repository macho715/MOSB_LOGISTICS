import hashlib
import inspect
from functools import wraps
from typing import List, Optional, TypeVar

from cachetools import TTLCache

T = TypeVar("T")


class CacheManager:
    def __init__(self):
        self.locations_cache = TTLCache(maxsize=100, ttl=300)
        self.shipments_cache = TTLCache(maxsize=100, ttl=300)
        self.legs_cache = TTLCache(maxsize=100, ttl=300)
        self.events_cache = TTLCache(maxsize=500, ttl=60)
        # Cache for location status with shorter TTL (30s) due to frequent changes.
        self.location_status_cache = TTLCache(maxsize=100, ttl=30)

    def get_cached_locations(self, key: str = "all") -> Optional[List]:
        return self.locations_cache.get(key)

    def set_cached_locations(self, key: str, value: List) -> None:
        self.locations_cache[key] = value

    def get_cached_shipments(self, key: str = "all") -> Optional[List]:
        return self.shipments_cache.get(key)

    def set_cached_shipments(self, key: str, value: List) -> None:
        self.shipments_cache[key] = value

    def get_cached_legs(self, key: str = "all") -> Optional[List]:
        return self.legs_cache.get(key)

    def set_cached_legs(self, key: str, value: List) -> None:
        self.legs_cache[key] = value

    def get_cached_events(self, key: str) -> Optional[List]:
        return self.events_cache.get(key)

    def set_cached_events(self, key: str, value: List) -> None:
        self.events_cache[key] = value

    def get_cached_location_status(self, key: str = "all") -> Optional[List]:
        return self.location_status_cache.get(key)

    def set_cached_location_status(self, key: str, value: List) -> None:
        self.location_status_cache[key] = value

    def invalidate_locations(self) -> None:
        self.locations_cache.clear()

    def invalidate_shipments(self) -> None:
        self.shipments_cache.clear()

    def invalidate_legs(self) -> None:
        self.legs_cache.clear()

    def invalidate_events(self) -> None:
        self.events_cache.clear()

    def get_cached_location_status(self, key: str = "all") -> Optional[List]:
        """Return cached location status list."""
        return self.location_status_cache.get(key)

    def set_cached_location_status(self, key: str, value: List) -> None:
        """Cache location status list."""
        self.location_status_cache[key] = value

    def invalidate_location_status(self) -> None:
        """Clear cached location status."""
        self.location_status_cache.clear()

    def invalidate_all(self) -> None:
        self.invalidate_locations()
        self.invalidate_shipments()
        self.invalidate_legs()
        self.invalidate_events()
        self.invalidate_location_status()


def cache_response(ttl: int = 300):
    def decorator(func):
        cache = TTLCache(maxsize=1000, ttl=ttl)

        def make_key(args, kwargs) -> str:
            raw = f"{func.__name__}:{args}:{kwargs}"
            return hashlib.md5(raw.encode("utf-8")).hexdigest()

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = make_key(args, kwargs)
                if cache_key in cache:
                    return cache[cache_key]
                result = await func(*args, **kwargs)
                cache[cache_key] = result
                return result

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = make_key(args, kwargs)
            if cache_key in cache:
                return cache[cache_key]
            result = func(*args, **kwargs)
            cache[cache_key] = result
            return result

        return sync_wrapper

    return decorator
