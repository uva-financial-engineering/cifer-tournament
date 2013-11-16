from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import render_template, flash, g, redirect, request, session, send_from_directory, url_for

from app import app, db
from models import User, Stock, AssetPrice, PortfolioAsset, Terror, Transaction
from forms import RegForm, LoginForm, TradeForm

# Constants

TODAY = "2013-08-16"
LAST_WEEKDAY = "2013-08-16"
RATE = Decimal("1.00002739763558")
TARGET = Decimal("50000000")

class Security:
    STOCK, CALL, PUT = range(3)

# Routes

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
        elif action == "trade" and tradeform.validate():
            security = tradeform.trade_asset.data.split(",")[0]
            strike = tradeform.trade_asset.data.split(",")[1]
            stock_id = tradeform.trade_asset.data.split(",")[2]
            is_buy = tradeform.trade_position.data == "buy"

            # Get basket item (or create it if nonexistent)
            portfolio_asset = PortfolioAsset.query.filter_by(user_id=session["user"], stock_id=stock_id, security=security, strike=strike).first()
            if portfolio_asset is None:
                portfolio_asset = PortfolioAsset(session["user"], stock_id, security, strike, 0)
                db.session.add(portfolio_asset)

            if is_buy:
                # Subtract from cash
                value = tradeform.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().ask
                user.cash -= Decimal("1.004") * value

                # Add items to basket
                portfolio_asset.qty += tradeform.trade_qty.data
            else:
                # Add to cash
                value = tradeform.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().bid
                user.cash += Decimal("0.996" if portfolio_asset.qty > 0 else "0.99") * value

                # Remove items from basket
                portfolio_asset.qty -= tradeform.trade_qty.data

            # Remove basket item if quantity is zero
            if portfolio_asset.qty == 0:
                db.session.delete(portfolio_asset)

            # Add transaction record
            db.session.add(Transaction(date=LAST_WEEKDAY, user_id=session["user"], is_buy=is_buy, stock_id=stock_id, security=security, strike=strike, qty=tradeform.trade_qty.data, value=value))

            # Save to database
            db.session.commit()
        else:
            # Generate tracking error table
            terrors = [(t.date, t.terror) for t in Terror.query.filter_by(user_id=session["user"]).order_by(Terror.date).all()]

            # Generate transaction history table
            transactions = Transaction.query.filter_by(user_id=session["user"]).order_by(Transaction.date).all()

            flash_errors(tradeform)
            return render_template("index.html", user=user, date=TODAY, tradeform=tradeform, terrors=terrors, transactions=transactions, js=generate_js(session["user"]))
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
        else:
            flash_errors(regform)
            flash_errors(loginform)
            return render_template("login.html", regform=regform, loginform=loginform, js=generate_js(-1))

    return redirect(url_for("index"))

@app.route("/midnight")
def midnight():
    """Advances current date by 1 day (should be called at midnight)."""

    global TODAY, LAST_WEEKDAY, RATE, TARGET

    # Calculate new date
    t = time.strptime(TODAY, "%Y-%m-%d")
    TODAY = (date(t.tm_year,t.tm_mon,t.tm_mday) + timedelta(1)).strftime("%Y-%m-%d")

    # Calculate most recent weekday
    asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=TODAY).all())
    if len(asset_prices):
        LAST_WEEKDAY = TODAY

        # Add interest to cash, then record it
        portfolio_values = dict()
        for user in User.query.all():
            user.cash *= RATE
            portfolio_values[user.id] = user.cash

        # Add value of basket items
        for portfolio_asset in PortfolioAsset.query.all():
            portfolio_values[portfolio_asset.user_id] += portfolio_asset.qty * asset_prices[(portfolio_asset.stock_id, portfolio_asset.security, portfolio_asset.strike)]

        # Store tracking errors
        TARGET *= RATE
        for user, value in portfolio_values.iteritems():
            terror = TARGET - value if value < TARGET else (value - TARGET) / 2
            db.session.add(Terror(TODAY, user, terror))

        db.session.commit()
        return redirect(url_for("index"))

    return redirect(url_for("index"))

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

# Helpers

def generate_js(user):
    if user > 0:
        authenticated = True;
        # Get portfolio assets
        portfolio_assets = dict(((a.stock_id, a.security, a.strike), a.qty) for a in PortfolioAsset.query.filter_by(user_id=session["user"]).all())
    else:
        authenticated = False;

    # Build stock table
    stocks = [[str(s.symbol), str(s.sector)] for s in Stock.query.order_by(Stock.id).all()]

    info = []
    for a in AssetPrice.query.filter_by(date=LAST_WEEKDAY).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all():
        a.symbol, a.sector = stocks[a.stock_id - 1]

        if a.security == Security.STOCK:
            a.name = "Stock"
        elif a.security == Security.CALL:
            a.name = str(a.strike) + " Call"
        else:
            a.name = str(a.strike) + " Put"

        info_array = [a.stock_id, int(a.security), float(a.strike), "%.2f" % float(a.bid), "%.2f" % float(a.ask)]

        if authenticated:
            # Add portfolio info
            if (a.stock_id, a.security, a.strike) in portfolio_assets:
                a.qty = portfolio_assets[(a.stock_id, a.security, a.strike)]
                a.value = a.qty * (a.bid + Decimal("0.005"))
            else:
                a.qty = 0
                a.value = 0

            info_array.append(int(a.qty))
            info_array.append("%.2f" % float(a.value))

        info.append(info_array)

    return ("AUTHENTICATED=" + str(authenticated).lower() + ";STOCKS=" + str(stocks) + ";INFO=" + str(info) + ";").replace(" ", "")

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")
