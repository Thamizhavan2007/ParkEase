# app/main.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import heapq
from collections import deque, defaultdict
import math
import os

app = FastAPI()

#CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Your frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://nt:123@smartparkingcluster.oukhdsg.mongodb.net/")
client = MongoClient(MONGO_URI)
db = client["smart_parking"]
slots_collection = db["slots"]
cars_collection = db["cars"]
queue_collection = db["queue"]  # Single document for queue
stats_collection = db["stats"]  # Single document for stats
pricing_heap_collection = db["pricing_heap"]  # For persisting heap, but we'll manage in memory for simplicity

# Initialize if not exists
if not stats_collection.find_one({"_id": "global"}):
    stats_collection.insert_one({
        "_id": "global",
        "revenue": 0.0,
        "total_parked": 0,
        "average_wait_time": 0.0,
        "wait_time_sum": 0.0,
        "total_exits": 0
    })

if not queue_collection.find_one({"_id": "queue"}):
    queue_collection.insert_one({"_id": "queue", "cars": []})

# Pricing Tiers: min-heap for rates based on occupancy thresholds
# Example tiers: (occupancy_threshold, rate)
pricing_tiers = []  # We'll load/init below
def init_pricing_tiers():
    global pricing_tiers
    pricing_tiers = [
        (0.5, 1.0),   # <50% occupancy: $1/hr
        (0.75, 1.5),  # 50-75%: $1.5/hr
        (1.0, 2.0)    # >75%: $2/hr
    ]
    heapq.heapify(pricing_tiers)

init_pricing_tiers()

# Parking Grid: 4x5 grid, 20 slots
ROWS, COLS = 4, 5
ENTRANCE = (0, 0)  # Assume entrance at top-left

# Graph for slots: each slot is a node (row,col), edges to adjacent slots
def build_graph():
    graph = defaultdict(list)
    for r in range(ROWS):
        for c in range(COLS):
            node = (r, c)
            # Up, down, left, right
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    dist = 1  # Manhattan distance or Euclidean? Using 1 for simplicity
                    graph[node].append(((nr, nc), dist))
    return graph

GRAPH = build_graph()

# Dijkstra to find nearest available slot from entrance
def dijkstra_find_nearest():
    import heapq
    distances = {node: float('inf') for node in GRAPH}
    distances[ENTRANCE] = 0
    pq = [(0, ENTRANCE)]
    prev = {node: None for node in GRAPH}

    while pq:
        dist, node = heapq.heappop(pq)
        if dist > distances[node]:
            continue
        for neighbor, weight in GRAPH[node]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))

    # Find nearest available slot
    available_slots = slots_collection.find({"occupied": False})
    min_dist = float('inf')
    nearest_slot = None
    for slot in available_slots:
        pos = (slot["row"], slot["col"])
        if distances[pos] < min_dist:
            min_dist = distances[pos]
            nearest_slot = slot["_id"]

    return nearest_slot

# Initialize slots if empty
if slots_collection.count_documents({}) == 0:
    for r in range(ROWS):
        for c in range(COLS):
            slots_collection.insert_one({
                "_id": f"slot_{r}_{c}",
                "row": r,
                "col": c,
                "occupied": False,
                "car_number": None
            })

# Models
class CarEntry(BaseModel):
    car_number: str

class CarExit(BaseModel):
    car_number: str

class CarStatus(BaseModel):
    car_number: str

# Helper Functions
def get_current_rate():
    occupancy = slots_collection.count_documents({"occupied": True}) / (ROWS * COLS)
    queue_doc = queue_collection.find_one({"_id": "queue"})
    queue_len = len(queue_doc["cars"]) if queue_doc else 0

    # Adjust based on occupancy and queue
    # Pop the smallest tier that matches
    for thresh, rate in sorted(pricing_tiers):  # Sort to check in order
        if occupancy <= thresh and queue_len == 0:
            return rate
    return pricing_tiers[-1][1]  # Max rate if high demand

def calculate_charge(entry_time, rate):
    duration = (datetime.now() - entry_time).total_seconds() / 3600  # hours
    return duration * rate

def update_stats(revenue_add=0.0, wait_time=0.0):
    stats = stats_collection.find_one({"_id": "global"})
    new_revenue = stats["revenue"] + revenue_add
    new_total_exits = stats["total_exits"] + 1 if revenue_add > 0 else stats["total_exits"]
    new_wait_sum = stats["wait_time_sum"] + wait_time
    new_avg_wait = new_wait_sum / new_total_exits if new_total_exits > 0 else 0.0

    stats_collection.update_one({"_id": "global"}, {"$set": {
        "revenue": new_revenue,
        "average_wait_time": new_avg_wait,
        "wait_time_sum": new_wait_sum,
        "total_exits": new_total_exits
    }})

# Endpoints
@app.post("/entry")
async def car_entry(car: CarEntry):
    if cars_collection.find_one({"car_number": car.car_number}):
        raise HTTPException(400, "Car already parked")

    nearest_slot_id = dijkstra_find_nearest()
    entry_time = datetime.now()
    rate = get_current_rate()
    wait_time = 0.0

    if nearest_slot_id:
        # Assign slot
        slots_collection.update_one({"_id": nearest_slot_id}, {"$set": {"occupied": True, "car_number": car.car_number}})
        cars_collection.insert_one({
            "car_number": car.car_number,
            "slot_id": nearest_slot_id,
            "entry_time": entry_time,
            "rate": rate
        })
        stats_collection.update_one({"_id": "global"}, {"$inc": {"total_parked": 1}})
        return {"message": f"Car {car.car_number} parked at {nearest_slot_id}. Rate: ${rate}/hr"}
    else:
        # Add to queue
        queue_doc = queue_collection.find_one({"_id": "queue"})
        queue_cars = queue_doc["cars"]
        queue_cars.append({
            "car_number": car.car_number,
            "queue_time": entry_time
        })
        queue_collection.update_one({"_id": "queue"}, {"$set": {"cars": queue_cars}})
        return {"message": f"Parking full. Car {car.car_number} added to queue."}

# Process queue when a slot frees up (called in exit)
def process_queue():
    queue_doc = queue_collection.find_one({"_id": "queue"})
    if not queue_doc or not queue_doc["cars"]:
        return

    queued_car = queue_doc["cars"].pop(0)  # FIFO
    queue_collection.update_one({"_id": "queue"}, {"$set": {"cars": queue_doc["cars"]}})

    nearest_slot_id = dijkstra_find_nearest()
    if nearest_slot_id:
        entry_time = datetime.now()
        wait_time = (entry_time - queued_car["queue_time"]).total_seconds()
        rate = get_current_rate()
        slots_collection.update_one({"_id": nearest_slot_id}, {"$set": {"occupied": True, "car_number": queued_car["car_number"]}})
        cars_collection.insert_one({
            "car_number": queued_car["car_number"],
            "slot_id": nearest_slot_id,
            "entry_time": entry_time,
            "rate": rate
        })
        stats_collection.update_one({"_id": "global"}, {"$inc": {"total_parked": 1}})
        update_stats(wait_time=wait_time)
        return {"message": f"Queued car {queued_car['car_number']} now parked at {nearest_slot_id}."}

@app.post("/exit")
async def car_exit(car: CarExit):
    car_doc = cars_collection.find_one({"car_number": car.car_number})
    if not car_doc:
        # Check if in queue
        queue_doc = queue_collection.find_one({"_id": "queue"})
        queue_cars = [c for c in queue_doc["cars"] if c["car_number"] != car.car_number]
        if len(queue_cars) < len(queue_doc["cars"]):
            queue_collection.update_one({"_id": "queue"}, {"$set": {"cars": queue_cars}})
            return {"message": f"Car {car.car_number} removed from queue."}
        raise HTTPException(404, "Car not found")

    # Free slot
    slots_collection.update_one({"_id": car_doc["slot_id"]}, {"$set": {"occupied": False, "car_number": None}})
    charge = calculate_charge(car_doc["entry_time"], car_doc["rate"])
    cars_collection.delete_one({"car_number": car.car_number})
    stats_collection.update_one({"_id": "global"}, {"$inc": {"total_parked": -1}})
    update_stats(revenue_add=charge)

    # Process next in queue
    process_queue()

    return {"message": f"Car {car.car_number} exited. Charge: ${charge:.2f}"}

@app.get("/status/{car_number}")
async def check_status(car_number: str):
    car_doc = cars_collection.find_one({"car_number": car_number})
    if car_doc:
        return {
            "status": "Parked",
            "slot": car_doc["slot_id"],
            "entry_time": car_doc["entry_time"],
            "rate": car_doc["rate"]
        }

    # Check queue
    queue_doc = queue_collection.find_one({"_id": "queue"})
    for idx, q_car in enumerate(queue_doc["cars"]):
        if q_car["car_number"] == car_number:
            return {"status": "Queued", "position": idx + 1}

    raise HTTPException(404, "Car not found")

@app.get("/stats")
async def get_stats():
    stats = stats_collection.find_one({"_id": "global"})
    occupancy = (stats["total_parked"] / (ROWS * COLS)) * 100
    queue_doc = queue_collection.find_one({"_id": "queue"})
    queue_len = len(queue_doc["cars"])
    current_rate = get_current_rate()
    return {
        "total_parked": stats["total_parked"],
        "occupancy_percentage": occupancy,
        "revenue": stats["revenue"],
        "average_wait_time": stats["average_wait_time"],
        "queue_length": queue_len,
        "current_rate": current_rate
    }

@app.get("/visualization")
async def get_visualization():
    grid = [[" " for _ in range(COLS)] for _ in range(ROWS)]
    for slot in slots_collection.find():
        r, c = slot["row"], slot["col"]
        if slot["occupied"]:
            grid[r][c] = "X"  # Occupied
        else:
            grid[r][c] = "."  # Free

    queue_doc = queue_collection.find_one({"_id": "queue"})
    queue_str = ", ".join([c["car_number"] for c in queue_doc["cars"]])

    viz = "\n".join([" ".join(row) for row in grid])
    return {
        "grid": viz,
        "queue": queue_str,
        "stats": await get_stats()
    }

# Note: For real visualization, integrate with a frontend like React or use libraries like Plotly, but here we use simple ASCII for demo.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)