from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

from database_setup import Base

"""
Create db session in one place so multiple python scripts can access
the same db session
"""
db_uri = "postgresql+psycopg2://username:password@localhost:5432/item-catalog"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
