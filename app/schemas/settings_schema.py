from pydantic import BaseModel
from typing import Optional


class Notifications(BaseModel):
    weather_notifications: bool
    news_notifications: bool

    class Config:
        orm_mode = True
