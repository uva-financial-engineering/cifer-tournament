from flask import render_template, g, request
from flask.ext.login import current_user

from app import app, db, lm
from models import User, Stock

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form["action"] == "login":
            if request.form["email"] != "t":
                stocks = Stock.query.all()
                return render_template("index.html", stocks=stocks)
            else:
                return render_template("login.html")
        else:
            return render_template("index.html")
    else:
        if g.user is not None and g.user.is_authenticated():
            stocks = Stock.query.all()
            return render_template("index.html", stocks=stocks)
        else:
            return render_template("login.html")
