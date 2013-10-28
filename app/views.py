import os

from flask import render_template, g, request, session, send_from_directory

from app import app, db
from models import User, Stock
from forms import RegistrationForm, LoginForm

@app.route("/", methods=["GET", "POST"])
def index():
    registrationform = RegistrationForm(request.form)
    loginform = LoginForm(request.form)

    if request.method == "POST":
        action = request.form["action"]
        if action == "register" and registrationform.validate():
            db.session.add(User(email=registrationform.email.data, password=registrationform.password.data))
            db.session.commit()
            session["user"] = User.query.filter_by(email=registrationform.email.data).first().id
        elif action == "login" and loginform.validate():
            session["user"] = User.query.filter_by(email=loginform.email.data).first().id
        elif action == "logout":
            session.pop("user", None)

    # User is logged in
    if "user" in session:
        stocks = Stock.query.all()
        return render_template("index.html", stocks=stocks)

    return render_template("login.html", registrationform=registrationform, loginform=loginform)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
       "favicon.ico", mimetype="image/vnd.microsoft.icon")
