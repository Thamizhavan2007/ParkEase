from pydantic import BaseModel
from typing import Optional, List


class Slot(BaseModel):
    slot_id: int
    node_id: int # node in graph
    occupied: bool = False
    car_number: Optional[str] = None


class SlotGraph(BaseModel):
    nodes: List[int]
    # adjacency: node -> list of (neighbor_node, weight)
    adjacency: dict