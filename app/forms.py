from flask.ext.wtf import Form
from wtforms import (validators, TextField, SubmitField, DecimalField,
    RadioField, PasswordField, HiddenField)

class RegForm(Form):
    reg_email = TextField("Email", [
        validators.InputRequired("Email address required."),
        validators.Email("Not a valid email address.")])
    reg_first = TextField("First Name", [
        validators.Length(1, 20, "Invalid first name length."),
        validators.InputRequired("First name required.")])
    reg_last = TextField("Last Name", [
        validators.Length(1, 40, "Invalid last name length."),
        validators.InputRequired("Last name required.")])
    reg_institution = TextField("Institution", [
        validators.Length(1, 40, "Invalid institution name length."),
        validators.InputRequired("Institution required.")])
    reg_password = PasswordField("Password", [
        validators.InputRequired("Password required.")])
    reg_password2 = PasswordField("Repeat Password", [
        validators.EqualTo("reg_password", "Passwords don't match."),
        validators.InputRequired("Please repeat your password.")])
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
        validators.AnyOf(["0", "1", "2"], "Invalid asset type."),
        validators.InputRequired("No security type chosen.")])
    trade_strike = HiddenField("Strike", [
        validators.InputRequired("No strike price chosen.")])
    trade_stock_id = HiddenField("Stock", [
        validators.InputRequired("No stock symbol chosen.")])
    trade_qty = DecimalField("Quantity", [
        validators.NumberRange(min=1, message="Quantity must be positive."),
        validators.InputRequired("No quantity chosen.")])
    trade_position = RadioField("Action", [
        validators.AnyOf(["buy", "sell"], "Invalid action."),
        validators.InputRequired("No action chosen.")],
        choices=[("buy", "Buy"), ("sell", "Sell")])
