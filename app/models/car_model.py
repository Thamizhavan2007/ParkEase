from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CarIn(BaseModel):
    car_number: str = Field(..., min_length=1)


class CarDB(BaseModel):
    car_number: str
    slot_id: Optional[int]
    entry_time: datetime
    exit_time: Optional[datetime] = None
    charge: Optional[float] = None


class CarOut(CarDB):
    pass