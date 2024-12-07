from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    year = SelectField('Year', choices=[
                       (7), (8), (9), (10), (11), (12), (13)], validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    year = SelectField('Year', choices=[
                       (7), (8), (9), (10), (11), (12), (13)], validators=[DataRequired()])
    # type = SelectField('Type', choices=[('article', 'Article'), ('newsletter', 'Newsletter')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    maths_class = StringField('Maths Class', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, first_name, last_name):
        user = User.query.filter(
            first_name == first_name.data,
            last_name == last_name.data
        ).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
