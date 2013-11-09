import os

from flask import render_template, g, request, session, send_from_directory

from app import app, db
from models import User, Stock
from forms import RegForm, LoginForm

@app.route("/", methods=["GET", "POST"])
def index():
    # Set up forms
    regform = RegForm(request.form)
    loginform = LoginForm(request.form)
    csrf_markup = '<input name="csrf_token" type="hidden" value="' + str(regform.csrf_token)[62:-2] + '">'
    regform.csrf_token_no_id = csrf_markup
    loginform.csrf_token_no_id = csrf_markup

    action = request.form["action"] if request.method == "POST" else None

    # User is logged in
    if "user" in session:
        if action == "logout":
            session.pop("user", None)
            return render_template("login.html", regform=regform, loginform=loginform)
        stocks = Stock.query.all()
        return render_template("index.html", stocks=stocks)
    else:
        if action == "register" and regform.validate():
            db.session.add(User(email=regform.reg_email.data, password=regform.reg_password.data))
            db.session.commit()
            session["user"] = User.query.filter_by(email=regform.reg_email.data).first().id
        elif action == "login" and loginform.validate():
            session["user"] = User.query.filter_by(email=loginform.login_email.data).first().id
            stocks = Stock.query.all()
            return render_template("index.html", stocks=stocks)

    # Show login screen by default
    return render_template("login.html", regform=regform, loginform=loginform)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
       "favicon.ico", mimetype="image/vnd.microsoft.icon")
