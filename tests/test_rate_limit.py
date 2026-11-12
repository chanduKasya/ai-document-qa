from docqa import rate_limit
from docqa.rate_limit import RateLimiter


def test_blocks_after_limit_then_allows_again(monkeypatch):
    clock = {"now": 1000.0}
    monkeypatch.setattr(rate_limit.time, "time", lambda: clock["now"])
    limiter = RateLimiter(2, 60)

    assert limiter.allow("visitor") is True
    assert limiter.allow("visitor") is True
    assert limiter.allow("visitor") is False
    assert limiter.allow("someone-else") is True

    clock["now"] += 61
    assert limiter.allow("visitor") is True
