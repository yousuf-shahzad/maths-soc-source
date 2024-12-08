"""
Authentication Forms Module
==========================

This module defines Flask-WTF forms for user authentication processes,
including login and registration.

Key Form Classes:
----------------
- LoginForm: For user login authentication
- RegistrationForm: For new user account registration

Dependencies:
------------
- Flask-WTF for form handling
- WTForms for form field and validation
- Custom User model for validation

Security Considerations:
----------------------
1. Validates required fields
2. Implements password confirmation
3. Checks for existing usernames during registration
4. Includes CSRF protection (default in FlaskForm)

Maintenance Notes:
-----------------
1. Ensure form validators are comprehensive
2. Update year choices as academic years change
3. Validate and sanitize user inputs server-side
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """
    Form for user login authentication.

    Fields:
    -------
    first_name : StringField
        User's first name (required)
    last_name : StringField
        User's last name (required)
    password : PasswordField
        User's password (required)
    year : SelectField
        User's current academic year (7-13)
    remember_me : BooleanField
        Option to maintain user session
    submit : SubmitField
        Button to submit login credentials
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    year = SelectField(
        "Year",
        choices=[
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
        ],
        validators=[DataRequired()],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """
    Form for creating a new user account.

    Fields:
    -------
    first_name : StringField
        User's first name (required)
    last_name : StringField
        User's last name (required)
    year : SelectField
        User's current academic year (7-13)
    password : PasswordField
        User's chosen password (required)
    password2 : PasswordField
        Password confirmation (must match password)
    maths_class : StringField
        User's mathematics class (required)
    submit : SubmitField
        Button to submit registration

    Methods:
    --------
    validate_username(first_name, last_name)
        Custom validation to prevent duplicate usernames
    """

    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    year = SelectField(
        "Year",
        choices=[
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10", "10"),
            ("11", "11"),
            ("12", "12"),
            ("13", "13"),
        ],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    maths_class = StringField("Maths Class", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_username(self, first_name, last_name):
        """
        Validate that the username (first name + last name) is unique.

        Args:
        -----
        first_name : StringField
            First name field to validate
        last_name : StringField
            Last name field to validate

        Raises:
        -------
        ValidationError
            If a user with the same first and last name already exists
        """
        user = User.query.filter(
            first_name == first_name.data, last_name == last_name.data
        ).first()
        if user is not None:
            raise ValidationError("Please use a different username.")
