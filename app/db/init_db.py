from app.settings import settings
from sqlalchemy import create_engine

database_url = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}" \
               f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
engine = create_engine(database_url)  # creates database engine from given environment variables
