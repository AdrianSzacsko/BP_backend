from pydantic import BaseModel
from typing import Optional


class Search_profile(BaseModel):
    name: str
    id: int

    class Config:
        orm_mode = True


class Get_farms(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float


class Get_Profile(BaseModel):
    id: int
    first_name: str
    last_name: str
    post_count: int
    like_count: int
    dislike_count: int
    farms: Optional[list[Get_farms]]
    is_like: Optional[bool]


class Like_dislike(BaseModel):
    profile_id: int
    is_like: Optional[bool]

    class Config:
        orm_mode = True


