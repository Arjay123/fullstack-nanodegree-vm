import random
import hashlib
import os

from flask import Flask, render_template, url_for, request, redirect, flash
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import exists

from database_setup import Item, User, ItemList, Base, create_db

from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json

from flask import make_response
import requests
import pprint


db_uri = "sqlite:///itemcatalog.db"
engine = create_engine(db_uri)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)
app.secret_key = "sosecret"


CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
FB_CLIENT_ID = json.loads(open("fb_client_secrets.json", "r").read())["web"]["client_id"]
FB_CLIENT_SECRET = json.loads(open("fb_client_secrets.json", "r").read())["web"]["client_secret"]

USERNAME_KEY = "username"
PICTURE_KEY = "picture"
EMAIL_KEY = "email"
ID_KEY = "user_id"
ACCESS_TOKEN_KEY = "access_token"
PROVIDER_KEY = "provider"

LOCAL_ID = "id"
FACEBOOK = "facebook"
GOOGLE = "google"


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
    lists = None
    if not item:
        return "This item does not exist: %s" % str(item_id)

    rand_items = session.query(Item).filter_by(category=item.category).all()
    sample_size = 4 if len(rand_items) >= 4 else len(rand_items)
    rand_items = random.sample(rand_items, sample_size)

    if ACCESS_TOKEN_KEY in login_session:
        user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
        lists = session.query(ItemList).filter_by(user=user).all()

    return render_template("item.html", sel_item=item, items=rand_items, lists=lists)
    

@app.route("/listAdd/<int:list_id>/<int:item_id>")
def addItemToList(list_id, item_id):
    
    item = session.query(Item).filter_by(id=item_id).first()
    item_list = session.query(ItemList).filter_by(id=list_id).first()

    if LOCAL_ID not in login_session:
        print "no idea"
        return

    if login_session[LOCAL_ID] != item_list.user.id:

        print "you don't own this list", login_session[LOCAL_ID], item_list.user.id
        return

    item_list.items.append(item)
    session.add(item_list)
    session.commit()


    return redirect(url_for('itemPage', item_id=item_id))

    
@app.route("/login")
def loginPage():
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route("/logout")
def logout():
    if ACCESS_TOKEN_KEY in login_session:
        if login_session[PROVIDER_KEY] == GOOGLE:
            result = gdisconnect()
        else:
            result = fbdisconnect()

        if not result:
            response = make_response(json.dumps('Failed to revoke token'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        login_session.clear()

        flash("You are logged out", "danger")

    return redirect(url_for('homepage'))


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

        
        user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()

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
    user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
    if not item:
        return "This item doesn't exist: %s" % str(item_id)

    if item.user != user:
        return "You don't authorization for that"

    errors = {}

    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']


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
    user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
    if not item:
        return "This item doesn't exist: %s" % str(item_id)

    if item.user != user:
        return "You don't have authorization for that"

    session.delete(item)
    session.commit()

    return "Okay"


@app.route("/user/items")
def userCreatedItems():

    #TODO - get logged in user
    user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
    items = session.query(Item).filter_by(user=user).all()

    return render_template("useritems.html", items=items)


@app.route("/user/lists")
@app.route("/user/lists/<int:list_id>")
def userCreatedLists(list_id=None):

    

    user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
    lists = session.query(ItemList).filter_by(user=user).all()
    items = []

    if list_id:
        items = session.query(ItemList).filter_by(id=list_id).one().items
    else:
        items = lists[0].items

    return render_template("useritemlists.html", lists=lists, items=items)


@app.route("/user/lists/create", methods=["POST"])
def createList():
    name = request.form['name']
    user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
    new_list = ItemList(name=name, user=user)
    session.add(new_list)
    session.commit()

    return redirect(url_for('userCreatedLists'))



@app.route("/success")
def success():

    # check if user already has an account using email
    found = session.query(exists().where(User.email==login_session[EMAIL_KEY])).scalar() 

    # if no account, create one
    if not found:
        print "created new user"
        new_user = User(name=login_session[USERNAME_KEY],
                        email=login_session[EMAIL_KEY],
                        image=login_session[PICTURE_KEY])
        session.add(new_user)
        session.commit()

    user = session.query(User).filter_by(email=login_session[EMAIL_KEY]).one()
    login_session[LOCAL_ID] = user.id

    flash("You are now logged in as %s" % login_session[USERNAME_KEY], "success")
    return redirect(url_for('homepage'))



@app.route("/gconnect", methods=["POST"])
def gconnect2():
    """
    Trades Google OAuth one-time code for an access token, then verifies info
    If user info is valid, stores user information in flask session
    """

    # Check that this url was requested via the google callback method
    if not request.headers.get('X-Requested-With'):
        client_response = make_response(json.dumps('Invalid header'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # Check if state variable is the same as when the login page was requested
    if request.args.get('state') != login_session['state']:
        client_response = make_response(json.dumps('Invalid state parameter.'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # exchange one time code for user access token
    try:
        flow = flow_from_clientsecrets('client_secrets.json',
                                    scope='',
                                    redirect_uri='postmessage')
        auth_code = request.data
        credentials = flow.step2_exchange(auth_code)
    except FlowExchangeError:
        client_response = make_response(json.dumps('Unable to exchange code '
            'for token'), 401)

        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    if credentials.access_token_expired:
        client_response = make_response(json.dumps('Access token expired'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # Verify token id is same as user attempting to log in using google OAuth
    access_token = credentials.access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
    response = requests.get(url, params={'access_token': access_token})
    result = response.json()

    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        client_response = make_response(json.dumps("Token's user ID doesn't "
            "match given user ID."), 401)

        client_response.headers['Content-Type'] = 'application/json'
        return client_response


    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        client_response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        client_response.headers['Content-Type'] = 'application/json'
        return client_response


    # Check if user is connected
    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        client_response = make_response(json.dumps('Current user is already '
                                    'connected.'), 200)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response


    # Store the access token in the session for later use.
    login_session[ACCESS_TOKEN_KEY] = credentials.access_token
    login_session[ID_KEY] = google_id


    # Get user info to store in flask session
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()


    # Store user info in session
    login_session[USERNAME_KEY] = data['name']
    login_session[PICTURE_KEY] = data['picture']
    login_session[EMAIL_KEY] = data['email']
    login_session[PROVIDER_KEY] = GOOGLE


    client_response = make_response(json.dumps('User is logged in.'), 200)
    client_response.headers['Content-Type'] = 'application/json'
    return client_response





@app.route("/fbconnect", methods=["POST"])
def fbconnect():

    # Check that this url was requested via the google callback method
    if not request.headers.get('X-Requested-With'):
        client_response = make_response(json.dumps('Invalid header'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # check state parameter
    if request.args.get("state") != login_session["state"]:
        client_response = make_response(json.dumps('Invalid state parameter.'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response


    # exchange short term access for long term
    url = "https://graph.facebook.com/oauth/access_token"
    params = {"grant_type": "fb_exchange_token",
              "client_id": FB_CLIENT_ID,
              "client_secret": FB_CLIENT_SECRET,
              "fb_exchange_token": request.data,
              "redirect_uri": "http://localhost:5000"}
    response = requests.get(url, params=params)

    r = response.json()
    if response.status_code != 200:
        pass

    access_token = r["access_token"]
    user_id = request.args.get("user_id")


    # Get app access token to verify user access token
    app_access = get_fb_app_access_token()
    if not app_access:
        pass

    # verify access token
    verify_url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": access_token,
        "access_token": app_access,
    }
    response = requests.get(verify_url, params=params)
    if response.status_code != 200:
        pass

    r = response.json()["data"]

    # app id check
    if r["app_id"] != FB_CLIENT_ID:
        print("app id not match")

    # application name check
    if r["application"] != "ItemCatalog":
        print("application name not match")

    # is_valid check,
    if not r["is_valid"]:
        print("access_token no longer valid")

    # user_id check
    if r["user_id"] != user_id:
        print("access token user id not match")


    user_info_url = "https://graph.facebook.com/me"
    params = {
        "fields": "email,name,picture",
        "access_token": access_token,
    }
    response = requests.get(user_info_url, params=params)
    if response.status_code != 200:
        pass

    r = response.json()

    login_session[ID_KEY] = r["id"]    
    login_session[EMAIL_KEY] = r["email"]
    login_session[USERNAME_KEY] = r["name"]
    login_session[PICTURE_KEY] = r["picture"]
    login_session[ACCESS_TOKEN_KEY] = access_token
    login_session[PROVIDER_KEY] = FACEBOOK


    client_response = make_response(json.dumps('User is logged in.'), 200)
    client_response.headers['Content-Type'] = 'application/json'
    return client_response





def gdisconnect():
    """
    Revokes access token for user in Google OAuth
    """
    url = ('https://accounts.google.com/o/oauth2/revoke')
    result = requests.get(url, params={'token': login_session['access_token']})

    return result.status_code == 200


def fbdisconnect():

    url = "https://graph.facebook.com/%s/permissions" % login_session[ID_KEY]
    params = {"access_token": login_session[ACCESS_TOKEN_KEY]}
    result = requests.delete(url, params=params)

    return result.status_code == 200


def get_fb_app_access_token():
    """
    Retrieves access token for this app, primarily used for verifying user 
    access tokens

    Returns: Access token as string if successful
    """
    url = "https://graph.facebook.com/oauth/access_token"
    params = {
        "client_id": FB_CLIENT_ID,
        "client_secret": FB_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print "Error", response.json()
        return

    result = response.json()
    app_id = result["access_token"].split('|')[0]

    # Check app id matches this client id
    if app_id != FB_CLIENT_ID:
        print "Error", response.json()
        return

    return result["access_token"]



if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)