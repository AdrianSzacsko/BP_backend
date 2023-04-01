from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse, Response

from app.models import Users, Settings
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from app.db.database import create_connection
from app.security import auth

from app.schemas.settings_schema import Notifications
from sqlalchemy import func

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)


@router.put("/notifications/", status_code=HTTP_200_OK,
            summary="Set the notifications for the currently logged in user",
            responses={404: {"description": "User not found"}})
def set_notifications(notifications: Notifications,
                      user: Users = Depends(auth.get_current_user),
                      db: Session = Depends(create_connection)):
    query = db.query(Settings).filter(Settings.user_id == user.id)

    query.update(notifications.dict())
    db.commit()

    return None


@router.get("/notifications/", status_code=HTTP_200_OK,
            response_model=Notifications,
            summary="Set the notifications for the currently logged in user",
            responses={404: {"description": "User not found"}})
def set_notifications(user: Users = Depends(auth.get_current_user),
                      db: Session = Depends(create_connection)):
    query = db.query(Settings).filter(Settings.user_id == user.id).first()
    return query
