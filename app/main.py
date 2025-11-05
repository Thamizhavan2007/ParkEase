from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.parking_service import parking_service
from app.db.database import init_db

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routes
from app.routes import parking_routes
app.include_router(parking_routes.router, prefix="/parking")

@app.on_event("startup")
async def startup_event():
    # Initialize DB indexes and documents
    await init_db()
    # Initialize parking service with 20 slots (4x5 grid)
    await parking_service.init_defaults(total_slots=20)