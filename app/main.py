import asyncio

import socketio as socketio
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi_amis_admin.admin.settings import Settings
from fastapi_amis_admin.admin.site import AdminSite
from sqlalchemy.orm import Session

from app.schemas.auth_schema import Token
from .db.database import create_connection
from .models import Users

from .routers import login, register, weather, farms, profile, feed, settings


from fastapi.middleware.cors import CORSMiddleware


# SOURCE: https://fastapi.tiangolo.com/tutorial/metadata/
import firebase_admin
from firebase_admin import credentials

from fastapi_scheduler import SchedulerAdmin

from .routers.weather import get_alert

cred = credentials.Certificate('firebase_cred.json')
firebase_admin.initialize_app(cred)

app = FastAPI()
#tasks = BackgroundTasks()


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

from tzlocal import get_localzone

site = AdminSite(settings=Settings(database_url_async='sqlite+aiosqlite:///amisadmin.db'))
scheduler = SchedulerAdmin.bind(site)
scheduler.timezone = get_localzone()


@scheduler.scheduled_job('cron', hour=10, minute=10,)
def interval_task():
    # print("Interval task running...")
    get_alert()


@app.on_event("startup")
async def startup():
    site.mount_app(app)
    scheduler.start()


"""@app.get('/me', summary='Get details of currently logged in user', response_model=Token)
async def get_me(user: Users = Depends(get_current_user)):
    return user"""

