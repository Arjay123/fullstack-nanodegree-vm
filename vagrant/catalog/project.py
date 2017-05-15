import random
import hashlib
import os

from flask import Flask, render_template, url_for, request, redirect, flash
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from database_setup import Item, User, ItemList, Base, create_db

from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

from flask import make_response
import requests


db_uri = "sqlite:///itemcatalog.db"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)
app.secret_key = "sosecret"


CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

def get_categories():
    """
    Retrieves all available item catagories

    Returns:
        List of all categories as strings
    """
    categories = session.query(Item.category).group_by(Item.category).all()
    return [cat[0] for cat in categories]

def get_item_by_id(item_id):
    """
    Retrieves item by its id

    Return:
        Item if found, else None
    """
    q = session.query(Item).filter_by(id=item_id)
    if session.query(q.exists()).scalar():
        return q.one()



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
    #TODO - update item view count
    #TODO - Create this item does not exist page
    item = get_item_by_id(item_id)
    if not item:
        return "This item does not exist: %s" % str(item_id)

    rand_items = session.query(Item).filter_by(category=item.category).all()
    sample_size = 4 if len(rand_items) >= 4 else len(rand_items)
    rand_items = random.sample(rand_items, sample_size)
    return render_template("item.html", sel_item=item, items=rand_items)
    
    
@app.route("/login")
def loginPage():
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    login_session['state'] = state
    return render_template("login.html", STATE=state)


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
    #TODO - set user to logged in user

    errors = {}
    params = {}

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']

        
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


        if form_valid:
            new_item = Item(name=name,
                            category=category,
                            description=description,
                            user=user,
                            views=0)
            session.add(new_item)
            session.commit()
            flash("Item successfully created", "success")
            return redirect(url_for('itemPage', item_id=new_item.id))
        else:
            flash("Item create has failed, see errors below", "danger")

    return render_template("create.html",
                            categories=get_categories(),
                            errors=errors,
                            params=params)


@app.route("/catalog/<int:item_id>/edit", methods=["GET", "POST"])
def editItemPage(item_id):

    #TODO - get logged in user
    item = get_item_by_id(item_id)
    user = session.query(User).filter_by(id=1).one()
    if not item:
        return "This item doesn't exist: %s" % str(item_id)

    if item.user != user:
        return "You don't authorization for that"

    errors = {}

    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']

        user = session.query(User).filter_by(id=1).one()


        form_valid = True
        if not name:
            form_valid = False
            errors['name'] = "Item name cannot be empty"

        if not category:
            form_valid = False
            errors['category'] = "Item category cannot be empty"

        if not description:
            form_valid = False
            errors['description'] = "Item description cannot be empty"

        if form_valid:
            item.name = name
            item.category = category
            item.description = description
            session.add(item)
            session.commit()
            flash("Item edits have been saved", "success")
        else:
            flash("Item edit has failed, see errors below", "danger")


    return render_template("edit.html",
                           item=item,
                           errors=errors,
                           categories=get_categories())



@app.route("/catalog/<int:item_id>/delete")
def deleteItem(item_id):
    item = get_item_by_id(item_id)

    #TODO - get logged in user
    #TODO - add message flashing
    #TODO - redirect to user's items list page
    user = session.query(User).filter_by(id=1).one()
    if not item:
        return "This item doesn't exist: %s" % str(item_id)

    if item.user != user:
        return "You don't authorization for that"

    session.delete(item)
    session.commit()

    return "Okay"


@app.route("/user/items")
def userCreatedItems():

    #TODO - get logged in user
    user = session.query(User).filter_by(id=1).one()
    items = session.query(Item).filter_by(user=user).all()

    return render_template("useritems.html", items=items)


@app.route("/gconnect", methods=["POST"])
def gconnect2():
    """
    Trades Google OAuth one-time code for an access token, then verifies info
    If user info is valid, stores user information in flask session
    """

    # Check that this url was requested via the google callback method
    if not request.headers.get('X-Requested-With'):
        response = make_response(json.dumps('Invalid header'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if state variable is the same as when the login page was requested
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # exchange one time code for user access token
    try:
        flow = flow_from_clientsecrets('client_secrets.json',
                                    scope='',
                                    redirect_uri='postmessage')
        auth_code = request.data
        credentials = flow.step2_exchange(auth_code)
    except FlowExchangeError:
        response = make_response(json.dumps('Unable to exchange code '
            'for token'), 401)

        response.headers['Content-Type'] = 'application/json'
        return response

    if credentials.access_token_expired:
        response = make_response(json.dumps('Access token expired'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify token id is same as user attempting to log in using google OAuth
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user is connected
    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps('Current user is already '
            'connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']


@app.route("/success")
def success():
    flash("You are now logged in as %s" % login_session['username'], "success")
    return redirect(url_for('homepage'))





if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)