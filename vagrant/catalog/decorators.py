from functools import wraps
from flask import session as login_session, redirect, url_for, abort
from database_setup import Item, User, ItemList, Base, create_db
from database import session


def user_exists(f):
    @wraps(f)
    def func(**kwargs):
        user_id = kwargs["user_id"]
        user = session.query(User).filter_by(id=user_id).first()

        if not user:
            print "User not found"
            abort(404)
        return f(user)
    return func


def user_logged_in(f):
    """
    Checks if user is logged in. If not logged in, redirect to login page.
    Adds user obj for logged in user to kwargs
    """
    @wraps(f)
    def func(**kwargs):
        if "username" not in login_session:
            return redirect(url_for('loginPage'))
        user = session.query(User).filter_by(id=login_session["id"]).first()
        if not user:
            print "error, user not found"
            abort(401)

        kwargs["user"] = user
        return f(**kwargs)
    return func


def item_exists(f):
    """
    Checks if item exists using id. If found, adds item to kwargs
    """
    @wraps(f)
    def func(**kwargs):
        item = session.query(Item).filter_by(id=kwargs["item_id"]).first()
        if not item:
            abort(404)
            print "item doesn't exist"
        kwargs["item"] = item
        return f(**kwargs)
    return func


def list_exists(f):
    """
    Checks if list exists using id. If found, adds list to kwargs
    """
    @wraps(f)
    def func(**kwargs):
        if "list_id" in kwargs:
            item_list = session.query(ItemList).filter_by(
                id=kwargs["list_id"]).first()

            if not item_list:
                abort(404)
            kwargs["item_list"] = item_list
        return f(**kwargs)
    return func


def user_owns_list(f):
    """
    Checks if user owns list
    """
    @wraps(f)
    def func(**kwargs):
        if "item_list" in kwargs:
            item_list = kwargs["item_list"]
            user = kwargs["user"]

            if item_list.user.id != user.id:
                print "You don't own this list"
                abort(403)

        return f(**kwargs)
    return func


def user_owns_item(f):
    """
    Checks if user owns item
    """
    @wraps(f)
    def func(**kwargs):
        item = kwargs["item"]
        user = kwargs["user"]

        if item.user.id != user.id:
            print "You don't own this item"
            abort(403)

        return f(**kwargs)
    return func


def item_in_list(f):
    """
    Checks if item exists in list
    """
    @wraps(f)
    def func(**kwargs):
        item = kwargs["item"]
        item_list = kwargs["item_list"]

        if item not in item_list.items:
            print "item not in list"
            abort(404)

        return f(**kwargs)
    return func
