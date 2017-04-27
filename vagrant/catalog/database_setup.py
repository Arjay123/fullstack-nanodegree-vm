from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from sqlalchemy.schema import Table


Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=True, unique=True)
    image = Column(String(250))




itemlist_table = Table('association', Base.metadata,
    Column("itemlist_id", Integer, ForeignKey("itemlist.id")),
    Column("item_id", Integer, ForeignKey("item.id"))
)


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    category = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    views = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship(User)



class ItemList(Base):
    __tablename__ = "itemlist"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)
    items = relationship("Item", secondary=itemlist_table)


    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)

    def add_item(self, item):
        self.items.add(item)



def create_db(uri="sqlite:///itemcatalog.db"):
    engine = create_engine(uri)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)