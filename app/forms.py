from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, SubmitField, validators, ValidationError, PasswordField

from app import db, app
from models import User

class RegForm(Form):
    reg_email = TextField("Email", [
        validators.Required("Please enter your email address."),
        validators.Email("Please enter your email address.")])
    reg_password = PasswordField("Password", [
        validators.Required("Please enter a password.")])
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
        validators.Required("Please enter your email address."),
        validators.Email("Please enter your email address.")])
    login_password = PasswordField("Password", [
        validators.Required("Please enter a password.")])
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
