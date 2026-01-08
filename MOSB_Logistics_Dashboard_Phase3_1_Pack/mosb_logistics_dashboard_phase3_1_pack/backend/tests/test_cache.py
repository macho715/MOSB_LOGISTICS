import time
from cachetools import TTLCache
from cache import cache_response

def test_cache_hit_miss():
    c = TTLCache(maxsize=10, ttl=1)
    calls = {"n":0}

    @cache_response(c)
    def f(x):
        calls["n"] += 1
        return x * 2

    assert f(2) == 4
    assert f(2) == 4
    assert calls["n"] == 1
    time.sleep(1.1)
    assert f(2) == 4
    assert calls["n"] == 2
