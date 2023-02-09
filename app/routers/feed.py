from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session, aliased
from starlette.responses import StreamingResponse, Response

from app.models import Users, Posts
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from typing import List, Optional

import io

from app.db.database import create_connection
from app.security import auth

from app.schemas.feed_schema import NewPost, GetFeed, GetFeedResponseProfile, GetFeedResponse
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users, Users_attributes, Likes_dislikes, Post_photos
from sqlalchemy import func, text, select
from app.routers.profile import check_if_picture
import datetime
from PIL import Image

router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)


@router.get("/", status_code=HTTP_200_OK,
            response_model=list[GetFeedResponse],
            summary="Retrieves the available posts based on distance",
            responses={404: {"description": "String not found"}})
def news_feed(distance_range: int,
              farm_id: int,
              user: Users = Depends(auth.get_current_user),
              db: Session = Depends(create_connection)):

    subquery_lat = db.query(Farms.latitude.label("farm_lat")).filter(Farms.id == farm_id).subquery()
    subquery_lon = db.query(Farms.longitude.label("farm_lon")).filter(Farms.id == farm_id).subquery()
    subquery1 = db.query(subquery_lon, subquery_lat, Posts).subquery()
    query = db.query(subquery1.c.farm_lat,
                     subquery1.c.farm_lon,
                     subquery1.c.id,
                     subquery1.c.user_id,
                     Users.first_name,
                     Users.last_name,
                     subquery1.c.post_name,
                     subquery1.c.latitude,
                     subquery1.c.longitude,
                     subquery1.c.category,
                     subquery1.c.text,
                     subquery1.c.date
                     ).join(Users, Users.id == subquery1.c.user_id).filter(
        func.acos(
            func.cos(func.radians(subquery1.c.farm_lat)) *
            func.cos(func.radians(subquery1.c.latitude)) *
            func.cos(func.radians(subquery1.c.longitude) -
                     func.radians(subquery1.c.farm_lon)) +
            func.sin(func.radians(subquery1.c.farm_lat)) *
            func.sin(func.radians(subquery1.c.latitude))
        ) * 6371 < distance_range
    ).order_by(subquery1.c.date).limit(100)

    result = query.all()
    if not result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Feed is empty.",
        )
    post_list = []
    for post in result:
        curr_post = GetFeedResponse(**post)
        photo_result = db.query(Post_photos.id).filter(
            Post_photos.post_id == curr_post.id).order_by(
            Post_photos.id).all()
        curr_post.photos_id = [photo_result[i]['id'] for i in range(len(photo_result))]
        post_list.append(curr_post)

    return post_list



@router.get("/post_pic/{post_pic}", status_code=HTTP_200_OK,
            summary="Retrieves a post picture based on the id.",
            responses={404: {"description": "Post picture was not found."}})
def get_post_pic(post_pic: int,
                 db: Session = Depends(create_connection),
                 user: Users = Depends(auth.get_current_user)):
    """
        Input parameters:
        - **profile_id**: id of the user

        Response values:
        - binary form of profile picture
    """

    result = db.query(Post_photos.photo).filter(Post_photos.id == post_pic).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post picture was not found."
        )

    if result[0] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post picture was not found."
        )
    # image_type = magic.from_buffer(filter_query[0], mime=True)
    image_type = Image.open(io.BytesIO(result[0])).format.lower()
    return Response(content=bytes(result[0]), media_type=f'image/{image_type}')


@router.get("/{profile_id}", status_code=HTTP_200_OK,
            response_model=list[GetFeedResponseProfile],
            summary="Retrieves the available posts for a user profile",
            responses={404: {"description": "String not found"}})
def profile_news_feed(profile_id: int,
                      user: Users = Depends(auth.get_current_user),
                      db: Session = Depends(create_connection)):
    result = db.query(Users).filter(Users.id == profile_id).first()
    if not result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found",
        )
    calc = aliased(Posts)
    result = db.query(calc.id,
                      calc.user_id,
                      Users.first_name,
                      Users.last_name,
                      calc.post_name,
                      calc.latitude,
                      calc.longitude,
                      calc.category,
                      calc.text,
                      calc.date) \
        .join(Users, calc.user_id == Users.id) \
        .filter(calc.user_id == profile_id) \
        .order_by(calc.date) \
        .limit(100) \
        .all()

    post_list = []
    for post in result:
        curr_post = GetFeedResponseProfile(**post)
        photo_result = db.query(Post_photos.id).filter(
            Post_photos.post_id == curr_post.id).order_by(
            Post_photos.id).all()
        curr_post.photos_id = [photo_result[i]['id'] for i in range(len(photo_result))]
        post_list.append(curr_post)

    return post_list


@router.post("/new_post", status_code=HTTP_200_OK,
             summary="Creates a new post for the current user",
             responses={404: {"description": "String not found"}})
def new_post(post: NewPost,
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    post = Posts(user_id=user.id,
                 post_name=post.post_name,
                 latitude=post.latitude,
                 longitude=post.longitude,
                 category=post.category,
                 text=post.text,
                 date=datetime.datetime.now())

    db.add(post)
    db.commit()
    db.refresh(post)
    return {"post_id": post.id}


@router.post("/new_post_photos", status_code=HTTP_200_OK,
             summary="Creates a new post for the current user",
             responses={404: {"description": "String not found"}})
def new_post(post_id: int,
             files: list[UploadFile],
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    validation = db.query(Posts).filter(Posts.id == post_id, Posts.user_id == user.id).first()
    if not validation:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile or Post was not found",
        )
    photos = []
    for photo in files:
        bytes = check_if_picture(photo)
        photos.append(Post_photos(photo=bytes, post_id=post_id))

    db.add_all(photos)
    db.commit()
    return
