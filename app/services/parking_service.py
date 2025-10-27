# import heapq, time
# from collections import deque
# from datetime import datetime

# class ParkingSystem:
#     def __init__(self, total_slots=10):
#         self.total_slots = total_slots
#         self.slots = [None] * total_slots  # represents slot occupancy
#         self.wait_queue = deque()           # FIFO queue
#         self.pricing_heap = []              # min-heap for dynamic pricing tiers
#         self.base_rate = 10                 # base rate per minute

#     def _update_pricing(self):
#         occupancy = sum(1 for s in self.slots if s is not None) / self.total_slots
#         dynamic_rate = self.base_rate * (1 + occupancy)
#         return round(dynamic_rate, 2)

#     def add_car(self, car_number):
#         if None in self.slots:
#             slot_id = self.slots.index(None)
#             self.slots[slot_id] = {
#                 "car_number": car_number,
#                 "entry_time": datetime.now(),
#                 "rate": self._update_pricing()
#             }
#             return f"Car {car_number} parked at slot {slot_id}"
#         else:
#             self.wait_queue.append(car_number)
#             return f"Parking full. Car {car_number} added to waiting queue."

#     def remove_car(self, car_number):
#         for i, slot in enumerate(self.slots):
#             if slot and slot["car_number"] == car_number:
#                 parked_time = (datetime.now() - slot["entry_time"]).seconds / 60
#                 charge = parked_time * slot["rate"]
#                 self.slots[i] = None

#                 # Assign slot to next in queue if exists
#                 if self.wait_queue:
#                     next_car = self.wait_queue.popleft()
#                     self.add_car(next_car)

#                 return f"Car {car_number} exited. Charge: ₹{round(charge, 2)}"

#         return f"Car {car_number} not found."




import asyncio
import heapq
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

from app.db.database import cars_col, slots_col, stats_col
from app.utils.helpers import now_utc

# Dijkstra implementation utilities
import math
from pymongo.errors import DuplicateKeyError
from bson import ObjectId

class AsyncBroadcaster:
    """Simple pub-sub broadcaster for WebSocket listeners."""
    def __init__(self):
        self.connections = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws):
        async with self.lock:
            self.connections.add(ws)

    async def disconnect(self, ws):
        async with self.lock:
            self.connections.discard(ws)

    async def broadcast(self, message: dict):
        async with self.lock:
            conns = list(self.connections)
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(ws)

broadcaster = AsyncBroadcaster()

class ParkingService:
    def __init__(self, entrance_node:int=0):
        # in-memory structures mirror DB; DB is source-of-truth on startup
        self.queue = deque()
        self.pricing_base = 5.0  # base rate per minute
        self.entrance_node = entrance_node
        self.lock = asyncio.Lock()

    async def load_slots(self):
        # expected slot documents: {slot_id, node_id, occupied, car_number}
        docs = await slots_col.find().to_list(length=None)
        self.slots = {d["slot_id"]: d for d in docs}
        # build mapping node->slot
        self.node_to_slot = {d["node_id"]: d["slot_id"] for d in docs}

    async def init_defaults(self, total_slots=20):
        # create default linear graph if slots empty
        count = await slots_col.count_documents({})
        if count == 0:
            # create slots with node ids 0..total_slots-1
            docs = []
            for i in range(total_slots):
                docs.append({
                    "slot_id": i,
                    "node_id": i+1,  # node 0 reserved for entrance
                    "occupied": False,
                    "car_number": None
                })
            await slots_col.insert_many(docs)
        await self.load_slots()
        # initialize stats doc if missing
        if await stats_col.count_documents({}) == 0:
            await stats_col.insert_one({
                "revenue": 0.0,
                "total_parked": 0,
                "total_exited": 0,
                "total_wait_time_seconds": 0.0
            })

    def _current_occupancy(self):
        occupied = sum(1 for s in self.slots.values() if s.get("occupied"))
        total = len(self.slots)
        return occupied, total

    def _dynamic_rate(self):
        occupied, total = self._current_occupancy()
        if total == 0:
            return self.pricing_base
        occupancy_ratio = occupied / total
        # simple formula: base * (1 + occupancy_ratio)
        return round(self.pricing_base * (1 + occupancy_ratio), 2)

    async def _update_slot_db(self, slot_id, occupied, car_number=None):
        await slots_col.update_one({"slot_id": slot_id}, {"$set": {"occupied": occupied, "car_number": car_number}})
        # sync in-memory
        self.slots[slot_id]["occupied"] = occupied
        self.slots[slot_id]["car_number"] = car_number

    async def _record_car_entry(self, car_number, slot_id):
        doc = {
            "car_number": car_number,
            "slot_id": slot_id,
            "entry_time": now_utc(),
            "exit_time": None,
            "charge": None
        }
        try:
            res = await cars_col.insert_one(doc)
            return res.inserted_id
        except DuplicateKeyError:
            # concurrent insert for same car_number happened
            return None

    async def _record_car_exit(self, car_number, charge, exit_time):
        res = await cars_col.find_one_and_update({"car_number": car_number, "exit_time": None}, {"$set": {"exit_time": exit_time, "charge": charge}})
        return res

    async def _update_stats_on_exit(self, parked_seconds, charge):
        # update revenue and counters
        await stats_col.update_one({}, {"$inc": {"revenue": charge, "total_exited": 1, "total_wait_time_seconds": parked_seconds}})

    async def _get_stats(self):
        doc = await stats_col.find_one({})
        if not doc:
            return {"revenue":0.0,"total_parked":0,"total_exited":0,"total_wait_time_seconds":0.0}
        return doc

    # Dijkstra: graph nodes are 0..N where 0 is entrance and others map to slot nodes
    async def find_nearest_free_slot(self, graph_adj: Dict[int, List[tuple]]):
        # standard Dijkstra from entrance to any free slot's node
        # build node -> free boolean
        free_nodes = set()
        for slot in self.slots.values():
            if not slot.get("occupied"):
                free_nodes.add(slot["node_id"])
        if not free_nodes:
            return None  # no free slots

        # Dijkstra
        start = self.entrance_node
        dist = {start: 0}
        prev = {}
        h = [(0, start)]
        visited = set()
        while h:
            d, u = heapq.heappop(h)
            if u in visited:
                continue
            visited.add(u)
            if u in free_nodes:
                # return corresponding slot id
                slot_id = self.node_to_slot.get(u)
                return slot_id
            for v, w in graph_adj.get(u, []):
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(h, (nd, v))
        return None

    async def add_car(self, car_number: str, graph_adj: Dict[int, List[tuple]]):
        async with self.lock:
            # check if car already parked
            existing = await cars_col.find_one({"car_number": car_number, "exit_time": None})
            if existing:
                return {"ok": False, "msg": "Car already parked"}

            slot_id = await self.find_nearest_free_slot(graph_adj)
            if slot_id is None:
                # enqueue
                self.queue.append({"car_number": car_number, "time": now_utc()})
                return {"ok": True, "queued": True, "msg": "Parking full. Car queued."}

            # assign - update slot then record entry. If recording fails due to duplicate key,
            # rollback the slot update to avoid inconsistent state.
            await self._update_slot_db(slot_id, True, car_number)
            inserted = await self._record_car_entry(car_number, slot_id)
            if inserted is None:
                # rollback slot occupation
                await self._update_slot_db(slot_id, False, None)
                return {"ok": False, "msg": "Concurrent insert detected. Car not parked."}
            # increment total_parked stat
            await stats_col.update_one({}, {"$inc": {"total_parked": 1}})
            # broadcast update
            await broadcaster.broadcast(await self.current_state())
            return {"ok": True, "queued": False, "msg": f"Parked at slot {slot_id}", "slot_id": slot_id}

    async def _assign_slot_to_next_in_queue(self, graph_adj: Dict[int, List[tuple]]):
        if not self.queue:
            return
        # try to assign slot to first queued car
        slot_id = await self.find_nearest_free_slot(graph_adj)
        if slot_id is None:
            return
        entry = self.queue.popleft()
        car_number = entry["car_number"]
        await self._update_slot_db(slot_id, True, car_number)
        inserted = await self._record_car_entry(car_number, slot_id)
        if inserted is None:
            # rollback and skip this queued car (it may already have been inserted concurrently)
            await self._update_slot_db(slot_id, False, None)
            return
        await stats_col.update_one({}, {"$inc": {"total_parked": 1}})
        await broadcaster.broadcast(await self.current_state())

    async def remove_car(self, car_number: str, graph_adj: Dict[int, List[tuple]]):
        async with self.lock:
            # find car active record
            doc = await cars_col.find_one({"car_number": car_number, "exit_time": None})
            if not doc:
                return {"ok": False, "msg": "Car not found or already exited"}
            slot_id = doc.get("slot_id")
            entry_time = doc.get("entry_time")
            exit_time = now_utc()
            parked_seconds = (exit_time - entry_time).total_seconds()
            # compute rate at exit using dynamic rate at exit
            rate_per_min = self._dynamic_rate()
            charge = round((parked_seconds/60.0) * rate_per_min, 2)
            await self._record_car_exit(car_number, charge, exit_time)
            await self._update_slot_db(slot_id, False, None)
            await self._update_stats_on_exit(parked_seconds, charge)
            # try assign next in queue
            await self._assign_slot_to_next_in_queue(graph_adj)
            await broadcaster.broadcast(await self.current_state())
            return {"ok": True, "charge": charge}

    async def current_state(self):
        # prepare lightweight state for UI
        stats = await self._get_stats()
        occupied, total = self._current_occupancy()
        avg_wait = None
        if stats.get("total_exited", 0) > 0:
            avg_wait = stats.get("total_wait_time_seconds", 0.0) / max(1, stats.get("total_exited", 1))
        # sanitize BSON ObjectId and other non-serializable fields for JSON response
        slots_list = []
        for s in self.slots.values():
            # make a shallow copy so we don't mutate in-memory doc
            doc = dict(s)
            # convert ObjectId to str if present
            if "_id" in doc and isinstance(doc["_id"], ObjectId):
                doc["_id"] = str(doc["_id"])
            slots_list.append(doc)

        state = {
            "slots": slots_list,
            "queue_length": len(self.queue),
            "pricing_rate_per_min": self._dynamic_rate(),
            "revenue": stats.get("revenue", 0.0),
            "occupancy": {"occupied": occupied, "total": total},
            "avg_wait_seconds": avg_wait
        }
        return state

parking_service = ParkingService()
