from flask import Flask, render_template, url_for



app = Flask(__name__)


@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/catalog", defaults={"category": None})
@app.route("/catalog/<string:category>")
def catalogPage(category):
    return render_template("catalog.html", category=category)


@app.route("/catalog/<int:item_id>")
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