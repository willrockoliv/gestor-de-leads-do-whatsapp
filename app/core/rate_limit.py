import time
from collections import defaultdict, deque


class SlidingWindowRateLimiter:
    def __init__(self):
        self._store: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        bucket = self._store[key]

        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, int(window_seconds - (now - bucket[0])))
            return False, retry_after

        bucket.append(now)
        return True, 0

    def clear(self) -> None:
        self._store.clear()
