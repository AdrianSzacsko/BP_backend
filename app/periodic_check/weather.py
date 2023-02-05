import datetime

from fastapi import Depends, APIRouter
from app.db.database import create_connection
from app.models import Farms, Settings, Weather, Weather_variables, Weather_current, Weather_hourly
from sqlalchemy.orm import Session
from app.routers.weather import create_dict_hourly_weather, create_dict_curr_weather


def update_weather_db(db: Session):
    farms_query = db.query(Farms.id,
                           Farms.user_id,
                           Farms.weather_id,
                           Farms.name,
                           Farms.latitude,
                           Farms.longitude)
    join_settings = farms_query.join(Settings, Settings.user_id == Farms.user_id)
    farms = join_settings.all()
    if len(farms) == 0:
        return

    for i in range(len(farms)):
        farm = farms[i]
        lat = float(farm[4])
        long = float(farm[5])
        dict_current = create_dict_curr_weather(lat, long)
        dict_hourly = create_dict_hourly_weather(lat, long)
        if farm[2]:
            #update current weather
            # do the update
            query = db.query(Weather).filter(Weather.id == farm[2])
            query.update(dict_current['weather'])

            # Update the Weather_current table
            query = db.query(Weather_current).filter(Weather_current.weather_id == farm[2])
            query.update({'refresh_time': datetime.datetime.now()})

            # Update the Weather_variables table
            query = db.query(Weather_variables).filter(Weather_variables.id == query.first().variables_id)
            query.update(dict_current['variables'])

            #update todo hourly weather

            db.commit()
        else:
            #update current weather
            # do the insert
            weather = Weather(**dict_current['weather'])
            weather_variables = Weather_variables(**dict_current['variables'])
            weather_current = Weather_current(weather=weather, weather_variables=weather_variables,
                                              refresh_time=datetime.datetime.now())
            # todo update hourly weather

            db.add_all([weather, weather_current, weather_variables])
            db.commit()
            farms_query = db.query(Farms)
            farms_query = farms_query.filter(Farms.id == farms[i].id)
            farms_query.update({Farms.weather_id: weather.id})
            db.commit()



    return
    # todo update from openweatherMap
