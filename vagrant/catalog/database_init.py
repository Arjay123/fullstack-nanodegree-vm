from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, Base

engine = create_engine("sqlite:///itemcatalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

item = Item(name="Nintendo Switch",
            category="Video Games",
            description="Nintendo's latest video game console")

session.add(item)
session.commit()