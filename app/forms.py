from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField, SubmitField, DecimalField, RadioField, validators, ValidationError, PasswordField, HiddenField

from app import db, app
from models import User, AssetPrice

class RegForm(Form):
    reg_email = TextField("Email", [
        validators.InputRequired("Email address required."),
        validators.Email("Not a valid email address.")])
    reg_first = TextField("First Name", [
        validators.InputRequired("First name required.")])
    reg_last = TextField("Last Name", [
        validators.InputRequired("Last name required.")])
    reg_institution = TextField("Institution", [
        validators.InputRequired("Institution required.")])
    reg_password = PasswordField("Password", [
        validators.InputRequired("Password required.")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

class LoginForm(Form):
    login_email = TextField("Email", [
        validators.InputRequired("Email address missing."),
        validators.Email("Not a valid email.")])
    login_password = PasswordField("Password", [
        validators.InputRequired("Password missing.")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

class TradeForm(Form):
    assets = AssetPrice.query.filter_by(date="2013-08-16").all()
    trade_asset = HiddenField("Asset", [validators.InputRequired("No asset chosen.")])
    trade_qty = DecimalField("Quantity", [validators.InputRequired("No quantity chosen.")])
    trade_position = RadioField("Action", [validators.InputRequired("No action chosen.")], choices=[("buy", "Buy"), ("sell", "Sell")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
