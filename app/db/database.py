from sqlalchemy.orm import sessionmaker

from app.db import init_db


def create_connection():
    """
        Creates a connection to database and returns a Session variable.
    """
    session = sessionmaker(autocommit=False, bind=init_db.engine)
    db = session()
    try:
        yield db
    finally:
        db.close()


def get_database(session):
    return
