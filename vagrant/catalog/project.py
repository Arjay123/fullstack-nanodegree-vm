import random
import hashlib
import os

from flask import Flask, render_template, url_for, request, redirect, flash
from flask import session as login_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import exists, desc

from database_setup import Item, User, ItemList, Base, create_db

from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json

from flask import make_response, abort
import requests


from decorators import user_logged_in, item_exists, list_exists, user_owns_list, user_owns_item, item_in_list
from database import session


app = Flask(__name__)
app.secret_key = "sosecret"
session.rollback()

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
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


@app.route("/")
def homepage():
    """
    Loads homepage w/ most viewed items showcased
    """
    items = session.query(Item).order_by(desc(Item.views)).limit(4)
    return render_template("homepage.html", items=items)


@app.route("/catalog")
def catalogPage():
    """
    Loads catalog page
    
    If order specified, show items in that order. A-Z by default
    If category selected, show items in that category. Items w/ views over
    100 by default
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
@item_exists
def itemPage(item, **kwargs):
    """
    Loads page for a specific item
    
    Also loads list of random items (4 or less) from the same category as
    selected item to display.

    Args:
        item - entity of selected item
    """

    # update item view count
    item.views += 1
    session.add(item)
    session.commit()
    
    # create list of random items to showcase
    rand_items = session.query(Item).filter_by(category=item.category).all()
    rand_items.remove(item)
    sample_size = 4 if len(rand_items) >= 4 else len(rand_items)
    rand_items = random.sample(rand_items, sample_size)

    params = {"sel_item": item,
              "items": rand_items}

    # if user logged in, pass in their item lists
    if USERNAME_KEY in login_session:
        user = session.query(User).filter_by(id=login_session[LOCAL_ID]).one()
        lists = session.query(ItemList).filter_by(user=user).all()
        params["lists"] = lists

    return render_template("item.html", **params)
    

@app.route("/listAdd/<int:list_id>/<int:item_id>")
@user_logged_in
@item_exists
@list_exists
@user_owns_list
def addItemToList(item, item_list, **kwargs):
    """
    Adds item to item list

    Args:
        item - item to add
        item_list - item list to add to
    """
    
    item_list.items.append(item)
    session.add(item_list)
    session.commit()

    flash("%s has been added to list: %s" %(item.name, item_list.name),
          "success")
    return redirect(url_for('itemPage', item_id=kwargs["item_id"]))



@app.route("/listRemove/<int:list_id>/<int:item_id>")
@user_logged_in
@item_exists
@list_exists
@user_owns_list
@item_in_list
def removeItemFromList(item, item_list, **kwargs):
    """
    Remove item from item list

    item - item to remove
    item_list - itemlist to remove from
    """
    item_list.items.remove(item)
    session.add(item_list)
    session.commit()

    flash("%s has been removed from list: %s" % (item.name, item_list.name),
          "success")

    return(redirect(url_for('userCreatedLists', list_id=item_list.id)))


@app.route("/listMove/<int:item_id>/<int:from_list_id>/<int:to_list_id>")
@user_logged_in
@item_exists
def moveItemBetweenLists(item, from_list_id, to_list_id, **kwargs):
    """
    Move item from one list to another

    item - item to be moved
    from_list_id - id of list to move from
    to_list_id - id of list to move to
    """
    from_list = session.query(ItemList).filter_by(id=from_list_id).first()
    to_list = session.query(ItemList).filter_by(id=to_list_id).first()

    if not from_list or not to_list:
        print "list don't exist"
        abort(404)

    if item not in from_list.items:
        print "that item is not in list"
        abort(404)

    from_list.items.remove(item)
    to_list.items.append(item)

    session.add(from_list)
    session.add(to_list)
    session.commit()

    flash("%s has been move from list: %s to list: %s" %
          (item.name, from_list.name, to_list.name), "success")

    return(redirect(url_for('userCreatedLists', list_id=from_list.id)))


@app.route("/login")
def loginPage():
    """
    Login page
    """

    # generate state var for validation after login attemp
    state = hashlib.sha256(os.urandom(1024)).hexdigest()
    login_session['state'] = state
    return render_template("login.html", STATE=state)


@app.route("/logout")
@user_logged_in
def logout(user):
    """
    Logout user based on third-party oauth provider
    """
    if login_session[PROVIDER_KEY] == GOOGLE:
        result = gdisconnect()
    else:
        result = fbdisconnect()

    login_session.clear()

    if not result:
        response = make_response(json.dumps('Failed to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

    flash("You are logged out", "danger")

    return redirect(url_for('homepage'))



@app.route("/create", methods=['GET', 'POST'])
@user_logged_in
def createItemPage():
    """ 
    Loads page for creating a new item. Requires user to be logged in
    """
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
@user_logged_in
@item_exists
@user_owns_item
def editItemPage(item, **kwargs):
    """
    Load page for editing item.

    Args:
        item - item to be edited
    """
    if not item:
        return "This item doesn't exist: %s" % str(item.id)

    if item.user != user:
        return "You don't have authorization for that"

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
            flash("Item edit has failed, fix errors below and try again",
                  "danger")

    return render_template("edit.html",
                           item=item,
                           errors=errors,
                           categories=get_categories())



@app.route("/catalog/<int:item_id>/delete")
@user_logged_in
@item_exists
@user_owns_item
def deleteItem(item, **kwargs):
    """
    Deletes item

    item - item to be deleted
    """

    #TODO - get logged in user
    #TODO - add message flashing
    #TODO - redirect to user's items list page

    session.delete(item)
    session.commit()

    flash("%s has been deleted." % item.name, "success")
    return redirect(url_for('userCreatedItems'))


@app.route("/user/items")
@user_logged_in
def userCreatedItems(user):
    """
    Loads manager page for all items created by user
    """
    items = session.query(Item).filter_by(user=user).all()
    return render_template("useritems.html", items=items)


@app.route("/user/lists")
@app.route("/user/lists/<int:list_id>")
@user_logged_in
@list_exists
@user_owns_list
def userCreatedLists(user, list_id=None, item_list=None):
    """
    Loads users created item lists page. If no list is selected, loads first
    one by default if any exist.

    user - user that created lists
    list_id - id of selected list
    item_list - selected list
    """
    items = []
    lists = session.query(ItemList).filter_by(user=user).all()

    if list_id:
        items = item_list.items
    else:
        if len(lists):
            items = lists[0].items
            list_id = lists[0].id

    return render_template("useritemlists.html",
                           lists=lists,
                           items=items,
                           list_id=list_id)


@app.route("/user/lists/create", methods=["POST"])
@user_logged_in 
def createList(user):
    """
    Creates a new list

    Args:
    user - user that is creating the list
    """
    name = request.form['name']
    new_list = ItemList(name=name, user=user)
    session.add(new_list)
    session.commit()

    return redirect(url_for('userCreatedLists'))



@app.route("/success")
def success():
    """
    This route is in between a successful login and a redirect to homepage.
    Checks if newly logged in user has an account, if not creates an account
    """
    # check if user already has an account using email
    found = session.query(exists().where(
        User.email==login_session[EMAIL_KEY])).scalar() 

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

    flash("You are now logged in as %s" % login_session[USERNAME_KEY],
        "success")
    return redirect(url_for('homepage'))



@app.route("/gconnect", methods=["POST"])
def gconnect2():
    """
    Trades Google OAuth one-time code for an access token, then verifies info
    If user info is valid, stores user information in flask session, else throw
    error
    """

    # Check that this url was requested via the google callback method
    if not request.headers.get('X-Requested-With'):
        client_response = make_response(json.dumps('Invalid header'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # Check if state variable is the same as when the login page was requested
    if request.args.get('state') != login_session['state']:
        client_response = make_response(
            json.dumps('Invalid state parameter.'), 401)
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
        client_response = make_response(
            json.dumps('Access token expired'), 401)

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
    """
    Trades Facebook short time token for long time token, then 
    verifies access token info. If valid, stores user info in 
    Flask session, else throw error
    """
    # Check that this url was requested via the google callback method
    if not request.headers.get('X-Requested-With'):
        client_response = make_response(json.dumps('Invalid header'), 401)
        client_response.headers['Content-Type'] = 'application/json'
        return client_response

    # check state parameter
    if request.args.get("state") != login_session["state"]:
        client_response = make_response(
            json.dumps('Invalid state parameter.'), 401)
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
    login_session[PICTURE_KEY] = r["picture"]["data"]["url"]
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
    """
    Revokes access token for user in Facebook OAuth
    """
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