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


class WeatherVariablesDaily(BaseModel):
    temp_day: Optional[float]
    temp_min: Optional[float]
    temp_max: Optional[float]
    temp_night: Optional[float]
    temp_eve: Optional[float]
    temp_morn: Optional[float]
    feels_like_day: Optional[float]
    feels_like_night: Optional[float]
    feels_like_eve: Optional[float]
    feels_like_morn: Optional[float]
    pressure: Optional[int]
    humidity: Optional[int]
    weather_main: Optional[str]
    weather_icon: Optional[str]
    weather_description: Optional[str]
    weather_id: Optional[int]
    wind_speed: Optional[float]
    wind_deg: Optional[int]
    wind_gust: Optional[float]
    clouds: Optional[float]
    rain: Optional[float]
    snow: Optional[float]
    pop: Optional[float]


class WeatherVariables(BaseModel):
    weather_main: Optional[str]
    weather_icon: Optional[str]
    weather_description: Optional[str]
    weather_id: Optional[int]
    main_temp: Optional[float]
    main_temp_min: Optional[float]
    main_temp_max: Optional[float]
    main_feels_like: Optional[float]
    main_pressure: Optional[int]
    main_sea_level: Optional[int]
    main_grnd_level: Optional[int]
    main_humidity: Optional[int]
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


class DailyResponse(BaseModel):
    weather: WeatherPydantic
    variables: list[WeatherVariablesDaily]

    class Config:
        orm_mode = True


class SearchResponse(BaseModel):
    display_name: Optional[str]
    type: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    importance: Optional[float]
    icon: Optional[str]

    class Config:
        orm_mode = True
