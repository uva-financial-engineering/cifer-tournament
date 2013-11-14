from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object("configheroku")

db = SQLAlchemy(app)
CsrfProtect(app)

from app import views, models, forms
