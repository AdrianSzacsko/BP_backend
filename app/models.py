import enum

from sqlalchemy import Column, Integer, Boolean, ForeignKey, text, CheckConstraint, NUMERIC, Enum
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP, VARCHAR, TEXT

from .db.base import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(VARCHAR(50), nullable=False)
    last_name = Column(VARCHAR(50), nullable=False)
    password = Column(VARCHAR(60), nullable=False)
    email = Column(VARCHAR(50), nullable=False)
    photo = Column(VARCHAR(100), nullable=True)
    registration_date = Column(TIMESTAMP(timezone=False), nullable=False, server_default=text('now()'))


class Users_attributes(Base):
    __tablename__ = "users_attributes"

    id = Column(Integer, primary_key=True, nullable=False)
    post_count = Column(Integer, CheckConstraint("post_count >= 0"), nullable=False, default=0)
    like_count = Column(Integer, CheckConstraint("like_count >= 0"), nullable=False, default=0)
    user_id = Column(Integer, ForeignKey(Users.id, ondelete='CASCADE'))
    #user = relationship('users', )


"""class Weather(Base):
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True)
    coord_lat = Column(NUMERIC(5, 3), unique=True)
    coord_lon = Column(NUMERIC(6, 3), unique=True)
    timezone = Column(Integer)
    name = Column(VARCHAR(50))
    sys_country = Column(VARCHAR(50))
    sys_sunset = Column(Integer)
    sys_sunrise = Column(Integer)
    current = relationship('Weather_current', backref='weather')
    hourly = relationship('Weather_hourly', backref='weather')
    farms = relationship('Farms', backref='weather')"""


class Farms(Base):
    __tablename__ = 'farms'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(Users.id, ondelete='cascade'))
    # weather_id = Column(Integer, ForeignKey(Weather.id, ondelete='set null'))
    name = Column(VARCHAR(50), nullable=False)
    latitude = Column(NUMERIC(17, 15), nullable=False)
    longitude = Column(NUMERIC(18, 15), nullable=False)
    #user = relationship("Users")
    CheckConstraint('latitude <= 90 and latitude >= -90', name='latitude_check'),
    CheckConstraint('longitude <= 180 and longitude >= -180', name='longitude_check'),


"""class Likes_dislikes(Base):
    __tablename__ = 'likes_dislikes'

    follower = Column(Integer, ForeignKey(Users.id, ondelete='cascade'), primary_key=True)
    followed_profile = Column(Integer, ForeignKey(Users.id, ondelete='cascade'), primary_key=True)
    is_like = Column(Boolean, nullable=False)
    #follower_user = relationship("Users", foreign_keys=[follower])
    #followed_user = relationship("Users", foreign_keys=[followed_profile])"""


class Interactions(Base):
    __tablename__ = 'interactions'

    follower = Column(Integer, ForeignKey(Users.id, ondelete='cascade'), primary_key=True)
    followed_profile = Column(Integer, ForeignKey(Users.id, ondelete='cascade'), primary_key=True)


class Posts(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(Users.id, ondelete='set null'))
    latitude = Column(NUMERIC(17, 15), nullable=False)
    longitude = Column(NUMERIC(18, 15), nullable=False)
    category = Column(VARCHAR(50), nullable=False)
    text = Column(TEXT, default='')
    date = Column(TIMESTAMP, default='now()')
    CheckConstraint('latitude <= 90 and latitude >= -90', name='latitude_check')
    CheckConstraint('longitude <= 180 and longitude >= -180', name='longitude_check')
    #post_photos = relationship('Post_photos', backref='posts')
    post_photos = relationship('Post_photos', back_populates='post')


"""class Comments(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey(Posts.id, ondelete='cascade'))
    text = Column(TEXT, default='')
    date = Column(TIMESTAMP(timezone=False), default='now()')
    #post = relationship("Posts", back_populates="comments")"""


class Post_photos(Base):
    __tablename__ = 'post_photos'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey(Posts.id, ondelete='cascade'))
    photo = Column(VARCHAR(100))
    post = relationship('Posts', back_populates='post_photos')


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(Users.id, ondelete='cascade'))
    min_temp = Column(Integer)
    max_temp = Column(Integer)
    weather_notifications = Column(Boolean, default=True)
    news_notifications = Column(Boolean, default=True)
    fcm_token = Column(VARCHAR(255))
    #user = relationship("Users")

#weather


"""class Weather_variables(Base):
    __tablename__ = "weather_variables"

    id = Column(Integer, primary_key=True)
    weather_main = Column(VARCHAR(50))
    weather_description = Column(TEXT)
    weather_icon = Column(VARCHAR(5))
    main_temp = Column(NUMERIC(4, 2))
    main_feels_like = Column(NUMERIC(4, 2))
    main_pressure = Column(Integer)
    main_humidity = Column(Integer)
    main_sea_level = Column(Integer)
    main_grnd_level = Column(Integer)
    visibility = Column(Integer)
    wind_speed = Column(NUMERIC(5, 2))
    wind_deg = Column(Integer)
    wind_gust = Column(NUMERIC(5, 2))
    clouds_all = Column(NUMERIC(5, 2))
    rain_1h = Column(NUMERIC(5, 2))
    snow_1h = Column(NUMERIC(5, 2))
    pop = Column(NUMERIC(5, 2))
    current = relationship('Weather_current', backref='weather_variables')
    hourly = relationship('Weather_hourly', backref='weather_variables')


class Weather_current(Base):
    __tablename__ = 'weather_current'

    weather_id = Column(Integer, ForeignKey(Weather.id, ondelete='cascade'), primary_key=True)
    variables_id = Column(Integer, ForeignKey(Weather_variables.id, ondelete='cascade'), primary_key=True)
    refresh_time = Column(TIMESTAMP(timezone=False))


class Weather_hourly(Base):
    __tablename__ = 'weather_hourly'

    weather_id = Column(Integer, ForeignKey(Weather.id, ondelete='cascade'), primary_key=True)
    variables_id = Column(Integer, ForeignKey(Weather_variables.id, ondelete='cascade'), primary_key=True)
    hour = Column(Integer)
    refresh_time = Column(TIMESTAMP(timezone=False))"""
