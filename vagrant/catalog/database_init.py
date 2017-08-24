from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base
from database_setup import create_db
from database_setup import Item
from database_setup import ItemList
from database_setup import User


create_db()
engine = create_engine("postgresql+psycopg2://username:password@localhost:5432/item-catalog")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

session.rollback()
session.execute("DELETE FROM association")
session.query(ItemList).delete()
session.query(Item).delete()
session.query(User).delete()
session.execute("ALTER SEQUENCE item_id_seq RESTART WITH 1")
session.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1")
session.execute("ALTER SEQUENCE itemlist_id_seq RESTART WITH 1")
session.commit()

# add users
user1 = User(name="Arjay Nguyen", email="arjay@email.com")
user2 = User(name="Mimi Nguyen", email="mimi@email.com")

session.add_all([user1, user2])
session.commit()

# add items
item1 = Item(name="Nintendo Switch",
             category="Video Games",
             description="Introducing Nintendo Switch, the new home video "
             "game system from Nintendo. In addition to providing single and"
             " multiplayer thrills at home, the Nintendo Switch system can"
             " be taken on the go so players can enjoy a full home console"
             " experience anytime, anywhere. The mobility of a handheld is"
             " now added to the power of a home gaming system, with"
             " unprecedented new play styles brought to life by the two new"
             " Joy-Con controllers.",
             user=user1,
             views=100,
             image="nintendoswitch.jpg")

item2 = Item(name="Macbook",
             category="Electronics",
             description="Our goal with MacBook was to do the impossible:"
             " engineer a full-size experience into the lightest and most"
             " compact Mac notebook ever. That meant reimagining every"
             " element to make it not only lighter and thinner but also"
             " better. The result is more than just a new notebook. It's the"
             " future of the notebook. And now, with sixth-generation Intel"
             " processors, improved graphics performance, faster flash"
             " storage, and up to 10 hours of battery life, MacBook is"
             " even more capable.",
             user=user2,
             views=75,
             image="macbook.jpg")

item3 = Item(name="Zelda: Breath of the Wild",
             category="Video Games",
             description="Explore the wilds of Hyrule any way you "
             "like-anytime, anywhere! - Climb up towers and mountain peaks"
             " in search of new destinations, then set your own path to get"
             " there and plunge into the wilderness. Along the way, you'll"
             " battle towering enemies, hunt wild beasts and gather"
             " ingredients for the food and elixirs you'll make to sustain"
             " you on your journey. With Nintendo Switch, you can literally"
             " take your journey anywhere.",
             user=user1,
             views=80,
             image="botw.jpg")

item4 = Item(name="Nike Men's Tiempo Legend VI FG Soccer Cleat (White, "
             "Electric Green)",
             category="Sports",
             description="Equipped with hidden innovations that bring your"
             " foot closer to the ball than ever, the Nike Tiempo Legend VI"
             " Firm-Ground Soccer Cleat is made with non-slip technologies"
             " and premium leather to truly dominate on the field.",
             user=user2,
             views=32,
             image="tiempo.jpg")

item5 = Item(name="Persona 5",
             category="Video Games",
             description="Persona 5 is a game about the internal and external"
             " conflicts of a group of troubled high school students - the"
             " protagonist and a collection of compatriots he meets in the"
             " game's story - who live dual lives as Phantom Thieves. They"
             " have the typically ordinary day-to-day of a Tokyo high"
             " schooler - attending class, after school activities and"
             " part-time jobs. But they also undertake fantastical adventures"
             " by using otherworldly powers to enter the hearts of people.",
             user=user1,
             views=45,
             image="persona5.jpg")

item6 = Item(name="Pencils (24 ct.)",
             category="Art Supplies",
             description="#1 Selling Mechanical Pencil",
             user=user2,
             views=121,
             image="pencils.jpg")

item7 = Item(name="Gamecube Controller",
             category="Video Games",
             description="Officially Licensed Controller by Nintendo - This"
             " is a first party controller!",
             user=user1,
             views=130,
             image="gcc.jpg")

item8 = Item(name="Baseball Cap",
             category="Clothing",
             description="100% Cotton Made. Lightweight / Durable / Smooth",
             user=user2,
             views=154,
             image="baseballcap.jpg")

item9 = Item(name="Wacom Tablet",
             category="Electronics",
             description="Perfect for beginning digital artists - draw,"
             " paint, and edit with an easy to use pen tablet.",
             user=user1,
             views=190,
             image="wacom.jpg")


session.add_all([item1, item2, item3, item4, item5, item6, item7, item8,
                 item9])
session.commit()

item_list1 = ItemList(name="Games", user=user1)

item_list1.items.append(item1)
item_list1.items.append(item3)
item_list1.items.append(item5)
item_list1.items.append(item7)

item_list2 = ItemList(name="Outdoors", user=user1, public=True)

item_list2.items.append(item4)
item_list2.items.append(item8)

item_list3 = ItemList(name="Art Supplies", user=user2, public=True)

item_list3.items.append(item6)
item_list3.items.append(item9)

session.add_all([item_list1, item_list2, item_list3])
session.commit()
print "Database sample data added"
