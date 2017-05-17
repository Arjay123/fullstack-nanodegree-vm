from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base


db_uri = "sqlite:///itemcatalog.db"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()