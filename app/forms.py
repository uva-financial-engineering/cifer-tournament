from flask.ext.wtf import Form
from wtforms import (validators, TextField, SubmitField, DecimalField,
    RadioField, PasswordField, HiddenField)

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
    reg_algorithm = RadioField("Algorithm",
        choices=[("yes", "Yes"), ("no", "No"), ("maybe", "Maybe")])

class LoginForm(Form):
    login_email = TextField("Email", [
        validators.InputRequired("Email address missing."),
        validators.Email("Not a valid email.")])
    login_password = PasswordField("Password", [
        validators.InputRequired("Password missing.")])

class TradeForm(Form):
    trade_security = HiddenField("Security", [
        validators.InputRequired("No security type chosen.")])
    trade_strike = HiddenField("Strike", [
        validators.InputRequired("No strike price chosen.")])
    trade_stock_id = HiddenField("Stock", [
        validators.InputRequired("No stock symbol chosen.")])
    trade_qty = DecimalField("Quantity", [
        validators.InputRequired("No quantity chosen.")])
    trade_position = RadioField("Action", [
        validators.InputRequired("No action chosen.")],
        choices=[("buy", "Buy"), ("sell", "Sell")])
