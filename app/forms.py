from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import FileField, RadioField, StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Optional
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from app import db
from app.models import User
import sqlalchemy as sa

class LoginForm(FlaskForm):


    
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired(),validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.DataRequired(),validators.Email()])
    first_name = StringField('First_name', [validators.DataRequired()])
    last_name = StringField('First_name', [validators.DataRequired()])
    password = PasswordField('Password',  [validators.DataRequired()])
    confirmPassword = PasswordField('Repeat Password', [validators.InputRequired(),
        validators.EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Username already in use. Choose a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')
        






class ChangeEmailForm(FlaskForm):
    email = StringField('New Email:', validators=[DataRequired(), Email()])
    submit = SubmitField('Change Email')

    def validate_email(self, email):
        if email.data == current_user.email:
            raise ValidationError('This is your current email address. Please choose a different one.')

        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email address already in use. Choose a different email.')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password:', validators=[DataRequired()])
    new_password = PasswordField('New Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password:', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')

    def validate_old_password(self, old_password):
        if not current_user.check_password(old_password.data):
            raise ValidationError('Incorrect old password. Please try again.')
        
        
class ChangeProfilePicForm(FlaskForm):
    profile_pic = RadioField('Select Profile Picture', choices=[
        ('man2.png', 'man2.png'),
        ('chicken.png', 'chicken.png'),
        ('dog.png', 'dog.png'),
        ('doof.png', 'doof.png'),
        ('man.png', 'man.png'),
        ('woman.png', 'woman.png'),
        ('woman2.png', 'woman2.png')
    ], coerce=str)
    submit = SubmitField('Change Profile Picture')
     