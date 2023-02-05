from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models import Users
from starlette.status import HTTP_200_OK
from typing import List, Optional

from app.db.database import create_connection
from app.security import auth

from app.schemas.profile_schema import Search_profile, Get_Profile, Get_farms
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
        func.lower(func.concat(func.lower(Users.first_name), ' ', func.lower(Users.last_name))).like(f"%{string}%")).all()

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
