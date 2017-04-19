from flask import Flask, render_template, url_for



app = Flask(__name__)


@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/catalog")
def catalogMainPage():
    return "This is the catalog main page"


@app.route("/catalog/<string:category>")
def catalogCategoryPage(category):
    return "This is the catalog page for %s" % category


@app.route("/catalog/<int:item_id>")
def itemPage(item_id):
    return "This is the item page for item: %s" % item_id


@app.route("/login")
def loginPage():
    return "This is the login page"

@app.route("/logout")
def logoutPage():
    return "This is the logout page"


@app.route("/create")
def createItemPage():
    return "This is the create item page"


@app.route("/catalog/<int:item_id>/edit")
def editItemPage(item_id):
    return "This is the edit page for item %s" % item_id


@app.route("/catalog/<int:item_id>/delete")
def deleteItemPage(item_id):
    return "This is the delete page for item %s" % item_id

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)