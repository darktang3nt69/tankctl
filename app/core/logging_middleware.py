import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from starlette.types import Message
import json

SENSITIVE_FIELDS = {"password", "token", "access_token", "auth_key"}


def mask_sensitive(data: any):
    if isinstance(data, dict):
        return {
            k: ("***MASKED***" if k in SENSITIVE_FIELDS else mask_sensitive(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive(item) for item in data]
    return data


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = structlog.get_logger("request")
        start_time = time.time()
        req_body = await request.body()
        # Save the body for downstream consumers
        async def receive() -> Message:
            return {"type": "http.request", "body": req_body, "more_body": False}
        request._receive = receive
        try:
            req_json = json.loads(req_body.decode()) if req_body else None
        except Exception:
            req_json = None
        masked_req = mask_sensitive(req_json) if req_json else None
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": int(process_time * 1000),
        }
        if masked_req:
            log_data["request_body"] = masked_req
        logger.info("request_completed", **log_data)
        return response 