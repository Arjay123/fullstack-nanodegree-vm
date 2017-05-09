from flask import Flask, render_template, url_for, request
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from database_setup import Item, User, ItemList, Base, create_db

db_uri = "sqlite:///itemcatalog.db"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
        


app = Flask(__name__)


@app.route("/")
def homepage():
    items = session.query(Item).order_by(desc(Item.views)).limit(4)
    return render_template("homepage.html", items=items)


@app.route("/catalog")
def catalogPage():
    categories = session.query(Item.category).group_by(Item.category).all()
    categories = [cat[0] for cat in categories]

    order = request.args.get('order')
    category = request.args.get('category')

    if not order:
        order = "name"

    order_param = Item.name
    if "views" in order:
        order_param = Item.views

    if category:
        items = session.query(Item).filter_by(category=category)
        categories.remove(category)
    else:
        items = session.query(Item).filter(Item.views>100)

    if "desc" in order:
        items = items.order_by(desc(order_param))
    else:
        items = items.order_by(order_param)

    return render_template("catalog.html",
                            category=category,
                            categories=categories,
                            items=items)


@app.route("/catalog/item/<int:item_id>")
def itemPage(item_id):
    return render_template("item.html")


@app.route("/login")
def loginPage():
    return render_template("login.html")

@app.route("/logout")
def logoutPage():
    return "This is the logout page"


@app.route("/create")
def createItemPage():
    return render_template("create.html")


@app.route("/catalog/<int:item_id>/edit")
def editItemPage(item_id):
    return render_template("edit.html")


@app.route("/catalog/<int:item_id>/delete")
def deleteItemPage(item_id):
    return "This is the delete page for item %s" % item_id

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)