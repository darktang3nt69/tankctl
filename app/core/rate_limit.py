from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple
import os

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
        self.requests_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        self.minute_requests: Dict[str, list] = {}
        self.hour_requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean up old requests
        self._cleanup_old_requests(current_time)

        # Check minute limit
        if client_ip in self.minute_requests:
            if len(self.minute_requests[client_ip]) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )

        # Check hour limit
        if client_ip in self.hour_requests:
            if len(self.hour_requests[client_ip]) >= self.requests_per_hour:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Hourly request limit exceeded. Please try again later.",
                        "retry_after": 3600
                    },
                    headers={"Retry-After": "3600"}
                )

        # Add current request
        if client_ip not in self.minute_requests:
            self.minute_requests[client_ip] = []
        if client_ip not in self.hour_requests:
            self.hour_requests[client_ip] = []

        self.minute_requests[client_ip].append(current_time)
        self.hour_requests[client_ip].append(current_time)

        response = await call_next(request)
        return response

    def _cleanup_old_requests(self, current_time: float):
        # Clean up minute requests older than 1 minute
        for ip in list(self.minute_requests.keys()):
            self.minute_requests[ip] = [
                t for t in self.minute_requests[ip]
                if current_time - t < 60
            ]
            if not self.minute_requests[ip]:
                del self.minute_requests[ip]

        # Clean up hour requests older than 1 hour
        for ip in list(self.hour_requests.keys()):
            self.hour_requests[ip] = [
                t for t in self.hour_requests[ip]
                if current_time - t < 3600
            ]
            if not self.hour_requests[ip]:
                del self.hour_requests[ip] 