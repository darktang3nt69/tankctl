from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import register, status, commands, config
from app.core.config import settings
from app.core.auth import get_current_tank
from app.db.init_db import init_db

# Initialize the database
init_db()

app = FastAPI(title="TankCTL - Aquarium Control API")

# CORS for Grafana
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider tightening in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(register.router)
app.include_router(status.router, dependencies=[Depends(get_current_tank)])
app.include_router(commands.router, dependencies=[Depends(get_current_tank)])
app.include_router(config.router, dependencies=[Depends(get_current_tank)])

@app.get("/")
def root():
    return {"message": "Aquarium Control API is live"}