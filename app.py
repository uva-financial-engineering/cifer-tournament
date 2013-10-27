from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager


# Config

SECRET_KEY = "TODO-change-this"
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/cifer"
USERNAME = "postgres"
PASSWORD = "postgres"

# Initialization

app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)

# Models

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class Stock(db.Model):
    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text, unique=True)
    name = db.Column(db.Text)
    bid = db.Column(db.Numeric)
    ask = db.Column(db.Numeric)

# Views

@app.route("/")
def index():
    stocks = Stock.query.all()

    return render_template("index.html", stocks=stocks)

if __name__ == "__main__":
    app.run(debug=True)
