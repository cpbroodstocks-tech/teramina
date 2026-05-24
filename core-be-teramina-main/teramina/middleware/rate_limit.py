import time
import logging
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# (max_requests, window_seconds)
_LIMITS = {
    "/api/user/login": (10, 60),       # 10 req/min — auth is expensive and sensitive
    "/api/user/firebase-verify-user": (10, 60),
    "/api/user/verify-with-refresh-token": (20, 60),
    "/api/": (120, 60),           # 120 req/min — general API
}
_DEFAULT_LIMIT = (200, 60)


def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _limit_for_path(path):
    for prefix, limit in _LIMITS.items():
        if path.startswith(prefix):
            return limit
    return _DEFAULT_LIMIT


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not path.startswith("/api/"):
            return self.get_response(request)

        ip = _get_client_ip(request)
        max_requests, window = _limit_for_path(path)

        bucket = int(time.time() // window)
        key = f"rl:{ip}:{bucket}"

        try:
            count = cache.get(key, 0)
        except Exception as exc:  # pragma: no cover - depends on cache backend availability
            logger.warning("Rate limit skipped because cache is unavailable: %s", exc)
            return self.get_response(request)

        if count >= max_requests:
            logger.warning("Rate limit exceeded: ip=%s path=%s", ip, path)
            return JsonResponse(
                {"code": 429, "message": "Too many requests. Please slow down."},
                status=429,
            )

        try:
            cache.set(key, count + 1, timeout=window * 2)
        except Exception as exc:  # pragma: no cover - depends on cache backend availability
            logger.warning("Rate limit counter not saved because cache is unavailable: %s", exc)
        return self.get_response(request)
