from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import (g, render_template, flash, redirect, request, session,
    send_from_directory, url_for)

from app import app, db
from models import Variable, User, Stock, AssetPrice, PortfolioAsset, Terror, Transaction
from forms import RegForm, LoginForm, TradeForm

# Constants

class Security:
    STOCK, CALL, PUT = range(3)

RATE = Decimal("1.00002739763558")
INITIAL_VALUE = Decimal("53709280")
FLASHES = [] # (category, message) tuples

# Routes

@app.before_request
def before_request():
    variables = Variable.query.first()

    g.status = variables.status
    g.today = variables.today
    g.contest_first_day = variables.contest_first_day
    g.last_weekday = variables.last_weekday
    g.day_after_contest = variables.day_after_contest

@app.route("/", methods=["GET", "POST"])
def index():
    """Main page that serves as both login screen and app screen."""

    # Create debug user if no users exist
    if not User.query.all():
        new_user = User("a@a.com", "a", "John", "Doe", "University of Virginia", True)
        db.session.add(new_user)
        create_portfolio(new_user, 1)
        db.session.commit()
        session["user"] = 1

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
                date=pretty_print(g.today),
                target=get_target() * RATE if g.status == "during" else None,
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

    # Calculate new date
    yesterday = g.today
    g.today = day_after(g.today)
    variables = Variable.query.first()
    variables.today = g.today

    if g.status == "before":
        if g.today == g.contest_first_day:
            variables.status = "during"

    elif g.status == "during":
        if g.today == g.day_after_contest:
            variables.status = "after"

        # Add interest to cash, then record it
        portfolio_values = dict()
        users = dict()
        for user in User.query.all():
            users[user.id] = user
            user.cash *= RATE
            portfolio_values[user.id] = user.cash

        # Calculate most recent weekday
        asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=g.today).all())

        if len(asset_prices):
            g.last_weekday = g.today
            variables.last_weekday = g.last_weekday
        else:
            asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=g.last_weekday).all())

        # Add value of basket items
        for portfolio_asset in PortfolioAsset.query.all():
            price_key = (portfolio_asset.stock_id, portfolio_asset.security, portfolio_asset.strike)
            portfolio_values[portfolio_asset.user_id] += portfolio_asset.qty * (asset_prices[price_key] if price_key in asset_prices else 0)

        # Store tracking errors
        target = get_target()
        for user, value in portfolio_values.iteritems():
            users[user].portfolio = value
            terror = target - value if value < target else (value - target) * Decimal("0.5")
            db.session.add(Terror(yesterday, user, terror))
    else:
        pass

    db.session.commit()
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

    if g.status == "before":
        FLASHES.append(("error", "Contest begins on " + pretty_print(g.contest_first_day) + "."))
        return

    if g.status == "after":
        FLASHES.append(("error", "Contest is over."))
        return

    if not form.validate():
        flash_errors(form)
        return

    # Check that market is open
    if g.today != g.last_weekday:
        FLASHES.append(("error", "The market is closed today."))
        return

    stock_id = int(form.trade_stock_id.data)
    security = int(form.trade_security.data)
    strike = Decimal(form.trade_strike.data)
    asset_key = (stock_id, security, strike)

    # Check that user didn't already trade asset today
    if asset_key in [(t.stock_id, t.security, t.strike) for t in Transaction.query.filter_by(user_id=user.id, date=g.today).all()]:
        FLASHES.append(("error", "You can't trade the same asset multiple times in the same day."))
        return

    asset_prices = dict(((a.stock_id, a.security, a.strike), a.bid + Decimal("0.005")) for a in AssetPrice.query.filter_by(date=g.today).all())

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

    if is_buy:
        # Subtract from cash
        ask = AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=g.today).first().ask
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
        # Check that sell doesn't cause quantity to cross over 0
        if portfolio_asset.qty > 0 and qty > portfolio_asset.qty:
            FLASHES.append(("error", "You can't switch from a long position to a short one in the same day."))
            return

        # Add to cash
        bid = AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=g.today).first().bid
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

    if new_margin > 22000000 and (not is_buy) and portfolio_asset.qty < 0:
        FLASHES.append(("error", "Margin can't exceed $22 million."))
        return

    # Check that user would have 30%+ of margin in cash
    if new_margin * Decimal("0.3") > user.cash and (is_buy or portfolio_asset.qty < 0):
        FLASHES.append(("error", "Held cash must exceed 30% of short sold assets' value."))
        return

    # Remove basket item if quantity is zero
    if portfolio_asset.qty == 0:
        db.session.delete(portfolio_asset)

    # Add transaction record
    db.session.add(Transaction(date=g.today, user_id=user.id, is_buy=is_buy, stock_id=stock_id, security=security, strike=strike, qty=qty, value=value))

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
        FLASHES.append(("error", "That email is already taken."))
        return

    if form.reg_algorithm.data == "yes":
        algorithm = True
    elif form.reg_algorithm.data == "no":
        algorithm = False
    else:
        algorithm = None

    # Add user
    new_user = User(email=form.reg_email.data, password=form.reg_password.data, first_name=form.reg_first.data, last_name=form.reg_last.data, institution=form.reg_institution.data, algorithm=algorithm)
    db.session.add(new_user)
    db.session.commit()
    session["user"] = User.query.filter_by(email=form.reg_email.data).first().id

    # Create user's portfolio
    create_portfolio(new_user, session["user"])
    db.session.commit()
    FLASHES.append(("success", "Registration successful! Feel free to test out functionality during the registration period before the real contest begins on 14 January."))

def generate_js(user):
    js = ""

    authenticated = user > 0
    asset_prices = AssetPrice.query.filter_by(date=g.last_weekday).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all()

    if authenticated:
        # Build portfolio table
        portfolio = []
        asset_prices_dict = dict(((a.stock_id, a.security, a.strike), a) for a in asset_prices)
        portfolio_assets = PortfolioAsset.query.filter_by(user_id=user).order_by(PortfolioAsset.security, PortfolioAsset.stock_id, PortfolioAsset.strike).all()
        portfolio_assets_dict = dict(((a.stock_id, a.security, a.strike), a) for a in portfolio_assets)
        for v in portfolio_assets:
            price = (asset_prices_dict[(v.stock_id, v.security, v.strike)].bid + Decimal("0.005")) if ((v.stock_id, v.security, v.strike) in asset_prices_dict) else 0
            portfolio.append([v.stock_id, 1 if v.liquid else 0, v.security, str(v.strike), int(v.qty), "%.2f" % float(v.qty * price)])

        # Generate tracking error table
        terrors = [[], [], []]

        terror_dict = dict()
        for t in Terror.query.filter_by(user_id=user).order_by(Terror.date).all():
            terror_dict[t.date.strftime("%Y-%m-%d")] = int(t.terror)

        day = g.contest_first_day
        i = 0
        cum_error = 0
        while day != g.day_after_contest:
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
        transactions = [[1 if t.is_buy else 0, t.stock_id, t.security, str(t.strike), int(t.qty), "%.2f" % float(t.value)] for t in Transaction.query.filter_by(user_id=user, date=g.today).all()]

        js = "CUMTERROR=" + str(cum_error) + ";TERRORS=" + str(terrors) + ";TRANSACTIONS=" + str(transactions) + ";PORTFOLIO=" + str(portfolio) + ";"

    # Build stock and options tables
    stocks = [[str(s.symbol), None, str(s.sector), None, None] for s in Stock.query.order_by(Stock.id).all()]
    options = []
    for v in asset_prices:
        liquid = 1

        if authenticated and (v.stock_id, v.security, v.strike) in portfolio_assets_dict and (not portfolio_assets_dict[(v.stock_id, v.security, v.strike)].liquid):
            liquid = 0

        if v.security == Security.STOCK:
            stocks[v.stock_id - 1][1] = liquid
            stocks[v.stock_id - 1][3] = "%.2f" % float(v.bid)
            stocks[v.stock_id - 1][4] = "%.2f" % float(v.ask)
        else:
            options.append([v.stock_id, liquid, v.security, float(v.strike), "%.2f" % float(v.bid), "%.2f" % float(v.ask)])

    return (js + "AUTHENTICATED=" + str(authenticated).lower() + ";STOCKS=" + str(stocks) + ";OPTIONS=" + str(options) + ";").replace(", ", ",")

def day_after(datetext):
    t = time.strptime(datetext, "%Y-%m-%d")
    return (date(t.tm_year, t.tm_mon, t.tm_mday) + timedelta(1)).strftime("%Y-%m-%d")

def create_portfolio(user, user_id):
    portfolio_assets = [
        (5, 0, -1, 250000),
        (5, 1, 14, 300000),
        (8, 1, 49, -100000),
        (8, 2, 55, 600000),
        (8, 2, 56, 1000000),
        (16, 1, 176, 1000000),
        (16, 1, 177, 300000),
        (2, 0, -1, -3000),
        (7, 1, 46, 200000),
        (7, 2, 50, -100000),
        (7, 2, 51, -50000),
        (29, 2, 96, 400000),
        (29, 2, 97, 500000),
        (29, 2, 98, 1000000),
        (13, 0, -1, 100000),
        (13, 1, 23, 400000),
        (13, 1, 24, 500000),
        (26, 1, 40, 500000),
        (26, 2, 43, 600000),
        (14, 1, 33, 600000),
        (14, 1, 34, 800000),
        (14, 1, 35, 1000000),
        (1, 0, -1, 400000),
        (1, 1, 8.5, -300000),
        (15, 0, -1, 3000),
        (17, 0, -1, 52000)]
    db.session.add_all([PortfolioAsset(user_id, a[0], a[1], a[2], a[3], False) for a in portfolio_assets])

    asset_bids = dict(((a.stock_id, a.security, a.strike), a.bid) for a in AssetPrice.query.filter_by(date=g.last_weekday).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all())
    portfolio_value = 18000000
    for a in portfolio_assets:
        if (a[0], a[1], a[2]) in asset_bids:
            portfolio_value += a[3] * (asset_bids[(a[0], a[1], a[2])] + Decimal("0.005"))
    user.portfolio = portfolio_value

def pretty_print(datetext):
    return time.strftime("%d %B", time.strptime(datetext, "%Y-%m-%d"))

def get_target():
    if g.status == "during":
        day = g.contest_first_day
        power = 0
        while day != g.today:
            power += 1
            day = day_after(day)
        return INITIAL_VALUE * (RATE ** power)

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
