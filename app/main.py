import asyncio

import socketio as socketio
from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.auth_schema import Token
from .db.database import create_connection
from .models import Users

from .routers import login, register, weather, farms, profile, feed, settings
from .periodic_check import weather as PeriodicWeather

from fastapi.middleware.cors import CORSMiddleware
from app.periodic_check.weather import update_weather_db

# SOURCE: https://fastapi.tiangolo.com/tutorial/metadata/
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate('firebase_cred.json')
firebase_admin.initialize_app(cred)

app = FastAPI()
tasks = BackgroundTasks()


#@app.on_event("startup")
#@app.get("/test")
#@repeat_every(seconds=5)
"""async def run_periodic():
    while True:
        update_weather_db(create_connection())
        await asyncio.sleep(5)
"""

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)

app.include_router(login.router)
app.include_router(register.router)
app.include_router(weather.router)
app.include_router(farms.router)
app.include_router(profile.router)
app.include_router(feed.router)
app.include_router(settings.router)

@app.get("/")
async def root():
    return {"message": "BP project by Adrian Szacsko"}


from app.security.deps import get_current_user


"""@app.get('/me', summary='Get details of currently logged in user', response_model=Token)
async def get_me(user: Users = Depends(get_current_user)):
    return user"""

