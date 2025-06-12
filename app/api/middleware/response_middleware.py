from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import json
from typing import Dict, Any

from app.api.utils.responses import create_success_response

class ResponseTransformMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if client accepts standardized responses
        accept_standardized = "application/vnd.tankctl.standardized+json" in request.headers.get("Accept", "")
        
        # Process the request and get the response
        response = await call_next(request)
        
        # Skip transformation for StreamingResponse
        if isinstance(response, StreamingResponse):
            return response

        # If it's a JSON response and already standardized, skip transformation
        if response.headers.get("content-type") == "application/json" and getattr(response, 'body', b'').startswith(b'{"success":'):
            return response

        # Only transform JSON responses when standardized format is requested and not already standardized
        if accept_standardized and response.headers.get("content-type") == "application/json":
            try:
                # Get the original response body
                body = await response.body()
                data = json.loads(body)
                
                # Create a standardized response
                return create_success_response(
                    data=data,
                    status_code=response.status_code
                )
            except Exception:
                # If transformation fails, return the original response
                return response
        
        return response 