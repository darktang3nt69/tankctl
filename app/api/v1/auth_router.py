from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.api.utils.responses import create_success_response, create_error_response
from app.schemas.responses import StandardResponse

# For JWT token creation (assuming you have these utils)
import jwt # This import will likely need to be replaced with a more specific jwt library later

router = APIRouter()

# Placeholder for JWT utility functions
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # This line might need adjustment based on your actual JWT library
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

class TokenResponse(StandardResponse):
    data: dict

@router.post("/auth/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and get access token.
    
    This endpoint authenticates using the non-rotating ADMIN_API_KEY and returns
    a JWT token for API access.
    
    The token should be included in the Authorization header of subsequent requests:
    `Authorization: Bearer {token}`
    
    Parameters:
    - username: Must be "admin"
    - password: The ADMIN_API_KEY value
    
    Example request:
    ```
    curl -X POST "http://localhost:8000/api/v1/auth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin&password=your_admin_api_key"
    ```
    
    Example response:
    ```json
    {
      "success": true,
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_expires_in": 604800
      },
      "meta": {
        "timestamp": "2025-06-12T10:35:00Z"
      }
    }
    ```
    
    Status codes:
    - 200: Successful authentication
    - 401: Invalid credentials
    
    Security considerations:
    - Store the token securely in the frontend
    - The token expires after 1 hour
    - Do not expose the ADMIN_API_KEY in client-side code
    """
    if form_data.username != "admin" or form_data.password != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(
        data={"sub": form_data.username},
        expires_delta=refresh_token_expires
    )

    return create_success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Convert minutes to seconds
            "refresh_token": refresh_token,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60 # Convert minutes to seconds
        }
    )

@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/refresh"))):
    """
    Refresh access token using a valid refresh token.
    
    This endpoint takes a valid refresh token and returns a new access token.
    The refresh token itself is not refreshed for simplicity and security.
    
    Parameters:
    - refresh_token: The refresh token obtained from the /auth/token endpoint.
    
    Example request:
    ```
    curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
      -H "Authorization: Bearer {refresh_token}"
    ```
    
    Example response:
    ```json
    {
      "success": true,
      "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600
      },
      "meta": {
        "timestamp": "2025-06-12T10:35:00Z"
      }
    }
    ```
    
    Status codes:
    - 200: Successful token refresh
    - 401: Invalid or expired refresh token
    """
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        return create_success_response(
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 # Convert minutes to seconds
            }
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/auth/docs", tags=["documentation"])
async def auth_documentation():
    """
    Authentication documentation for frontend developers.
    
    This endpoint provides detailed information about the authentication flow
    and best practices for token handling in the frontend.
    
    Authentication flow:
    1. Frontend sends username ("admin") and password (ADMIN_API_KEY) to /api/v1/auth/token
    2. Backend validates credentials and returns JWT token and refresh token
    3. Frontend includes access token in Authorization header for subsequent requests
    4. Backend validates access token for each protected endpoint
    5. If access token is expired, frontend uses refresh token to get a new access token from /api/v1/auth/refresh
    
    Token storage best practices:
    - Store tokens in memory for single-page applications
    - For PWAs, consider using IndexedDB or localStorage with proper security measures
    - Clear tokens on logout or when expired
    - Implement token refresh if needed for long sessions
    
    Example token usage:
    ```javascript
    // Authentication
    async function login(adminApiKey) {
      const response = await fetch('/api/v1/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'username': 'admin',
          'password': adminApiKey
        })
      });
      
      const data = await response.json();
      if (data.success) {
        // Store tokens securely
        sessionStorage.setItem('access_token', data.data.access_token);
        sessionStorage.setItem('refresh_token', data.data.refresh_token);
        return true;
      }
      return false;
    }
    
    // Using token for API requests
    async function fetchData(url) {
      let accessToken = sessionStorage.getItem('access_token');
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });
      
      if (response.status === 401) {
        // Try refreshing the token
        const newAccessToken = await refreshAccessToken();
        if (newAccessToken) {
          sessionStorage.setItem('access_token', newAccessToken);
          // Retry the original request with the new token
          return await fetch(url, {
            headers: {
              'Authorization': `Bearer ${newAccessToken}`
            }
          });
        }
      }
      return response.json();
    }
    
    // Refresh access token
    async function refreshAccessToken() {
      const refreshToken = sessionStorage.getItem('refresh_token');
      if (!refreshToken) return null;
      
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });
      
      const data = await response.json();
      if (data.success) {
        return data.data.access_token;
      }
      return null;
    }
    ```
    """
    return {
        "authentication_flow": {
            "steps": [
                "Frontend sends username ('admin') and password (ADMIN_API_KEY) to /api/v1/auth/token",
                "Backend validates credentials and returns JWT token",
                "Frontend includes token in Authorization header for subsequent requests",
                "Backend validates token for each protected endpoint"
            ]
        },
        "token_storage": {
            "best_practices": [
                "Store tokens in memory for single-page applications",
                "For PWAs, consider using IndexedDB or localStorage with proper security measures",
                "Clear tokens on logout or when expired",
                "Implement token refresh if needed for long sessions"
            ]
        },
        "example_code": {
            "authentication": "async function login(adminApiKey) { ... }",
            "api_request": "async function fetchData(url) { ... }"
        }
    } 