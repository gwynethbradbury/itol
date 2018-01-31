from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
# from ..models import User


# class LoginForm(FlaskForm):
#     user = StringField('Username', validators=[Required(), Length(1, 10)])
#     password = PasswordField('Password', validators=[Required(), Length(7, 30)])
#     submit = SubmitField('Log In')
#
# class RescueReqForm(FlaskForm):
#     user = StringField('Username', validators=[Required(), Length(1, 10)])
#     email = StringField('Email', validators=[Required(), Length(7, 70)])
#     submit = SubmitField('Rescue My Account')
#
#
# class ActivateForm(FlaskForm):
#     user = StringField('Username', validators=[Required(), Length(1, 10)])
#     email = StringField('Email Address', validators=[Required(), Length(1, 70)])
#     actcode = StringField ('Activation Code', validators=[Required(), Length(35)])
#     password = PasswordField('Password', validators=[
#         Required(), Length(7,15), EqualTo('password2', message='Passwords must match.')])
#     password2 = PasswordField('Confirm password', validators=[Required()])
#     submit = SubmitField('Activate Account')

class ChangePWForm(FlaskForm):
    # user = StringField('Username', validators=[Required()])#, Length(1, 10)])
    oldpw = PasswordField ('Old Password', validators=[Required(), Length(7,15)])
    password = PasswordField('New Password', validators=[
        Required(), Length(7,15), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Change Password')
