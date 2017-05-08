import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from database_setup import Item, User, ItemList, Base, create_db

db_uri = "sqlite:///itemcatalog_test.db"
create_db(db_uri)
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
        

class TestCatalogDB(unittest.TestCase):

    def setUp(self):
        db_init()
        self.user = session.query(User).filter_by(id=1).one()


    def tearDown(self):
        session.rollback()


    def test_ItemCreateShouldPass(self):
        item_id = 10
        name = "Name"
        category="Category"
        description="Description"
        views=0

        item = Item(name=name,
                    category=category,
                    description=description,
                    user=self.user)

        session.add(item)
        session.commit()

        self.assertEqual(item_id, item.id)
        self.assertEqual(name, item.name)
        self.assertEqual(category, item.category)
        self.assertEqual(views, item.views)
        self.assertEqual(self.user, item.user)


    def test_ItemCreateShouldFail_NoName(self):
        item_id = 10
        name = None
        category="Category"
        description="Description"
        views=0

        item = Item(name=name,
                    category=category,
                    description=description,
                    user=self.user)

        session.add(item)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemCreateShouldFail_NoCategory(self):
        item_id = 10
        name = "Name"
        category=None
        description="Description"
        views=0

        item = Item(name=name,
                    category=category,
                    description=description,
                    user=self.user)

        session.add(item)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemCreateShouldFail_NoDesc(self):
        item_id = 10
        name = "Name"
        category="Category"
        description=None
        views=0

        item = Item(name=name,
                    category=category,
                    description=description,
                    user=self.user)

        session.add(item)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemCreateShouldFail_NoUser(self):
        item_id = 10
        name = "Name"
        category="Category"
        description="Description"

        item = Item(name=name,
            category=category,
            description=description,
            user=None)

        session.add(item)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemReadShouldPass_ID(self):
        item_id=1

        found = session.query(Item).filter_by(id=item_id).one()

        self.assertEqual(item_id, found.id)


    def test_ItemReadShouldPass_Name(self):
        item_name="Nintendo Switch"

        found = session.query(Item).filter_by(name=item_name).one()

        self.assertEqual(item_name, found.name)


    def test_ItemReadShouldFail_NoID(self):
        item_id = 123
        
        self.assertRaises(NoResultFound, 
            session.query(Item).filter_by(id=item_id).one)      


    def test_ItemReadShouldFail_NoName(self):
        item_name = "NoName"
        
        self.assertRaises(NoResultFound, 
            session.query(Item).filter_by(name=item_name).one)  


    def test_ItemUpdateShouldPass(self):
        item_id = 1
        new_name = "Newname"
        new_category = "NewCategory"
        new_desc = "NewDesc"

        item = session.query(Item).filter_by(id=item_id).one()

        item.name = new_name
        item.category = new_category
        item.description = new_desc

        session.add(item)
        session.commit()

        item = session.query(Item).filter_by(id=item_id).one()

        self.assertEqual(item_id, item.id)
        self.assertEqual(new_name, item.name)
        self.assertEqual(new_category, item.category)
        self.assertEqual(new_desc, item.description)


    def test_ItemDeleteShouldPass(self):
        item_id = 1

        item = session.query(Item).filter_by(id=item_id).one()

        session.delete(item)
        session.commit()

        self.assertRaises(NoResultFound,
            session.query(Item).filter_by(id=item_id).one)


    def test_UserCreateShouldPass(self):

        user_name="Kyle Kyle"
        user_email="kyle@email.com"
        user_id = 3
        user = User(name=user_name, email=user_email)
        

        session.add(user)
        session.commit()

        self.assertEqual(user_id, user.id)
        self.assertEqual(user_name, user.name)
        self.assertEqual(user_email, user.email)


    def test_UserCreateShouldPass_NullEmails(self):

        user1 = User(name="User1")
        user2 =User(name="User2")

        session.add(user1)
        session.add(user2)
        session.commit()

        self.assertEqual(3, user1.id)
        self.assertEqual(4, user2.id)


    def test_UserCreateShouldFail_NoName(self):
        user = User(name=None)

        session.add(user)
        self.assertRaises(IntegrityError, session.commit)


    def test_UserCreateShouldFail_SameEmail(self):
        user = User(name="Username", email="arjay@email.com")

        session.add(user)
        self.assertRaises(IntegrityError, session.commit)


    def test_UserReadShouldPass_ID(self):
        user_id = 1

        user = session.query(User).filter_by(id=user_id).one()
        self.assertEqual(user_id, user.id)


    def test_UserReadShouldPass_Email(self):
        user_email = "arjay@email.com"

        user = session.query(User).filter_by(email=user_email).one()
        self.assertEqual(user_email, user.email)


    def test_UserReadShouldFail_NoID(self):
        user_id = 3
        
        self.assertRaises(NoResultFound,
            session.query(User).filter_by(id=user_id).one)


    def test_UserReadShouldFail_NoEmail(self):
        user_email = "no@email.com"

        self.assertRaises(NoResultFound,
            session.query(User).filter_by(email=user_email).one)


    def test_UserUpdateShouldPass(self):
        user_id = 1
        new_name = "NewName"
        new_email = "NewEmail@email.com"

        user = session.query(User).filter_by(id=user_id).one()

        user.name = new_name
        user.email = new_email

        session.add(user)
        session.commit()

        user = session.query(User).filter_by(id=user_id).one()

        self.assertEqual(user_id, user.id)
        self.assertEqual(new_name, user.name)
        self.assertEqual(new_email, user.email)


    def test_UserDeleteShouldPass(self):
        user_id = 1

        user = session.query(User).filter_by(id=user_id).one()
        
        session.delete(user)
        session.commit()

        self.assertRaises(NoResultFound,
            session.query(User).filter_by(id=user_id).one)


    def test_ItemListCreateShouldPass(self):
        item_list = ItemList(name="List", user=self.user)

        session.add(item_list)
        session.commit()

        self.assertEqual(3, item_list.id)
        self.assertEqual("List", item_list.name)


    def test_ItemListCreateShouldFail_NoName(self):
        item_list = ItemList(name=None, user=self.user)

        session.add(item_list)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemListCreateShouldFail_NoUser(self):
        item_list = ItemList(name="Name", user=None)

        session.add(item_list)
        self.assertRaises(IntegrityError, session.commit)


    def test_ItemListReadShouldPass(self):
        item_list = session.query(ItemList).filter_by(id=1).one()

        self.assertEqual(1, item_list.id)


    def test_ItemListReadShouldFail_ID(self):
        self.assertRaises(NoResultFound,
            session.query(ItemList).filter_by(id=123).one)


    def test_ItemListUpdateShouldPass(self):
        item_list = session.query(ItemList).filter_by(id=1).one()
        orig_length = len(item_list.items)

        new_item = session.query(Item).filter_by(id=9).one()
        item_list.items.append(new_item)

        session.add(item_list)
        session.commit()

        item_list = session.query(ItemList).filter_by(id=1).one()
        self.assertEqual(orig_length+1, len(item_list.items))


    def test_ItemListDeleteShouldPass(self):
        item_list = session.query(ItemList).filter_by(id=1).one()

        session.delete(item_list)
        session.commit()

        self.assertRaises(NoResultFound, 
            session.query(ItemList).filter_by(id=1).one)

        



def db_init():
    # delete existing entries in db
    session.rollback()
    session.query(Item).delete()
    session.query(User).delete()
    session.query(ItemList).delete()
    session.commit()

    # add users
    user1 = User(name="Arjay Nguyen", email="arjay@email.com")
    user2 = User(name="Mimi Nguyen", email="mimi@email.com")

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

    item_list = ItemList(name="List1", user=user1)

    item_list.items.append(item1)
    item_list.items.append(item2)
    item_list.items.append(item3)

    item_list2 = ItemList(name="List2", user=user2)

    item_list2.items.append(item3)
    item_list2.items.append(item4)
    item_list2.items.append(item5)

    session.add_all([item_list, item_list2])
    session.commit()



if __name__ == '__main__':
    unittest.main()