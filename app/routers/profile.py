import os
import random
import string

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse, Response

from app.models import Users
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from typing import List, Optional

import io

from app.db.database import create_connection
from app.security import auth

from app.schemas.profile_schema import Search_profile, Get_Profile, Like_dislike
from app.schemas.farms_schema import GetFarms
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users, Users_attributes, Interactions
from sqlalchemy import func
from PIL import Image

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    responses={401: {"description": "Not authorized to perform this action."}}
)


@router.get("/search/{string}", status_code=HTTP_200_OK,
            response_model=list[Search_profile],
            summary="Retrieves the available profiles")
def search_profiles(string: str,
                    user: Users = Depends(auth.get_current_user),
                    db: Session = Depends(create_connection)):
    query = db.query(Users.first_name,
                     Users.last_name,
                     Users.id)
    results = query.filter(
        func.lower(func.concat(func.lower(Users.first_name), ' ', func.lower(Users.last_name))).like(
            f"%{string.lower()}%")).all()

    return [Search_profile(**profile) for profile in results]


@router.get("/{profile_id}", status_code=HTTP_200_OK,
            response_model=Get_Profile,
            summary="Retrieves the available profile",
            responses={404: {"description": "Profile not found"}})
def get_profile(profile_id: str,
                user: Users = Depends(auth.get_current_user),
                db: Session = Depends(create_connection)):
    profile_query = db.query(Users.id,
                             Users.first_name,
                             Users.last_name,
                             Users_attributes.post_count,
                             Users_attributes.like_count,
                             Users.photo.label("picture_path"),
                             ).filter(Users.id == profile_id).join(Users_attributes).first()

    if profile_query is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile was not found."
        )

    farms_query = db.query(Farms.id,
                           Farms.name,
                           Farms.latitude,
                           Farms.longitude).filter(Farms.user_id == profile_id).all()
    interaction = db.query(Interactions).filter(Interactions.followed_profile == profile_id,
                                                Interactions.follower == user.id).first()

    profile = Get_Profile(**profile_query)
    profile.farms = [GetFarms(**farm) for farm in farms_query]
    if interaction is None:
        profile.interaction = False
    else:
        profile.interaction = True
    # TODO delete picture path, profile pic is based on ID
    return profile


@router.get("/profile_pic/{profile_id}", status_code=HTTP_200_OK,
            summary="Retrieves a profile picture based on the id.",
            responses={404: {"description": "Post picture not found."}})
def get_profile_pic(profile_id: int,
                    db: Session = Depends(create_connection),
                    user: Users = Depends(auth.get_current_user)):
    """
        Input parameters:
        - **profile_id**: id of the user

        Response values:
        - binary form of profile picture
    """

    result = db.query(Users.photo).filter(Users.id == profile_id).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile picture was not found."
        )

    if result[0] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile picture was not found."
        )
    # image_type = magic.from_buffer(filter_query[0], mime=True)
    try:
        with open("Images/Profile/" + result[0], "rb") as buffer:
            image_bytes = buffer.read()
    except FileNotFoundError:
        db.query(Users).filter(Users.id == profile_id).update({"photo": None})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile picture was not found."
        )

    image_type = Image.open(io.BytesIO(image_bytes)).format.lower()
    return Response(content=bytes(image_bytes), media_type=f'image/{image_type}')

    # image_type = Image.open(io.BytesIO(result[0])).format.lower()
    # return Response(content=bytes(result[0]), media_type=f'image/{image_type}')


@router.delete("/delete", status_code=HTTP_200_OK,
               summary="Deletes the user profile",
               responses={404: {"description": "Profile not found"}})
def delete_profile(user: Users = Depends(auth.get_current_user),
                   db: Session = Depends(create_connection)):
    query = db.query(Users).filter(Users.id == user.id).first()
    if query:

        # likes and dislikes should be corrected
        followed_profiles = db.query(Interactions).filter(Interactions.follower == user.id).all()
        for followed_profile in followed_profiles:
            profile = db.query(Users_attributes).filter(
                Users_attributes.user_id == followed_profile.followed_profile)
            profile.update({'like_count': profile.first().like_count - 1})
            db.commit()

        db.delete(query)
        db.commit()
        return True
    else:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found.",
        )


def check_if_picture(file: UploadFile = File(...)):
    # check_filetype
    supported_files = ["image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in supported_files:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported file type.",
        )
    file_bytes = file.file.read()
    size = len(file_bytes)
    if size > 10 * 1024 * 1024:  # 3MB = 3*1024 KB = 3* 1024 * 1024
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected file is too large.",
        )
    return file_bytes


@router.put("/pic", status_code=HTTP_200_OK,
            summary="Puts new profile picture",
            responses={404: {"description": "Profile not found"}})
def modify_profile_pic(file: UploadFile = File(...),
                       user: Users = Depends(auth.get_current_user),
                       db: Session = Depends(create_connection)):
    query = db.query(Users).filter(Users.id == user.id)
    query_row = query.first()

    if not query_row:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found.",
        )
    file_bytes = check_if_picture(file)

    letters = string.ascii_letters + string.digits
    path = ''.join(random.choice(letters) for _ in range(50)) + "." + file.content_type.split("/")[1]

    # TODO check if path exists

    if query_row.photo:
        os.remove("Images/Profile/" + query_row.photo)

    with open("Images/Profile/" + path, "wb") as buffer:
        buffer.write(file_bytes)

    query.update({"photo": path})
    # query.update({"photo": file_bytes})
    db.commit()
    return StreamingResponse(io.BytesIO(file_bytes), media_type=file.content_type)


@router.put("/delete_pic", status_code=HTTP_200_OK,
            summary="Deletes current profile picture",
            responses={404: {"description": "Profile not found"}})
def delete_profile_pic(db: Session = Depends(create_connection),
                       user: Users = Depends(auth.get_current_user)):
    """
        Response values:

        - **photo**: empty photo value
    """

    query = db.query(Users).filter(Users.id == user.id)
    query_row = query.first()

    if not query_row:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found.",
        )

    if query_row.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to perform this action."
        )

    if os.path.exists("Images/Profile/" + query_row.photo):
        os.remove("Images/Profile/" + query_row.photo)
    else:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile picture was not found.",
        )

    query.update({"photo": None})
    db.commit()

    return {"photo": None}


@router.put("/like_dislike", status_code=HTTP_200_OK,
            summary="Likes or dislikes another profile",
            responses={404: {"description": "Profile not found"}})
def like_dislike(like_dislike: Like_dislike,
                 user: Users = Depends(auth.get_current_user),
                 db: Session = Depends(create_connection)):
    query = db.query(Users).filter(Users.id == like_dislike.profile_id).first()
    if query is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Profile was not found.",
        )
    query = db.query(Interactions).filter(Interactions.follower == user.id,
                                          Interactions.followed_profile == like_dislike.profile_id)
    result = query.first()
    attributes = db.query(Users_attributes).filter(Users_attributes.user_id == like_dislike.profile_id)
    attr_value = attributes.first()
    if result and like_dislike.interaction is False:
        # it exists
        attributes.update({'like_count': attr_value.like_count - 1})

        db.delete(result)
        db.commit()
    elif not result and like_dislike.interaction is True:
        # need to create new relation
        relation = Interactions(follower=user.id, followed_profile=like_dislike.profile_id)
        attributes.update({'like_count': attr_value.like_count + 1})
        db.add(relation)
        db.commit()
        db.refresh(relation)
