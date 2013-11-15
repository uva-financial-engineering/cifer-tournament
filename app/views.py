from __future__ import division

import os
import math
import time
from datetime import date, timedelta
from decimal import Decimal

from flask import render_template, flash, g, redirect, request, session, send_from_directory, url_for

from app import app, db
from models import User, Stock, AssetPrice, PortfolioAsset, Terror
from forms import RegForm, LoginForm, TradeForm

# Constants

TODAY = "2013-08-16"
LAST_WEEKDAY = "2013-08-16"
RATE = Decimal("1.0000273976355823353284453")
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
            return index()
        elif action == "trade" and tradeform.validate():
            security = tradeform.trade_asset.data.split(",")[0]
            strike = tradeform.trade_asset.data.split(",")[1]
            stock_id = tradeform.trade_asset.data.split(",")[2]

            # Get basket item (or create it if nonexistent)
            portfolio_asset = PortfolioAsset.query.filter_by(user_id=session["user"], stock_id=stock_id, security=security, strike=strike).first()
            if portfolio_asset is None:
                portfolio_asset = PortfolioAsset(session["user"], stock_id, security, strike, 0)
                db.session.add(portfolio_asset)

            if tradeform.trade_position.data == "buy":
                # Subtract from cash
                user.cash -= Decimal("1.004") * tradeform.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().ask

                # Add items to basket
                portfolio_asset.qty += tradeform.trade_qty.data
            else:
                # Add to cash
                user.cash += Decimal("0.996" if portfolio_asset.qty > 0 else "0.99") * tradeform.trade_qty.data * AssetPrice.query.filter_by(stock_id=stock_id, security=security, strike=strike, date=LAST_WEEKDAY).first().bid

                # Remove items from basket
                portfolio_asset.qty -= tradeform.trade_qty.data

            # Remove basket item if quantity is zero
            if portfolio_asset.qty == 0:
                db.session.delete(portfolio_asset)

            # Save to database
            db.session.commit()

        # Generate stock table
        stocks = dict((s.id, (s.symbol, s.sector)) for s in Stock.query.all())
        assets = AssetPrice.query.filter_by(date=LAST_WEEKDAY).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all()
        app.logger.debug("Time: " + str(time.time() - g.start))
        portfolio_assets = dict(((a.stock_id, a.security, a.strike), a.qty) for a in PortfolioAsset.query.filter_by(user_id=session["user"]).all())

        for asset in assets:
            asset.symbol, asset.sector = stocks[asset.stock_id]

            if asset.security == Security.STOCK:
                asset.name = "Stock"
            elif asset.security == Security.CALL:
                asset.name = str(asset.strike) + " Call"
            else:
                asset.name = str(asset.strike) + " Put"

            # Add portfolio data
            if (asset.stock_id, asset.security, asset.strike) in portfolio_assets:
                basket_shares = portfolio_assets[(asset.stock_id, asset.security, asset.strike)]
                asset.shares = basket_shares
                asset.value = basket_shares * (asset.bid + Decimal("0.005"))
            else:
                asset.shares = 0
                asset.value = 0

        # Generate tracking error table
        terrors = []
        for terror in Terror.query.filter_by(user_id=session["user"]).order_by(Terror.date).all():
            terrors.append((terror.date, terror.terror))

        flash_errors(tradeform)
        return render_template("index.html", user=user, date=TODAY, assets=assets, tradeform=tradeform, terrors=terrors)
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

        stocks = dict((s.id, (s.symbol, s.sector)) for s in Stock.query.all())
        assets = AssetPrice.query.filter_by(date=LAST_WEEKDAY).order_by(AssetPrice.security, AssetPrice.stock_id, AssetPrice.strike).all()

        for asset in assets:
            asset.symbol, asset.sector = stocks[asset.stock_id]

            if asset.security == Security.STOCK:
                asset.name = "Stock"
            elif asset.security == Security.CALL:
                asset.name = str(asset.strike) + " Call"
            else:
                asset.name = str(asset.strike) + " Put"

        flash_errors(regform)
        flash_errors(loginform)
        return render_template("login.html", regform=regform, loginform=loginform, assets=assets)

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

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")
