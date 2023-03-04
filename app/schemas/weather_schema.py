from pydantic import BaseModel, Field
from typing import Optional


class WeatherLocation(BaseModel):
    latitude: float
    longitude: float


class WeatherPydantic(BaseModel):
    coord_lat: Optional[float] = Field(default=0)
    coord_lon: Optional[float] = Field(default=0)
    timezone: Optional[int] = Field(default=0)
    name: Optional[str] = Field(default='')
    sys_country: Optional[str] = Field(default='')
    sys_sunset: Optional[int] = Field(default=0)
    sys_sunrise: Optional[int] = Field(default=0)


class WeatherVariables(BaseModel):
    weather_main: Optional[str] = Field(default='')
    weather_icon: Optional[str] = Field(default='')
    main_temp: Optional[float] = Field(default=0)
    main_feels_like: Optional[float] = Field(default=0)
    main_pressure: Optional[int] = Field(default=0)
    main_sea_level: Optional[int] = Field(default=0)
    main_grnd_level: Optional[int] = Field(default=0)
    visibility: Optional[int] = Field(default=0)
    wind_speed: Optional[float] = Field(default=0)
    wind_deg: Optional[int] = Field(default=0)
    wind_gust: Optional[float] = Field(default=0)
    clouds_all: Optional[float] = Field(default=0)
    rain_1h: Optional[float] = Field(default=0)
    snow_1h: Optional[float] = Field(default=0)
    pop: Optional[float] = Field(default=0)


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
