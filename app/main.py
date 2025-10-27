from fastapi import FastAPI
from app.routes import parking_routes

app = FastAPI(title="Smart Parking System API")

app.include_router(parking_routes.router, prefix="/parking", tags=["Parking"])

@app.get("/")
def home():
    return {"message": "Smart Parking System API is running 🚗"}
