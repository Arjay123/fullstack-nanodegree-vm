from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table


Base = declarative_base()


class User(Base):
    """
    Represents a user object

    id - ID of user in db
    name - Name of user
    email - Email of user, must be unique but can be empty
    image - Link to image of user from third-party auth website (i.e. google)
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=True, unique=True)
    image = Column(String(250))


"""
Table that holds which items are held in item list
"""
itemlist_table = Table('association', Base.metadata,
                       Column('id', Integer, primary_key=True),
                       Column("itemlist_id", Integer,
                              ForeignKey("itemlist.id")),
                       Column("item_id", Integer, ForeignKey("item.id"))
                       )


class Item(Base):
    """
    Represents an item in db

    id - ID of item in db
    name - Name of item
    category - Category of item
    description - Description of item
    views - number of views item has
    user_id - id of user that created the item
    user - user entity that created the item
    """
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    category = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    views = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship(User)


class ItemList(Base):
    """
    Represents an ItemList in db.
    ItemList is a list of Items created by a user

    id - ID of itemlist in db
    name - name of itemlist
    user_id - id of user who created itemlist
    user - user entity who created itemlist
    items - items in list
    """
    __tablename__ = "itemlist"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship(User)
    items = relationship("Item",
                         secondary=itemlist_table,
                         passive_deletes=True)


def create_db(uri="sqlite:///itemcatalog.db"):
    """
    Creates the database at the provided uri
    """
    engine = create_engine(uri)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
