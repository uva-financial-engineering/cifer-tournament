from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SelectField, SubmitField, DecimalField, RadioField, validators, ValidationError, PasswordField

from app import db, app
from models import User, Stock, AssetPrice

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
        validators.InputRequired("Email address missing."),
        validators.Email("Not a valid email.")])
    login_password = PasswordField("Password", [
        validators.InputRequired("Password missing.")])
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
            self.login_email.errors.append("Invalid email or password.")
            return False

class TradeForm(Form):
    assets = AssetPrice.query.filter_by(date="2013-08-16").all()
    trade_asset = TextField("Asset", [validators.InputRequired("No asset chosen.")])
    trade_qty = DecimalField("Quantity", [validators.InputRequired("Enter a quantity.")])
    trade_position = RadioField("Action", [validators.InputRequired("Enter a position.")], choices=[("buy", "Buy"), ("sell", "Sell")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        return True
