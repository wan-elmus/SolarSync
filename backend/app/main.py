from fastapi import FastAPI
from app.core.database import engine
from app.models import Base
from app.api import jobs, sizing, predictions, technicians, users, weather, websockets
from app.core.scheduler import schedule_weather_updates, shutdown_scheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SolarSync")

Base.metadata.create_all(bind=engine)

app.include_router(jobs.router)
app.include_router(sizing.router)
app.include_router(predictions.router)
app.include_router(technicians.router)
app.include_router(users.router)
app.include_router(weather.router)
app.include_router(websockets.router)

@app.on_event("startup")
async def startup_event():
    schedule_weather_updates(app)
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()
    logger.info("Scheduler stopped")

@app.get("/")
async def root():
    return {"message": "Welcome to SolarSync"}