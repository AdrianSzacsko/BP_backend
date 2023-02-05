from pydantic import BaseModel
from typing import Optional


class PostFarm(BaseModel):
    name: str
    lat: float
    long: float

class DeleteFarm(BaseModel):
    name: str
