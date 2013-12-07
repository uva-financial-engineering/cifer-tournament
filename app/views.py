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

class Security:
    STOCK, CALL, PUT = range(3)

class Status:
    BEFORE, DURING, AFTER = False, True, False

RATE = Decimal("1.00002739763558")
TARGET = Decimal("56041830")
FLASHES = [] # (category, message) tuples

TODAY = "2014-01-14"
CONTEST_FIRST_DAY = "2014-01-14"
LAST_WEEKDAY = CONTEST_FIRST_DAY
DAY_AFTER_CONTEST = "2014-02-19"

# Routes

@app.route("/", methods=["GET", "POST"])
def index():
    """Main page that serves as both login screen and app screen."""

    # Create debug user if no users exist
    if not User.query.all():
        db.session.add(User("a@a.com", "a", "John", "Doe", "University of Virginia", True))
        create_portfolio(1)
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
            flash_all()
            return render_template("index.html",
                user=user,
                date=pretty_print(TODAY),
                target=TARGET,
                tradeform=TradeForm(request.form),
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

    # Calculate new date
    yesterday = TODAY
    TODAY = day_after(TODAY)

    if Status.BEFORE:
        if TODAY == CONTEST_FIRST_DAY:
            Status.BEFORE, Status.DURING = False, True

    elif Status.DURING:
        if TODAY == DAY_AFTER_CONTEST:
            Status.DURING, Status.AFTER = False, True

        # Add interest to cash, then record it
        portfolio_values = dict()
        users = dict()
        for user in User.query.all():
            users[user.id] = user
            user.cash *= RATE
            portfolio_values[user.id] = user.cash

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
    else:
        pass

    return "0"

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

    if Status.BEFORE:
        FLASHES.append(("error", "Contest begins on " + pretty_print(CONTEST_FIRST_DAY) + "."))
        return

    if Status.AFTER:
        FLASHES.append(("error", "Contest is over."))
        return

    if not form.validate():
        flash_errors(form)
        return

    # Check that market is open
    if TODAY != LAST_WEEKDAY:
        FLASHES.append(("error", "The market is closed today."))
        return

    stock_id = int(form.trade_stock_id.data)
    security = int(form.trade_security.data)
    strike = Decimal(form.trade_strike.data)
    asset_key = (stock_id, security, strike)

    # Check that user didn't already trade asset today
    if asset_key in [(t.stock_id, t.security, t.strike) for t in Transaction.query.filter_by(user_id=user.id, date=TODAY).all()]:
        FLASHES.append(("error", "You can't trade the same asset multiple times in the same day."))
        return

    asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=TODAY).all())

    # Check that asset is tradable today and has nonzero value
    if asset_key not in asset_prices:
        FLASHES.append(("error", "You cannot trade assets that are currently worthless."))
        return

    # Get basket item (or create it if nonexistent)
    portfolio_assets = dict(((int(a.stock_id), int(a.security), Decimal(a.strike)), a) for a in PortfolioAsset.query.filter_by(user_id=user.id).all())
    if asset_key in portfolio_assets:
        portfolio_asset = portfolio_assets[asset_key]

        # Check that asset is liquid
        if not portfolio_asset.liquid:
            FLASHES.append(("error", "Asset is illiquid."))
            return
    else:
        portfolio_asset = PortfolioAsset(session["user"], stock_id, security, strike, 0, True)
        portfolio_assets[asset_key] = portfolio_asset
        db.session.add(portfolio_asset)

    qty = form.trade_qty.data
    is_buy = form.trade_position.data == "buy"

    # Check that sell/shortsell doesn't cross over 0
    if (not is_buy) and portfolio_asset.qty > 0 and qty > portfolio_asset.qty:
        FLASHES.append(("error", "You can't switch from a long position to a short one in the same day."))
        return


    if is_buy:
        # Subtract from cash
        ask = AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=TODAY).first().ask
        value = Decimal("1.004") * qty * ask
        user.cash -= value

        # Check that required amount of cash is present in portfolio
        if user.cash < 0:
            FLASHES.append(("error", "You don't have enough cash."))
            return

        # Add items to basket
        portfolio_asset.qty += qty

        # Update portfolio value
        user.portfolio += qty * (ask - Decimal("0.005")) - value
    else:
        # Add to cash
        bid = AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=TODAY).first().bid
        value = Decimal("0.996" if portfolio_asset.qty > 0 else "0.99") * qty * bid
        user.cash += value

        # Remove items from basket
        portfolio_asset.qty -= qty

        # Update portfolio value
        user.portfolio += value - qty * (bid + Decimal("0.005"))

    # Check whether margin would exceed $22 million:
    new_margin = 0
    for k, v in portfolio_assets.iteritems():
        if v.qty < 0 and k in asset_prices:
            new_margin += asset_prices[k] * (-v.qty)

    if new_margin > 22000000:
        FLASHES.append(("error", "Margin can't exceed $22 million."))
        return

    # Check that user would have 30%+ of margin in cash
    if new_margin > user.cash * Decimal("0.3"):
        FLASHES.append(("error", "Margin can't exceed 30% of cash."))
        return

    # Remove basket item if quantity is zero
    if portfolio_asset.qty == 0:
        db.session.delete(portfolio_asset)

    # Add transaction record
    db.session.add(Transaction(date=TODAY, user_id=user.id, is_buy=is_buy, stock_id=stock_id, security=security, strike=strike, qty=qty, value=value))

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

    # Add user
    db.session.add(User(email=form.reg_email.data, password=form.reg_password.data, first_name=form.reg_first.data, last_name=form.reg_last.data, institution=form.reg_institution.data, algorithm=algorithm))
    db.session.commit()
    session["user"] = User.query.filter_by(email=form.reg_email.data).first().id

    # Create user's portfolio
    create_portfolio(session["user"])
    db.session.commit()
    FLASHES.append(("success", "Registration successful! Feel free to test out functionality during the registration period before the real contest begins on 14 January."))

def generate_js(user):
    js = ""

    authenticated = user > 0

    if authenticated:
        # Get portfolio assets
        portfolio_assets = dict(((a.stock_id, a.security, a.strike), (a.qty, 1 if a.liquid else 0)) for a in PortfolioAsset.query.filter_by(user_id=user).all())

        # Generate tracking error table
        terrors = [[], [], []]

        terror_dict = dict()
        for t in Terror.query.filter_by(user_id=user).order_by(Terror.date).all():
            terror_dict[t.date.strftime("%Y-%m-%d")] = int(t.terror)

        day = CONTEST_FIRST_DAY
        i = 0
        cum_error = 0
        while day != DAY_AFTER_CONTEST:
            terrors[0].append(i)
            terrors[1].append(pretty_print(day))

            if day in terror_dict:
                terrors[2].append(terror_dict[day])
                cum_error += terror_dict[day]
            else:
                terrors[2].append(0)

            day = day_after(day)
            i += 1

        # Get transaction history for today
        transactions = [[1 if t.is_buy else 0, t.stock_id, t.security, str(t.strike), int(t.qty), "%.2f" % float(t.value)] for t in Transaction.query.filter_by(user_id=user, date=TODAY).all()]

        js = "CUMTERROR=" + str(cum_error) + ";TERRORS=" + str(terrors) + ";TRANSACTIONS=" + str(transactions) + ";"

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

def create_portfolio(user_id):
    db.session.add_all([
        PortfolioAsset(user_id, 5, 0, -1, 250000, False),
        PortfolioAsset(user_id, 5, 1, 14, 300000, False),
        PortfolioAsset(user_id, 8, 1, 49, -100000, False),
        PortfolioAsset(user_id, 8, 2, 55, 600000, False),
        PortfolioAsset(user_id, 8, 2, 56, 1000000, False),
        PortfolioAsset(user_id, 16, 1, 176, 1000000, False),
        PortfolioAsset(user_id, 16, 1, 177, 300000, False),
        PortfolioAsset(user_id, 2, 0, -1, -3000, False),
        PortfolioAsset(user_id, 7, 1, 46, 200000, False),
        PortfolioAsset(user_id, 7, 2, 50, -100000, False),
        PortfolioAsset(user_id, 7, 2, 51, -50000, False),
        PortfolioAsset(user_id, 29, 2, 96, 400000, False),
        PortfolioAsset(user_id, 29, 2, 97, 500000, False),
        PortfolioAsset(user_id, 29, 2, 98, 1000000, False),
        PortfolioAsset(user_id, 13, 0, -1, 100000, False),
        PortfolioAsset(user_id, 13, 1, 23, 400000, False),
        PortfolioAsset(user_id, 13, 1, 24, 500000, False),
        PortfolioAsset(user_id, 26, 1, 40, 500000, False),
        PortfolioAsset(user_id, 26, 2, 43, 600000, False),
        PortfolioAsset(user_id, 14, 1, 33, 600000, False),
        PortfolioAsset(user_id, 14, 1, 34, 800000, False),
        PortfolioAsset(user_id, 14, 1, 35, 1000000, False),
        PortfolioAsset(user_id, 1, 0, -1, 400000, False),
        PortfolioAsset(user_id, 1, 1, 8.5, -300000, False),
        PortfolioAsset(user_id, 15, 0, -1, 3000, False),
        PortfolioAsset(user_id, 17, 0, -1, 52000, False)])

def pretty_print(datetext):
    return time.strftime("%d %B", time.strptime(datetext, "%Y-%m-%d"))

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
