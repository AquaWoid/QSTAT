from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import dotenv

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass