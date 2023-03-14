from pydantic import BaseModel
from typing import Optional


class PostFarm(BaseModel):
    name: str
    latitude: float
    longitude: float


class DeleteFarm(BaseModel):
    id: int


class GetFarms(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float

    class Config:
        orm_mode = True
