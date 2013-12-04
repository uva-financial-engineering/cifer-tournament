from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import (render_template, flash, redirect, request, session,
    send_from_directory, url_for)

from app import app, db
from models import User, Stock, AssetPrice, PortfolioAsset, Terror, Transaction
from forms import RegForm, LoginForm, TradeForm

# Constants

TODAY = "2014-01-14"
LAST_WEEKDAY = TODAY
DAY_AFTER_CONTEST = "2014-02-22"

RATE = Decimal("1.00002739763558")
TARGET = Decimal("56041830")
FLASHES = [] # (category, message) tuples

class Security:
    STOCK, CALL, PUT = range(3)

# Routes

@app.route("/", methods=["GET", "POST"])
def index():
    """Main page that serves as both login screen and app screen."""

    # Create debug user if no users exist
    if not User.query.all():
        db.session.add(User("a@a.com", "a", "John", "Doe", "University of Virginia", True))

        db.session.add(PortfolioAsset(1, 5, 0, -1, 250000, False))
        db.session.add(PortfolioAsset(1, 5, 1, 14, 300000, False))
        db.session.add(PortfolioAsset(1, 8, 1, 49, -100000, False))
        db.session.add(PortfolioAsset(1, 8, 2, 55, 600000, False))
        db.session.add(PortfolioAsset(1, 8, 2, 56, 1000000, False))
        db.session.add(PortfolioAsset(1, 16, 1, 176, 1000000, False))
        db.session.add(PortfolioAsset(1, 16, 1, 177, 300000, False))
        db.session.add(PortfolioAsset(1, 2, 0, -1, -3000, False))
        db.session.add(PortfolioAsset(1, 7, 1, 46, 200000, False))
        db.session.add(PortfolioAsset(1, 7, 2, 50, -100000, False))
        db.session.add(PortfolioAsset(1, 7, 2, 51, -50000, False))
        db.session.add(PortfolioAsset(1, 29, 2, 96, 400000, False))
        db.session.add(PortfolioAsset(1, 29, 2, 97, 500000, False))
        db.session.add(PortfolioAsset(1, 29, 2, 98, 1000000, False))
        db.session.add(PortfolioAsset(1, 13, 0, -1, 100000, False))
        db.session.add(PortfolioAsset(1, 13, 1, 23, 400000, False))
        db.session.add(PortfolioAsset(1, 13, 1, 24, 500000, False))
        db.session.add(PortfolioAsset(1, 26, 1, 40, 500000, False))
        db.session.add(PortfolioAsset(1, 26, 2, 43, 600000, False))
        db.session.add(PortfolioAsset(1, 14, 1, 33, 600000, False))
        db.session.add(PortfolioAsset(1, 14, 1, 34, 800000, False))
        db.session.add(PortfolioAsset(1, 14, 1, 35, 1000000, False))
        db.session.add(PortfolioAsset(1, 1, 0, -1, 400000, False))
        db.session.add(PortfolioAsset(1, 1, 1, 8.5, -300000, False))
        db.session.add(PortfolioAsset(1, 15, 0, -1, 3000, False))
        db.session.add(PortfolioAsset(1, 17, 0, -1, 52000, False))

        db.session.commit()

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
            return render_template("index.html",
                user=user,
                date=TODAY,
                target=TARGET,
                tradeform=TradeForm(request.form),
                transactions=transactions,
                js=generate_js(session["user"]))
    else:
        # Handle POST requests
        if action == "register":
            register(RegForm(request.form))
        elif action == "login":
            login(LoginForm(request.form))
        else:
            flash_all()
            return render_template("login.html",
                regform=RegForm(request.form),
                loginform=LoginForm(request.form),
                js=generate_js(-1))

    return redirect(url_for("index"))

@app.route("/midnight")
def midnight():
    """Advances current date by 1 day (should be called at midnight UTC)."""

    global TODAY, LAST_WEEKDAY, TARGET

    # Add interest to cash, then record it
    portfolio_values = dict()
    users = dict()
    for user in User.query.all():
        users[user.id] = user
        user.cash *= RATE
        portfolio_values[user.id] = user.cash

    # Calculate new date
    yesterday = TODAY
    TODAY = day_after(TODAY)

    # Calculate most recent weekday
    asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=TODAY).all())

    if len(asset_prices):
        LAST_WEEKDAY = TODAY
    else:
        asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=LAST_WEEKDAY).all())

    # Add value of basket items
    for portfolio_asset in PortfolioAsset.query.all():
        price_key = (portfolio_asset.stock_id, portfolio_asset.security, portfolio_asset.strike)
        portfolio_values[portfolio_asset.user_id] += portfolio_asset.qty * (asset_prices[price_key] if price_key in asset_prices else 0)

    # Store tracking errors
    TARGET *= RATE
    for user, value in portfolio_values.iteritems():
        users[user].portfolio = value
        terror = TARGET - value if value < TARGET else (value - TARGET) * Decimal("0.5")
        db.session.add(Terror(yesterday, user, terror))

    db.session.commit()
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

    # Check that asset is tradable today and has nonzero value      asset_prices
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

    if not form.validate():
        flash_errors(form)
        return

    if User.query.filter_by(email=form.reg_email.data.lower()).first():
        FLASHES.append(("error", "That email is already taken"))
        return

    if form.reg_algorithm.data == "yes":
        algorithm = True
    elif form.reg_algorithm.data == "no":
        algorithm = False
    else:
        algorithm = None

    db.session.add(User(email=form.reg_email.data, password=form.reg_password.data, first_name=form.reg_first.data, last_name=form.reg_last.data, institution=form.reg_institution.data, algorithm=algorithm))
    db.session.commit()
    session["user"] = User.query.filter_by(email=form.reg_email.data).first().id

def generate_js(user):
    js = ""

    if user > 0:
        authenticated = True;
        # Get portfolio assets
        portfolio_assets = dict(((a.stock_id, a.security, a.strike), (a.qty, 1 if a.liquid else 0)) for a in PortfolioAsset.query.filter_by(user_id=session["user"]).all())

        # Generate tracking error table
        terrors = [[], [], []]
        day = 0
        for t in Terror.query.filter_by(user_id=session["user"]).order_by(Terror.date).all():
            terrors[0].append(day)
            terrors[1].append(t.date.strftime("%d-%b"))
            terrors[2].append(int(t.terror))
            day += 1

        # Set tracking errors of future days to 0
        t = TODAY
        while t != DAY_AFTER_CONTEST:
            terrors[0].append(day)
            terrors[1].append(time.strftime("%d-%b", time.strptime(t, "%Y-%m-%d")))
            terrors[2].append(0)
            day += 1
            t = day_after(t)

        js = "TERRORS=" + str(terrors) + ";"
    else:
        authenticated = False;

    # Build stock table
    stocks = [[str(s.symbol), None, str(s.sector), None, None] for s in Stock.query.order_by(Stock.id).all()]

    portfolio = []
    options = []

    for a in AssetPrice.query.filter_by(date=LAST_WEEKDAY).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all():

        liquid = 1

        if authenticated and ((a.stock_id, a.security, a.strike) in portfolio_assets):
            qty, liquid = portfolio_assets[(a.stock_id, a.security, a.strike)]

            portfolio.append([a.stock_id, liquid, a.security, str(a.strike), int(qty), "%.2f" % float(qty * (a.bid + Decimal("0.005")))])

        if a.security == Security.STOCK:
            stocks[a.stock_id - 1][1] = liquid
            stocks[a.stock_id - 1][3] = "%.2f" % float(a.bid)
            stocks[a.stock_id - 1][4] = "%.2f" % float(a.ask)
        else:
            options.append([a.stock_id, liquid, a.security, float(a.strike), "%.2f" % float(a.bid), "%.2f" % float(a.ask)])

    return (js + "AUTHENTICATED=" + str(authenticated).lower() + (";PORTFOLIO=" + str(portfolio) if authenticated else "") + ";STOCKS=" + str(stocks) + ";OPTIONS=" + str(options) + ";").replace(", ", ",")

def day_after(datetext):
    t = time.strptime(datetext, "%Y-%m-%d")
    return (date(t.tm_year, t.tm_mon, t.tm_mday) + timedelta(1)).strftime("%Y-%m-%d")

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
