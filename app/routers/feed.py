import random
import string

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session, aliased
from starlette.responses import StreamingResponse, Response

from app.models import Users, Posts, Settings
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_405_METHOD_NOT_ALLOWED
from typing import List, Optional

import io

from app.db.database import create_connection
from app.security import auth

from app.schemas.feed_schema import NewPost, GetFeed, GetFeedResponse
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users, Users_attributes, Post_photos, Interactions
from sqlalchemy import func, text, select, desc
from app.routers.profile import check_if_picture
import datetime
from PIL import Image
from firebase_admin import messaging

router = APIRouter(
    prefix="/feed",
    tags=["Feed"],
    responses={401: {"description": "Not authorized to perform this action."}}
)


@router.get("/", status_code=HTTP_200_OK,
            response_model=list[GetFeedResponse],
            summary="Retrieves the available posts based on distance",
            responses={404: {"description": "Feed is empty"}})
def news_feed(distance_range: int,
              latitude: float,
              longitude: float,
              user: Users = Depends(auth.get_current_user),
              db: Session = Depends(create_connection)):

    #subquery_lat = db.query(Farms.latitude.label("farm_lat")).filter(Farms.id == farm_id).subquery()
    #subquery_lon = db.query(Farms.longitude.label("farm_lon")).filter(Farms.id == farm_id).subquery()
    #subquery1 = db.query(subquery_lon, subquery_lat, Posts).subquery()

    query = db.query(Posts.id,
                     Posts.user_id,
                     Users.first_name,
                     Users.last_name,
                     Posts.latitude,
                     Posts.longitude,
                     Posts.category,
                     Posts.text,
                     Posts.date
                     ).join(Users, Users.id == Posts.user_id).filter(
        func.acos(
            func.cos(func.radians(latitude)) *
            func.cos(func.radians(Posts.latitude)) *
            func.cos(func.radians(Posts.longitude) -
                     func.radians(longitude)) +
            func.sin(func.radians(latitude)) *
            func.sin(func.radians(Posts.latitude))
        ) * 6371 < distance_range
    ).order_by(desc(Posts.date)).limit(100)

    """query = db.query(subquery1.c.farm_lat,
                     subquery1.c.farm_lon,
                     subquery1.c.id,
                     subquery1.c.user_id,
                     Users.first_name,
                     Users.last_name,
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
        ) * 6371 < feed.distance_range
    ).order_by(subquery1.c.date).limit(100)"""

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

    try:
        with open("Images/Feed/" + result[0], "rb") as buffer:
            image_bytes = buffer.read()
    except FileNotFoundError:
        db.query(Post_photos).filter(Post_photos.id == post_pic).delete()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post picture was not found."
        )

    # image_type = magic.from_buffer(filter_query[0], mime=True)
    image_type = Image.open(io.BytesIO(image_bytes)).format.lower()
    return Response(content=bytes(image_bytes), media_type=f'image/{image_type}')


@router.get("/profile_feed/{profile_id}", status_code=HTTP_200_OK,
            response_model=list[GetFeedResponse],
            summary="Retrieves the available posts for a user profile",
            responses={404: {"description": "Profile not found"}})
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
        curr_post = GetFeedResponse(**post)
        photo_result = db.query(Post_photos.id).filter(
            Post_photos.post_id == curr_post.id).order_by(
            Post_photos.id).all()
        curr_post.photos_id = [photo_result[i]['id'] for i in range(len(photo_result))]
        post_list.append(curr_post)

    return post_list


@router.post("/new_post", status_code=HTTP_200_OK,
             summary="Creates a new post for the current user")
def new_post(post: NewPost,
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    post = Posts(user_id=user.id,
                 latitude=post.latitude,
                 longitude=post.longitude,
                 category=post.category,
                 text=post.text,
                 date=datetime.datetime.now())

    db.add(post)

    attributes = db.query(Users_attributes).filter(Users_attributes.user_id == user.id)
    values = attributes.first()
    attributes.update({"post_count": values.post_count + 1})
    db.commit()
    db.refresh(post)

    # create msg
    title = "New post"
    body = f"{user.first_name}  {user.last_name} has posted about {post.category}, Check it out!"
    create_and_send_multicast_news(db, user, title, body)

    return {"post_id": post.id}


@router.post("/new_post_photos/{post_id}", status_code=HTTP_200_OK,
             summary="Add new post photos for a post")
def new_post_photos(post_id: int,
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

        letters = string.ascii_letters + string.digits
        path = ''.join(random.choice(letters) for _ in range(50)) + "." + photo.content_type.split("/")[1]

        with open("Images/Feed/" + path, "wb") as buffer:
            buffer.write(bytes)

        photos.append(Post_photos(photo=path, post_id=post_id))

    db.add_all(photos)
    db.commit()
    return


@router.delete("/{post_id}", status_code=HTTP_200_OK,
             summary="Deletes a post for the current user",
             responses={404: {"description": "Profile or post not found"}})
def delete_post(post_id: int,
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    validation = db.query(Posts).filter(Posts.id == post_id, Posts.user_id == user.id).first()
    if not validation:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile or Post was not found",
        )
    if validation.user_id != user.id:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Cannot delete others post",
        )

    db.delete(validation)
    db.commit()
    return


@router.get("/notifications/{profile_id}",  status_code=HTTP_200_OK,
             summary="Try the notification through firebase",
             responses={404: {"description": "Profile not found"},
                        405: {"description": "The user has not allowed notifications or token is missing"}})
def try_notification(profile_id: int,
           db: Session = Depends(create_connection)):

    query = db.query(Settings).filter(Settings.user_id == profile_id).first()
    if not query:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found",
        )
    if query.fcm_token and query.news_notifications:
        message = messaging.Message(
            notification=messaging.Notification(
                title='User defined Notification',
                body='This is a user defined notification to try out how the notifications work',
            ),
            token=query.fcm_token,
        )

        # Send a message to the device corresponding to the provided
        # registration token.
        response = messaging.send(message)
        # Response is a message ID string.
        return {'Firebase response:': response}
    else:
        raise HTTPException(
            status_code=HTTP_405_METHOD_NOT_ALLOWED,
            detail="The user has not allowed notifications or token is missing",
        )


# handle messaging
def create_and_send_multicast_news(db, user, title, body):
    followers = db.query(Interactions, Settings.fcm_token, Settings.news_notifications).filter(Interactions.followed_profile == user.id)\
        .join(Settings, Interactions.follower == Settings.user_id).all()
    tokens = check_tokens(followers)
    send_multicast(tokens, title, body)


def check_tokens(users_settings):
    tokens = []
    for user_settings in users_settings:
        if user_settings.fcm_token and user_settings.news_notifications:
            tokens.append(user_settings.fcm_token)
    return tokens


def send_multicast(registration_tokens, title, body):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=registration_tokens,
    )
    response = messaging.send_multicast(message)
    if response.failure_count > 0:
        responses = response.responses
        failed_tokens = []
        for idx, resp in enumerate(responses):
            if not resp.success:
                # The order of responses corresponds to the order of the registration tokens.
                failed_tokens.append(registration_tokens[idx])
        print('List of tokens that caused failures: {0}'.format(failed_tokens))
