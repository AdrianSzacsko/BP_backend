import datetime

from pydantic import BaseModel
from typing import Optional


class GetFeed(BaseModel):
    distance_range: int
    farm_id: int

    class Config:
        orm_mode = True


class GetFeedResponse(BaseModel):
    farm_lat: float
    farm_lon: float
    id: int
    user_id: int
    first_name: str
    last_name: str
    post_name: str
    latitude: float
    longitude: float
    category: str
    text: str
    date: datetime.datetime
    photos_id: Optional[list[int]]

    class Config:
        orm_mode = True


class GetFeedResponseProfile(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    post_name: str
    latitude: float
    longitude: float
    category: str
    text: str
    date: datetime.datetime
    photos_id: Optional[list[int]]

    class Config:
        orm_mode = True


class NewPost(BaseModel):
    post_name: str
    latitude: float
    longitude: float
    category: str
    text: str

    class Config:
        orm_mode = True


