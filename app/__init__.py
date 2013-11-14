import os

from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.jinja_env.add_extension("jinja2htmlcompress.HTMLCompress")

# Load config file based on environment
if "DYNO" in os.environ:
    app.config.from_object("configheroku")
else:
    app.config.from_object("config")

db = SQLAlchemy(app)
CsrfProtect(app)

from app import views, models, forms
