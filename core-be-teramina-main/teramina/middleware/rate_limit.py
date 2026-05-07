import time
import logging
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# (max_requests, window_seconds)
_LIMITS = {
    "/api/auth/": (10, 60),       # 10 req/min — auth is expensive and sensitive
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

        count = cache.get(key, 0)
        if count >= max_requests:
            logger.warning("Rate limit exceeded: ip=%s path=%s", ip, path)
            return JsonResponse(
                {"code": 429, "message": "Too many requests. Please slow down."},
                status=429,
            )

        cache.set(key, count + 1, timeout=window * 2)
        return self.get_response(request)
