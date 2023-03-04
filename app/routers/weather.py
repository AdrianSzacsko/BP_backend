from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models import Users
from starlette.status import HTTP_200_OK
from typing import List, Optional

from app.db.database import create_connection
from app.security import auth

from app.schemas.weather_schema import CurrentResponse, HourlyResponse, WeatherVariables, WeatherPydantic, \
    WeatherLocation, SearchResponse

import requests
from app.settings import settings

from app.miscFunctions.coordinates import check_coors

router = APIRouter(
    prefix="/weather",
    tags=["Weather"]
)


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


def get_OpenWeather(lat: float, long: float, curr=True):
    check_coors(long, lat)
    try:
        if curr:
            response = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&appid={settings.OPENWEATHERMAP_KEY}&units=metric")
        else:
            response = requests.get(
                f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={lat}&lon={long}&appid={settings.OPENWEATHERMAP_KEY}&units=metric")
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


def create_dict_curr_weather(lat: float, long: float):
    data = get_OpenWeather(lat, long, curr=True)
    flattened = flatten_dict(data)

    weather = {}
    variables = {}

    for key in WeatherVariables.__fields__.keys():
        variables[key] = flattened.get(key, None)

    for key in WeatherPydantic.__fields__.keys():
        weather[key] = flattened.get(key, None)
    return {'weather': weather, 'variables': variables}


def create_dict_hourly_weather(lat: float, long: float):
    data = get_OpenWeather(lat, long, curr=False)
    weather = {}
    variables = []
    for i in range(len(data['list'])):
        flattened = flatten_dict(data['list'][i])
        variables.append({})
        for key in WeatherVariables.__fields__.keys():
            variables[i][key] = flattened.get(key, None)

    data['sys'] = data['city']
    del data['city']
    flattened = flatten_dict(data)
    for key in WeatherPydantic.__fields__.keys():
        weather[key] = flattened.get(key, None)

    # some keys have sys in them, we need to delete them
    bad_keys = {'sys_name': 'name', 'sys_coord_lat': 'coord_lat',
                'sys_coord_lon': 'coord_lon', 'sys_timezone': 'timezone'}
    for key in bad_keys.keys():
        weather[bad_keys[key]] = flattened.get(key, None)

    return {'weather': weather, 'variables': variables}


@router.get("/curr/{latitude}{longitude}", response_model=CurrentResponse, status_code=HTTP_200_OK,
            summary="Retrieves current weather for a given location.",
            responses={404: {"description": "Location not found"}})
def get_curr_weather(lat: Optional[float] = 0,
                     long: Optional[float] = 0,
                     user: Users = Depends(auth.get_current_user),
                     db: Session = Depends(create_connection)):
    return create_dict_curr_weather(lat, long)


@router.get("/hourly/{latitude}{longitude}", response_model=HourlyResponse, status_code=HTTP_200_OK,
            summary="Retrieves current weather for a given location.",
            responses={404: {"description": "Location not found"}})
def get_hourly_weather(lat: Optional[float] = 0,
                       long: Optional[float] = 0,
                       user: Users = Depends(auth.get_current_user),
                       db: Session = Depends(create_connection)):
    return create_dict_hourly_weather(lat, long)


from app.periodic_check.weather import update_weather_db


@router.put("/test_periodic", status_code=HTTP_200_OK,
            summary="Test function for periodic weather updates",
            responses={404: {"description": "Location not found"}})
def get_hourly_weather(db: Session = Depends(create_connection)):
    update_weather_db(db)


@router.get("/search/{string}", response_model=list[SearchResponse], status_code=HTTP_200_OK,
            summary="Retrieves the location from text search",
            responses={404: {"description": "Location not found"}})
def get_search_location(string: str,
                       user: Users = Depends(auth.get_current_user),
                       db: Session = Depends(create_connection)):
    data = get_Nominatim(string)
    result = []
    for item in data:
        result.append({})
        for key in SearchResponse.__fields__.keys():
            result[len(result) - 1][key] = item.get(key, None)
        # check for duplicate
        for dictionary in result[:len(result)-1]:
            if result[len(result) - 1]['type'] == dictionary['type'] \
                    and result[len(result) - 1]['display_name'] == dictionary['display_name']:
                result.pop(len(result) - 1)
                break
    return result
