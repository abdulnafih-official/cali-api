import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import ROLE_LIMITS
from app.db.models import User

_windows: dict[int, deque[float]] = defaultdict(deque)


async def rate_limited_user(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> User:
    per_min, total_cap = ROLE_LIMITS[user.role]

    # 1) role-based per-minute sliding window
    now = time.monotonic()
    window = _windows[user.id]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= per_min:
        retry = int(60 - (now - window[0])) + 1
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Rate limit of {per_min}/min exceeded",
            headers={"Retry-After": str(retry)},
        )

    # 2) lifetime total quota, atomic increment in Postgres
    stmt = update(User).where(User.id == user.id)
    if total_cap is not None:
        stmt = stmt.where(User.total_requests < total_cap)
    result = await db.execute(stmt.values(total_requests=User.total_requests + 1))
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Total request quota exhausted")

    window.append(now)
    return user