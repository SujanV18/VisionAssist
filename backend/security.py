import hashlib
import secrets
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import HTTPException

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def hash_password(password):
    salt = secrets.token_hex(16)
    derived = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f'scrypt${salt}${derived}'

def check_password(password, encoded):
    _, salt, expected = encoded.split('$')
    actual = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return secrets.compare_digest(actual, expected)

class RateLimiter:
    """Single-process local MVP limiter; use shared limits before multi-worker deployment."""
    def __init__(self):
        self.buckets = defaultdict(deque)
        self.lock = Lock()

    def check(self, key, maximum, seconds=60):
        current = time.monotonic()
        with self.lock:
            for stale in list(self.buckets):
                if not self.buckets[stale] or self.buckets[stale][-1] <= current - 3600:
                    del self.buckets[stale]
            bucket = self.buckets[key]
            while bucket and bucket[0] <= current - seconds:
                bucket.popleft()
            if len(bucket) >= maximum:
                raise HTTPException(429, 'Too many attempts. Please try again later.', headers={'Retry-After': str(seconds)})
            bucket.append(current)
