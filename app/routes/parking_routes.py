# from fastapi import APIRouter
# from app.services.parking_service import ParkingSystem

# router = APIRouter()
# parking = ParkingSystem(total_slots=10)

# @router.post("/entry/{car_number}")
# def car_entry(car_number: str):
#     return {"message": parking.add_car(car_number)}

# @router.post("/exit/{car_number}")
# def car_exit(car_number: str):
#     return {"message": parking.remove_car(car_number)}

# @router.get("/status")
# def parking_status():
#     return {
#         "slots": parking.slots,
#         "queue": list(parking.wait_queue)
#     }




from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi import BackgroundTasks
from typing import Dict, List
from app.services.parking_service import parking_service, broadcaster
from app.db import database
from app.utils.helpers import now_utc

router = APIRouter()

# Example graph adjacency: node 0 (entrance) connects to slot nodes 1..N
# For simplicity, create a star graph edges (0->node) with weight=1.
# In production you can load a custom graph from DB or config.

async def default_graph_adj():
    # ensure slots are loaded from DB into the service
    if not hasattr(parking_service, "slots"):
        await parking_service.load_slots()

    # create adjacency mapping using current slots
    # Build a 4x5 grid (rows x cols) of slot nodes. Node ids in DB are assigned as 1..N
    rows = 4
    cols = 5
    # Build mapping between node_id and (r,c)
    node_to_rc = {}
    rc_to_node = {}
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            node_id = idx + 1
            node_to_rc[node_id] = (r, c)
            rc_to_node[(r, c)] = node_id

    adj = {}
    # entrance node 0 connects to all nodes in the first row (r=0)
    adj[0] = []
    for c in range(cols):
        nid = rc_to_node[(0, c)]
        adj[0].append((nid, 1))

    # connect grid neighbors (4-neighborhood) and link first-row nodes back to entrance
    for node_id, (r, c) in node_to_rc.items():
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbors.append((rc_to_node[(nr, nc)], 1))
        if r == 0:
            # make graph undirected with entrance
            neighbors.append((0, 1))
        adj[node_id] = neighbors

    return adj

@router.post("/entry/{car_number}")
async def car_entry(car_number: str):
    adj = await default_graph_adj()
    res = await parking_service.add_car(car_number, adj)
    return res

@router.post("/exit/{car_number}")
async def car_exit(car_number: str):
    adj = await default_graph_adj()
    res = await parking_service.remove_car(car_number, adj)
    return res

@router.get("/status")
async def status():
    return await parking_service.current_state()

# WebSocket endpoint to stream live updates
@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await broadcaster.connect(ws)
    try:
        # send initial state
        await ws.send_json(await parking_service.current_state())
        while True:
            # keep connection open; expect ping messages from client
            data = await ws.receive_text()
            # echo or respond with current state
            await ws.send_json(await parking_service.current_state())
    except WebSocketDisconnect:
        await broadcaster.disconnect(ws)
