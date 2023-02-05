from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str


class PostRegister(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

    class Config:
        orm_mode = True


class PostLogin(BaseModel):
    email: str
    password: str
