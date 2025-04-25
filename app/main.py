from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import register, status, commands, config
from app.core.config import settings
from app.core.auth import get_current_tank
from app.core.rate_limit import RateLimitMiddleware
from app.db.init_db import init_db
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# Initialize the database
init_db()

app = FastAPI(
    title="TankCTL - Aquarium Control API",
    description="A Kubernetes-Inspired Control Plane for Smart Aquariums",
    version="1.0.0"
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS for Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider tightening in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request data",
            "errors": exc.errors()
        },
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid data format",
            "errors": exc.errors()
        },
    )

# Routes
app.include_router(register.router)
app.include_router(status.router, dependencies=[Depends(get_current_tank)])
app.include_router(commands.router, dependencies=[Depends(get_current_tank)])
app.include_router(config.router, dependencies=[Depends(get_current_tank)])

@app.get("/")
def root():
    return {
        "message": "Aquarium Control API is live",
        "version": "1.0.0",
        "documentation": "/docs"
    }