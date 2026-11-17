
import logging
import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app


# --------------------------------------------------
# Logging configuration
# --------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "demo-api",
        })


logger = logging.getLogger("demo-api")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False


# --------------------------------------------------
# Prometheus metrics
# --------------------------------------------------

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Kubernetes Observability Demo API",
    version="1.0.0",
    description="Demo application for Kubernetes monitoring and logging.",
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    if request.url.path in ["/metrics", "/health", "/ready"]:
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    except Exception:
        logger.exception("Unhandled application exception")
        raise

    finally:
        duration = time.perf_counter() - start_time

        route = request.scope.get("route")
        endpoint = getattr(route, "path", request.url.path)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        logger.info(
            f"HTTP {request.method} {endpoint} "
            f"status={status_code} duration={duration:.4f}s"
        )


# --------------------------------------------------
# Application endpoints
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "application": "demo-api",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/hello")
async def hello():
    logger.info("Hello endpoint called")

    return {
        "message": "Hello from Kubernetes Observability Platform!"
    }


@app.get("/simulate-error")
async def simulate_error():
    logger.error("Simulated application error")

    return JSONResponse(
        status_code=500,
        content={"error": "Simulated application error"},
    )


@app.get("/slow")
async def slow():
    time.sleep(2)

    return {
        "message": "Slow response completed",
        "delay_seconds": 2,
    }


# --------------------------------------------------
# Prometheus metrics endpoint
# --------------------------------------------------

app.mount("/metrics", make_asgi_app())
