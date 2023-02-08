from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.models import Users
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from typing import List, Optional

import io

from app.db.database import create_connection
from app.security import auth

from app.schemas.profile_schema import Search_profile, Get_Profile, Get_farms, Like_dislike
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users, Users_attributes, Likes_dislikes
from sqlalchemy import func

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


@router.get("/search/{string}", status_code=HTTP_200_OK,
            response_model=list[Search_profile],
            summary="Retrieves the available profiles",
            responses={404: {"description": "String not found"}})
def search_profiles(string: str,
                    user: Users = Depends(auth.get_current_user),
                    db: Session = Depends(create_connection)):
    query = db.query(func.concat(Users.first_name, ' ', Users.last_name).label("name"),
                     Users.id, Users.photo)
    results = query.filter(
        func.lower(func.concat(func.lower(Users.first_name), ' ', func.lower(Users.last_name))).like(f"%{string.lower()}%")).all()

    return [Search_profile(**profile) for profile in results]


@router.get("/{profile_id}}", status_code=HTTP_200_OK,
            response_model=Get_Profile,
            summary="Retrieves the available profile",
            responses={404: {"description": "String not found"}})
def get_profile(profile_id: str,
                    user: Users = Depends(auth.get_current_user),
                    db: Session = Depends(create_connection)):
    profile_query = db.query(Users.id,
                     Users.first_name,
                     Users.last_name,
                     Users.photo,
                     Users_attributes.post_count,
                     Users_attributes.like_count,
                     Users_attributes.dislike_count,
                     ).filter(Users.id == profile_id).join(Users_attributes).first()

    farms_query = db.query(Farms.id,
                           Farms.name,
                           Farms.latitude,
                           Farms.longitude).filter(Farms.user_id == profile_id).all()
    is_like_query = db.query(Likes_dislikes).filter(Likes_dislikes.followed_profile == profile_id, Likes_dislikes.follower == user.id).first()

    profile = Get_Profile(**profile_query)
    profile.farms = [Get_farms(**farm) for farm in farms_query]
    if is_like_query is None:
        profile.is_like = None
    else:
        profile.is_like = is_like_query.is_like



    return profile


@router.delete("/delete", status_code=HTTP_200_OK,
            summary="Deletes the user profile",
            responses={404: {"description": "String not found"}})
def delete_profile(user: Users = Depends(auth.get_current_user),
                   db: Session = Depends(create_connection)):
    query = db.query(Users).filter(Users.id == user.id).first()
    if query:

        #likes and dislikes should be corrected
        followed_profiles = db.query(Likes_dislikes).filter(Likes_dislikes.follower == user.id).all()
        for followed_profile in followed_profiles:
            if followed_profile.is_like:
                profile = db.query(Users_attributes).filter(Users_attributes.user_id == followed_profile.followed_profile)
                profile.update({'like_count': profile.first().like_count - 1})
            elif followed_profile.is_like is False:
                profile = db.query(Users_attributes).filter(
                    Users_attributes.user_id == followed_profile.followed_profile)
                profile.update({'dislike_count': profile.first().dislike_count - 1})
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
    if size > 3 * 1024 * 1024:  # 3MB = 3*1024 KB = 3* 1024 * 1024
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
    query.update({"photo": file_bytes})
    db.commit()
    return StreamingResponse(io.BytesIO(file_bytes), media_type=file.content_type)


@router.put("/delete_pic", status_code=HTTP_200_OK,
            summary="Deletes current profile picture",
            responses={404: {"description": "Profile was not found"}})
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
    query = db.query(Likes_dislikes).filter(Likes_dislikes.follower == user.id, Likes_dislikes.followed_profile == like_dislike.profile_id)
    result = query.first()
    if result:
        #it exists
        if like_dislike.is_like is True or like_dislike.is_like is False:
            query.update({'is_like': like_dislike.is_like})
        else:
            db.delete(result)
        db.commit()
    else:
        #need to create new relation
        relation = Likes_dislikes(follower=user.id, followed_profile=like_dislike.profile_id, is_like=like_dislike.is_like)
        db.add(relation)
        db.commit()
        db.refresh(relation)



