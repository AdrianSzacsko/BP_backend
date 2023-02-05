from fastapi import HTTPException
from starlette import status


def check_coors(long: float, lat: float):
    if not (180 >= long >= -180):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Longitude out of bounds."
        )
    if not (90 >= lat >= -90):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Latitude out of bounds."
        )
    return
