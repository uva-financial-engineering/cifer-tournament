from __future__ import division

import os
import math
import time
from decimal import Decimal

from flask import render_template, g, request, session, send_from_directory

from app import app, db
from models import User, Stock, StockPrice, BasketItem, Terror
from forms import RegForm, LoginForm, TradeForm

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
                user.cash -= Decimal(1.004) * tradeform.trade_qty.data * StockPrice.query.filter_by(stock_id=tradeform.trade_stock.data, date="2013-08-16").first().ask

                # Add items to basket
                basket_item.qty += tradeform.trade_qty.data
            else:
                # Add to cash
                user.cash += Decimal(0.996 if basket_item.qty > 0 else 0.99) * tradeform.trade_qty.data * StockPrice.query.filter_by(stock_id=tradeform.trade_stock.data, date="2013-08-16").first().bid

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
            stocks[i].bid = StockPrice.query.filter_by(stock_id=i + 1, date="2013-08-16").first().bid
            stocks[i].ask = stocks[i].bid + Decimal(1) / Decimal(100)

            # Add portfolio data
            basket_shares = BasketItem.query.filter_by(user_id=session["user"], stock_id=i + 1, strike=-1).first()
            if basket_shares:
                stocks[i].shares = basket_shares.qty
                stocks[i].value = basket_shares.qty * (stocks[i].bid + Decimal(1) / Decimal(200))
            else:
                stocks[i].shares = 0
                stocks[i].value = 0

        return render_template("index.html", user=user, stocks=stocks, tradeform=tradeform)
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

    # Add interest to cash, then record it
    portfolio_values = dict()
    for user in User.query.all():
        user.cash *= Decimal(math.exp(1 / 36500))
        portfolio_values[user.id] = user.cash

    # Add value of basket items
    for basket_item in BasketItem.query.all():
        portfolio_values[basket_item.user_id] += basket_item.qty * (StockPrice.query.filter_by(stock_id=basket_item.stock_id, date="2013-08-19").first().bid + Decimal(1) / Decimal(200))

    # Store tracking errors
    target = 50000000 * Decimal(math.exp(1 / 36500))
    for user, value in portfolio_values.iteritems():
        terror = target - value if value < target else (value - target) / 2
        db.session.add(Terror("2013-08-19", user, terror))

    db.session.commit()

    return str(portfolio_values)

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
