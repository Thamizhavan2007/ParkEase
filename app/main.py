# from fastapi import FastAPI
# from app.routes import parking_routes

# app = FastAPI(title="Smart Parking System API")

# app.include_router(parking_routes.router, prefix="/parking", tags=["Parking"])

# @app.get("/")
# def home():
#     return {"message": "Smart Parking System API is running 🚗"}




import asyncio
from fastapi import FastAPI
from app.routes.parking_routes import router as parking_router
from app.db.database import init_db
from app.services.parking_service import parking_service

app = FastAPI(title="Smart Parking System")
app.include_router(parking_router, prefix="/parking")

@app.on_event("startup")
async def startup_event():
    # ensure DB collections and default slots exist
    await init_db()
    await parking_service.init_defaults(total_slots=12)

@app.get("/")
async def root():
    return {"msg": "Smart Parking System running"}