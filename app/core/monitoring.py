import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Prometheus metric collectors
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total count of HTTP requests handled by the service.",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request processing latency in seconds.",
    ["method", "endpoint"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to instrument FastAPI endpoints and expose request statistics."""
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.time() - start_time
            # Fall back to URL path if route object is not found (e.g. 404s)
            route = request.scope.get("route")
            endpoint = route.path if route else request.url.path
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                http_status=status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)

def metrics_route(request: Request):
    """FastAPI route handler that returns raw Prometheus metric lines."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
