from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session, aliased
from starlette.responses import StreamingResponse

from app.models import Users, Posts
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from typing import List, Optional

import io

from app.db.database import create_connection
from app.security import auth

from app.schemas.feed_schema import NewPost, GetFeed, GetFeedResponseProfile, GetFeedResponse
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users, Users_attributes, Likes_dislikes, Post_photos
from sqlalchemy import func, text
from app.routers.profile import check_if_picture
import datetime

router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)


@router.get("/", status_code=HTTP_200_OK,
            response_model=list[GetFeedResponse],
            summary="Retrieves the available posts based on distance",
            responses={404: {"description": "String not found"}})
def news_feed(get_feed: GetFeed,
                    user: Users = Depends(auth.get_current_user),
                    db: Session = Depends(create_connection)):
    subquery1 = db.query(
        text("farms.latitude").label("farm_lat"),
        text("farms.longitude").label("farm_lon")
    ).filter(text(f"farms.id = {get_feed.farm_id}")).subquery()

    # Build subquery 2
    posts = aliased(Posts)
    subquery2 = db.query(
        subquery1.c.farm_lat,
        subquery1.c.farm_lon,
        posts.id,
        posts.user_id,
        posts.post_name,
        posts.latitude,
        posts.longitude,
        posts.category,
        posts.text,
        posts.date
    ).select_entity_from(posts).subquery()

    # Build main query
    calc = aliased(subquery2)
    users = aliased(Users)
    query = db.query(
        calc.c.farm_lat,
        calc.c.farm_lon,
        calc.c.id,
        calc.c.user_id,
        users.first_name,
        users.last_name,
        calc.c.post_name,
        calc.c.latitude,
        calc.c.longitude,
        calc.c.category,
        calc.c.text,
        calc.c.date
    ).select_entity_from(calc).join(
        users, calc.c.user_id == users.id
    ).filter(
        func.acos(
            func.cos(func.radians(calc.c.farm_lat)) *
            func.cos(func.radians(calc.c.latitude)) *
            func.cos(func.radians(calc.c.longitude) -
                     func.radians(calc.c.farm_lon)) +
            func.sin(func.radians(calc.c.farm_lat)) *
            func.sin(func.radians(calc.c.latitude))
        ) * 6371 < get_feed.distance_range
    ).order_by(
        calc.c.date
    ).limit(100)

    # Execute the query
    result = query.all()
    if not result:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Feed is empty.",
        )
    return result


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
    return result


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

