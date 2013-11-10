from werkzeug import generate_password_hash, check_password_hash

from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    cash = db.Column(db.Numeric)
    margin = db.Column(db.Numeric)

    def __init__(self, email, password):
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, plaintext):
        self.password = generate_password_hash(plaintext)

    def check_password(self, plaintext):
        return check_password_hash(self.password, plaintext)

class Stock(db.Model):
    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text, unique=True)

class StockPrice(db.Model):
    __tablename__ = "stock_prices"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    stock_id = db.Column(db.Integer)
    bid = db.Column(db.Numeric)
    ask = db.Column(db.Numeric)

class BasketItem(db.Model):
    __tablename__ = "basket_items"

    def __init__(self, user_id, stock_id, is_call, strike, qty):
        self.user_id = user_id
        self.stock_id = stock_id
        self.is_call = is_call
        self.strike = strike
        self.qty = qty

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    stock_id = db.Column(db.Integer)
    is_call = db.Column(db.Boolean)
    strike = db.Column(db.Numeric)
    qty = db.Column(db.Numeric)
