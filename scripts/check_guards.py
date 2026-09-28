"""Exercise isolated test users against the real local Redis."""
import uuid
from fastapi import HTTPException
from app.store import get_redis_client
from app.cost_guard import CostGuard
from app.rate_limiter import RateLimiter

client = get_redis_client()
guard = CostGuard(client, 10.0)
limiter = RateLimiter(client, 10)
user = 'budget-experiment-' + uuid.uuid4().hex[:8]
guard.record(user, 10.01)
limiter.check(user)
try:
    guard.check(user)
except HTTPException as exc:
    print('rate allowed, cost:', exc.status_code, exc.detail)
client.delete(guard._key(user), limiter._key(user))
user = 'rate-experiment-' + uuid.uuid4().hex[:8]
guard.check(user)
for _ in range(10):
    limiter.check(user, now=1000)
try:
    limiter.check(user, now=1001)
except HTTPException as exc:
    print('budget allowed (spent=0), rate:', exc.status_code, exc.detail)
client.delete(limiter._key(user))
