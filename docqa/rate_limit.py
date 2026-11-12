"""Simple rate limits, so strangers on a public link cannot use up the Groq quota."""
import threading
import time


class RateLimiter:
    """Allow at most `limit` actions per `window_seconds` for each key (like each visitor)."""

    def __init__(self, limit, window_seconds):
        self.limit = limit
        self.window_seconds = window_seconds
        self.hits = {}  # key -> list of times the key was allowed through
        self.lock = threading.Lock()

    def allow(self, key):
        now = time.time()
        cutoff = now - self.window_seconds

        with self.lock:
            recent = []
            for hit_time in self.hits.get(key, []):
                if hit_time > cutoff:
                    recent.append(hit_time)

            if len(recent) >= self.limit:
                self.hits[key] = recent
                return False

            recent.append(now)
            self.hits[key] = recent

            # Stop the dictionary growing forever on a long-running server.
            if len(self.hits) > 10000:
                self._forget_idle_keys(cutoff)
            return True

    def _forget_idle_keys(self, cutoff):
        idle = []
        for key in self.hits:
            times = self.hits[key]
            if len(times) == 0 or times[-1] <= cutoff:
                idle.append(key)
        for key in idle:
            del self.hits[key]
