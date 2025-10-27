from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv


load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://nt:123@smartparkingcluster.oukhdsg.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "smartparking")


client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


cars_col = db["cars"]
slots_col = db["slots"]
stats_col = db["stats"]


# ensure indexes can be created on startup if needed
async def init_db():
    await cars_col.create_index("car_number", unique=True)
    await slots_col.create_index("slot_id", unique=True)
# stats is singleton document