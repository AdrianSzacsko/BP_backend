from pydantic import BaseModel
from typing import Optional


class WeatherLocation(BaseModel):
    latitude: float
    longitude: float


class WeatherPydantic(BaseModel):
    coord_lat: Optional[float]
    coord_lon: Optional[float]
    timezone: Optional[int]
    name: Optional[str]
    sys_country: Optional[str]
    sys_sunset: Optional[int]
    sys_sunrise: Optional[int]

    class Config:
        orm_mode = True


class WeatherVariables(BaseModel):
    weather_main: Optional[str]
    weather_icon: Optional[str]
    main_temp: Optional[float]
    main_feels_like: Optional[float]
    main_pressure: Optional[int]
    main_sea_level: Optional[int]
    main_grnd_level: Optional[int]
    visibility: Optional[int]
    wind_speed: Optional[float]
    wind_deg: Optional[int]
    wind_gust: Optional[float]
    clouds_all: Optional[float]
    rain_1h: Optional[float]
    snow_1h: Optional[float]
    pop: Optional[float]

    class Config:
        orm_mode = True


class CurrentResponse(BaseModel):
    weather: WeatherPydantic
    variables: WeatherVariables

    class Config:
        orm_mode = True


class HourlyResponse(BaseModel):
    weather: WeatherPydantic
    variables: list[WeatherVariables]

    class Config:
        orm_mode = True
