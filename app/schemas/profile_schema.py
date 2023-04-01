from pydantic import BaseModel
from typing import Optional
from app.schemas.farms_schema import GetFarms


class Search_profile(BaseModel):
    first_name: str
    last_name: str
    id: int

    class Config:
        orm_mode = True


class Get_Profile(BaseModel):
    id: int
    first_name: str
    last_name: str
    post_count: int
    like_count: int
    farms: Optional[list[GetFarms]]
    interaction: Optional[bool]
    picture_path: Optional[str]


class Like_dislike(BaseModel):
    profile_id: int
    interaction: Optional[bool]

    class Config:
        orm_mode = True


