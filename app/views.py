from flask import render_template, g, request, session

from app import app, db
from models import User, Stock
from forms import RegistrationForm, LoginForm

@app.route("/", methods=["GET", "POST"])
def index():
    regform = RegistrationForm()
    logform = LoginForm()

    if request.method == "POST":
        action = request.form["action"]
        if action == "register" and regform.validate():
            db.session.add(User(email=regform.email.data, password=regform.password.data))
            db.session.commit()
            session["user"] = User.query.filter_by(email=regform.email.data).first().id
        elif action == "login" and logform.validate():
            session["user"] = User.query.filter_by(email=logform.email.data).first().id
        elif action == "logout":
            session.pop("user", None)

    # User is logged in
    if "user" in session:
        stocks = Stock.query.all()
        return render_template("index.html", stocks=stocks)

    return render_template("login.html", regform=regform, logform=logform)
