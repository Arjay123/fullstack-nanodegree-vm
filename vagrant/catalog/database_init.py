from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, Base, User, ItemList

engine = create_engine("sqlite:///itemcatalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# delete existing entries in db
session.query(Item).delete()
session.query(User).delete()
session.query(ItemList).delete()

# add users
user1 = User(name="Arjay Nguyen")
user2 = User(name="Mimi Nguyen")

session.add_all([user1, user2])
session.commit()

# add items
item1 = Item(name="Nintendo Switch",
             category="Video Games",
             description="Nintendo's latest video game console",
             user=user1,
             views=100)

item2 = Item(name="Macbook",
             category="Electronics",
             description="An Apple laptop",
             user=user2,
             views=75)

item3 = Item(name="Zelda: Breath of the Wild",
             category="Video Games",
             description="A great game",
             user=user1,
             views=80)

item4 = Item(name="Nike Tiempo Soccer Boots",
             category="Sports",
             description="Great soccer boots",
             user=user2,
             views=32)

item5 = Item(name="Persona 5 for PS4",
             category="Video Games",
             description="Another great JRPG by Atlus",
             user=user1,
             views=45)

item6 = Item(name="Pencils (set of 4)",
             category="Art Supplies",
             description="A set of pencils for drawing",
             user=user2,
             views=121)

item7 = Item(name="Gamecube Controller",
             category="Video Games",
             description="A controller for smash bros",
             user=user1,
             views=130)

item8 = Item(name="Baseball Cap",
             category="Clothing",
             description="A hat for your head",
             user=user2,
             views=154)

item9 = Item(name="Wacom Tablet",
             category="Electronics",
             description="A tablet for drawing",
             user=user1,
             views=190)



session.add_all([item1, item2, item3, item4, item5, item6, item7, item8,
                 item9])
session.commit()