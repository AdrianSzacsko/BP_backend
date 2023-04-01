import datetime

from pydantic import BaseModel
from typing import Optional


class GetFeed(BaseModel):
    distance_range: int
    latitude: float
    longitude: float

    class Config:
        orm_mode = True


class GetFeedResponse(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    latitude: float
    longitude: float
    category: str
    text: str
    date: datetime.datetime
    photos_id: Optional[list[int]]

    class Config:
        orm_mode = True


class NewPost(BaseModel):
    latitude: float
    longitude: float
    category: str
    text: str

    class Config:
        orm_mode = True


