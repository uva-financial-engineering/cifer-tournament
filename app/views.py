import os

from flask import render_template, g, request, session, send_from_directory

from app import app, db
from models import User, Stock, StockPrice
from forms import RegForm, LoginForm, TradeForm

@app.route("/", methods=["GET", "POST"])
def index():
    action = request.form["action"] if request.method == "POST" else None

    # User is logged in
    if "user" in session:
        user = User.query.filter_by(id=session["user"]).first()

        tradeform = TradeForm(request.form)
        csrf_markup = '<input name="csrf_token" type="hidden" value="' + str(tradeform.csrf_token)[62:-2] + '">'
        tradeform.csrf_token_no_id = csrf_markup

        if action == "logout":
            session.pop("user", None)
            return index()
        elif action == "trade" and tradeform.validate():
            if tradeform.trade_position.data == 0:
                user.cash -= float(tradeform.trade_qty.data)
            else:
                user.cash += float(tradeform.trade_qty.data)
            db.session.commit()

        stocks = Stock.query.all()
        for i in xrange(len(stocks)):
            stocks[i].bid = StockPrice.query.filter_by(stock_id=i + 1).first().bid
            stocks[i].ask = StockPrice.query.filter_by(stock_id=i + 1).first().ask

        return render_template("index.html", user=user, stocks=stocks, tradeform=tradeform)
    else:
        regform = RegForm(request.form)
        loginform = LoginForm(request.form)
        csrf_markup = '<input name="csrf_token" type="hidden" value="' + str(regform.csrf_token)[62:-2] + '">'
        regform.csrf_token_no_id = csrf_markup
        loginform.csrf_token_no_id = csrf_markup

        if action == "register" and regform.validate():
            db.session.add(User(email=regform.reg_email.data, password=regform.reg_password.data))
            db.session.commit()
            session["user"] = User.query.filter_by(email=regform.reg_email.data).first().id
        elif action == "login" and loginform.validate():
            session["user"] = User.query.filter_by(email=loginform.login_email.data).first().id
            stocks = Stock.query.all()
            return index()

        return render_template("login.html", regform=regform, loginform=loginform)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
       "favicon.ico", mimetype="image/vnd.microsoft.icon")
