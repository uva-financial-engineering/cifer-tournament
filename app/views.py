from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import render_template, flash, redirect, request, session, send_from_directory, url_for

from app import app, db
from models import User, Stock, AssetPrice, PortfolioAsset, Terror, Transaction
from forms import RegForm, LoginForm, TradeForm

# Constants

TODAY = "2013-08-16"
LAST_WEEKDAY = "2013-08-16"
RATE = Decimal("1.00002739763558")
TARGET = Decimal("50000000")
FLASHES = [] # (category, message) tuples

class Security:
    STOCK, CALL, PUT = range(3)

# Routes

@app.route("/", methods=["GET", "POST"])
def index():
    """Main page that serves as both login screen and app screen."""

    global FLASHES

    # Identifies which form (if any) was submitted
    action = request.form["action"] if request.method == "POST" else None

    if "user" in session:
        user = User.query.filter_by(id=session["user"]).first()

        # Handle POST requests
        if action == "logout":
            session.pop("user", None)
        elif action == "trade":
            trade(user, TradeForm(request.form))
        else:
            # Generate transaction history table
            transactions = Transaction.query.filter_by(user_id=session["user"]).order_by(Transaction.date).all()

            flash_all()
            return render_template("index.html", user=user, date=TODAY, tradeform=TradeForm(request.form), transactions=transactions, js=generate_js(session["user"]))
    else:
        # Handle POST requests
        if action == "register":
            register(RegForm(request.form))
        elif action == "login":
            login(LoginForm(request.form))
        else:
            flash_all()
            return render_template("login.html", regform=RegForm(request.form), loginform=LoginForm(request.form), js=generate_js(-1))

    return redirect(url_for("index"))

@app.route("/midnight")
def midnight():
    """Advances current date by 1 day (should be called at midnight)."""

    global TODAY, LAST_WEEKDAY, RATE, TARGET

    # Calculate new date
    t = time.strptime(TODAY, "%Y-%m-%d")
    TODAY = (date(t.tm_year, t.tm_mon, t.tm_mday) + timedelta(1)).strftime("%Y-%m-%d")

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
            terror = TARGET - value if value < TARGET else (value - TARGET) * Decimal("0.5")
            db.session.add(Terror(TODAY, user, terror))

        db.session.commit()
        return redirect(url_for("index"))

    return redirect(url_for("index"))

@app.route("/ping")
def ping():
    return "0"

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"),
       "favicon.ico", mimetype="image/vnd.microsoft.icon")

# Helpers

def trade(user, form):
    global FLASHES

    if not form.validate():
        flash_errors(form)
        return

    # Check that asset exists and has nonzero value                 asset_prices
    # Check whether margin exceeds $22 million:                     users, portfolio_assets, asset_prices
    # Check that user has 30%+ of margin in cash                    users, portfolio_assets, asset_prices
    # Check that required amount of cash is present in portfolio    users, portfolio_assets, asset_prices
    # Check that sell/shortsell doesn't cross over 0                users, portfolio_assets, asset_prices
    # Check that user didn't already trade asset today              users, transactions
    # Check that asset isn't in initial portfolio                   users, portfolio_assets

    security = form.trade_security.data
    strike = form.trade_strike.data
    stock_id = form.trade_stock_id.data
    is_buy = form.trade_position.data == "buy"

    # Get basket item (or create it if nonexistent)
    portfolio_asset = PortfolioAsset.query.filter_by(user_id=session["user"], stock_id=stock_id, security=security, strike=strike).first()
    if portfolio_asset is None:
        portfolio_asset = PortfolioAsset(session["user"], stock_id, security, strike, 0, True)
        db.session.add(portfolio_asset)

    if is_buy:
        # Subtract from cash
        value = Decimal("1.004") * form.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().ask
        user.cash -= value

        # Add items to basket
        portfolio_asset.qty += form.trade_qty.data
    else:
        # Add to cash
        value = Decimal("0.996" if portfolio_asset.qty > 0 else "0.99") * form.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().bid
        user.cash += value

        # Remove items from basket
        portfolio_asset.qty -= form.trade_qty.data

    # Remove basket item if quantity is zero
    if portfolio_asset.qty == 0:
        db.session.delete(portfolio_asset)

    # Add transaction record
    db.session.add(Transaction(date=LAST_WEEKDAY, user_id=session["user"], is_buy=is_buy, stock_id=stock_id, security=security, strike=strike, qty=form.trade_qty.data, value=value))

    # Save to database
    db.session.commit()

    FLASHES.append(("success", "Trade successful."))

def login(form):
    global FLASHES

    if not form.validate():
        flash_errors(form)
        return

    user = User.query.filter_by(email = form.login_email.data.lower()).first()
    if not (user and user.check_password(form.login_password.data)):
        FLASHES.append(("error", "Invalid email or password."))
        return

    session["user"] = User.query.filter_by(email=form.login_email.data).first().id

def register(form):
    global FLASHES

    if not regform.validate():
        flash_errors(form)
        return

    if User.query.filter_by(email=form.reg_email.data.lower()).first():
        FLASHES.append(("error", "That email is already taken"))
        return

    db.session.add(User(email=form.reg_email.data, password=form.reg_password.data))
    db.session.commit()
    session["user"] = User.query.filter_by(email=form.reg_email.data).first().id

def generate_js(user):
    js = ""

    if user > 0:
        authenticated = True;
        # Get portfolio assets
        portfolio_assets = dict(((a.stock_id, a.security, a.strike), (a.qty, a.liquid)) for a in PortfolioAsset.query.filter_by(user_id=session["user"]).all())

        # Generate tracking error table
        terrors = [[]] * 3
        day = 0
        for t in Terror.query.filter_by(user_id=session["user"]).order_by(Terror.date).all():
            terrors[0].append(day)
            terrors[1].append(t.date.strftime("%d-%b"))
            terrors[2].append(int(t.terror))
            day += 1
        js = "TERRORS=" + str(terrors) + ";"
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
                a.qty, a.liquid = portfolio_assets[(a.stock_id, a.security, a.strike)]
                a.value = a.qty * (a.bid + Decimal("0.005"))
            else:
                a.liquid = 1
                a.qty = 0
                a.value = 0

            info_array.append(1 if a.liquid else 0)
            info_array.append(int(a.qty))
            info_array.append("%.2f" % float(a.value))

        info.append(info_array)

    return (js + "AUTHENTICATED=" + str(authenticated).lower() + ";STOCKS=" + str(stocks) + ";INFO=" + str(info) + ";").replace(" ", "")

def flash_errors(form):
    global FLASHES

    for field, errors in form.errors.items():
        for error in errors:
            FLASHES.append(("error", error))

def flash_all():
    global FLASHES

    for category, message in FLASHES:
        flash(message, category)
    FLASHES = []
