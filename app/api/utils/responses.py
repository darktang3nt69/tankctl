from typing import Any, Dict, List, Optional, TypeVar, Generic, Type, Union
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

from app.schemas.responses import StandardResponse, ErrorModel, ResponseMeta, PaginationMeta

T = TypeVar('T')

def create_success_response(
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response"""
    response_meta = ResponseMeta(timestamp=datetime.utcnow())
    
    if meta and "pagination" in meta:
        pagination = PaginationMeta(**meta["pagination"])
        response_meta.pagination = pagination
    
    response = StandardResponse(
        success=True,
        data=data,
        error=None,
        meta=response_meta
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode='json', exclude_none=True) # Use .model_dump() for Pydantic v2
    )

def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """Create a standardized error response"""
    error = ErrorModel(
        code=code,
        message=message,
        details=details
    )
    
    response = StandardResponse(
        success=False,
        data=None,
        error=error,
        meta=ResponseMeta(timestamp=datetime.utcnow())
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode='json', exclude_none=True) # Use .model_dump() for Pydantic v2
    )

def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    size: int,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized paginated response"""
    pages = (total + size - 1) // size if size > 0 else 0
    
    pagination = {
        "pagination": {
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
    }
    
    return create_success_response(
        data=data,
        meta=pagination,
        status_code=status_code
    ) 