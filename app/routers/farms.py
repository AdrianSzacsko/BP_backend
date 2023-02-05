from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models import Users
from starlette.status import HTTP_200_OK
from typing import List, Optional

from app.db.database import create_connection
from app.security import auth

from app.schemas.farms_schema import PostFarm, DeleteFarm
from app.miscFunctions.coordinates import check_coors
from app.models import Farms, Users

import requests
from app.settings import settings

router = APIRouter(
    prefix="/farms",
    tags=["Farms"]
)


@router.post("/", status_code=HTTP_200_OK,
             summary="Creates new farm",
             responses={404: {"description": "Location not found"}})
def add_farm(post_farm: PostFarm,
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    check_coors(post_farm.long, post_farm.lat)
    farm = db.query(Farms).filter(Farms.user_id == user.id, Farms.name == post_farm.name).first()
    if farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm already exists."
        )
    farm = Farms(user_id=user.id, name=post_farm.name, latitude=post_farm.lat, longitude=post_farm.long)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return


@router.delete("/", status_code=HTTP_200_OK,
             summary="Creates new farm",
             responses={404: {"description": "Location not found"}})
def delete_farm(
             del_farm: DeleteFarm,
             user: Users = Depends(auth.get_current_user),
             db: Session = Depends(create_connection)):
    farm = db.query(Farms).filter(Farms.user_id == user.id, Farms.name == del_farm.name).first()
    if farm:
        db.delete(farm)
        db.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm not found."
        )
    return
