from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import render_template, g, request, session, send_from_directory

from app import app, db
from models import User, Stock, StockPrice, OptionPrice, BasketItem, Terror
from forms import RegForm, LoginForm, TradeForm

TODAY = "2013-08-16"
LAST_WEEKDAY = "2013-08-16"
RATE = Decimal("1.0000273976355823353284453")
TARGET = Decimal("50000000")

@app.route("/", methods=["GET", "POST"])
def index():
    """Main page that serves as both login screen and app screen."""

    # Identifies which form (if any) was submitted
    action = request.form["action"] if request.method == "POST" else None

    if "user" in session:
        user = User.query.filter_by(id=session["user"]).first()

        # Generate form
        tradeform = TradeForm(request.form)

        # Handle POST requests
        if action == "logout":
            session.pop("user", None)
            return index()
        elif action == "trade" and tradeform.validate():
            # Get basket item (or create it if nonexistent)
            basket_item = BasketItem.query.filter_by(user_id=session["user"], stock_id=tradeform.trade_stock.data, strike=-1).first()
            if basket_item is None:
                basket_item = BasketItem(session["user"], tradeform.trade_stock.data, True, -1, 0)
                db.session.add(basket_item)

            if tradeform.trade_position.data == "buy":
                # Subtract from cash
                user.cash -= Decimal("1.004") * tradeform.trade_qty.data * StockPrice.query.filter_by(stock_id=tradeform.trade_stock.data, date=LAST_WEEKDAY).first().ask

                # Add items to basket
                basket_item.qty += tradeform.trade_qty.data
            else:
                # Add to cash
                user.cash += Decimal("0.996" if basket_item.qty > 0 else "0.99") * tradeform.trade_qty.data * StockPrice.query.filter_by(stock_id=tradeform.trade_stock.data, date=LAST_WEEKDAY).first().bid

                # Remove items from basket
                basket_item.qty -= tradeform.trade_qty.data

            # Remove basket item if quantity is zero
            if basket_item.qty == 0:
                db.session.delete(basket_item)

            # Save to database
            db.session.commit()

        # Generate stock table
        stocks = Stock.query.all()
        for i in xrange(len(stocks)):
            # Add bid/ask data
            stocks[i].bid = StockPrice.query.filter_by(stock_id=i + 1, date=LAST_WEEKDAY).first().bid
            stocks[i].ask = stocks[i].bid + Decimal("0.01")

            # Add portfolio data
            basket_shares = BasketItem.query.filter_by(user_id=session["user"], stock_id=i + 1, strike=-1).first()
            if basket_shares:
                stocks[i].shares = basket_shares.qty
                stocks[i].value = basket_shares.qty * (stocks[i].bid + Decimal("0.005"))
            else:
                stocks[i].shares = 0
                stocks[i].value = 0

        return render_template("index.html", user=user, date=TODAY, stocks=stocks, tradeform=tradeform)
    else:
        # Generate forms
        regform = RegForm(request.form)
        loginform = LoginForm(request.form)

        # Handle POST requests
        if action == "register" and regform.validate():
            db.session.add(User(email=regform.reg_email.data, password=regform.reg_password.data))
            db.session.commit()
            session["user"] = User.query.filter_by(email=regform.reg_email.data).first().id
        elif action == "login" and loginform.validate():
            session["user"] = User.query.filter_by(email=loginform.login_email.data).first().id
            return index()

        return render_template("login.html", regform=regform, loginform=loginform)

@app.route("/midnight")
def midnight():
    """Advances current date by 1 day (should be called at midnight)."""

    global TODAY, LAST_WEEKDAY, RATE, TARGET

    # Calculate new date
    t = time.strptime(TODAY, "%Y-%m-%d")
    TODAY = (date(t.tm_year,t.tm_mon,t.tm_mday) + timedelta(1)).strftime("%Y-%m-%d")

    # Calculate most recent weekday
    stock_prices = dict((s.stock_id, s.bid + Decimal("0.005")) for s in StockPrice.query.filter_by(date=TODAY).all())
    if len(stock_prices):
        LAST_WEEKDAY = TODAY

        option_prices = dict((o.stock_id, o.bid + Decimal("0.005")) for o in OptionPrice.query.filter_by(date=TODAY).all())

        # Add interest to cash, then record it
        portfolio_values = dict()
        for user in User.query.all():
            user.cash *= RATE
            portfolio_values[user.id] = user.cash

        # Add value of basket items
        for basket_item in BasketItem.query.all():
            portfolio_values[basket_item.user_id] += basket_item.qty * (stock_prices[basket_item.stock_id] if basket_item.strike < 0 else option_prices[basket_item.stock_id])

        # Store tracking errors
        TARGET *= RATE
        for user, value in portfolio_values.iteritems():
            terror = TARGET - value if value < TARGET else (value - TARGET) / 2
            db.session.add(Terror(TODAY, user, terror))

        db.session.commit()
        return str(portfolio_values) + "\n" + str(TODAY)

    return str(TODAY)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
       "favicon.ico", mimetype="image/vnd.microsoft.icon")

# Timing code

@app.before_request
def before_request():
    g.start = time.time()

@app.teardown_request
def teardown_request(exception=None):
    app.logger.debug("Time: " + str(time.time() - g.start))
