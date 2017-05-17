from functools import wraps
from flask import session as login_session, redirect, url_for, abort
from database_setup import Item, User, ItemList, Base, create_db
from database import session


def user_logged_in(f):
    @wraps(f)
    def func(*args, **kwargs):
        if "username" not in login_session:
            return redirect(url_for('loginPage'))
        return f(*args, **kwargs)
    return func


def item_exists(f):
    @wraps(f)
    def func(**kwargs):
        item = session.query(Item).filter_by(id=kwargs["item_id"]).first()
        if not item:
            abort(404)
        kwargs["item"] = item
        return f(**kwargs)
    return func


