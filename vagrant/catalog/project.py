import random

from flask import Flask, render_template, url_for, request, redirect
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

from database_setup import Item, User, ItemList, Base, create_db

db_uri = "sqlite:///itemcatalog.db"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


def get_categories():
    """
    Retrieves all available item catagories

    Returns:
        List of all categories as strings
    """
    categories = session.query(Item.category).group_by(Item.category).all()
    return [cat[0] for cat in categories]


@app.route("/")
def homepage():
    """
    Loads homepage
    """
    items = session.query(Item).order_by(desc(Item.views)).limit(4)
    return render_template("homepage.html", items=items)


@app.route("/catalog")
def catalogPage():
    """
    Loads catalog page
    """

    order = request.args.get('order')
    category = request.args.get('category')

    if not order:
        order = "name"

    order_param = Item.name
    if "views" in order:
        order_param = Item.views

    categories = get_categories()
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


@app.route("/catalog/<int:item_id>")
def itemPage(item_id):
    """
        Loads page for a specific item

        Args:
            item_id - id of item to load
    """

    #TODO - remove item from sampler set
    item = session.query(Item).filter_by(id=item_id).one()
    rand_items = session.query(Item).filter_by(category=item.category).all()
    sample_size = 4 if len(rand_items) >= 4 else len(rand_items)
    rand_items = random.sample(rand_items, sample_size)
    return render_template("item.html", sel_item=item, items=rand_items)


@app.route("/login")
def loginPage():
    return render_template("login.html")


@app.route("/logout")
def logoutPage():
    return "This is the logout page"


@app.route("/create", methods=['GET', 'POST'])
def createItemPage():
    """ 
        Loads page for creating a new item. Requires user
        to be logged in
    """

    # TODO - Check user login, if none, defer to login page

    errors = {}
    params = {}

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']

        #TODO - set user to logged in user
        user = session.query(User).filter_by(id=1).one()

        params = {"name": name,
                  "category": category,
                  "description": description}

        form_valid = True
        if not name:
            form_valid = False
            errors['name'] = "Item name is required"

        if not category:
            form_valid = False
            errors['category'] = "Item category is required"

        if not description:
            form_valid = False
            errors['description'] = "Item description is required"

        #TODO - if error send back to form w/ entries, and errors
        if form_valid:
            new_item = Item(name=name,
                            category=category,
                            description=description,
                            user=user,
                            views=0)
            session.add(new_item)
            session.commit()
            return redirect(url_for('itemPage', item_id=new_item.id))

    return render_template("create.html",
                            categories=get_categories(),
                            errors=errors,
                            params=params)


@app.route("/catalog/<int:item_id>/edit")
def editItemPage(item_id):
    return render_template("edit.html")


@app.route("/catalog/<int:item_id>/delete")
def deleteItem(item_id):
    return "This is the page to delete item:", item_id




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)