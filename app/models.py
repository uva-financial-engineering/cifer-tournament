from werkzeug import generate_password_hash, check_password_hash

from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    institution = db.Column(db.Text)
    cash = db.Column(db.Numeric)
    portfolio = db.Column(db.Numeric)
    algorithm = db.Column(db.Boolean)

    def __init__(self, email, password, first_name, last_name, institution, algorithm):
        self.email = email.lower()
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.institution = institution
        self.cash = 18000000
        self.algorithm = algorithm

    def set_password(self, plaintext):
        self.password = generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return check_password_hash(self.password, plaintext)

class Stock(db.Model):
    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text, unique=True)
    sector = db.Column(db.Text)

class AssetPrice(db.Model):
    __tablename__ = "asset_prices"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    stock_id = db.Column(db.Integer)
    security = db.Column(db.SmallInteger)
    strike = db.Column(db.Numeric)
    bid = db.Column(db.Numeric)
    ask = db.Column(db.Numeric)

class PortfolioAsset(db.Model):
    __tablename__ = "portfolio_assets"

    def __init__(self, user_id, stock_id, security, strike, qty, liquid):
        self.user_id = user_id
        self.stock_id = stock_id
        self.security = security
        self.strike = strike
        self.qty = qty
        self.liquid = liquid

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    stock_id = db.Column(db.Integer)
    security = db.Column(db.SmallInteger)
    strike = db.Column(db.Numeric)
    qty = db.Column(db.Numeric)
    liquid = db.Column(db.Boolean)

class Terror(db.Model):
    __tablename__ = "terrors"

    def __init__(self, date, user_id, terror):
        self.date = date
        self.user_id = user_id
        self.terror = terror

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)
    terror = db.Column(db.Numeric)

class Transaction(db.Model):
    __tablename__ = "transactions"

    def __init__(self, date, user_id, is_buy, stock_id, security, strike, qty, value):
        self.date = date
        self.user_id = user_id
        self.is_buy = is_buy
        self.stock_id = stock_id
        self.security = security
        self.strike = strike
        self.qty = qty
        self.value = value

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)
    is_buy = db.Column(db.Boolean)
    stock_id = db.Column(db.Integer)
    security = db.Column(db.SmallInteger)
    strike = db.Column(db.Numeric)
    qty = db.Column(db.Numeric)
    value = db.Column(db.Numeric)
