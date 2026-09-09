import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self):
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, interval_seconds: int) -> bool:
        now = time.monotonic()
        bucket = self._attempts[key]
        while bucket and now - bucket[0] >= interval_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    def clear(self, key: str) -> None:
        self._attempts.pop(key, None)


login_limiter = SlidingWindowRateLimiter()
login_account_limiter = SlidingWindowRateLimiter()
registration_limiter = SlidingWindowRateLimiter()
