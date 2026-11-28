"""Giới hạn tần suất đơn giản trong bộ nhớ cho đăng nhập, đăng ký và /chat.

Phù hợp với triển khai một tiến trình chạy local của đồ án. Khi chạy nhiều worker
hoặc nhiều máy chủ cần thay bằng kho dùng chung (ví dụ Redis).
"""

from collections import defaultdict, deque
from dataclasses import dataclass
import threading
import time

from fastapi import HTTPException, Request

from app.core.config import settings


@dataclass(frozen=True)
class Limit:
    max_requests: int
    window_seconds: float


# Đăng nhập: chặn dò mật khẩu nhưng vẫn cho người dùng gõ nhầm vài lần.
LOGIN_LIMIT = Limit(max_requests=10, window_seconds=5 * 60)
# Đăng ký: hạn chế tạo tài khoản hàng loạt từ một địa chỉ.
REGISTER_LIMIT = Limit(max_requests=5, window_seconds=10 * 60)
# Chat: mỗi câu RAG mất hàng chục giây trên máy local, 20 câu/phút đã là rất rộng.
CHAT_LIMIT = Limit(max_requests=20, window_seconds=60)


class RateLimiter:
    def __init__(self, enabled: bool = True) -> None:
        # Có thể tắt bằng RATE_LIMIT_ENABLED=false (ví dụ khi chạy kiểm thử tự động).
        self.enabled = enabled
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: Limit) -> None:
        if not self.enabled:
            return
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= limit.window_seconds:
                hits.popleft()
            if len(hits) >= limit.max_requests:
                retry_after = max(1, int(limit.window_seconds - (now - hits[0])) + 1)
                raise HTTPException(
                    status_code=429,
                    detail=f"Bạn thao tác quá nhanh. Vui lòng thử lại sau {retry_after} giây.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter(enabled=settings.rate_limit_enabled)


def client_key(request: Request, scope: str, extra: str = "") -> str:
    host = request.client.host if request.client else "unknown"
    return f"{scope}:{host}:{extra}"
