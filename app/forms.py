from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField, SubmitField, DecimalField, RadioField, validators, ValidationError, PasswordField

from app import db, app
from models import User, Stock, AssetPrice

class RegForm(Form):
    reg_email = TextField("Email", [
        validators.InputRequired("Please enter your email address."),
        validators.Email("Please enter your email address.")])
    reg_first = TextField("First Name", [
        validators.InputRequired("Please enter your first name.")])
    reg_last = TextField("Last Name", [
        validators.InputRequired("Please enter your last name.")])
    reg_institution = TextField("Institution", [
        validators.InputRequired("Please enter your institution.")])
    reg_password = PasswordField("Password", [
        validators.InputRequired("Please enter a password.")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        if User.query.filter_by(email=self.reg_email.data.lower()).first():
            self.reg_email.errors.append("That email is already taken")
            return False
        else:
            return True

class LoginForm(Form):
    login_email = TextField("Email", [
        validators.InputRequired("Please enter your email address."),
        validators.Email("Please enter your email address.")])
    login_password = PasswordField("Password", [
        validators.InputRequired("Please enter a password.")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email = self.login_email.data.lower()).first()
        if user and user.check_password(self.login_password.data):
            return True
        else:
            self.login_email.errors.append("Invalid e-mail or password")
            return False

class TradeForm(Form):
    stocks = [(s.id, s.symbol) for s in Stock.query.all()]
    assets = AssetPrice.query.filter_by(date="2013-08-16").all()
    trade_stock = SelectField("Symbol", [validators.InputRequired("Please choose a stock")], coerce=int, choices=stocks)
    trade_asset = SelectField("Asset", [validators.InputRequired("Please choose an asset")], coerce=str, choices=[(("1" if a.is_call else "0") + "," + str(a.strike), ("1" if a.is_call else "0") + "," + str(a.strike)) for a in assets])
    trade_qty = DecimalField("Quantity", [validators.InputRequired("Enter a quantity.")])
    trade_position = RadioField("Action", [validators.InputRequired("Enter a position")], choices=[("buy", "Buy"), ("sell", "Sell")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        return True
