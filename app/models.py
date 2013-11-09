from werkzeug import generate_password_hash, check_password_hash

from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)

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
