import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Item, User, ItemList, Base, create_db

db_uri = "sqlite:///itemcatalog_test.db"
create_db(db_uri)
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
        

class TestCatalogDB(unittest.TestCase):

    def test_one(self):
        self.assertEqual(True, True)


    def test_two(self):
        self.assertEqual(True, True)
        for item in session.query(Item).all():
            print item.name, item.id


    def setUp(self):
        db_init()




        
def db_init():
    session.query(Item).delete()
    session.query(User).delete()
    session.query(ItemList).delete()

    item = Item(name="Nintendo Switch",
            category="Video Games",
            description="Nintendo's latest video game console")

    session.add(item)
    session.commit()



if __name__ == '__main__':
    unittest.main()