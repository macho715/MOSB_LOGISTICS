import time

from cache import CacheManager
from cachetools import TTLCache


def test_cache_hit():
    cache = CacheManager()
    test_data = [{"id": 1, "name": "test"}]
    cache.set_cached_locations("all", test_data)
    cached = cache.get_cached_locations("all")
    assert cached == test_data


def test_cache_miss():
    cache = CacheManager()
    cached = cache.get_cached_locations("missing")
    assert cached is None


def test_cache_ttl():
    cache = CacheManager()
    cache.locations_cache = TTLCache(maxsize=100, ttl=1)
    test_data = [{"id": 1}]
    cache.set_cached_locations("all", test_data)
    assert cache.get_cached_locations("all") == test_data
    time.sleep(2)
    assert cache.get_cached_locations("all") is None


def test_cache_invalidation():
    cache = CacheManager()
    cache.set_cached_locations("all", [{"id": 1}])
    cache.invalidate_locations()
    assert cache.get_cached_locations("all") is None
