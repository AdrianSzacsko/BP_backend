from enum import Enum

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session, sessionmaker

from app.db import init_db
from app.models import Users, Farms, Settings
from starlette.status import HTTP_200_OK
from typing import List, Optional

from app.db.database import create_connection
from app.routers.feed import check_tokens, send_multicast
from app.security import auth

from app.schemas.weather_schema import CurrentResponse, HourlyResponse, WeatherVariables, WeatherPydantic, \
    WeatherLocation, SearchResponse, DailyResponse, WeatherVariablesDaily

import requests
from app.settings import settings

from app.miscFunctions.coordinates import check_coors

router = APIRouter(
    prefix="/weather",
    tags=["Weather"]
)


class WeatherType(Enum):
    Current = 1
    Hourly = 2
    Daily = 3


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, list):
            for elem in v:
                items.extend(flatten_dict(elem, new_key, sep=sep).items())
        elif isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_OpenWeather(lat: float, long: float, type=WeatherType.Current):
    check_coors(long, lat)
    try:
        if type == WeatherType.Current:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={settings.OPENWEATHERMAP_KEY}&units=metric")
        elif type == WeatherType.Hourly:
            response = requests.get(
                f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={long}&appid={settings.OPENWEATHERMAP_KEY}&units=metric&cnt=24")
        else:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={long}&appid={settings.OPENWEATHERMAP_KEY}&units=metric&cnt=16")

        response.raise_for_status()
        weather_data = response.json()
        return weather_data
    except requests.exceptions.HTTPError as errh:
        raise HTTPException(status_code=500, detail="OpenWeatherMap API Error")
    except requests.exceptions.ConnectionError as errc:
        raise HTTPException(status_code=500, detail="Error Connecting")
    except requests.exceptions.Timeout as errt:
        raise HTTPException(status_code=500, detail="Timeout Error")
    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=500, detail="Something went wrong")


def get_keys_values(variables, key, dict):
    try:
        variables[key] = dict.get(key, 0)
    except Exception:
        variables[key] = dict.get(key, '')
    return variables


def create_dict_curr_weather(lat: float, long: float):
    data = get_OpenWeather(lat, long, type=WeatherType.Current)
    flattened = flatten_dict(data)

    weather = {}
    variables = {}

    for key in WeatherVariables.__fields__.keys():
        get_keys_values(variables, key, flattened)

    for key in WeatherPydantic.__fields__.keys():
        get_keys_values(weather, key, flattened)
    return {'weather': weather, 'variables': variables}


def create_dict_hourly_weather(lat: float, long: float):
    data = get_OpenWeather(lat, long, type=WeatherType.Hourly)
    weather = {}
    variables = []
    for i in range(len(data['list'])):
        flattened = flatten_dict(data['list'][i])
        variables.append({})
        for key in WeatherVariables.__fields__.keys():
            get_keys_values(variables[i], key, flattened)

    data['sys'] = data['city']
    del data['city']
    flattened = flatten_dict(data)
    for key in WeatherPydantic.__fields__.keys():
        get_keys_values(weather, key, flattened)

    # some keys have sys in them, we need to delete them
    bad_keys = {'sys_name': 'name', 'sys_coord_lat': 'coord_lat',
                'sys_coord_lon': 'coord_lon', 'sys_timezone': 'timezone'}
    for key in bad_keys.keys():
        try:
            weather[bad_keys[key]] = flattened.get(key, 0)
        except Exception:
            weather[bad_keys[key]] = flattened.get(key, '')

    return {'weather': weather, 'variables': variables}


def create_dict_daily_weather(lat: float, long: float):
    data = get_OpenWeather(lat, long, type=WeatherType.Daily)
    weather = {}
    variables = []
    for i in range(len(data['list'])):
        flattened = flatten_dict(data['list'][i])
        variables.append({})
        for key in WeatherVariablesDaily.__fields__.keys():
            get_keys_values(variables[i], key, flattened)

    data['sys'] = data['city']
    del data['city']
    flattened = flatten_dict(data)
    for key in WeatherPydantic.__fields__.keys():
        get_keys_values(weather, key, flattened)

    # some keys have sys in them, we need to delete them
    bad_keys = {'sys_name': 'name', 'sys_coord_lat': 'coord_lat',
                'sys_coord_lon': 'coord_lon', 'sys_timezone': 'timezone'}
    for key in bad_keys.keys():
        try:
            weather[bad_keys[key]] = flattened.get(key, 0)
        except Exception:
            weather[bad_keys[key]] = flattened.get(key, '')

    return {'weather': weather, 'variables': variables}


def get_Nominatim(search_string: str):
    if len(search_string) < 1:
        raise HTTPException(status_code=500, detail="Search string not correct")
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?q={search_string}&format=json&accept-language=en")
        response.raise_for_status()
        search_data = response.json()
        return search_data
    except requests.exceptions.HTTPError as errh:
        raise HTTPException(status_code=500, detail="Nominatim API Error")
    except requests.exceptions.ConnectionError as errc:
        raise HTTPException(status_code=500, detail="Error Connecting")
    except requests.exceptions.Timeout as errt:
        raise HTTPException(status_code=500, detail="Timeout Error")
    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=500, detail="Something went wrong")


@router.get("/curr/{lat}/{long}", response_model=CurrentResponse, status_code=HTTP_200_OK,
            summary="Retrieves current weather for a given location.",
            responses={404: {"description": "Location not found"}})
def get_curr_weather(lat: float,
                     long: float,
                     # user: Users = Depends(auth.get_current_user),
                     db: Session = Depends(create_connection)):
    return create_dict_curr_weather(lat, long)


@router.get("/hourly/{lat}/{long}", response_model=HourlyResponse, status_code=HTTP_200_OK,
            summary="Retrieves hourly weather for a given location.",
            responses={404: {"description": "Location not found"}})
def get_hourly_weather(lat: float,
                       long: float,
                       # user: Users = Depends(auth.get_current_user),
                       db: Session = Depends(create_connection)):
    return create_dict_hourly_weather(lat, long)


@router.get("/daily/{lat}/{long}", response_model=DailyResponse, status_code=HTTP_200_OK,
            summary="Retrieves daily weather for a given location.",
            responses={404: {"description": "Location not found"}})
def get_daily_weather(lat: float,
                      long: float,
                      # user: Users = Depends(auth.get_current_user),
                      db: Session = Depends(create_connection)):
    return create_dict_daily_weather(lat, long)


@router.get("/search/{string}", response_model=list[SearchResponse], status_code=HTTP_200_OK,
            summary="Retrieves the location from text search",
            responses={404: {"description": "Location not found"}})
def get_search_location(string: str,
                        db: Session = Depends(create_connection)):
    data = get_Nominatim(string)
    result = []
    for item in data:
        result.append({})
        for key in SearchResponse.__fields__.keys():
            result[len(result) - 1][key] = item.get(key, None)
        # check for duplicate
        for dictionary in result[:len(result) - 1]:
            if result[len(result) - 1]['type'] == dictionary['type'] \
                    and result[len(result) - 1]['display_name'] == dictionary['display_name']:
                result.pop(len(result) - 1)
                break
    return result


"""@router.get("/alert", status_code=HTTP_200_OK,
            summary="Generates a weather alert")
def get_search_location(db: Session = Depends(create_connection)):"""


def get_alert():
    SessionLocal = sessionmaker(autocommit=False, bind=init_db.engine)
    db = SessionLocal()
    try:
        coordinates_set = set()
        query = db.query(Farms.latitude, Farms.longitude, Settings.fcm_token, Settings.news_notifications) \
            .join(Settings, Settings.user_id == Farms.user_id).all()
        for result in query:
            if result.fcm_token and result.news_notifications:
                weather_forecast = create_dict_daily_weather(result.latitude, result.longitude)
                title = "Tomorrow in " + weather_forecast['weather']['name'] + " : " + \
                        weather_forecast['variables'][1]['weather_description'].capitalize()
                body = "Temperature will be " + str(weather_forecast['variables'][1]['temp_day']) + "°C" + "\n" + \
                       "At night will be " + str(weather_forecast['variables'][1]['temp_night']) + "°C"
                send_multicast([result.fcm_token], title, body)
            continue
    finally:
        db.close()
